# Post-Mortem: Immich Service Not Appearing in Traefik Router

**Date:** June 13, 2025  
**Duration:** ~45 minutes  
**Severity:** Medium - Service unavailable via reverse proxy  
**Status:** Resolved  

## Summary

The Immich photo management service was not appearing as a router in Traefik, making it inaccessible via the reverse proxy at `https://photos.bowline.im`. The issue was caused by incompatible timeout middleware configuration labels that prevented Traefik v3 from accepting the container's routing configuration.

## Timeline

- **01:00 UTC** - Issue reported: Immich not showing up as router in Traefik
- **01:03 UTC** - Investigation began: Checked Immich docker-compose configuration
- **01:04 UTC** - Verified Immich containers running and healthy
- **01:05 UTC** - Found error in Traefik logs: `"field not found, node: timeout"`
- **01:07 UTC** - Identified root cause: Deprecated timeout middleware syntax
- **01:08 UTC** - First attempt: Updated timeout syntax to Traefik v3 format
- **01:12 UTC** - Verification failed: Same error persisted with updated syntax
- **01:13 UTC** - Second attempt: Removed timeout middleware completely
- **01:14 UTC** - Success: "photos" router appeared in Traefik configuration
- **01:16 UTC** - Final verification: SSL certificate configured, service responding

## Root Cause Analysis

### Primary Cause
Immich's docker-compose.yml contained timeout middleware labels using deprecated Traefik v2 syntax:

```yaml
- "traefik.http.middlewares.immich-timeouts.timeout.readTimeout=600s"
- "traefik.http.middlewares.immich-timeouts.timeout.idleTimeout=600s"  
- "traefik.http.middlewares.immich-timeouts.timeout.writeTimeout=600s"
```

### Why This Caused the Issue
1. **Syntax Incompatibility**: Traefik v3.4.1 no longer supports this timeout middleware syntax
2. **Configuration Rejection**: When Traefik encountered the invalid syntax, it rejected the entire container configuration
3. **Silent Failure**: The container appeared healthy, but Traefik filtered it out during configuration parsing

### Contributing Factors
- **Version Migration**: The configuration was written for an older Traefik version
- **Insufficient Documentation**: The timeout middleware syntax changes weren't immediately apparent
- **Container Restart Caching**: Simple container restarts didn't refresh the labels; full recreation was required

## What Went Well

1. **Systematic Investigation**: Methodical approach checking service health, network connectivity, and log analysis
2. **Effective Log Analysis**: Traefik's detailed debug logging clearly identified the problematic middleware
3. **Quick Iteration**: Rapid testing of different solutions once root cause was identified
4. **Proper Verification**: Confirmed both router appearance and SSL certificate provisioning

## What Could Be Improved

1. **Documentation**: Need better tracking of Traefik version compatibility for middleware configurations
2. **Monitoring**: Could implement alerts for containers being filtered out by Traefik
3. **Testing**: Should test configuration changes in development before applying to production services

## Action Items

### Immediate (Completed)
- [x] Remove incompatible timeout middleware from Immich configuration
- [x] Verify Immich accessibility via `https://photos.bowline.im`
- [x] Document the resolution process

### Short-term (Next 1-2 weeks)
- [ ] Audit other services for deprecated Traefik middleware syntax
- [ ] Update CLAUDE.md with Traefik v3 middleware examples
- [ ] Create monitoring alert for Traefik container filtering events

### Long-term (Next month)
- [ ] Implement automated testing for Traefik configuration changes
- [ ] Document Traefik version upgrade procedures
- [ ] Consider implementing timeout functionality at the Traefik entrypoint level if needed

## Technical Details

### Error Signature
```json
{
  "level": "error",
  "providerName": "docker", 
  "container": "immich-server-immich-[id]",
  "error": "field not found, node: timeout",
  "caller": "github.com/traefik/traefik/v3/pkg/provider/docker/config.go:46"
}
```

### Final Working Configuration
```yaml
services:
  immich-server:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.photos.rule=Host(`photos.bowline.im`)"
      - "traefik.http.services.photos.loadbalancer.server.port=2283"
      - "traefik.http.services.photos.loadbalancer.responseForwarding.flushInterval=1s"
```

### Environment Context
- **Traefik Version**: v3.4.1
- **Docker Compose Version**: 2.36.2
- **Immich Version**: v1.134.0
- **Network**: External frontend network with Cloudflare DNS challenge

## Lessons Learned

1. **Middleware Compatibility**: Always verify middleware syntax compatibility when upgrading Traefik major versions
2. **Container Recreation**: Configuration label changes require full container recreation, not just restart
3. **Health Check Dependencies**: Traefik waits for container health checks before accepting configurations
4. **Progressive Debugging**: Remove complex configurations first, then add back features incrementally

## Prevention Measures

1. **Version Compatibility Matrix**: Maintain documentation of supported middleware syntax by Traefik version
2. **Configuration Validation**: Implement pre-deployment validation for Traefik labels
3. **Monitoring Enhancement**: Add alerting for containers filtered out due to configuration errors
4. **Documentation Updates**: Keep homelab documentation current with supported syntax examples

---

**Prepared by:** Claude Code  
**Reviewed by:** [To be completed by team]  
**Next Review Date:** July 13, 2025