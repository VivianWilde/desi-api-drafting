# Rancher/Spin Setup

## Cache Volume

- Under `storage`, create a `PersistentVolumeClaim` named `desi-api-cache`. Under `customize`, set the access mode to `many node read-write`

## Server (Deployment)

### Pod

- Add annotations as described in [DESI docs](https://desi.lbl.gov/trac/wiki/Computing/NerscSpin/Security#AddingaDESIread-onlypassword)
- Security Context: Specify the user ID to run as (any user with DESI permissions is fine)
- Add a bind-mount named _spectro-redux_ pointing to `/global/cfs/cdirs/desi/spectro/redux` (or wherever `$DESI_SPECTRO_REDUX` points)
- Add a bind-mount named _public_ pointing to `/global/cfs/cdirs/desi/public` (or wherever `$DESI_ROOT/public` points)
- Add a persistent volume claim named _cache_ pointing to the persistent cache volume we created

#### Config File and Intermediates

- Add a bind mount named _config_ pointing to the directory where the config file (`config.toml`) is being stored on CFS.
- Add a bind mount named _intermediate_ (or whatever you like) pointing to the directory where the intermediate formats (HDF5 and Memmap) are stored.

### Container

- Image: `vivianwilde/desiapi` (or you can build the image from the repo yourself, and push it to whatever name you prefer, I'm not your boss)
- Networking: Add a networking service of type _Cluster IP_, named _Flask_ running on port _5000_ over _TCP_.
- Command: `python -u -m desiapi.web.cli`, with arguments just `server` (the `-u` is just to make sure logging to the terminal works nicely)
- Security Context: Input "Run As User ID" matching the pod Filsystem Group ID, and select "must run as non-root user"
- Mount _spectro-redux_ at `/desi/spectro/redux`
- Mount _public_ at `/desi/public`
- Mount _cache_ at `/cache`
- Mount _config_ at `/config`
- Mount _intermediate_ at `/intermediate`

#### Environment Variables

- `DESI_API_CONFIG_FILE` is the env var that defines where (within the container) to look for the config file. Point it to `/config/config.toml` (where you mounted the config file)
- `DESI_API_INTERMEDIATE` defines where to look for intermediate formats. Point it to `/intermediate`

## Ingress

- Create a new ingress. Set the request host to `ingress.desiapi.development.svc.spin.nersc.org` (or whatever, really)
- Under `rules`, add a single rule:
  - Path: Type `Prefix`, and `/` as the value
  - Target Service: `desi-api-dev-private`
  - Port: 5000

## Cache Clean (Cron Job)

- Set the schedule to `0 * * * *`, i.e run every hour on the hour

### Pod

- Create a new job named `desi-api-cache-clean`
- Add a bind mount named _config_ pointing to the directory where the config file (`config.toml`) is being stored on CFS.
- Add a persistent volume claim named _cache_ pointing to the persistent cache volume we created
- Security Context: Specify the user ID to run as (any user with DESI permissions is fine)

### Container

- Image: `vivianwilde/desiapi` (or you can build the image from the repo yourself, and push it to whatever name you prefer, I'm not your boss)
- Command: `python -u -m desiapi.web.cli`, with arguments just `clean_cache`
- Security Context: Input "Run As User ID" matching the pod Filsystem Group ID, and select "must run as non-root user"
- Mount _cache_ at `/cache`
- `DESI_API_CONFIG_FILE` is the env var that defines where (within the container) to look for the config file. Point it to `/config/config.toml` (where you mounted the config file)
- Security Context: Input "Run As User ID" matching the pod Filsystem Group ID, and select "must run as non-root user"
