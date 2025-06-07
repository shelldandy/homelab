CORE_SERVICES = traefik authentik adguard
MEDIA_SERVICES = qbittorrent arr jellyfin immich navidrome icloud-photos-downloader metube grafana wedding-share pinchflat
UTILITIES_SERVICES = forgejo filebrowser pingvin-share hoarder woodpecker watchtower calibre searxng docmost

ALL_SERVICES = $(CORE_SERVICES) $(MEDIA_SERVICES) $(UTILITIES_SERVICES)

.PHONY: start stop status logs \
	start-core stop-core \
	start-media stop-media \
	start-utilities stop-utilities \
	$(addprefix start-,$(ALL_SERVICES)) \
	$(addprefix stop-,$(ALL_SERVICES))

start: start-core start-media start-utilities

stop: stop-utilities stop-media stop-core

start-core:
	@for service in $(CORE_SERVICES); do \
		$(MAKE) start-$$service; \
	done

stop-core:
	@for service in $(CORE_SERVICES); do \
		$(MAKE) stop-$$service; \
	done

start-media:
	@for service in $(MEDIA_SERVICES); do \
		$(MAKE) start-$$service; \
	done

stop-media:
	@for service in $(MEDIA_SERVICES); do \
		$(MAKE) stop-$$service; \
	done

start-utilities:
	@for service in $(UTILITIES_SERVICES); do \
		$(MAKE) start-$$service; \
	done

stop-utilities:
	@for service in $(UTILITIES_SERVICES); do \
		$(MAKE) stop-$$service; \
	done

start-%:
	@if [ -d "$*" ]; then \
	  if [ -f "$*/docker-compose.yml" ] || [ -f "$*/docker-compose.yaml" ]; then \
	    echo "Starting $*..."; \
	    cd $*/ && docker compose up -d; \
	  else \
	    echo "Skipping $*: no docker-compose.yml or docker-compose.yaml found in $*/"; \
	  fi; \
	else \
	  echo "Skipping $*: directory $* does not exist."; \
	fi

stop-%:
	@if [ -d "$*" ]; then \
	  if [ -f "$*/docker-compose.yml" ] || [ -f "$*/docker-compose.yaml" ]; then \
	    echo "Stopping $*..."; \
	    cd $*/ && docker compose down; \
	  else \
	    echo "Skipping $*: no docker-compose.yml or docker-compose.yaml found in $*/"; \
	  fi; \
	else \
	  echo "Skipping $*: directory $* does not exist."; \
	fi

status:
	@for service in $(ALL_SERVICES); do \
		echo "Status for $$service:"; \
		cd $$service && docker compose ps; \
	done

logs:
	@for service in $(ALL_SERVICES); do \
		echo "Logs for $$service:"; \
		cd $$service && docker compose logs --tail=10; \
	done

services-check:
	@echo "Checking for missing service directories..."
	@dirs=$$(find . -maxdepth 1 -type d ! -name "." ! -name ".*" | sed 's|^./||'); \
	missing=0; \
	for dir in $$dirs; do \
		if ! echo "$(ALL_SERVICES)" | grep -qw "$$dir"; then \
			echo "Directory '$$dir' is not listed in any service list"; \
			missing=1; \
		fi; \
	done; \
	if [ $$missing -eq 0 ]; then \
		echo "No missing service directories found."; \
	fi; \
	echo "Checking for service names without corresponding directories..."; \
	extra=0; \
	for service in $(ALL_SERVICES); do \
		if [ ! -d "$$service" ]; then \
			echo "Service '$$service' is listed but directory does not exist"; \
			extra=1; \
		fi; \
	done; \
	if [ $$extra -eq 0 ]; then \
		echo "No extra services found without directories."; \
	fi 