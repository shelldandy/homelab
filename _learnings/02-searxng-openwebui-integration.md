# Post-Mortem: SearXNG Integration with OpenWebUI

**Date:** June 16, 2025  
**Duration:** ~60 minutes  
**Severity:** Medium - Web search functionality unavailable in OpenWebUI  
**Status:** Resolved  

## Summary

OpenWebUI's web search functionality was failing with 403 FORBIDDEN errors when attempting to query the SearXNG search engine. The issue was caused by SearXNG running with outdated configuration that lacked JSON format support and had restrictive API access settings. The resolution involved migrating SearXNG configuration to the homelab repository with proper JSON support and restarting the service to apply new settings.

## Timeline

- **16:30 UTC** - Issue reported: OpenWebUI web search returning 403 errors
- **16:32 UTC** - Investigation began: Checked OpenWebUI logs revealing SearXNG 403 responses
- **16:35 UTC** - Verified network connectivity: SearXNG accessible from OpenWebUI container
- **16:38 UTC** - Identified configuration issue: Missing JSON format support
- **16:40 UTC** - Analyzed existing SearXNG setup: Using external volume mounts
- **16:45 UTC** - Decision made: Migrate configuration files to homelab repository
- **16:47 UTC** - Created new settings.yml with JSON format enabled
- **16:50 UTC** - Updated docker-compose.yml to use bind mounts
- **16:52 UTC** - Created limiter.toml for API access configuration
- **16:55 UTC** - Restarted SearXNG service to apply new configuration
- **16:58 UTC** - Success: SearXNG returning JSON responses correctly
- **17:00 UTC** - Final verification: Complex search queries working from OpenWebUI

## Root Cause Analysis

### Primary Cause
SearXNG was running with configuration that did not support JSON format output, which is required for OpenWebUI integration:

```yaml
# Original settings.yml - Missing JSON support
search:
  formats:
    - html  # JSON format was missing
```

### Why This Caused the Issue
1. **Missing JSON Support**: OpenWebUI requires SearXNG to return responses in JSON format
2. **Old Configuration**: SearXNG was running with 8-day-old configuration from external volume
3. **API Restrictions**: Default limiter settings were too restrictive for API access
4. **Service State**: Container needed restart to pick up configuration changes

### Contributing Factors
- **External Volume Management**: Configuration stored outside repository made version control difficult
- **Service Longevity**: Container running for 8 days without configuration updates
- **Network Assumption**: Initially assumed network connectivity was the issue
- **Documentation Gap**: OpenWebUI integration requirements not clearly documented

## What Went Well

1. **Systematic Debugging**: Proper log analysis identified the exact failing URL and error code
2. **Network Testing**: Confirmed connectivity between services using container exec
3. **Configuration Management**: Successfully migrated to repository-based configuration
4. **Documentation**: Comprehensive search.md provided clear integration requirements
5. **Incremental Testing**: Tested each configuration change step by step

## What Could Be Improved

1. **Configuration Versioning**: Should have repository-based config from the start
2. **Service Documentation**: Integration requirements should be in CLAUDE.md
3. **Monitoring**: No alerting for service integration failures
4. **Testing**: Should test integrations after major configuration changes

## Action Items

### Immediate (Completed)
- [x] Add JSON format support to SearXNG settings.yml
- [x] Create non-restrictive limiter.toml configuration
- [x] Migrate configuration files to homelab repository
- [x] Update docker-compose.yml to use bind mounts
- [x] Restart SearXNG service with new configuration
- [x] Verify OpenWebUI web search functionality

### Short-term (Next 1-2 weeks)
- [ ] Audit other services for external volume dependencies
- [ ] Document all service integration requirements in CLAUDE.md
- [ ] Create monitoring for inter-service communication failures
- [ ] Add integration testing to service deployment procedures

### Long-term (Next month)
- [ ] Implement automated testing for service integrations
- [ ] Create configuration management standards for all services
- [ ] Document service dependency matrix
- [ ] Consider implementing health checks for integration endpoints

## Technical Details

### Error Signature
```json
{
  "error": "403 Client Error: FORBIDDEN for url: http://searxng:8080/search?q=Bitcoin+price+trends+June+2025&format=json&pageno=1&safesearch=1&language=en-US&time_range=&categories=&theme=simple&image_proxy=0",
  "service": "open_webui.routers.retrieval",
  "function": "process_web_search"
}
```

### Configuration Changes Made

**settings.yml** - Added JSON format support:
```yaml
search:
  formats:
    - html
    - json  # Required for OpenWebUI integration

server:
  port: 8080
  bind_address: "0.0.0.0"  # Allow network access
```

**limiter.toml** - Non-restrictive API access:
```toml
[botdetection.ip_limit]
link_token = false

[botdetection.ip_lists]
block_ip = []
pass_ip = []
```

**docker-compose.yml** - Bind mount configuration:
```yaml
volumes:
  - ./settings.yml:/etc/searxng/settings.yml:ro
  - ./limiter.toml:/etc/searxng/limiter.toml:ro
```

### Final Working Integration
- **OpenWebUI URL**: `http://searxng:8080/search?q=<query>`
- **Network**: Both services on `backend` external network
- **External Access**: SearXNG remains accessible at `search.bowline.im`
- **Format Support**: JSON responses enabled for API integration

### Environment Context
- **SearXNG Version**: searxng/searxng:latest
- **OpenWebUI Version**: ghcr.io/open-webui/open-webui:main
- **Docker Network**: External backend network
- **Reverse Proxy**: Traefik with TinyAuth middleware

## Lessons Learned

1. **Configuration Management**: Keep all service configurations in version control
2. **Service Dependencies**: Document integration requirements clearly
3. **Container Lifecycle**: Configuration changes require service restarts
4. **Network Architecture**: Verify internal service communication before external
5. **JSON API Requirements**: Many modern integrations require JSON format support

## Prevention Measures

1. **Repository Standards**: All configuration files should be repository-managed
2. **Integration Documentation**: Document service dependencies in CLAUDE.md
3. **Testing Procedures**: Test integrations after configuration changes
4. **Monitoring**: Implement health checks for critical service integrations
5. **Configuration Validation**: Validate configuration before service deployment

## Integration Requirements

### For Future OpenWebUI + SearXNG Deployments
1. **JSON Format**: Must enable JSON format in SearXNG settings
2. **Network Access**: Services must share a Docker network
3. **API Configuration**: Non-restrictive limiter settings required
4. **URL Format**: Use `http://searxng:8080/search?q=<query>` in OpenWebUI
5. **Service Restart**: Restart SearXNG after configuration changes

### OpenWebUI Settings
```yaml
environment:
  ENABLE_RAG_WEB_SEARCH: True
  RAG_WEB_SEARCH_ENGINE: "searxng"
  SEARXNG_QUERY_URL: "http://searxng:8080/search?q=<query>"
```

---

**Prepared by:** Claude Code  
**Reviewed by:** [To be completed by team]  
**Next Review Date:** July 16, 2025