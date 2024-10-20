## Environment Setup

This project requires a DuckDNS token to be set. You can do this by:

1. Creating a `.env` file in the project root with the content:
   ```
   DUCKDNS_TOKEN=your_actual_token_here
   ```
2. Or by setting the environment variable before running docker-compose:
   ```
   export DUCKDNS_TOKEN=your_actual_token_here
   docker-compose up -d
   ```

Make sure to keep your token secret and never commit it to version control.
