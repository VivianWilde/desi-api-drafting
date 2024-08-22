# Example Requests

All of these requests should be prefaced by `BASE_URL/api/v1/`. `BASE_URL` is either `127.0.0.1:5000` or `ingress.whatever... . spin.nersc.org` if you're running it on Spin.

## Spectra Plot

- spectra/plot/jura/radec/210.9,24.8,180
- spectra/plot/jura/tile/80858/600,900,1000
- spectra/plot/jura/targets/39628368387245557,39628368404022902

## Spectra Download

- spectra/download/jura/radec/210.9,24.8,180
- spectra/download/jura/tile/80858/600,900,1000
- spectra/download/jura/radec/210.9,24.8,180

## Zcat Plot

- zcat/plot/jura/radec/210.9,24.8,180
- zcat/plot/jura/tile/80858/600,900,1000
- zcat/plot/jura/targets/39628368387245557,39628368404022902

## Zcat Download

- zcat/download/jura/radec/210.9,24.8,180
- zcat/download/jura/tile/80858/600,900,1000
- zcat/download/jura/targets/39628368387245557,39628368404022902

## Filters (and non-default columns)

- spectra/download/jura/radec/210.9,24.8,180?healpix=>8939
- zcat/download/jura/radec/210.9,24.8,180?healpix=>8939
- zcat/download/jura/tile/80858/600,900,1000?fiber=<
- zcat/download/jura/targets/39628368387245557,39628368404022902?survey==sv2
