# Jarvis - Wyoming Speech Services

Home Assistant voice services stack with AMD GPU acceleration for Spanish language processing.

## Services

### Whisper - Speech-to-Text (STT)
- **Image**: `fyhertz/rocm-wyoming-whisper:latest`
- **Port**: `10300`
- **Language**: Spanish (`es`)
- **GPU**: AMD ROCm acceleration via RX 7900XTX
- **Model**: `small-int8` (optimized for VRAM)

### Piper - Text-to-Speech (TTS)
- **Image**: `rhasspy/wyoming-piper:latest`
- **Port**: `10200`
- **Voice**: `es_ES-davefx-medium` (Spanish)
- **Runtime**: CPU (ROCm support not yet available)

## Prerequisites

### EndeavourOS Setup
```bash
# Install ROCm runtime
yay -S rocm-opencl-runtime

# Add user to video group
sudo usermod -a -G video $USER

# Verify ROCm installation
rocminfo

# Create external networks
docker network create backend
```

### Environment Variables
Create `.env` file:
```env
CONFIG_PATH=/path/to/config
```

## Usage

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

## Home Assistant Integration

Add to Home Assistant `configuration.yaml`:

```yaml
# Speech-to-Text (Whisper)
stt:
  - platform: wyoming
    uri: tcp://jarvis-host:10300

# Text-to-Speech (Piper)
tts:
  - platform: wyoming
    uri: tcp://jarvis-host:10200
```

## Configuration

### Whisper Options
- **MODEL**: `tiny`, `base`, `small`, `small-int8`, `medium`, `large`
- **LANGUAGE**: `es` (Spanish), `en` (English), etc.
- **BEAM_SIZE**: Higher = more accurate, slower (1-10)

### Piper Voice Options
Spanish voices available:
- `es_ES-davefx-medium`
- `es_ES-mls_10246-low`
- `es_MX-ald-medium`

Change voice in docker-compose.yml command or via Home Assistant GUI.

## Troubleshooting

### GPU Not Detected
```bash
# Check ROCm installation
rocminfo

# Verify device permissions
ls -la /dev/kfd /dev/dri

# Check user groups
groups $USER
```

### Container Issues
```bash
# Check container logs
docker compose logs whisper
docker compose logs piper

# Restart services
docker compose restart
```

## Performance Notes

- **Whisper**: GPU-accelerated on AMD RX 7900XTX via ROCm
- **Piper**: CPU-only (fast enough for real-time TTS)
- **Memory**: Whisper `small-int8` model uses ~2GB VRAM
- **First run**: Downloads models automatically (may take time)