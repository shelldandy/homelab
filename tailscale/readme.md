# Tailscale

Tailscale creates a secure mesh VPN network connecting all your devices, making your homelab accessible from anywhere.

## Features

- **Zero-config VPN**: Automatically creates encrypted connections between devices
- **Subnet Router**: Exposes your homelab network to remote Tailscale devices
- **Exit Node**: Routes internet traffic through your homelab (optional)
- **MagicDNS**: Access devices by name instead of IP addresses
- **Access Controls**: Fine-grained permissions via Tailscale admin console

## Setup

### 1. Generate Authentication Key

1. Go to [Tailscale Admin Console](https://login.tailscale.com/admin/settings/keys)
2. Click **Generate auth key**
3. Configure:
   - **Reusable**: ✅ (allows container recreation)
   - **Ephemeral**: ❌ (keeps the node persistent)
   - **Preauthorized**: ✅ (auto-approves the device)
   - **Tags**: Add `tag:homelab` or similar for organization

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your values
```

### 3. Deploy

```bash
# Create required networks (if not already created)
docker network create frontend
docker network create backend

# Start Tailscale
docker compose up -d

# Check logs
docker compose logs -f
```

### 4. Enable Subnet Routing (Optional)

If you want to access your homelab network remotely:

1. Set `TS_ROUTES` in `.env` to your network (e.g., `192.168.1.0/24`)
2. Add `--advertise-routes` to `TS_EXTRA_ARGS`
3. Restart container: `docker compose up -d`
4. Approve subnet routes in [Tailscale Admin Console](https://login.tailscale.com/admin/machines)

### 5. Enable Exit Node (Optional)

To route internet traffic through your homelab:

1. Add `--advertise-exit-node` to `TS_EXTRA_ARGS`
2. Restart container: `docker compose up -d`
3. Enable exit node in [Tailscale Admin Console](https://login.tailscale.com/admin/machines)

## Configuration Options

| Variable | Description | Example |
|----------|-------------|---------|
| `TS_AUTHKEY` | Authentication key from Tailscale | `tskey-auth-...` |
| `TS_ROUTES` | Subnet routes to advertise | `192.168.1.0/24` |
| `TS_EXTRA_ARGS` | Additional tailscale up arguments | `--accept-routes --advertise-exit-node` |
| `HOSTNAME` | Node name in Tailscale | `homelab-tailscale` |
| `TS_ACCEPT_DNS` | Accept Tailscale DNS | `false` (if using Pi-hole/AdGuard) |

## Common Use Cases

### Basic VPN Access
```env
TS_AUTHKEY=tskey-auth-your-key
TS_EXTRA_ARGS=--accept-routes
```

### Subnet Router (Access homelab from anywhere)
```env
TS_AUTHKEY=tskey-auth-your-key
TS_ROUTES=192.168.1.0/24
TS_EXTRA_ARGS=--advertise-routes --accept-routes
```

### Exit Node + Subnet Router
```env
TS_AUTHKEY=tskey-auth-your-key
TS_ROUTES=192.168.1.0/24
TS_EXTRA_ARGS=--advertise-exit-node --advertise-routes --accept-routes
```

### With Custom DNS (Pi-hole/AdGuard)
```env
TS_AUTHKEY=tskey-auth-your-key
TS_ACCEPT_DNS=false
TS_EXTRA_ARGS=--accept-routes
```

## Security Notes

- 2024 Security Update: Stateful filtering is enabled by default
- For site-to-site networking, you may need: `--stateful-filtering=false --snat-subnet-routes=false`
- Keep auth keys secure and rotate them regularly
- Use tags for access control in larger deployments

## Accessing Services

Once Tailscale is running, you can:
- Access homelab services via Tailscale IP or MagicDNS names
- Use Traefik with Tailscale IPs for internal access
- Connect mobile devices for secure remote access

## Troubleshooting

### Container Won't Start
- Check that `/dev/net/tun` exists: `ls -la /dev/net/tun`
- Verify Docker has required capabilities
- Check system has IP forwarding: `cat /proc/sys/net/ipv4/ip_forward`

### Subnet Routes Not Working
- Verify routes are approved in Tailscale admin console
- Check `TS_ROUTES` matches your actual network
- Ensure IP forwarding is enabled on the host

### DNS Issues
- If using Pi-hole/AdGuard, set `TS_ACCEPT_DNS=false`
- Check MagicDNS is enabled in Tailscale settings

### Logs
```bash
# View container logs
docker compose logs -f

# Check Tailscale status
docker compose exec tailscale tailscale status

# View current configuration
docker compose exec tailscale tailscale status --peers
```