#!/usr/bin/env python3
"""
Energy Analysis Script for Solar+Battery System Sizing

Queries Home Assistant's REST API to analyze energy consumption vs solar generation,
then recommends battery capacity and inverter sizing for off-grid autonomy.
"""

import argparse
import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

try:
    import requests
except ImportError:
    print("Error: 'requests' library required. Install with: pip install requests")
    sys.exit(1)

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# Load .env from the parent directory (home-assistant/.env)
ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
if load_dotenv and os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
elif os.path.exists(ENV_PATH):
    # Fallback: parse .env manually if python-dotenv is not installed
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


ENERGY_KEYWORDS = {
    "consumption": ["grid", "consumption", "load", "total_energy", "import", "consumed"],
    "generation": ["solar", "pv", "generation", "production", "export", "inverter", "growatt"],
    "battery": ["battery", "soc", "charge", "discharge"],
}
ENERGY_UNITS = {"kWh", "Wh", "W", "kW"}


class EnergyAnalyzer:
    def __init__(self, base_url, token):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _get(self, path, params=None, timeout=30):
        url = f"{self.base_url}{path}"
        resp = requests.get(url, headers=self.headers, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    def discover_energy_entities(self):
        """Discover and categorize energy-related entities."""
        states = self._get("/api/states")
        categories = {"consumption": [], "generation": [], "battery": [], "power": []}

        for entity in states:
            eid = entity.get("entity_id", "")
            attrs = entity.get("attributes", {})
            friendly = attrs.get("friendly_name", "").lower()
            unit = attrs.get("unit_of_measurement", "")
            device_class = attrs.get("device_class", "")
            state_class = attrs.get("state_class", "")

            if unit not in ENERGY_UNITS and device_class not in ("energy", "power"):
                continue

            eid_lower = eid.lower()
            search_text = f"{eid_lower} {friendly}"
            info = {
                "entity_id": eid,
                "friendly_name": attrs.get("friendly_name", eid),
                "state": entity.get("state"),
                "unit": unit,
                "device_class": device_class,
                "state_class": state_class,
            }

            categorized = False
            for category, keywords in ENERGY_KEYWORDS.items():
                if any(kw in search_text for kw in keywords):
                    categories[category].append(info)
                    categorized = True
                    break

            if not categorized and unit in ("W", "kW"):
                categories["power"].append(info)
            elif not categorized:
                categories["consumption"].append(info)

        return categories

    def fetch_history(self, entity_id, days):
        """Fetch historical state data, chunked into 7-day windows."""
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days)
        all_history = []

        chunk_start = start
        while chunk_start < now:
            chunk_end = min(chunk_start + timedelta(days=7), now)
            start_iso = chunk_start.strftime("%Y-%m-%dT%H:%M:%S+00:00")
            end_iso = chunk_end.strftime("%Y-%m-%dT%H:%M:%S+00:00")

            path = f"/api/history/period/{start_iso}"
            params = {
                "filter_entity_id": entity_id,
                "end_time": end_iso,
                "minimal_response": "",
                "significant_changes_only": "1",
            }

            try:
                data = self._get(path, params=params, timeout=60)
                if data and len(data) > 0:
                    all_history.extend(data[0])
            except requests.exceptions.RequestException as e:
                print(f"  Warning: Failed to fetch {start_iso[:10]} to {end_iso[:10]}: {e}")

            chunk_start = chunk_end

        # Filter valid numeric entries
        valid = []
        for entry in all_history:
            state = entry.get("state", "")
            if state in ("unknown", "unavailable", ""):
                continue
            try:
                val = float(state)
                ts_str = entry.get("last_changed") or entry.get("last_updated", "")
                if not ts_str:
                    continue
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                valid.append({"value": val, "timestamp": ts})
            except (ValueError, TypeError):
                continue

        valid.sort(key=lambda x: x["timestamp"])
        return valid

    def process_cumulative_sensor(self, history):
        """Process total_increasing sensor (kWh meter) into daily/hourly data."""
        if len(history) < 2:
            return [], {}

        daily = defaultdict(float)
        hourly = defaultdict(lambda: defaultdict(float))

        for i in range(1, len(history)):
            prev = history[i - 1]
            curr = history[i]
            delta = curr["value"] - prev["value"]

            # Negative delta = meter reset; use current value as the delta
            if delta < 0:
                delta = curr["value"]
            # Skip unreasonably large deltas (likely bad data)
            if delta > 100:
                continue

            date_key = curr["timestamp"].astimezone().strftime("%Y-%m-%d")
            hour = curr["timestamp"].astimezone().hour
            daily[date_key] += delta
            hourly[date_key][hour] += delta

        return daily, hourly

    def process_power_sensor(self, history, unit):
        """Process instantaneous power sensor (W/kW) into daily/hourly energy (kWh)."""
        if len(history) < 2:
            return {}, {}

        daily = defaultdict(float)
        hourly = defaultdict(lambda: defaultdict(float))
        multiplier = 1.0 if unit == "kW" else 0.001  # W -> kW

        for i in range(1, len(history)):
            prev = history[i - 1]
            curr = history[i]
            dt_hours = (curr["timestamp"] - prev["timestamp"]).total_seconds() / 3600

            # Skip gaps longer than 1 hour (likely sensor offline)
            if dt_hours > 1.0 or dt_hours <= 0:
                continue

            avg_power_kw = ((prev["value"] + curr["value"]) / 2) * multiplier
            energy_kwh = avg_power_kw * dt_hours

            if energy_kwh < 0:
                continue

            date_key = curr["timestamp"].astimezone().strftime("%Y-%m-%d")
            hour = curr["timestamp"].astimezone().hour
            daily[date_key] += energy_kwh
            hourly[date_key][hour] += energy_kwh

        return daily, hourly

    def process_entity(self, entity_info, days):
        """Fetch and process an entity based on its type."""
        eid = entity_info["entity_id"]
        state_class = entity_info.get("state_class", "")
        unit = entity_info.get("unit", "")

        print(f"  Fetching {days} days of history for {eid}...")
        history = self.fetch_history(eid, days)
        print(f"  Got {len(history)} data points")

        if not history:
            return {}, {}

        if state_class in ("total_increasing", "total") or unit in ("kWh", "Wh"):
            daily, hourly = self.process_cumulative_sensor(history)
            # Convert Wh to kWh
            if unit == "Wh":
                daily = {k: v / 1000 for k, v in daily.items()}
                hourly = {
                    d: {h: v / 1000 for h, v in hours.items()}
                    for d, hours in hourly.items()
                }
            return daily, hourly
        else:
            return self.process_power_sensor(history, unit)

    def compute_stats(self, daily, hourly):
        """Compute summary statistics from daily/hourly data."""
        if not daily:
            return None

        daily_values = list(daily.values())
        avg = sum(daily_values) / len(daily_values)
        max_day = max(daily_values)
        min_day = min(daily_values)

        # Hourly profile: average kWh per hour across all days
        hour_totals = defaultdict(list)
        for day_hours in hourly.values():
            for h in range(24):
                hour_totals[h].append(day_hours.get(h, 0))

        hourly_profile = {}
        for h in range(24):
            vals = hour_totals[h]
            hourly_profile[h] = sum(vals) / len(vals) if vals else 0

        peak_hour = max(hourly_profile, key=hourly_profile.get)
        peak_kwh = hourly_profile[peak_hour]

        return {
            "daily_avg_kwh": avg,
            "daily_max_kwh": max_day,
            "daily_min_kwh": min_day,
            "num_days": len(daily_values),
            "hourly_profile": hourly_profile,
            "peak_hour": peak_hour,
            "peak_hour_kwh": peak_kwh,
            "peak_hour_w": peak_kwh * 1000,
        }


def calculate_system(consumption_stats, generation_stats, sunlight_hours, autonomy_hours,
                     safety_margin, current_inverter_kw=None):
    """Calculate recommended battery, solar, and inverter sizing."""
    daily_avg = consumption_stats["daily_avg_kwh"]
    daily_max = consumption_stats["daily_max_kwh"]
    peak_w = consumption_stats["peak_hour_w"]
    hourly_profile = consumption_stats["hourly_profile"]

    # Battery: cover autonomy_hours of consumption, accounting for DoD and losses
    battery_dod = 0.90  # 90% depth of discharge for LFP
    battery_kwh_raw = daily_avg * (autonomy_hours / 24)
    battery_kwh = battery_kwh_raw * safety_margin / battery_dod

    # Solar: must charge battery + cover daytime load during sunlight hours
    # Assume peak sun hours centered around noon
    sun_start = max(0, 12 - int(sunlight_hours / 2))
    sun_end = min(23, 12 + int(math.ceil(sunlight_hours / 2)))
    daytime_load = sum(hourly_profile.get(h, 0) for h in range(sun_start, sun_end + 1))
    solar_kw = (battery_kwh_raw + daytime_load) / sunlight_hours * safety_margin

    # Inverter: must handle peak instantaneous load
    required_inverter_kw = peak_w / 1000 * safety_margin
    # Also consider startup surges (e.g., AC compressor) - add 50% headroom
    recommended_inverter_kw = required_inverter_kw * 1.5

    # Practical unit sizing
    panel_w = 550
    battery_unit_kwh = 5.12  # Common LFP battery module
    num_panels = math.ceil(solar_kw * 1000 / panel_w)
    num_battery_units = math.ceil(battery_kwh / battery_unit_kwh)

    result = {
        "battery_kwh": battery_kwh,
        "battery_kwh_raw": battery_kwh_raw,
        "battery_units": num_battery_units,
        "battery_unit_kwh": battery_unit_kwh,
        "solar_kw": solar_kw,
        "num_panels": num_panels,
        "panel_w": panel_w,
        "required_inverter_kw": required_inverter_kw,
        "recommended_inverter_kw": recommended_inverter_kw,
        "daytime_load_kwh": daytime_load,
        "sun_window": f"{sun_start}:00-{sun_end}:00",
    }

    if current_inverter_kw is not None:
        result["current_inverter_kw"] = current_inverter_kw
        result["inverter_sufficient"] = current_inverter_kw >= required_inverter_kw

    if generation_stats:
        gen_avg = generation_stats["daily_avg_kwh"]
        result["current_generation_avg"] = gen_avg
        result["self_sufficiency"] = (gen_avg / daily_avg * 100) if daily_avg > 0 else 0

    return result


def print_report(consumption_stats, generation_stats, system, args):
    """Print formatted analysis report."""
    cs = consumption_stats
    start_date = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

    print()
    print("=" * 55)
    print("         ENERGY ANALYSIS REPORT")
    print("=" * 55)
    print(f"Period: {start_date} to {end_date} ({cs['num_days']} days)")
    print()

    # Consumption
    print("--- CONSUMPTION ---")
    print(f"  Daily average:  {cs['daily_avg_kwh']:>7.1f} kWh")
    print(f"  Daily maximum:  {cs['daily_max_kwh']:>7.1f} kWh")
    print(f"  Daily minimum:  {cs['daily_min_kwh']:>7.1f} kWh")
    print(f"  Peak hour:      {cs['peak_hour']:>2d}:00 ({cs['peak_hour_kwh']:.2f} kWh avg)")
    print()

    # Generation
    if generation_stats:
        gs = generation_stats
        print("--- GENERATION (current system) ---")
        print(f"  Daily average:  {gs['daily_avg_kwh']:>7.1f} kWh")
        print(f"  Daily maximum:  {gs['daily_max_kwh']:>7.1f} kWh")
        if "self_sufficiency" in system:
            print(f"  Self-sufficiency: {system['self_sufficiency']:.1f}%")
        print()

    # Hourly profile
    print("--- HOURLY CONSUMPTION PROFILE ---")
    profile = cs["hourly_profile"]
    max_val = max(profile.values()) if profile else 1
    bar_width = 35

    for h in range(24):
        val = profile.get(h, 0)
        bar_len = int(val / max_val * bar_width) if max_val > 0 else 0
        bar = "#" * bar_len
        print(f"  {h:02d}:00 | {bar:<{bar_width}} {val:.2f} kWh")
    print()

    # Recommendations
    print("--- RECOMMENDED SYSTEM ---")
    print(f"  Target: {args.autonomy_hours:.0f}h autonomy, {args.sunlight_hours:.0f}h sunlight")
    print(f"  Safety margin: {(args.safety_margin - 1) * 100:.0f}%")
    print()
    print(f"  Battery capacity:  {system['battery_kwh']:.1f} kWh")
    print(f"    ({system['battery_units']} x {system['battery_unit_kwh']} kWh LFP modules)")
    print(f"    Raw need: {system['battery_kwh_raw']:.1f} kWh (before DoD + margin)")
    print()
    print(f"  Solar capacity:    {system['solar_kw']:.1f} kW")
    print(f"    ({system['num_panels']} x {system['panel_w']}W panels)")
    print(f"    Charging window: {system['sun_window']}")
    print(f"    Daytime load during sun: {system['daytime_load_kwh']:.1f} kWh")
    print()
    print(f"  Inverter:          {system['recommended_inverter_kw']:.1f} kW recommended")
    print(f"    Continuous load: {system['required_inverter_kw']:.1f} kW")
    print(f"    With surge headroom: {system['recommended_inverter_kw']:.1f} kW")

    if "current_inverter_kw" in system:
        current = system["current_inverter_kw"]
        if system["inverter_sufficient"]:
            print(f"    Current inverter ({current:.1f} kW): SUFFICIENT")
        else:
            print(f"    Current inverter ({current:.1f} kW): UPGRADE NEEDED")
    print()

    # Assumptions
    print("--- ASSUMPTIONS ---")
    print(f"  - Effective sunlight: {args.sunlight_hours:.1f} hours/day")
    print(f"  - Autonomy target: {args.autonomy_hours:.0f} hours")
    print(f"  - Battery DoD: 90% (LFP)")
    print(f"  - System losses: ~10% (included in safety margin)")
    print(f"  - Surge headroom: 50% above peak continuous load")
    print("=" * 55)


def select_entity(entities, category, override=None):
    """Select the best entity for a category, or use override."""
    if override:
        for e in entities:
            if e["entity_id"] == override:
                return e
        # If override not found in discovered list, construct a basic info dict
        return {"entity_id": override, "unit": "kWh", "state_class": "total_increasing"}

    if not entities:
        return None

    # Prefer entities with state_class total_increasing and kWh unit
    scored = []
    for e in entities:
        score = 0
        if e.get("state_class") in ("total_increasing", "total"):
            score += 10
        if e.get("unit") in ("kWh", "Wh"):
            score += 5
        if e.get("device_class") == "energy":
            score += 3
        scored.append((score, e))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


def print_discovered(categories):
    """Print discovered entities for user reference."""
    print()
    print("=== DISCOVERED ENERGY ENTITIES ===")
    for cat, entities in categories.items():
        if not entities:
            continue
        print(f"\n--- {cat.upper()} ({len(entities)}) ---")
        for e in entities:
            state_info = f"{e['state']} {e['unit']}" if e.get("state") else "N/A"
            sc = f" [{e['state_class']}]" if e.get("state_class") else ""
            print(f"  {e['entity_id']}")
            print(f"    {e['friendly_name']} = {state_info}{sc}")
    print()


def _default_ha_url():
    """Build HA URL from env: HA_URL > SUBDOMAIN.DOMAIN > fallback."""
    if os.environ.get("HA_URL"):
        return os.environ["HA_URL"]
    subdomain = os.environ.get("SUBDOMAIN")
    domain = os.environ.get("DOMAIN")
    if subdomain and domain:
        return f"https://{subdomain}.{domain}"
    return "http://homeassistant:8123"


def main():
    parser = argparse.ArgumentParser(
        description="Analyze energy data from Home Assistant for solar+battery sizing"
    )
    parser.add_argument(
        "--url", default=_default_ha_url(),
        help="Home Assistant URL (default: HA_URL env, or built from SUBDOMAIN.DOMAIN)",
    )
    parser.add_argument(
        "--token", default=os.environ.get("HA_TOKEN"),
        help="Home Assistant long-lived access token (default: HA_TOKEN env from .env)",
    )
    parser.add_argument("--days", type=int, default=30, help="Days of history to analyze (default: 30)")
    parser.add_argument("--sunlight-hours", type=float, default=2.0, help="Effective sunlight hours/day (default: 2.0)")
    parser.add_argument("--autonomy-hours", type=float, default=24.0, help="Hours of autonomy target (default: 24)")
    parser.add_argument("--safety-margin", type=float, default=1.25, help="Safety margin multiplier (default: 1.25 = 25%%)")
    parser.add_argument("--consumption-entity", help="Override consumption entity ID")
    parser.add_argument("--generation-entity", help="Override generation entity ID")
    parser.add_argument("--current-inverter-kw", type=float, help="Current inverter capacity in kW")
    parser.add_argument("--discover-only", action="store_true", help="Only list discovered energy entities")
    args = parser.parse_args()

    if not args.token:
        print("Error: No HA token provided. Use --token or set HA_TOKEN env variable.")
        sys.exit(1)

    analyzer = EnergyAnalyzer(args.url, args.token)

    # Test connection
    print(f"Connecting to {args.url}...")
    try:
        api_info = analyzer._get("/api/")
        print(f"Connected: {api_info.get('message', 'OK')}")
    except requests.exceptions.HTTPError as e:
        print(f"Error: HTTP {e.response.status_code} from {e.response.url}")
        if e.response.status_code == 401:
            print("  Check your HA_TOKEN in .env")
        elif e.response.status_code == 404:
            print(f"  API not found at {args.url}/api/ — check your HA_URL or SUBDOMAIN/DOMAIN in .env")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"Error: Cannot reach {args.url} — is Home Assistant running?")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Discover entities
    print("Discovering energy entities...")
    categories = analyzer.discover_energy_entities()
    print_discovered(categories)

    if args.discover_only:
        return

    # Select entities
    consumption_entity = select_entity(
        categories["consumption"], "consumption", args.consumption_entity
    )
    generation_entity = select_entity(
        categories["generation"], "generation", args.generation_entity
    )

    if not consumption_entity:
        print("Error: No consumption entity found. Use --consumption-entity to specify one.")
        sys.exit(1)

    print(f"Using consumption entity: {consumption_entity['entity_id']}")
    if generation_entity:
        print(f"Using generation entity: {generation_entity['entity_id']}")
    else:
        print("No generation entity found (solar sizing will be based on consumption only)")

    # Process consumption
    print(f"\nAnalyzing {args.days} days of data...")
    cons_daily, cons_hourly = analyzer.process_entity(consumption_entity, args.days)
    consumption_stats = analyzer.compute_stats(cons_daily, cons_hourly)

    if not consumption_stats:
        print("Error: No consumption data available. Check your entity ID and history retention.")
        sys.exit(1)

    # Process generation
    generation_stats = None
    if generation_entity:
        gen_daily, gen_hourly = analyzer.process_entity(generation_entity, args.days)
        generation_stats = analyzer.compute_stats(gen_daily, gen_hourly)

    # Calculate system
    system = calculate_system(
        consumption_stats, generation_stats,
        args.sunlight_hours, args.autonomy_hours,
        args.safety_margin, args.current_inverter_kw,
    )

    # Print report
    print_report(consumption_stats, generation_stats, system, args)


if __name__ == "__main__":
    main()
