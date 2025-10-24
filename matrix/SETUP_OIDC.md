# Matrix Synapse + Pocket ID OIDC Integration Setup

This guide walks you through configuring Matrix Synapse to use Pocket ID for SSO authentication.

## Prerequisites

- Matrix Synapse running and accessible at `https://matrix.bowline.im`
- Pocket ID running and accessible at `https://pocket-id.bowline.im` (or your configured subdomain)
- Admin access to Pocket ID

## Step 1: Create OIDC Client in Pocket ID

1. **Login to Pocket ID** admin interface at `https://pocket-id.bowline.im`

2. **Navigate to Applications/Clients** section

3. **Create New OIDC Client** with the following settings:
   - **Client Name**: `Matrix Synapse`
   - **Client Type**: `Confidential` (requires client secret)
   - **Application Type**: `Web Application`
   - **Grant Types**:
     - ✅ `authorization_code`
   - **Redirect URIs**:
     ```
     https://matrix.bowline.im/_synapse/client/oidc/callback
     ```
   - **Scopes**:
     - ✅ `openid` (required)
     - ✅ `profile` (for display name)
     - ✅ `email` (for email address)
   - **Post Logout Redirect URIs** (optional):
     ```
     https://element.bowline.im
     ```

4. **Save and note down**:
   - **Client ID** (e.g., `matrix-synapse`)
   - **Client Secret** (will be shown once - save it securely!)

5. **Configure Claims Mapping** (if needed):
   - Ensure `preferred_username` claim is mapped to username/userid field
   - Verify `email` and `name` claims are available

## Step 2: Configure Matrix Synapse

### Initial Setup (First Time Only)

Before starting the Matrix containers for the first time, you need to create the configuration file:

1. **Copy the example config to the data directory**:
   ```bash
   cd /home/bowlinedandy/homelab/matrix
   cp synapse-config.yaml.example data/synapse-config.yaml
   ```

2. **Edit the config file with your OIDC credentials**:
   ```bash
   nano data/synapse-config.yaml
   ```

3. **Find the OIDC section** (around line 78) and update these three values:
   ```yaml
   oidc_providers:
     - idp_id: pocketid
       idp_name: "Pocket ID"
       discover: true
       issuer: "https://auth.bowline.im"  # ← UPDATE: Your Pocket ID URL
       client_id: "your-client-id-here"    # ← UPDATE: From Pocket ID
       client_secret: "your-client-secret-here"  # ← UPDATE: From Pocket ID
   ```

4. **Save the file** (Ctrl+O, Enter, Ctrl+X in nano)

### Notes on Configuration Files

- **synapse-config.yaml.example**: Template file tracked in git (safe to commit)
- **data/synapse-config.yaml**: Your actual config with secrets (gitignored, never committed)
- The `data/` directory is in `.gitignore` to protect your credentials

## Step 3: Restart Matrix Synapse

Apply the configuration changes:

```bash
cd /home/bowlinedandy/homelab/matrix
docker compose restart synapse
```

Check logs for any errors:
```bash
docker compose logs -f synapse
```

Look for lines like:
- ✅ `Loaded OIDC provider 'Pocket ID'`
- ❌ If errors occur, check client ID/secret and issuer URL

## Step 4: Test the Integration

### Test via Element Web

1. **Navigate to**: `https://element.bowline.im`

2. **Click "Sign In"** - you should see:
   - Standard username/password fields (fallback)
   - **"Sign in with Pocket ID"** button (new!)

3. **Click "Sign in with Pocket ID"**:
   - Redirects to Pocket ID login
   - Enter Pocket ID credentials
   - Redirects back to Element - you're logged in!

4. **Check your Matrix ID**: Should be `@{username}:bowline.im`
   - Where `{username}` is your `preferred_username` from Pocket ID

### Test via Synapse Admin

1. Navigate to `https://matrix-console.bowline.im`
2. Login with admin credentials
3. Check "Users" section - OIDC users will show with external ID links

## Step 5: User Migration (Optional)

### For Existing Matrix Users

Existing users with password accounts can link their Pocket ID:

1. **Login with password** first
2. **Go to Settings** → **Security & Privacy**
3. **Link OIDC account** (if available in Element)
4. Future logins can use Pocket ID

### For New Users

If registration is enabled (`enable_registration: true`):
- New users can register via Pocket ID
- Matrix account created automatically on first OIDC login
- Username derived from Pocket ID `preferred_username`

## Troubleshooting

### "Login failed" or redirect loop

1. **Check Pocket ID redirect URI** matches exactly:
   ```
   https://matrix.bowline.im/_synapse/client/oidc/callback
   ```

2. **Verify issuer URL** in .env matches Pocket ID URL

3. **Check Synapse logs**:
   ```bash
   docker compose logs synapse | grep -i oidc
   ```

### "preferred_username not found"

1. In Pocket ID, ensure user profiles have username field populated
2. Alternative: Change data/synapse-config.yaml to use `email` instead:
   ```yaml
   user_mapping_provider:
     config:
       localpart_template: "{{ user.email.split('@')[0] }}"
   ```
   Then restart: `docker compose restart synapse`

### Users can't login with password anymore

If you accidentally disabled password auth:
1. Edit data/synapse-config.yaml
2. Ensure `password_config: enabled: true` exists (or remove any password_config section)
3. Restart: `docker compose restart synapse`

## Security Notes

- **Client Secret**: Stored in data/synapse-config.yaml (gitignored directory)
- **Never commit**: The data/ directory is in .gitignore - never commit it to git
- **HTTPS Required**: OIDC requires secure connections
- **Scopes**: Only request necessary scopes (openid, profile, email)
- **Logout**: Implement proper logout flow in Element config

## Advanced Configuration

### Auto-Join Rooms

Add new OIDC users to default rooms:
```yaml
# In data/synapse-config.yaml
auto_join_rooms:
  - "#welcome:bowline.im"
  - "#general:bowline.im"
```
Then restart: `docker compose restart synapse`

### Attribute Mapping Customization

Change how user attributes map in data/synapse-config.yaml:
```yaml
user_mapping_provider:
  config:
    localpart_template: "{{ user.preferred_username }}"
    display_name_template: "{{ user.name }}"
    email_template: "{{ user.email }}"
    # Add custom attributes:
    # picture_template: "{{ user.picture }}"
```
Then restart: `docker compose restart synapse`

### Force OIDC Only

To disable password login (not recommended initially):
```yaml
# In data/synapse-config.yaml
password_config:
  enabled: false
  localdb_enabled: false
```
Then restart: `docker compose restart synapse`

## References

- [Synapse OIDC Documentation](https://element-hq.github.io/synapse/latest/openid.html)
- [Pocket ID Documentation](https://pocket-id.org/docs/)
- [Element SSO Configuration](https://github.com/vector-im/element-web/blob/develop/docs/sso.md)
