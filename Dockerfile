FROM desipod:dev

#- Get the config-location branch of desi-api-testing,
#- which has a workaround for the default config location.
# RUN  mkdir -p $DESI_ROOT/code \
#   && cd $DESI_ROOT/code \
#   && git clone https://github.com/VivianWilde/desi-api-drafting \
#   && cd desi-api-drafting \
#   && git checkout config-location
RUN pip install pandas numpyencoder
# Bring in the code, and also some of the other fripperies
COPY *.py /code/
COPY docker-utilities/default.toml /config/default.toml

# Crontab TODO

# ENTRYPOINT cd $DESI_ROOT/code/desi-api-drafting && python cli.py
ENTRYPOINT python /code/cli.py $@
