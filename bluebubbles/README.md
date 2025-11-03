# BlueBubbles

BlueBubbles server running in a macOS VM via Docker-OSX, integrated with the homelab's Traefik reverse proxy and Pocket ID authentication.

## Overview

This setup runs BlueBubbles in a macOS virtual machine using Docker-OSX. The service is accessible via:
- **VNC**: `bluebubbles-vnc.bowline.im` (protected with Pocket ID OIDC auth)
- **BlueBubbles API**: `bluebubbles.bowline.im` (handles its own authentication)

**macOS Version**: This configuration uses macOS Monterey (12) for proven stability and compatibility.

**Note on Docker Images**: Docker-OSX only publishes a few base images to Docker Hub (`:latest`, `:naked`, `:auto`). The specific macOS version is selected using the `SHORTNAME` environment variable (e.g., `SHORTNAME=monterey`), not via image tags. Version-specific tags like `:monterey` or `:ventura` are only for local builds.

## Prerequisites

Before starting, ensure you have:

1. **Required packages installed**:
   - `docker` or `podman`
   - `docker-compose` or `podman-compose`
   - `tigervnc` (or another VNC viewer) for accessing the VM

   **Note**: You do NOT need to install qemu on the host - the disk creation script runs it in a container!

2. **System requirements**:
   - `/dev/kvm` device available (virtualization support)
   - Sufficient disk space (at least 128GB for the macOS VM)

3. **Networks created**:
   ```bash
   docker network create frontend
   ```

4. **Traefik and Pocket ID running** for reverse proxy and authentication

## Initial Setup

### 1. Configure Environment

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

Edit `.env` to set your preferences (VNC password, screen resolution, etc.)

### 2. Create Virtual Disk

Create the main disk image for macOS using the provided script:

```bash
./create-disk.sh
```

This script runs qemu-img inside a Docker container, creating a 128GB disk at `${CONFIG_PATH}/maindisk.qcow2`.

To create a disk with a different size, pass it as an argument:
```bash
./create-disk.sh 256G  # Creates a 256GB disk
```

### 3. Run Initial Setup

Start the setup container to install macOS:

```bash
docker compose -f docker-compose.setup.yml up
```

**Note**: This will take a while as it downloads the Docker-OSX image and prepares the VM.

### 4. Install macOS

1. **Access VNC**: Connect to `bluebubbles-vnc.bowline.im` (authenticate via Pocket ID)

2. **Boot into recovery**: Select "MacOS Base System" from the boot loader

3. **Format the disk**:
   - Open Disk Utility
   - Select your drive and click "Erase"
   - Name it (e.g., "Macintosh HD")
   - Format: APFS (or "MacOS extended (Journaled)" for Monterey)
   - Click "Erase" and close Disk Utility

4. **Install macOS**: Click "Reinstall macOS" and follow the installation wizard

5. **Test iMessage**: Once on the desktop, test sending an iMessage to yourself to verify it works

### 5. Extract Boot Disk

**BEFORE shutting down the VM**, extract the generated boot disk:

```bash
docker cp bluebubbles-setup:/home/arch/OSX-KVM/OpenCore/OpenCore.qcow2 /mnt/docker-data/bluebubbles/bootdisk.qcow2
```

### 6. Shutdown Setup

Stop the setup container:

```bash
docker compose -f docker-compose.setup.yml down
```

## Production Usage

### Starting BlueBubbles

Once setup is complete and you have both disk images, start the production container:

```bash
docker compose up -d
```

### Installing BlueBubbles Server

1. Connect to VNC at `bluebubbles-vnc.bowline.im`
2. Inside macOS, download and install BlueBubbles from [bluebubbles.app/install](https://bluebubbles.app/install/)
3. Configure the BlueBubbles server (use port 1234)
4. The server will be accessible at `bluebubbles.bowline.im`

### Accessing the Services

- **VNC**: https://bluebubbles-vnc.bowline.im
  - Protected with Pocket ID authentication
  - Default password: Set in `.env` (default: `vncpass`)

- **BlueBubbles Server**: https://bluebubbles.bowline.im
  - Handles its own authentication
  - Configure in the BlueBubbles app inside macOS

### Managing the Service

```bash
# View logs
docker compose logs -f

# Restart service
docker compose restart

# Stop service
docker compose down

# Update container image
docker compose pull && docker compose up -d
```

## Private API Setup

To enable BlueBubbles Private API features:

1. Follow the [official Private API installation guide](https://docs.bluebubbles.app/private-api/installation)
2. When disabling SIP, follow instructions for "Physical Mac, INTEL"
3. **Do NOT** follow the VM-specific SIP instructions - use the standard guide

See [specs.md](./specs.md) for more details.

## Troubleshooting

### VM Won't Boot

- Check that `/dev/kvm` is accessible: `ls -l /dev/kvm`
- Verify virtualization is enabled in BIOS
- Check logs: `docker compose logs`

### iMessage Not Working

- Ensure you're using a valid Apple ID
- Check that the VM has internet connectivity
- May need to restart the setup from scratch with a new disk

### VNC Connection Issues

- Verify Traefik is running and the frontend network exists
- Check VNC password in `.env` matches what you're using
- Try connecting via Pocket ID authentication

### Performance Issues

- Increase allocated CPU/RAM (modify compose file)
- Use APFS instead of extended journaled filesystem
- Ensure host has sufficient resources

## File Structure

```
bluebubbles/
├── .env                          # Your configuration (not in git)
├── .env.example                  # Example configuration
├── create-disk.sh                # Script to create virtual disk (dockerized)
├── docker-compose.yml            # Production configuration
├── docker-compose.setup.yml      # Initial setup configuration
├── README.md                     # This file
└── specs.md                      # Original setup guide and reference
```

## Disk Images

Located at `${CONFIG_PATH}` (default: `/mnt/docker-data/bluebubbles/`):
- `maindisk.qcow2` - Main macOS disk (128GB+)
- `bootdisk.qcow2` - Boot disk with serial number and OpenCore config

**Important**: Back up these files regularly! They contain your entire macOS installation.

## Additional Notes

- The setup uses Docker-OSX's "naked" image for production (lighter and faster)
- All setup steps use Docker - no need to install qemu or other tools on the host
- ALSA errors in logs can be safely ignored
- The VM runs headless with VNC access only
- Screen resolution can be adjusted in `.env` (WIDTH/HEIGHT variables)

### Changing macOS Version

To use a different macOS version, edit the `SHORTNAME` environment variable in both docker-compose files:

**Available SHORTNAME values:**
- `high-sierra` (10.13)
- `mojave` (10.14)
- `catalina` (10.15)
- `big-sur` (11)
- `monterey` (12) - currently configured
- `ventura` (13)
- `sonoma` (14)
- `sequoia` (15)

**Note**: Changing the version after initial setup requires recreating the disk images.

## References

- [BlueBubbles Documentation](https://docs.bluebubbles.app/)
- [Docker-OSX Repository](https://github.com/sickcodes/Docker-OSX)
- [Original Setup Guide](./specs.md)
