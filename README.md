# PassPredict Web API

[![pipeline status](https://gitlab.com/samtx/passpredict-api/badges/main/pipeline.svg)](https://gitlab.com/samtx/passpredict-api/-/commits/main)

## Locations database

Initial data for world cities latitude/longitude coordinates provided by simplemaps.com, licensed CCA 4.0, downloaded 10/7/2020


## Compile App

Use `pip-compile` to update frozen dependencies in `requirements.txt` based on `requirements.in`.

Compile cython extensions with `python setup.py build_ext --inplace`
