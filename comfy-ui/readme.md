# [comfy-ui](https://github.com/comfyanonymous/ComfyUI)

The most powerful and modular diffusion model GUI, api and backend with a graph/nodes interface.

Using docker image from: https://github.com/YanWenKun/ComfyUI-Docker

## Downloading new models

See: https://huggingface.co/docs/hub/models-downloading

```sh

git clone git@hf.co:<MODEL ID>
# example: git clone git@hf.co:bigscience/bloom
```

## Hardlink models

cd into the repo then run:

```sh

# example
ln example.safetensors /path/to/CONFIG_PATH/ComfyUI/models/<DIRECTORY>/example.safetensors

# Concrete example
ln flux1-dev-fp8.safetensors /path/to/CONFIG_PATH/ComfyUI/models/checkpoints/flux1-dev-fp8.safetensors
```

## Networking

Since I have a dedicated AI machine running on a different machine than the one for the other services there's a dummy/proxy service i can call on the main machine

```sh
docker compose -f frontend.yml up -d
```
