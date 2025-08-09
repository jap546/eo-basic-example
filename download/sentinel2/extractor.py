from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from download.sentinel2.aoi import AoiManager, ProcessingArea
from download.sentinel2.finder import StacItemFinder
from download.sentinel2.processor import DataProcessor
from download.sentinel2.writer import RasterWriter

if TYPE_CHECKING:
    from .config import Sentinel2Config


class Sentinel2Extractor:
    """Orchestrates the download and processing of Sentinel-2 data."""

    def __init__(self, config: Sentinel2Config, base_output_dir: Path):
        self.config = config
        self.aoi_manager = AoiManager(config, base_output_dir)
        self.finder = StacItemFinder(config, self.aoi_manager)
        self.processor = DataProcessor(config)
        self.writer = RasterWriter()

    def _generate_output_path(
        self, area: ProcessingArea, start_time: pd.Timestamp, end_time: pd.Timestamp
    ) -> Path:
        """Generates a unique, descriptive output path for a given area and time period."""
        base_stem = self.config.output_filename
        start_str = start_time.strftime("%Y-%m-%d")
        end_str = end_time.strftime("%Y-%m-%d")

        if self.config.resample_period:
            time_suffix = f"{start_str}_{end_str}"
            final_filename = f"{base_stem}_{time_suffix}.tif"
        else:
            final_filename = f"{base_stem}.tif"

        return area.output_path.parent / final_filename

    def run(self) -> list[Path]:
        """
        Executes the end-to-end data extraction and processing workflow.
        Returns a list of paths to the successfully created files.
        """
        print("Starting Sentinel-2 processing job...")
        discovered_items = self.finder.find_all()
        if not discovered_items:
            print("No items to process. Exiting.")
            return []

        areas_by_name = {area.name: area for area in self.aoi_manager.get_areas()}
        successfully_created_files: list[Path] = []

        for (area_name, datetime_range), items in discovered_items.items():
            area = areas_by_name.get(area_name)
            if not area:
                print(f"--> Could not find area information for '{area_name}'. Skipping.")
                continue

            start_str, end_str = datetime_range.split("/")
            start_time = pd.to_datetime(start_str)
            end_time = pd.to_datetime(end_str)

            print(f"\n--- Processing area: {area.name} | Window: {datetime_range} ---")
            final_output_path = self._generate_output_path(area, start_time, end_time)

            if final_output_path.exists():
                print(f"Output file already exists at {final_output_path}. Skipping.")
                successfully_created_files.append(final_output_path)
                continue

            print(f"Processing {len(items)} items...")
            composite = self.processor.process_to_composite(
                items=items, search_bbox=area.search_bbox, clip_gdf=area.clip_gdf
            )

            if composite is None:
                print("No valid composite was generated for this window.")
                continue

            self.writer.write(raster_data=composite, output_path=final_output_path)
            successfully_created_files.append(final_output_path)

        print("\nSentinel-2 job finished.")
        return successfully_created_files
