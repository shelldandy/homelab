# MCP (Model Context Protocol) Service

This service provides MCP-to-OpenAPI proxy functionality using [mcpo](https://github.com/open-webui/mcpo), allowing Open WebUI to interact with MCP tool servers through standard REST APIs.

## Overview

The MCP service runs internally on the backend network and converts MCP tool servers into OpenAPI-compatible REST endpoints. This allows Open WebUI to easily integrate with various MCP-based tools without implementing the MCP protocol directly.

## Quick Start

1. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

2. Start the service:
   ```bash
   docker compose up -d
   ```

3. Check the logs:
   ```bash
   docker compose logs -f
   ```

## Configuration

### Environment Variables

- `TZ`: Timezone for MCP servers (default: America/New_York)
- `CONFIG_PATH`: Base path for configuration storage

### Current MCP Servers

The service is currently configured with:

- **mcp-server-time**: Provides time-related functions
  - Get current time
  - Time zone conversions
  - Date formatting

## API Access

### Internal Access (Docker Network)

- **Base URL**: `http://mcp:8000`
- **Documentation**: `http://mcp:8000/docs`
- **OpenAPI Spec**: `http://mcp:8000/openapi.json`

### Integration with Open WebUI

1. In Open WebUI, go to Settings → Admin Panel → OpenAPI Servers
2. Add a new OpenAPI server with URL: `http://mcp:8000`
3. The MCP tools will be automatically discovered and available

## Adding Additional MCP Servers

To add more MCP servers, modify the `docker-compose.yml` command section. For example, to add multiple servers:

```yaml
command: >
  sh -c "
  pip install mcpo uv &&
  uvx mcpo --host 0.0.0.0 --port 8000 -- uvx mcp-server-time --local-timezone=${TZ:-America/New_York}
  "
```

For multiple servers, you can chain them or create separate mcpo instances on different ports.

## Available MCP Servers

Popular MCP servers you can add:

- **mcp-server-time**: Time utilities
- **mcp-server-filesystem**: File system operations
- **mcp-server-brave-search**: Web search via Brave
- **mcp-server-github**: GitHub integration

Find more at: https://github.com/modelcontextprotocol/servers

## Troubleshooting

### Health Check

The service includes a health check that verifies the API documentation is accessible:

```bash
docker compose ps
```

### Logs

View detailed logs:

```bash
docker compose logs mcp
```

### Manual Testing

Test the API directly:

```bash
# From another container on the backend network
curl http://mcp:8000/docs
curl http://mcp:8000/openapi.json
```

## Security

This service runs only on the internal backend network and is not exposed externally. It's designed to be consumed by Open WebUI and other internal services only.

## Dependencies

- Python 3.11
- mcpo (MCP-to-OpenAPI proxy)
- uv (Python package installer)
- mcp-server-time (example MCP server)