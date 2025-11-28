# Homelab Backup Service

Automated daily backups of critical homelab data using [offen/docker-volume-backup](https://github.com/offen/docker-volume-backup).

## Overview

This backup system creates encrypted, compressed backups of your homelab data daily at 4:00 AM with dual storage:

- **Local backups**: Full backups stored on `/dev/sdc` including all data
- **Cloud backups**: Encrypted backups to Backblaze B2, excluding large music files

### What Gets Backed Up

| Data Source                      | Description                    | Local | Backblaze B2  |
| -------------------------------- | ------------------------------ | ----- | ------------- |
| `/mnt/docker-data`               | Docker configurations and data | ✅    | ✅            |
| `/mnt/navidrome` (configs)       | Navidrome database and configs | ✅    | ✅            |
| `/mnt/navidrome/share`           | Music files                    | ✅    | ❌ (excluded) |
| `~/homelab/immich/data/library`  | Immich photos and videos       | ✅    | ✅            |
| `~/homelab/immich/data/postgres` | Immich database                | ✅    | ✅            |

### Backup Schedule

- **Time**: Daily at 4:00 AM
- **Duration**: ~5-15 minutes (all services stopped during backup)
- **Retention**: 14 days for both local and cloud backups
- **Encryption**: GPG passphrase-based encryption

## Setup Instructions

### 1. Prerequisites

Ensure the `backend` Docker network exists:

```bash
docker network create backend
```

### 2. Mount `/dev/sdc` (if not already mounted)

```bash
# Create mount point
sudo mkdir -p /mnt/backup-drive

# Find UUID of /dev/sdc
sudo blkid /dev/sdc

# Add to /etc/fstab (replace UUID with your actual UUID)
UUID=your-uuid-here /mnt/backup-drive ext4 defaults 0 2

# Mount the drive
sudo mount -a
```

### 3. Create Backblaze B2 Bucket

1. Log in to [Backblaze B2](https://www.backblaze.com/b2/cloud-storage.html)
2. Go to **Buckets** → **Create a Bucket**
   - Bucket Name: `homelab-backups` (or your choice)
   - Files in Bucket: **Private**
   - Encryption: **Disable** (we use GPG encryption)
3. Go to **App Keys** → **Add a New Application Key**
   - Name: `homelab-backup-service`
   - Allow access to: Select your bucket
   - Permissions: **Read and Write**
   - Save the **keyID** and **applicationKey** (shown only once!)

### 4. Configure Environment Variables

```bash
cd /home/bowlinedandy/homelab/backup
cp .env.example .env
nano .env
```

Fill in the required values:

- `GPG_PASSPHRASE`: Strong passphrase for encryption (store securely!)
- `LOCAL_BACKUP_PATH`: Path on `/dev/sdc` (e.g., `/mnt/backup-drive/homelab`)
- `B2_BUCKET_NAME`: Your B2 bucket name
- `B2_KEY_ID`: Application Key ID from Backblaze
- `B2_APPLICATION_KEY`: Application Key from Backblaze
- `B2_ENDPOINT`: S3-compatible endpoint for your region (see `.env.example`)

### 5. Add Stop Labels to All Services

To ensure safe backups, all Docker services must be stopped during backup. Add this label to every service's `docker-compose.yml`:

```yaml
services:
  your-service:
    labels:
      - "docker-volume-backup.stop-during-backup=true"
```

Run this command to add labels to all services automatically:

```bash
cd /home/bowlinedandy/homelab
for dir in */; do
  if [ -f "${dir}docker-compose.yml" ] && [ "$dir" != "backup/" ]; then
    echo "Adding label to ${dir}docker-compose.yml"
    # You'll need to add the label manually to each file
  fi
done
```

**Note**: Labels must be added to the main service in each compose file (not sidecar containers).

### 6. Start the Backup Service

```bash
cd /home/bowlinedandy/homelab/backup
docker compose up -d
```

### 7. Verify Setup

Check that both backup containers are running:

```bash
docker compose ps
```

View logs:

```bash
# Local backup logs
docker logs -f backup-local

# Backblaze backup logs
docker logs -f backup-backblaze
```

### 8. Test Backup (Optional but Recommended)

Trigger a manual backup to test:

```bash
# Test local backup
docker compose exec backup-local backup

# Test Backblaze backup
docker compose exec backup-backblaze backup
```

## Backup Storage Estimates

### Local Storage (`/dev/sdc`)

- Per backup: ~15-20 GB (full data including music)
- 14 days retention: ~210-280 GB
- **Ensure `/dev/sdc` has at least 300 GB free**

### Backblaze B2

- Per backup: ~5-10 GB (excludes music files)
- 14 days retention: ~70-140 GB
- **Monthly cost**: ~$0.42-$0.84 at $6/TB/month

## Restore Procedures

### Restore from Local Backup

1. List available backups:

   ```bash
   ls -lh /mnt/backup-drive/homelab/
   ```

2. Extract a backup:

   ```bash
   # Navigate to backup directory
   cd /mnt/backup-drive/homelab

   # Decrypt and extract
   gpg --decrypt backup-local-2025-01-15_04-00-00.tar.gz.gpg | tar -xzv -C /tmp/restore
   ```

3. Enter your GPG passphrase when prompted

4. Restore specific files as needed:
   ```bash
   # Example: Restore Immich photos
   sudo rsync -av /tmp/restore/backup/immich-library/ ~/homelab/immich/data/library/
   ```

### Restore from Backblaze B2

1. Install and configure B2 CLI (if not already installed):

   ```bash
   # Install
   pip install b2

   # Authorize
   b2 authorize-account <B2_KEY_ID> <B2_APPLICATION_KEY>
   ```

2. List available backups:

   ```bash
   b2 ls homelab-backups
   ```

3. Download a backup:

   ```bash
   b2 download-file-by-name homelab-backups backup-b2-2025-01-15_04-00-00.tar.gz.gpg /tmp/
   ```

4. Decrypt and extract:

   ```bash
   cd /tmp
   gpg --decrypt backup-b2-2025-01-15_04-00-00.tar.gz.gpg | tar -xzv -C /tmp/restore
   ```

5. Restore files as needed (same as local restore)

## Monitoring and Maintenance

### Check Backup Status

```bash
# View recent backup logs
docker logs --tail 100 backup-local
docker logs --tail 100 backup-backblaze

# Check last backup time
ls -lht /mnt/backup-drive/homelab/ | head -n 5
```

### Set Up Notifications (Optional)

Edit `.env` and add a notification URL:

```env
# Discord webhook
NOTIFICATION_URLS=discord://webhook_id/webhook_token

# Multiple services (comma-separated)
NOTIFICATION_URLS=discord://...,gotify://host/token
```

Supported services:

- Discord
- Slack
- Telegram
- Gotify
- Email (SMTP)
- And many more: https://containrrr.dev/shoutrrr/v0.8/services/overview/

### Manual Backup Triggers

```bash
# Trigger backup outside of schedule
docker compose exec backup-local backup
docker compose exec backup-backblaze backup
```

### Update Backup Containers

```bash
cd /home/bowlinedandy/homelab/backup
docker compose pull
docker compose up -d
```

## Troubleshooting

### Backups Not Running

1. Check container status:

   ```bash
   docker compose ps
   ```

2. Check for errors in logs:

   ```bash
   docker compose logs
   ```

3. Verify cron schedule:
   ```bash
   docker compose exec backup-local cat /etc/crontabs/root
   ```

### Services Not Stopping During Backup

Ensure labels are correctly added to all services:

```bash
docker inspect <container-name> | grep docker-volume-backup
```

### Backblaze Upload Failures

1. Verify credentials in `.env`
2. Check B2 endpoint is correct for your region
3. Ensure application key has read/write permissions
4. Check network connectivity:
   ```bash
   docker compose exec backup-backblaze ping -c 3 s3.us-west-000.backblazeb2.com
   ```

### Insufficient Storage

If backups are failing due to storage:

1. Reduce retention period in `.env`:

   ```env
   BACKUP_RETENTION_DAYS=7
   ```

2. Manually clean old backups:

   ```bash
   # Local
   find /mnt/backup-drive/homelab -type f -mtime +7 -delete

   # Backblaze (use B2 lifecycle rules in web UI)
   ```

## Security Best Practices

1. **GPG Passphrase**: Store in a password manager, not in plain text
2. **B2 Credentials**: Use application keys with minimal permissions (bucket-specific)
3. **Backup Testing**: Test restores monthly to ensure backups are valid
4. **Offsite Storage**: Backblaze B2 provides geographic redundancy
5. **3-2-1 Rule**: 3 copies, 2 different media, 1 offsite (we have 2 copies, 2 media, 1 offsite)

## Additional Notes

- **Immich Database Dumps**: Immich auto-creates daily database dumps at 2:00 AM in `data/library/backups`. Our backup at 4:00 AM captures these.
- **Navidrome Music**: Music files in `/mnt/navidrome/share` are backed up locally but excluded from cloud to save costs. Ensure you have another source for music files.
- **Downtime Window**: All services are stopped from 4:00-4:15 AM. Plan maintenance accordingly.
- **Network Bandwidth**: Initial B2 upload may take hours depending on data size and upload speed.

## Related Documentation

- [offen/docker-volume-backup Documentation](https://offen.github.io/docker-volume-backup/)
- [Backblaze B2 S3-Compatible API](https://www.backblaze.com/b2/docs/s3_compatible_api.html)
- [Immich Backup Guide](https://immich.app/docs/administration/backup-and-restore)
