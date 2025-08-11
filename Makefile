CORE_SERVICES = traefik pocket-id adguard vaultwarden home-assistant
MEDIA_SERVICES = qbittorrent arr jellyfin navidrome icloud-photos-downloader metube grafana pinchflat # wedding-share
UTILITIES_SERVICES = forgejo hoarder watchtower calibre searxng docmost open-webui orbi

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

start-%:
	@echo "Starting $*..."; \
	cd $*/ && docker compose up -d; \

stop-%:
	@echo "Stopping $*..."; \
	cd $*/ && docker compose down; \

start-all:
	@for service in $(ALL_SERVICES); do \
		$(MAKE) start-$$service; \
	done

stop-all:
	@for service in $(ALL_SERVICES); do \
		$(MAKE) stop-$$service; \
	done
