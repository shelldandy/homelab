# Gitea with Actions Runner

To set up the Actions Runner:

1. First start Gitea without the runner:

```bash
docker-compose up -d gitea db
```

2. After Gitea is running, get the runner registration token:

   - Log into Gitea web interface
   - Go to Site Administration → Actions → Runners
   - Click "Create new runner" to get a registration token
   - Copy the token

3. Add the token to your `.env` file:

```bash
RUNNER_REGISTRATION_TOKEN=your_token_here
```

4. Start the runner:

```bash
docker-compose up -d runner
```

Key features of this setup:

- Runner has access to Docker socket to run containerized workflows
- Includes predefined labels for Ubuntu runners
- Stores runner data in the same data directory as other services
- Automatically registers with your Gitea instance
- Can run Docker-in-Docker workflows

Some important notes:

1. The runner needs Docker socket access to run containers
2. You can customize runner labels to support different environments
3. The runner will auto-register using the provided token
4. Runner data is persisted in `${DATA_PATH}/runner`

To check the runner status:

```bash
docker logs gitea-runner
```

Would you like me to explain how to:

1. Set up specific workflow examples?
2. Configure additional runner labels?
3. Set up runner-specific security policies?
