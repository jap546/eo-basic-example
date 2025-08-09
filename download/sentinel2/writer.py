from pathlib import Path

import rioxarray as rio  # noqa: F401
import xarray as xr


class RasterWriter:
    """Writes xarray data to a raster file."""

    def write(self, raster_data: xr.DataArray, output_path: Path) -> None:
        """
        Saves a DataArray to a COG file, creating directories if needed.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        raster_data.rio.to_raster(output_path, tiled=True, driver="COG")
        print(f"Successfully saved data to: {output_path}")
