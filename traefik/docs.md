Transport
respondingTimeouts¶

respondingTimeouts are timeouts for incoming requests to the Traefik instance. Setting them has no effect for UDP entryPoints.
transport.respondingTimeouts.readTimeout

Optional, Default=60s

readTimeout is the maximum duration for reading the entire request, including the body.

If zero, no timeout exists.
Can be provided in a format supported by time.ParseDuration or as raw values (digits). If no units are provided, the value is parsed assuming seconds. We strongly suggest adapting this value accordingly to your needs.
File (YAML)
File (TOML)
CLI

## Static configuration

--entryPoints.name.address=:8888
--entryPoints.name.transport.respondingTimeouts.readTimeout=42

transport.respondingTimeouts.writeTimeout

Optional, Default=0s

writeTimeout is the maximum duration before timing out writes of the response.

It covers the time from the end of the request header read to the end of the response write. If zero, no timeout exists.
Can be provided in a format supported by time.ParseDuration or as raw values (digits). If no units are provided, the value is parsed assuming seconds.
File (YAML)

## Static configuration

entryPoints:
name:
address: ":8888"
transport:
respondingTimeouts:
writeTimeout: 42

File (TOML)
CLI
transport.respondingTimeouts.idleTimeout

Optional, Default=180s

idleTimeout is the maximum duration an idle (keep-alive) connection will remain idle before closing itself.

If zero, no timeout exists.
Can be provided in a format supported by time.ParseDuration or as raw values (digits). If no units are provided, the value is parsed assuming seconds.
File (YAML)

## Static configuration

entryPoints:
name:
address: ":8888"
transport:
respondingTimeouts:
idleTimeout: 42
