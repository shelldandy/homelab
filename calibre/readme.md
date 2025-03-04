# calibre and calibre-web

## calibre

This is only needed the first time to setup the database which will be used by calibre-web.

Can be commented out after the first use and setup.

## calibre-web

### Setup

After setting up make sure to change the default password `admin123` optionally you can set another user to be the admin other than the `admin` user.

#### External binaries

Make sure to point to the appropriate calibre binaries to have book conversion available (ie: fully deprecating the need for normal calibre) under `Admin > Edit Basic Configuration > External Binaries`:

- Path to calibre binaries: `/usr/bin`
- Calibre E-Book Converter Settings: `/usr/bin/ebook-convert`
- Path to Kepubify E-Book Converter: `/usr/bin/kepubify`
- Location of Unrar binary: `/usr/bin/unrar`

#### Default theme

Set up a nicer default theme: `Admin > Edit UI Configuration > View Configuration > Theme: calibrur dark theme`

#### Kobo Sync

You can actually sync your library to a Kobo device. [See kobo-sync page](kobo-sync.md)

### Known issues

#### Login loop

When setting calibre-web behind a reverse-proxy you might get locked out of the application by being redirected to the login page multiple times.
To fix this, first expose port 8083 of the service like this:

```yml
ports:
  - 8083:8083
```

After that log in to `http://local_ip_address:8083` and go to `Admin > Edit Basic Configuration > Security Settings > Session Protection` and set it to `Basic`. Once you do that and save then you can stop the container, remove the exposed port and continue using normally.
