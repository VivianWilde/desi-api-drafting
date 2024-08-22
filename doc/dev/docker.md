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
- After that, the `desiapi` container copies the code and other files (such as HTML templates and config files) from the repo into the container, declares a `cache` volume and some useful environment variables, and then simply forwards arguments to `docker run` to `cli.py`.

