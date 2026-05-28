# llama-cpp (ROCm)

OpenAI-compatible LLM server for Home Assistant's Assist conversation agent.
Runs `llama.cpp`'s `server` binary on AMD ROCm against the RX 7900 XTX.

## Model

Qwen3-4B-Instruct (Q4_K_M GGUF, ~3 GB VRAM). Pulled on first start via the
`-hf` flag — no manual download needed. Cached under `${CONFIG_PATH}/cache`
(mounted at `/root/.cache` inside the container, so it covers both the
HF model cache at `~/.cache/huggingface/hub` and the llama.cpp prompt cache).
A container recreate reuses this cache — startup drops from minutes to ~1 s.

To swap models, edit the `-hf ...` arg in `docker-compose.yml`. Reasonable
upgrades on the 7900 XTX:

- `unsloth/Qwen3-14B-Instruct-GGUF:Q4_K_M` (~9 GB)
- `unsloth/Qwen3-30B-A3B-Instruct-GGUF:Q4_K_M` (~18 GB, MoE — strong)

## Network

Attached to the `backend` external network and publishes port `8080` on the
host (`0.0.0.0:8080`) so Home Assistant on a different LAN machine
(`10.0.0.99`) can reach it at `http://10.0.0.98:4545/v1`.

If you ever move HA onto this host, you can drop the `ports:` block and use
the Docker-internal `http://llama-cpp:8080/v1` instead.

**Security note:** `llama-server` has no authentication. The port is exposed
on the LAN, not the internet, but anyone on the LAN can hit the endpoint.
For an auth-gated path, add a Traefik label and route via the existing
`oidc-auth` middleware (see `home-assistant/docker-compose.yml` for the
labeling pattern).

## Home Assistant wiring

1. Settings → Devices & Services → Add Integration → **OpenAI Conversation**
2. Base URL: `http://10.0.0.98:4545/v1`
3. API key: any non-empty string (llama.cpp ignores it)
4. Model: `qwen3-4b-instruct` (matches the `--alias` in the compose command)
5. Enable **"Control Home Assistant"** so it can call Assist intents.
6. Settings → Voice assistants → your pipeline → **Conversation agent** →
   switch from the default to the new OpenAI Conversation entry. Keep
   Whisper (STT) and Piper (TTS) selections unchanged.

## ROCm notes

- Device passthrough mirrors `ollama/` and `jarvis/whisper`: `/dev/kfd`,
  `/dev/dri`, plus the `video` group.
- `HSA_OVERRIDE_GFX_VERSION=11.0.0` matches the 7900 XTX (gfx1100) and avoids
  the common "GPU not detected" path when ROCm misreads the arch.
- The ggml-org ROCm image is built but not CI-tested upstream; if it fails to
  start with this gfx, fall back to building from `ggml-org/llama.cpp`
  Dockerfile (`.devops/cuda.Dockerfile` analog `.devops/rocm.Dockerfile`) or
  use `rocm/llama.cpp` from Docker Hub.
