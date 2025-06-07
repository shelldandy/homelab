CORE_SERVICES = traefik authentik adguard
MEDIA_SERVICES = qbittorrent arr jellyfin immich navidrome icloud-photos-downloader metube grafana wedding-share pinchflat
UTILITIES_SERVICES = forgejo filebrowser pingvin-share hoarder woodpecker watchtower calibre searxng docmost

ALL_SERVICES = $(CORE_SERVICES) $(MEDIA_SERVICES) $(UTILITIES_SERVICES)

check-missing-services:
	@echo "Checking for service names without corresponding directories..."; \
	extra=0; \
	for service in $(ALL_SERVICES); do \
		if [ ! -d "$$service" ]; then \
			echo "Service '$$service' is listed but directory does not exist"; \
			extra=1; \
		fi; \
	done; \
	if [ $$extra -eq 0 ]; then \
		echo "No missing service directories found."; \
	fi

check-extra-services:
	@echo "Checking for directories not listed in any service list..."; \
	missing=0; \
	dirs=$$(find . -maxdepth 1 -type d ! -name "." ! -name ".*" | sed 's|^./||'); \
	for dir in $$dirs; do \
		if ! echo "$(ALL_SERVICES)" | grep -qw "$$dir"; then \
			echo "Directory '$$dir' is not listed in any service list"; \
			missing=1; \
		fi; \
	done; \
	if [ $$missing -eq 0 ]; then \
		echo "No extra directories found."; \
	fi

check-services: check-missing-services check-extra-services