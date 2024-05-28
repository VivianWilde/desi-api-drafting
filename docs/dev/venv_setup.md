# Virtual Env Setup
```shell
python -m venv ~/venvs/desi-api-new
source ~/venvs/desi-api-new/bin/activate
# Everything after is inside the environment
python -m pip install --upgrade pip setuptools wheel
python -m pip install sphinx sphinx_rtd_theme # If you want to be able to build docs
python -m pip install astropy scipy numba "numpy<2.0" pytest fitsio "bokeh<3" flask numpyencoder requests
python -m pip install --no-deps git+https://github.com/desihub/desiutil
python -m pip install --no-deps git+https://github.com/desihub/desitarget
python -m pip install --no-deps git+https://github.com/desihub/desispec
python -m pip install --no-deps git+https://github.com/desihub/prospect
python -m pip install --no-deps git+https://github.com/desihub/redrock

git clone https://github.com/desihub/redrock-templates ~/d/urap/libs/new-rr-templates 
# The path is just to do with my specific file structure

curl  https://raw.githubusercontent.com/desihub/redrock-templates/0.7.2/rrtemplate-qso.fits -o ~/d/urap/libs/new-rr-templates/rrtemplate-qso.fits

export RR_TEMPLATE_DIR=~/d/urap/libs/new-rr-templates
```

