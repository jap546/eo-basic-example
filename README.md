## Background
Example repo for mapping proxy urban development within Greater Manchester using Sentinel-2 data.

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

Vector data is the Combined Authorities boundaries downloaded from ONS, where we'll use the Greater Manchester boundary to clip our data.

Raster data is downloaded using `rioxarray` and `dask` to download EO data from the [Microsoft Planetary Computer](https://planetarycomputer.microsoft.com/) STAC catalog and calculate the medians to reduce noise (i.e. cloud cover). ***Note***: each year of Sentinel data is ~1GB of data.

You can then work through the example notebook in `urban_development.ipynb`, which:
- Loads up the median Red, Green, Blue, SWIR1.6 and SWIR2.2 bands from Sentinel-2
- Calculates the Enhanced Normalised Difference Impervious Surfaces Index (ENDISI)
- Delineates proxy urban development

---
## TODO
- Refactor EO download process into wider pydantic model
- Calculate geometric median instead of median
- Double check dask workflows - are they actually working, optimal chunksizing, gateway cluster vs. multithreaded?
- Rerun over additional years