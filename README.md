## Background
Example repo for mapping proxy urban development within Greater London using Sentinel-2 data.
---
## Getting started
Install the python dependencies with `poetry`:
```
poetry install
```

Ensure the python inpreter is set for the newly installed `poetry` environment, then run the CLI command:
```
download
```

This will download all data within `download_config.json` and `download_config_raster.json` to local files.

Vector data is the regions downloaded from ONS, where we'll use the Greater London boundaries to clip our data.

Raster data is downloaded using `rioxarray` and `dask` to download EO data from STAC catalogues and calculate the medians to reduce noise (i.e. clouds).

You can then work through the example notebook in `urban_development.ipynb`, which:
- Loads up the median Red, Green, Blue, SWIR1.6 and SWIR2.2 bands from Sentinel-2
- Calculates the Enhanced Normalised Difference Impervious Surfaces Index (ENDISI)
- Delineates proxy urban development
---
## TODO
1. Refactor EO download process into wider pydantic model
2. Rerun analysis additional years to map urban change
