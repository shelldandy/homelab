# [iCloud Photos Downloader](https://github.com/boredazfcuk/docker-icloudpd/tree/master)

An Alpine Linux container for the iCloud Photos Downloader command line utility

## [MFA](https://github.com/boredazfcuk/docker-icloudpd/blob/master/CONFIGURATION.md#multifactor-authentication)

If your Apple ID account has multifactor authentication enabled, you will see that the container waits for a multifactor authentication cookie to be created:

```shell
ERROR    Cookie does not exist."
INFO      - Please create your cookie using the --Initialise script command line option."
INFO      - Syntax: docker exec -it <container name> sync-icloud.sh --Initialise"
INFO      - Example: docker exec -it icloudpd sync-icloud.sh --Initialise"
INFO     Restarting in 5 minutes..."
```

Without this cookie, synchronisation cannot be started.

As per the error, the container needs to be initialised by using the --Initialise command line option. With the first container still running, connect to it and launch the initialisation process by running the following at the terminal prompt (assuming the container name is `icloudpd`):

```shell
docker exec -it icloudpd sync-icloud.sh --Initialise
```

## [Failsafe feature](https://github.com/boredazfcuk/docker-icloudpd/blob/master/CONFIGURATION.md#failsafe-feature)

Make sure to create a `.mounted` file inside of the `dowload_path` directory used in the env file.
