# vLLM

High-performance LLM inference server with AMD ROCm GPU acceleration.

## Overview

vLLM is a fast and easy-to-use library for LLM inference and serving. This setup uses AMD's optimized ROCm Docker image for high-performance inference on AMD GPUs.

## Hardware Requirements

- AMD GPU with ROCm support (RX 6000/7000 series, MI series)
- ROCm drivers installed on host system
- Sufficient GPU memory for your chosen model

## Quick Start

1. Copy environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your configuration paths and model preferences

3. Start the service:
   ```bash
   docker compose up -d
   ```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CONFIG_PATH` | `/opt/vllm` | Path for model cache and configuration |
| `VLLM_MODEL` | `microsoft/DialoGPT-medium` | HuggingFace model to load |
| `VLLM_HOST` | `0.0.0.0` | Server bind address |
| `VLLM_PORT` | `8000` | Server port |
| `VLLM_GPU_MEMORY_UTILIZATION` | `0.9` | GPU memory usage fraction |
| `VLLM_MAX_MODEL_LEN` | `2048` | Maximum sequence length |
| `VLLM_TENSOR_PARALLEL_SIZE` | `1` | Number of GPUs for tensor parallelism |

### Model Selection

Popular models that work well with vLLM:

- **Small**: `microsoft/DialoGPT-medium` (117M parameters)
- **Medium**: `microsoft/DialoGPT-large` (345M parameters)  
- **Large**: `meta-llama/Llama-2-7b-chat-hf` (7B parameters)
- **Instruction**: `mistralai/Mistral-7B-Instruct-v0.1` (7B parameters)

## API Usage

vLLM provides an OpenAI-compatible API server. Once running, you can interact with it at `http://localhost:8000`.

### Example API Call

```bash
curl -X POST "http://localhost:8000/v1/completions" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "microsoft/DialoGPT-medium",
       "prompt": "Hello, how are you?",
       "max_tokens": 50,
       "temperature": 0.7
     }'
```

### Chat Completions API

```bash
curl -X POST "http://localhost:8000/v1/chat/completions" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "microsoft/DialoGPT-medium",
       "messages": [
         {"role": "user", "content": "Hello, how are you?"}
       ],
       "max_tokens": 50
     }'
```

## Integration

### With Open WebUI

Add vLLM as a model provider in Open WebUI:
1. Go to Settings → Models
2. Add endpoint: `http://vllm:8000/v1`
3. Set API key (if configured)

### With Other Services

The vLLM server is accessible on the `backend` network at `http://vllm:8000` for other homelab services.

## Monitoring

### View Logs
```bash
docker compose logs -f vllm
```

### Check GPU Usage
```bash
# On host system
rocm-smi
# or
radeontop
```

## Troubleshooting

### Common Issues

**Model Download Fails**
- Ensure internet connectivity
- Check if model exists on HuggingFace
- Verify sufficient disk space in `CONFIG_PATH`

**Out of Memory Errors**
- Reduce `VLLM_GPU_MEMORY_UTILIZATION` (try 0.8 or 0.7)
- Use a smaller model
- Decrease `VLLM_MAX_MODEL_LEN`

**ROCm Not Detected**
- Verify ROCm installation: `rocm-smi`
- Check GPU devices are accessible: `ls /dev/dri`
- Ensure user is in `video` group

**Slow Inference**
- Increase `VLLM_GPU_MEMORY_UTILIZATION` if memory allows
- Use quantized models for better performance
- Check GPU utilization with `rocm-smi`

### Performance Tuning

For optimal performance:
1. Use the highest `VLLM_GPU_MEMORY_UTILIZATION` your GPU can handle
2. Choose appropriate `VLLM_MAX_MODEL_LEN` for your use case
3. Consider using multiple GPUs with `VLLM_TENSOR_PARALLEL_SIZE > 1`

## Model Management

Models are automatically downloaded to `${CONFIG_PATH}/huggingface/` on first use. Large models may take significant time and storage:

- 7B models: ~13GB
- 13B models: ~26GB
- 30B+ models: 60GB+

Clean up unused models by removing directories from the cache path.

## Security

- vLLM runs on the internal `backend` network by default
- No authentication is configured by default
- For external access, configure Traefik reverse proxy with authentication