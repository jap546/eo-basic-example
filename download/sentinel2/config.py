from __future__ import annotations

from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

import download.configure.validate.exceptions as e
from download.sentinel2.constants import TIME_PERIOD_LOOKUP
from download.sentinel2.model import BoundingBox, CoordinateReferenceSystems

ResamplePeriod = [*TIME_PERIOD_LOOKUP.keys()]


class Sentinel2Config(BaseModel):
    """A Pydantic model to strictly configure Sentinel-2 data extraction."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    bbox: BoundingBox | None = None
    boundary_path: Path | None = Field(None, description="Path to a vector file with boundaries.")
    boundary_filter_column: str | None = Field(
        None, description="Column in the boundary file to filter by."
    )
    boundary_filter_values: list[str] | None = Field(
        None, description="List of values to select from the filter column."
    )

    collection: str = Field("sentinel-2-l2a", description="STAC collection to search.")
    resolution: int = Field(..., gt=0, description="Output resolution in meters.")
    start_date: date
    end_date: date
    source_crs: CoordinateReferenceSystems = CoordinateReferenceSystems.WGS84.to_epsg_code()
    target_crs: CoordinateReferenceSystems = CoordinateReferenceSystems.BNG.to_epsg_code()
    max_cloud_cover: int = Field(25, ge=0, le=100)
    resample_period: str | None = Field(
        None, description="Time period to resample data to (e.g., 'quarterly')."
    )
    composite_method: str = Field(
        "median", description="The compositing method to use: 'median' or 'quartile'."
    )

    output_filename: str = Field(..., description="Descriptive filename stem (without extension).")

    @model_validator(mode="after")
    def _validate_inputs(self) -> Sentinel2Config:
        """Validates that AOI inputs are logical and complete."""
        if self.bbox and self.boundary_path:
            raise e.ConflictingInputError(param1="bbox", param2="boundary_path")
        if not self.bbox and not self.boundary_path:
            msg = "You must provide either 'bbox' or 'boundary_path'."
            raise e.BboxOrBoundaryError(msg)
        if self.boundary_path:
            if not self.boundary_filter_column:
                raise e.RequiredInputError(param1="boundary_path", param2="boundary_filter_column")
            if not self.boundary_filter_values:
                raise e.RequiredInputError(param1="boundary_path", param2="boundary_filter_values")
        return self
