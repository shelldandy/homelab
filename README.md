# Docker Compose Setup

This is a docker-compose setup for a few services I use on my homelab machine.

## Tips & Tricks

### Migrate from named to bind volume

```sh
docker-compose down
```

```yml
# Add to docker-compose
volume-copier:
  image: alpine
  volumes:
    # Named volume
    - data:/source
    # Bind volume path
    - ${CONFIG_PATH}/data:/destination
  command: sh -c "cp -av /source/. /destination/ && echo 'Config copy complete'"
```

Then run this on the directory

```sh
docker-compose run --rm volume-copier
```

You can now update the volume paths in the services that need it.
