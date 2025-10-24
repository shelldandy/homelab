# Matrix Authentication Service (MAS) Implementation Guide

**Status:** 📋 Planning Document - Not Yet Implemented

This guide provides a complete plan for deploying Matrix Authentication Service (MAS) to enable QR code login and Element X support with Pocket ID SSO.

---

## Table of Contents

1. [Overview](#overview)
2. [Why Deploy MAS?](#why-deploy-mas)
3. [Architecture](#architecture)
4. [Prerequisites](#prerequisites)
5. [Implementation Steps](#implementation-steps)
6. [Migration Procedure](#migration-procedure)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)
9. [Rollback Procedure](#rollback-procedure)
10. [References](#references)

---

## Overview

**Matrix Authentication Service (MAS)** is a dedicated OAuth2/OIDC authentication server for Matrix. It sits between your Matrix clients and your identity provider (Pocket ID), handling all authentication flows.

### Current Setup
```
Element Classic → Synapse (OIDC) → Pocket ID
```

### With MAS
```
Element X / Element Classic → MAS (OIDC) → Pocket ID
                               ↓
                            Synapse (trusts MAS)
```

---

## Why Deploy MAS?

### Essential Features Enabled
- ✅ **Element X Support**: Element X ONLY works with MAS-based authentication
- ✅ **QR Code Login**: Works seamlessly with OIDC providers
- ✅ **Modern OAuth2 Flows**: Better security and session management
- ✅ **Device Management**: Improved session controls

### Current Limitations Without MAS
- ❌ Element X is completely unusable (no password, no MAS SSO)
- ❌ QR code login shows "Not supported by your account provider"
- ⚠️ Stuck on Element Classic as ecosystem moves to Element X
- ⚠️ Will become outdated as Matrix.org and ecosystem standardize on MAS

### Timeline
- **April 2025**: Matrix.org migrated to MAS
- **Future**: Element Classic will be phased out in favor of Element X
- **Now**: MAS is the recommended authentication approach

---

## Architecture

### Network Architecture

```
┌─────────────┐
│   Traefik   │ (Reverse Proxy)
└──────┬──────┘
       │
       ├─────────────────────┬─────────────────────┬──────────────────
       │                     │                     │
┌──────▼──────┐      ┌──────▼──────┐      ┌──────▼──────┐
│   Element   │      │     MAS     │      │   Synapse   │
│   (Web)     │      │   (Auth)    │      │  (Matrix)   │
└─────────────┘      └──────┬──────┘      └──────┬──────┘
                            │                     │
                     ┌──────▼──────┐      ┌──────▼──────┐
                     │  MAS Postgres│     │Synapse Postgres│
                     └─────────────┘      └─────────────┘
                            │
                     ┌──────▼──────┐
                     │  Pocket ID  │
                     └─────────────┘
```

### Authentication Flow

1. **User accesses Element** (Web/Mobile/X)
2. **Element redirects to MAS** for login
3. **MAS redirects to Pocket ID** (OIDC provider)
4. **User authenticates** with Pocket ID
5. **Pocket ID returns to MAS** with auth token
6. **MAS creates session** and issues Matrix access token
7. **Element uses token** to communicate with Synapse
8. **Synapse validates token** with MAS

---

## Prerequisites

### Before You Start

- ✅ Current Synapse setup working with Pocket ID OIDC
- ✅ Docker and docker-compose installed
- ✅ Traefik configured and running
- ✅ Pocket ID running and accessible
- ✅ Admin access to Pocket ID
- ⏱️ **Time**: 1-2 hours for full deployment
- 🧪 **Environment**: Recommend testing on staging first if possible

### Versions Required

- **Synapse**: 1.106+ (you have latest)
- **MAS**: Latest stable (ghcr.io/matrix-org/matrix-authentication-service)
- **PostgreSQL**: 15+ (for MAS database)

---

## Implementation Steps

### Step 1: Backup Current Configuration

**⚠️ CRITICAL: Always backup before major changes!**

```bash
cd /home/bowlinedandy/homelab/matrix

# Backup current configs
cp docker-compose.yml docker-compose.yml.backup
cp data/synapse-config.yaml data/synapse-config.yaml.backup
cp .env .env.backup

# Backup Synapse data (optional but recommended)
docker compose exec postgres pg_dump -U synapse synapse > backup_synapse_$(date +%Y%m%d).sql
```

### Step 2: Add MAS PostgreSQL Database

**Edit `docker-compose.yml`** - Add MAS database service:

```yaml
  mas-postgres:
    image: postgres:16-alpine
    container_name: mas-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: mas
      POSTGRES_USER: mas
      POSTGRES_PASSWORD: ${MAS_POSTGRES_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=C"
      TZ: ${TZ}
    volumes:
      - ${CONFIG_PATH}/matrix/mas-postgres:/var/lib/postgresql/data
    networks:
      - matrix
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mas -d mas"]
      interval: 30s
      timeout: 5s
      retries: 3
```

### Step 3: Add MAS Service

**Edit `docker-compose.yml`** - Add MAS service:

```yaml
  matrix-auth-service:
    image: ghcr.io/matrix-org/matrix-authentication-service:latest
    container_name: matrix-auth-service
    restart: unless-stopped
    command: ["server"]
    volumes:
      - ./mas-config.yaml:/config/config.yaml:ro
    environment:
      TZ: ${TZ}
    networks:
      - matrix
      - frontend
    depends_on:
      mas-postgres:
        condition: service_healthy
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.mas.rule=Host(`auth-matrix.${DOMAIN}`)"
      - "traefik.http.services.mas.loadbalancer.server.port=8080"
      - "traefik.http.routers.mas.tls=true"
      - "traefik.http.routers.mas.tls.certresolver=myresolver"
      - "traefik.http.routers.mas.entrypoints=websecure"
```

**Note:** MAS will be accessible at `https://auth-matrix.bowline.im`

### Step 4: Update Environment Variables

**Edit `.env`** - Add MAS-specific variables:

```env
# Matrix Authentication Service (MAS)
MAS_POSTGRES_PASSWORD=  # Generate with: openssl rand -base64 32
MAS_SECRETS_ENCRYPTION=  # Generate with: openssl rand -hex 64
MAS_SECRETS_KEYS=  # Generate with: openssl rand -base64 64
MAS_CLIENTS_SECRET=  # Generate with: openssl rand -base64 64
```

**Generate all secrets:**
```bash
echo "MAS_POSTGRES_PASSWORD=$(openssl rand -base64 32)"
echo "MAS_SECRETS_ENCRYPTION=$(openssl rand -hex 64)"
echo "MAS_SECRETS_KEYS=$(openssl rand -base64 64)"
echo "MAS_CLIENTS_SECRET=$(openssl rand -base64 64)"
```

Add these to your `.env` file.

### Step 5: Create MAS Configuration

**Create `mas-config.yaml`** in matrix directory:

```yaml
# Matrix Authentication Service Configuration
# Documentation: https://matrix-org.github.io/matrix-authentication-service/

# HTTP listener configuration
http:
  listeners:
    - name: web
      resources:
        - name: discovery
        - name: human
        - name: oauth
        - name: compat
        - name: graphql
        - name: assets
      binds:
        - address: "[::]:8080"

  # Public URL where MAS is accessible
  public_base: "https://auth-matrix.bowline.im"

  # OIDC issuer (same as public_base for MAS)
  issuer: "https://auth-matrix.bowline.im"

# Database configuration
database:
  uri: "postgresql://mas:${MAS_POSTGRES_PASSWORD}@mas-postgres/mas"

# Secrets for encryption and signing
secrets:
  # Secret for encrypting cookies and tokens
  encryption: "${MAS_SECRETS_ENCRYPTION}"

  # Keys for signing tokens (rotate periodically)
  keys:
    - kid: "key-1"
      key: "${MAS_SECRETS_KEYS}"

# Matrix homeserver configuration
matrix:
  homeserver: "bowline.im"
  endpoint: "http://synapse:8008"
  secret: "${MAS_CLIENTS_SECRET}"

# Upstream OIDC provider (Pocket ID)
upstream_oauth2:
  providers:
    - id: "pocketid"
      issuer: "https://auth.bowline.im"
      human_name: "Pocket ID"
      brand_name: "pocketid"

      # Discovery endpoint (MAS will fetch OIDC config)
      discovery_mode: "oidc"

      # Client credentials from Pocket ID
      client_id: "edeab497-0783-4ecc-a482-a3f345343abf"
      client_secret: "EzXbdkYyhhpYdeOo2WOuKdh4vVYDEJEz"

      # Token authentication method
      token_endpoint_auth_method: "client_secret_post"

      # Scopes to request
      scope: "openid profile email"

      # Claims mapping
      claims_imports:
        localpart:
          action: "require"
          template: "{{ user.preferred_username }}"
        displayname:
          action: "suggest"
          template: "{{ user.name }}"
        email:
          action: "suggest"
          template: "{{ user.email }}"
          set_email_verification: "import"

# Client configuration (Element and other Matrix clients)
clients:
  # This is auto-configured by MAS for Matrix clients
  # Element will automatically discover this via /.well-known

# Email configuration (optional, for password reset if enabled)
# email:
#   from: "matrix@bowline.im"
#   reply_to: "no-reply@bowline.im"
#   transport: smtp
#   hostname: "smtp.example.com"
#   port: 587
#   mode: "starttls"
#   username: "matrix@bowline.im"
#   password: "${SMTP_PASSWORD}"

# Branding (optional)
branding:
  service_name: "Bowline Matrix"
  policy_uri: "https://bowline.im/privacy"
  tos_uri: "https://bowline.im/terms"

# Experimental features
experimental:
  # Enable device code flow for QR login
  oauth2_device_code_grant: true
```

### Step 6: Update Pocket ID Configuration

**Login to Pocket ID** and update your Matrix OIDC client:

1. Navigate to your "Matrix Synapse" OIDC client
2. **Update Redirect URIs** to:
   ```
   https://auth-matrix.bowline.im/oauth2/callback
   https://auth-matrix.bowline.im/upstream/callback/pocketid
   ```
3. **Update Post Logout Redirect URIs**:
   ```
   https://element.bowline.im
   https://auth-matrix.bowline.im
   ```
4. Save changes

### Step 7: Update Synapse Configuration

**Edit `data/synapse-config.yaml`** - Replace OIDC section with MAS delegation:

**Remove this:**
```yaml
# OIDC/SSO Configuration - Pocket ID Integration
oidc_providers:
  - idp_id: pocketid
    # ... all the OIDC config ...
```

**Add this instead:**
```yaml
# Matrix Authentication Service (MAS) Integration
# Delegate all authentication to MAS
experimental_features:
  msc3861:
    enabled: true
    issuer: "https://auth-matrix.bowline.im"
    client_id: "0000000000000000000SYNAPSE"
    client_auth_method: "client_secret_basic"
    client_secret: "${MAS_CLIENTS_SECRET}"  # Same as in mas-config.yaml
    admin_token: "${MAS_ADMIN_TOKEN}"  # For admin operations

    # Account management endpoints
    account_management_url: "https://auth-matrix.bowline.im/account"

    # Disable Synapse's native auth
    disable_password_login: true
```

**Important:** The `MAS_CLIENTS_SECRET` must match between `mas-config.yaml` and `synapse-config.yaml`.

### Step 8: Update Element Configuration

**Edit `element-config.json`** - MAS is auto-discovered, but verify:

```json
{
  "default_server_config": {
    "m.homeserver": {
      "base_url": "https://matrix.bowline.im",
      "server_name": "bowline.im"
    }
  },
  // ... rest of config stays the same
}
```

Element will automatically discover MAS via `.well-known/matrix/client`.

### Step 9: Generate Admin Token

**Generate an admin token** for user migration:

```bash
cd /home/bowlinedandy/homelab/matrix

# Start MAS first time to initialize database
docker compose up -d mas-postgres matrix-auth-service

# Wait for MAS to initialize
sleep 10

# Generate admin token
docker compose exec matrix-auth-service mas-cli manage generate-token \
  --admin \
  --expires-in-days 365 \
  --user admin

# Save this token - you'll need it for .env
```

Add to `.env`:
```env
MAS_ADMIN_TOKEN=mas_xxxxxxxxxxxxxxxxxxxxxx
```

### Step 10: Deploy Services

**Start all services:**

```bash
cd /home/bowlinedandy/homelab/matrix

# Start MAS and database
docker compose up -d mas-postgres matrix-auth-service

# Wait for MAS to be ready
sleep 15

# Check MAS health
docker compose exec matrix-auth-service mas-cli doctor

# If healthy, restart Synapse with new config
docker compose restart synapse

# Restart Element to pick up new config
docker compose restart element-web
```

### Step 11: Verify Deployment

**Check all services are running:**

```bash
# Check containers
docker compose ps

# Check MAS logs
docker compose logs matrix-auth-service --tail 50

# Check Synapse logs for MAS connection
docker compose logs synapse --tail 50 | grep -i "msc3861\|mas\|auth"

# Test MAS health endpoint
curl https://auth-matrix.bowline.im/health

# Test OIDC discovery
curl https://auth-matrix.bowline.im/.well-known/openid-configuration
```

All should return successful responses.

---

## Migration Procedure

### Migrating Existing Users

**Important:** Existing users will need to re-authenticate after MAS deployment.

#### Option 1: Automatic Session Migration (Recommended)

MAS can attempt to preserve existing sessions:

```bash
# Run migration tool
docker compose exec matrix-auth-service mas-cli manage import-users \
  --homeserver-url "http://synapse:8008" \
  --admin-token "${MAS_ADMIN_TOKEN}"

# This will:
# - Import all existing Synapse users
# - Attempt to preserve sessions
# - Link OIDC identities where possible
```

#### Option 2: Manual Re-authentication

1. **Notify users** that they'll need to re-login
2. Users open Element and click "Sign In"
3. Choose "Sign in with Pocket ID"
4. Authenticate via Pocket ID
5. MAS creates new session

#### Post-Migration

- Check user migration status:
  ```bash
  docker compose exec matrix-auth-service mas-cli manage list-users
  ```

- Verify OIDC linkage:
  ```bash
  docker compose exec matrix-auth-service mas-cli manage list-upstream-links
  ```

---

## Testing

### Test Checklist

#### 1. Basic Authentication
- [ ] Access Element Web: https://element.bowline.im
- [ ] Click "Sign In"
- [ ] Verify "Sign in with Pocket ID" button appears
- [ ] Click and authenticate via Pocket ID
- [ ] Verify successful login

#### 2. Element X Support
- [ ] Install Element X on mobile
- [ ] Change homeserver to `matrix.bowline.im`
- [ ] Verify SSO option appears
- [ ] Authenticate via Pocket ID
- [ ] Verify successful login

#### 3. QR Code Login
- [ ] Login on Element Desktop/Web
- [ ] Go to Settings → Sessions
- [ ] Click "Link new device"
- [ ] QR code should appear
- [ ] Open Element X on mobile
- [ ] Scan QR code
- [ ] Verify device links successfully
- [ ] Check E2E encryption keys synced

#### 4. Session Management
- [ ] Go to MAS account page: https://auth-matrix.bowline.im/account
- [ ] Verify all active sessions shown
- [ ] Test logging out a session
- [ ] Verify session ends in Element

#### 5. Federation
- [ ] Send message to user on another server
- [ ] Verify federation still works
- [ ] Join public room on matrix.org
- [ ] Verify can send/receive messages

---

## Troubleshooting

### Common Issues

#### Issue: "Failed to connect to authentication service"

**Symptoms:**
- Element shows connection error
- Can't login

**Solutions:**
1. Check MAS is running: `docker compose ps matrix-auth-service`
2. Check MAS logs: `docker compose logs matrix-auth-service --tail 100`
3. Verify MAS accessible: `curl https://auth-matrix.bowline.im/health`
4. Check Traefik routes: `docker compose logs traefik | grep mas`

#### Issue: "Invalid client" or "Client authentication failed"

**Symptoms:**
- Error during OIDC flow
- Pocket ID shows error

**Solutions:**
1. Verify redirect URIs in Pocket ID match exactly:
   - `https://auth-matrix.bowline.im/oauth2/callback`
   - `https://auth-matrix.bowline.im/upstream/callback/pocketid`
2. Check client ID/secret match between Pocket ID and mas-config.yaml
3. Check MAS logs for authentication errors

#### Issue: "QR code login not available"

**Symptoms:**
- QR option doesn't appear
- Shows "Not supported"

**Solutions:**
1. Verify `oauth2_device_code_grant: true` in mas-config.yaml
2. Restart MAS: `docker compose restart matrix-auth-service`
3. Check Element X is latest version
4. Clear Element cache and re-login

#### Issue: Synapse won't start after MAS config

**Symptoms:**
- Synapse container restarting
- Errors about MSC3861

**Solutions:**
1. Check `MAS_CLIENTS_SECRET` matches in both configs
2. Verify MAS is accessible from Synapse container:
   ```bash
   docker compose exec synapse curl http://matrix-auth-service:8080/health
   ```
3. Check Synapse logs: `docker compose logs synapse | grep -i msc3861`

#### Issue: Existing users can't login

**Symptoms:**
- "User not found" errors
- Can't authenticate

**Solutions:**
1. Check user migration completed:
   ```bash
   docker compose exec matrix-auth-service mas-cli manage list-users
   ```
2. Re-run migration if needed
3. Users may need to re-register via Pocket ID SSO

### Debug Commands

```bash
# Check MAS health
docker compose exec matrix-auth-service mas-cli doctor

# List all users in MAS
docker compose exec matrix-auth-service mas-cli manage list-users

# List OIDC linkages
docker compose exec matrix-auth-service mas-cli manage list-upstream-links

# Check MAS database connection
docker compose exec matrix-auth-service mas-cli database status

# View MAS configuration (sanitized)
docker compose exec matrix-auth-service mas-cli config dump

# Test OIDC flow manually
curl -v https://auth-matrix.bowline.im/.well-known/openid-configuration
```

---

## Rollback Procedure

### If Something Goes Wrong

**⚠️ If MAS deployment fails, you can rollback:**

#### Step 1: Restore Configuration

```bash
cd /home/bowlinedandy/homelab/matrix

# Restore backups
cp docker-compose.yml.backup docker-compose.yml
cp data/synapse-config.yaml.backup data/synapse-config.yaml
cp .env.backup .env
```

#### Step 2: Revert Pocket ID Changes

1. Login to Pocket ID
2. Restore Matrix client redirect URIs to:
   ```
   https://matrix.bowline.im/_synapse/client/oidc/callback
   ```

#### Step 3: Restart Services

```bash
# Remove MAS services
docker compose down matrix-auth-service mas-postgres

# Restart Synapse with old config
docker compose restart synapse element-web
```

#### Step 4: Verify Rollback

```bash
# Check services running
docker compose ps

# Test SSO login via Synapse (old flow)
# Go to Element and login with Pocket ID
```

---

## Post-Deployment

### Maintenance Tasks

#### Regular Health Checks

```bash
# Check MAS health
docker compose exec matrix-auth-service mas-cli doctor

# Check logs for errors
docker compose logs matrix-auth-service --tail 100 | grep -i error

# Monitor database size
docker compose exec mas-postgres psql -U mas -d mas -c "\dt+"
```

#### Rotating Secrets

Periodically rotate MAS secrets:

```bash
# Generate new key
NEW_KEY=$(openssl rand -base64 64)

# Add to mas-config.yaml keys array
# Update MAS_SECRETS_KEYS in .env
# Restart MAS
docker compose restart matrix-auth-service
```

#### Backup MAS Database

```bash
# Regular backup
docker compose exec mas-postgres pg_dump -U mas mas > backup_mas_$(date +%Y%m%d).sql
```

### Monitoring

**Key metrics to monitor:**
- MAS container health
- Authentication success/failure rates
- Session creation/expiration
- Database size and performance
- OIDC upstream (Pocket ID) availability

---

## Security Considerations

### Secrets Management

- ✅ Use strong, randomly generated secrets
- ✅ Store secrets in `.env` file (gitignored)
- ✅ Never commit secrets to version control
- ✅ Rotate secrets periodically (every 6-12 months)
- ✅ Use different secrets for each component

### Network Security

- ✅ MAS only accessible via Traefik (HTTPS)
- ✅ Postgres databases not exposed externally
- ✅ Internal communication uses Docker network
- ✅ OIDC flows use PKCE for additional security

### Session Security

- ✅ Short-lived access tokens
- ✅ Refresh tokens for long-lived sessions
- ✅ Session timeout configuration in MAS
- ✅ Device session management UI for users

---

## References

### Official Documentation

- **MAS Documentation**: https://matrix-org.github.io/matrix-authentication-service/
- **MAS GitHub**: https://github.com/matrix-org/matrix-authentication-service
- **Synapse MSC3861**: https://element-hq.github.io/synapse/latest/usage/configuration/config_documentation.html#experimental_features
- **Matrix.org MAS Migration**: https://matrix.org/blog/2025/04/morg-now-running-mas/

### Community Guides

- **Docker Compose Setup**: https://willlewis.co.uk/blog/posts/stronger-matrix-auth-mas-synapse-docker-compose/
- **Ansible Playbook**: https://github.com/spantaleev/matrix-docker-ansible-deploy/blob/master/docs/configuring-playbook-matrix-authentication-service.md
- **OIDC Compatibility**: https://areweoidcyet.com/

### Support

- **Matrix Room**: `#matrix-authentication-service:matrix.org`
- **Synapse Room**: `#synapse:matrix.org`
- **GitHub Issues**: https://github.com/matrix-org/matrix-authentication-service/issues

---

## Conclusion

Deploying MAS is a significant upgrade that:
- ✅ Enables Element X support
- ✅ Provides QR code login
- ✅ Future-proofs your Matrix server
- ✅ Aligns with Matrix ecosystem direction

While it adds complexity, the benefits outweigh the costs as the Matrix ecosystem moves toward OIDC-native authentication.

**When you're ready to deploy**, follow this guide step-by-step, test thoroughly, and you'll have a modern Matrix authentication setup!

---

**Document Version:** 1.0
**Last Updated:** 2025-10-24
**Status:** Ready for implementation when needed
**Estimated Time:** 1-2 hours for full deployment
