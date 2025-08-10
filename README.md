# Background

This is purely a learning & development project in my spare time exploring various Sentinel-2 datasets and what can be used with them.

So far includes:

- Download pipeline for vector & raster data
- Notebook [exploring proxy urban development](https://github.com/jap546/eo-basic-example/notebooks/urban_development.ipynb) in Greater Manchester

---

## About this project

Default Python is set to `3.12`.

This project uses:

- [`uv`](https://docs.astral.sh/uv/) for Python package and dependency management.
- [`pre-commit`](https://pre-commit.com/) ensuring code quality & consistency, prevent commits of sensitive information (e.g. secrets).
- [`ruff`](https://docs.astral.sh/ruff/) for linting and formatting.
- [`mypy`](https://mypy.readthedocs.io/en/stable/#) for checking type hints.
- [`nox`](https://nox.thea.codes/en/stable/) for automated code quality checks in multiple Python environments.

---

## Getting started

Have included a `Makefile` for convenience, assuming `uv` & `pre-commit` are installed, run:

```zsh
make install && make setup
```

Activate the environment:

```zsh
source .venv/bin/activate
```

Then to download data, run:

```zsh
download
```

This will download all data within `download_config.json` to local disk which may take awhile.

We download the [Combined Authorities (Generalised) boundaries](https://geoportal.statistics.gov.uk/datasets/ons::combined-authorities-may-2025-boundaries-en-bgc/about) from Office for National Statistics. We filter for Greater Manchester and use this data to create a mask for our Sentinel-2 data.

Raster data is downloaded from the [Microsoft Planetary Computer](https://planetarycomputer.microsoft.com/) STAC catalog. We use [`stackstac`](https://stackstac.readthedocs.io/en/latest/) which turns a STAC collection into a lazy `xarray.DataArray` using [`dask`](https://docs.dask.org/en/latest/array.html). We filter for good pixels within the Scene Classification Layer, then create a composite image by calculating a simple median for every pixel.

---

## TODO

- Explore using [coiled](https://coiled.io/) for cloud compute
- Rerun over additional years
