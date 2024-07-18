FROM desipod

# RUN git clone https://github.com/VivianWilde/desi-api-drafting /cloned
RUN mkdir -p /code
# COPY /cloned/py/desiapi /code/desiapi
COPY py/desiapi /code/desiapi
# ADD templates /templates
COPY etc/docker/default.toml /config/default.toml

# For 
# RUN git clone https://github.com/VivianWilde/desi-api-drafting.git /code
# COPY /code/docker-utilities/default.toml /config/default.toml

# Handled in Desipod
# ENV DESI_ROOT=/desi
# ENV DESI_SPECTRO_REDUX=/desi/spectro/redux
# ENV RR_TEMPLATE_DIR=/desi/redrock-templates
ENV PYTHONPATH="/code:${PYTHONPATH}"

VOLUME /cache

# Crontab TODO

# ENTRYPOINT cd $DESI_ROOT/code/desi-api-drafting && python cli.py
ENTRYPOINT python -m desiapi.web.cli $1
