# Matrix Server Quick Start

## ✅ Current Status

Your Matrix server is **running successfully**! All services are operational:

- ✅ Synapse (Matrix homeserver)
- ✅ PostgreSQL (database)
- ✅ Redis (cache)
- ✅ Element Web (web client)
- ✅ Synapse Admin (admin UI)

## 🌐 Access URLs

- **Matrix Server API**: https://chat.bowline.im
- **Element Web Client**: https://element.bowline.im
- **Admin Console**: https://chat-console.bowline.im

## 👤 Create Your First User

To create an admin user, run:

```bash
docker exec -it synapse register_new_matrix_user \
  http://localhost:8008 \
  -c /data/homeserver.yaml \
  --admin
```

You'll be prompted for:
- **Username**: (e.g., `admin`, `yourname`)
- **Password**: (your choice)
- **Confirmation**: yes

Your Matrix ID will be: `@username:bowline.im`

## 🚀 Using Element Web

1. Visit https://element.bowline.im
2. Click **"Sign In"**
3. Ensure homeserver is set to: `https://chat.bowline.im`
4. Enter your Matrix ID: `@username:bowline.im`
5. Enter your password
6. Start chatting!

## 🔧 Admin Tasks

### Access Admin UI

1. Visit https://chat-console.bowline.im
2. Enter homeserver: `https://chat.bowline.im`
3. Log in with admin credentials
4. Manage users, rooms, and settings

### Create Additional Users

```bash
# Regular user
docker exec -it synapse register_new_matrix_user \
  http://localhost:8008 \
  -c /data/homeserver.yaml

# Admin user
docker exec -it synapse register_new_matrix_user \
  http://localhost:8008 \
  -c /data/homeserver.yaml \
  --admin
```

### Enable Public Registration (Optional)

To allow anyone to register:

1. Edit `synapse-config.yaml`:
   ```yaml
   enable_registration: true
   ```

2. Restart Synapse:
   ```bash
   docker compose restart synapse
   ```

## 📝 Configuration Files

All configuration is version controlled in this directory:

- **docker-compose.yml**: Service definitions
- **synapse-config.yaml**: Custom Synapse settings (PostgreSQL, Redis, features)
- **element-config.json**: Element Web client settings
- **.env**: Environment variables (not version controlled)

## 🔍 Monitoring

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f synapse
docker compose logs -f postgres
docker compose logs -f redis
```

### Check Status

```bash
docker compose ps
```

### Test API

```bash
# Should return version info
curl http://localhost:8008/_matrix/client/versions
```

## 🌍 Federation

Your server is configured for federation (connecting to other Matrix servers).

### Requirements

1. **Port 8448 must be accessible** from the internet
2. **DNS records**:
   - A record: `chat.bowline.im` → your server IP
   - (Optional) SRV record for federation

### Test Federation

Visit: https://federationtester.matrix.org/

### Open Firewall Port

```bash
# Allow federation port
sudo ufw allow 8448/tcp comment 'Matrix Federation'

# Verify
sudo ufw status
```

## 🛠️ Common Commands

```bash
# Restart all services
docker compose restart

# Update images
docker compose pull && docker compose up -d

# Stop everything
docker compose down

# View database logs
docker compose logs -f postgres

# Access PostgreSQL
docker exec -it matrix-postgres psql -U synapse -d synapse
```

## 📊 Next Steps

1. **Create your admin user** (see above)
2. **Test login** via Element Web
3. **Invite friends** to join your server
4. **Set up federation** (if desired)
5. **Configure email notifications** (optional, see README.md)
6. **Add TURN server** for VoIP (optional, see README.md)

## 🔒 Security Notes

- Registration is **disabled by default** (only admins can create users)
- Rate limiting is **enabled** to prevent abuse
- Encryption is **enabled by default** for all rooms
- Keep your server **updated regularly**

## 📚 Documentation

- Full README: `README.md`
- Synapse Docs: https://matrix-org.github.io/synapse/latest/
- Matrix Docs: https://matrix.org/docs/
- Element Docs: https://element.io/help

## 💡 Tips

- **Backup important data**:
  - `/mnt/docker-data/matrix/synapse/` (keys, config, media)
  - `/mnt/docker-data/matrix/postgres/` (database)
- **Monitor disk space** (media uploads can grow)
- **Use admin UI** for user management
- **Test federation** before inviting external users

Enjoy your Matrix server! 🎉
