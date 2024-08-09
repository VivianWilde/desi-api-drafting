# Docker Setup
Running the docker container correctly is a little tricky, since generating the right options to mount the DESI data we need is finnicky. Because I like you and do not want you to suffer, I've constructed a `run.py` file. Once you've locally built/downloaded the container, simply run `python run.py` and specify:
1. A command
2. A path to a configuration file
3. A mode to run in, one of Private or Public
This will generate and run the appropriate docker command, including the appropriate port forwarding and file-mounting witchcraft for the server to just work (TM).
For instance `python run.py server -c ./config.toml -m public` to run a server that only exposes public DESI releases, and uses config values from `config.toml`

## Container Structure
- We have a base container `desipod`, essentially builds python and all of the basic libraries/dependencies, including the ones from DESI.
- `desipod` does a few hacks to handle multiple versions of some repositories (like the redrock templates repository).
- After that, the `desiapi` container copies the code and other files (such as HTML templates and config files) from the repo into the container, declares a `cache` volume and some useful environment variables, and then simply forwards arguments to `docker run` to  `cli.py`.

## Little Trip-Ups
- For reasons that have been eaten by a wildebeest, if you run a server in a docker container, even if you enable port forwarding, the server won't be accessible from localhost.
- To get around this we specify `app.run(host="0.0.0", debug=True)` in the `webapp.py` file, so that the app responds to requests from outside the Docker container as well
### Redrock Template Shenanigans
- TODO: Document the redrock template shenanigans here.
- They have mysteriously disappeared and everything is fine


# Rancher/Spin Setup
## Cache Volume
## Server (Deployment)
### Pod
- Add annotations as described in [DESI docs](https://desi.lbl.gov/trac/wiki/Computing/NerscSpin/Security#AddingaDESIread-onlypassword)
- Security Context: Specify the user ID to run as (any user with DESI permissions is fine)
- Add a bind-mount named *spectro-redux* pointing to `/global/cfs/cdirs/desi/spectro/redux` (or wherever `$DESI_SPECTRO_REDUX` points)
- Add a bind-mount named *public* pointing to `/global/cfs/cdirs/desi/public` (or wherever `$DESI_ROOT/public` points)
- TODO cache setup
### Container
- Image: `vivianwilde/desiapi` (or you can build the image from the repo yourself, and push it to whatever name you prefer, I'm not your boss)
- Networking: Add a networking service of type *Cluster IP*, named *Flask* running on port *5000* over *TCP*.
- Command: `python -m desiapi.web.cli`, with arguments just `server`
- Env Vars: `DESI_API_CONFIG_FILE` is the env var that defines where (within the container) to look for the config file. Point it to wherever you mounted the config file from CFS.
- Security Context: Input "Run As User ID" matching the pod Filsystem Group ID, and select "must run as non-root user"
- Mount *spectro-redux* at `/desi/spectro/redux`
- Mount *public* at `/desi/public`
- Mount *cache* at `/cache`
## Ingress

## Cache Clean (Cron Job)


