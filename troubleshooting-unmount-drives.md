# Troubleshooting Drive Unmounting with systemd Automount

## Problem
Unable to unmount media drives due to systemd automount automatically remounting them when accessed.

## Diagnosis Steps

### 1. Check Current Mount Status
```bash
mount | grep -E "(media|share|cloud-backups|navidrome)"
df -h | grep -E "(media|share|cloud-backups|navidrome)"
```

### 2. Identify Processes Using the Drives
```bash
fuser -v /mnt/media /mnt/media2 /mnt/media3
lsof +D /mnt 2>/dev/null | head -20
```

### 3. Check for systemd Automount Units
```bash
systemctl list-units --all | grep -E "(automount|mount)" | grep -E "(media|cloud|navidrome)"
```

### 4. Check Docker Container Usage
```bash
docker ps --format "table {{.Names}}\t{{.Mounts}}" | grep -i media
find /home/bowlinedandy/homelab -name "docker-compose.yml" -exec grep -l "/mnt/media" {} \;
```

## Root Cause
systemd automount units automatically remount drives when they are accessed, even after manual unmounting. The drives were managed by these automount units:

- `mnt-media.automount`
- `mnt-media2.automount` 
- `mnt-media3.automount`
- `mnt-navidrome.automount`
- `mnt-cloud\x2dbackups.automount`

## Solution

### Stop Automount and Unmount Drives
```bash
# Media drives
sudo systemctl stop mnt-media.automount mnt-media2.automount mnt-media3.automount
sudo umount /mnt/media /mnt/media2 /mnt/media3

# Navidrome and cloud-backups
sudo systemctl stop mnt-navidrome.automount mnt-cloud\\x2dbackups.automount
sudo umount /mnt/navidrome /mnt/cloud-backups
```

### Prevent Auto-start on Reboot (Optional)
```bash
# Media drives
sudo systemctl disable mnt-media.automount mnt-media2.automount mnt-media3.automount

# Navidrome and cloud-backups  
sudo systemctl disable mnt-navidrome.automount mnt-cloud\\x2dbackups.automount
```

## Key Findings

### Drive Status Before Unmounting
- `/mnt/media` (7.3T, 91% full) - /dev/sdc1
- `/mnt/media2` (13T, 97% full) - /dev/sde1  
- `/mnt/media3` (3.6T, 100% full) - /dev/sdf1
- `/mnt/navidrome` (916G, 62% full) - /dev/sdb1
- `/mnt/cloud-backups` (7.3T, 93% full) - /dev/sdd1

### mergerfs Status
The `media-merged` mergerfs drive was already inactive:
- No active mergerfs processes running
- systemd unit `mnt-media\x2dmerged-share.mount` was in "loaded inactive dead" state
- mergerfs automatically becomes unavailable when underlying drives are unmounted

## Notes
- Use escaped characters (`\\x2d`) in systemctl commands for mount names with hyphens
- systemd automount will remount drives on any access, including simple `ls` commands
- mergerfs mounts depend on their underlying drives being available
- Always check for Docker containers that might be using the mounts before unmounting