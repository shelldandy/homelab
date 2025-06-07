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
	@echo "Starting $*..."
	@cd $*/ && docker compose up -d

stop-%:
	@echo "Stopping $*..."
	@cd $*/ && docker compose down

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