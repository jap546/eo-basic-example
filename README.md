## Background
Example repo for mapping proxy urban development within Greater Manchester using Sentinel-2 data.

---
## Getting started
Install the Python dependencies with [`poetry`](https://python-poetry.org/):
```
poetry install
```

Ensure the Python interpreter is set for the newly installed `poetry` environment, then run the CLI command:
```
download
```

This will download all data within `download_config.json` and `download_config_raster.json` to local files.

Vector data is the Combined Authorities boundaries downloaded from ONS, where we'll use the Greater Manchester boundary to clip our data.

Raster data is downloaded from the [Microsoft Planetary Computer](https://planetarycomputer.microsoft.com/) STAC catalog. We use [`stackstac`](https://stackstac.readthedocs.io/en/latest/) which turns a STAC collection into a lazy `xarray.DataArray` using [`dask`](https://docs.dask.org/en/latest/array.html). We then compute the medians to reduce noise (i.e. cloud cover) and clip to the Greater Manchester boundary.

***Note***: each year of Sentinel data is ~1GB of data.

You can work through the example notebook in `urban_development.ipynb`, which:
- Loads up the median Red, Green, Blue, SWIR1.6 and SWIR2.2 bands from Sentinel-2
- Calculates the Enhanced Normalised Difference Impervious Surfaces Index (ENDISI) based on [Chen et al. (2019)](https://www.spiedigitallibrary.org/journals/journal-of-applied-remote-sensing/volume-13/issue-01/016502/Enhanced-normalized-difference-index-for-impervious-surface-area-estimation-at/10.1117/1.JRS.13.016502.full)
- Delineates proxy urban development

---
## TODO
- Refactor EO download process into wider pydantic model
- Calculate geometric median instead of median
- Double check dask workflows - are they actually working, optimal chunksizes, kubernetes gateway cluster vs. multithreaded?
- Rerun over additional years
- Move from `poetry` to [`uv`](https://docs.astral.sh/uv/)
