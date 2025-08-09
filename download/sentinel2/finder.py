from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from download.sentinel2.aoi import AoiManager
from download.sentinel2.constants import TIME_PERIOD_LOOKUP
from download.sentinel2.stac import StacSearcher

if TYPE_CHECKING:
    from pystac import ItemCollection

    from .config import Sentinel2Config


class StacItemFinder:
    """Discovers STAC items for all configured areas and time windows."""

    def __init__(self, config: Sentinel2Config, aoi_manager: AoiManager):
        self.config = config
        self.aoi_manager = aoi_manager
        self.stac_searcher = StacSearcher(config)

    def _get_time_windows(self) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
        """Generates time windows based on the config."""
        if not self.config.resample_period:
            return [(pd.Timestamp(self.config.start_date), pd.Timestamp(self.config.end_date))]

        period_code = TIME_PERIOD_LOOKUP[self.config.resample_period]
        periods = pd.period_range(
            start=self.config.start_date, end=self.config.end_date, freq=period_code
        )
        return [(p.start_time, p.end_time) for p in periods]

    def find_all(self) -> dict[tuple[str, str], ItemCollection]:
        """

        Finds all STAC items for all configured jobs and returns them in a dictionary.
        Also prints a summary of the findings.
        """
        print("--- Starting STAC Item Discovery ---")
        time_windows = self._get_time_windows()
        all_items: dict[tuple[str, str], ItemCollection] = {}
        total_found = 0

        for area in self.aoi_manager.get_areas():
            print(f"\nSearching for area: {area.name}")
            for start_time, end_time in time_windows:
                datetime_range = f"{start_time.date().isoformat()}/{end_time.date().isoformat()}"
                print(f"  - Time window: {datetime_range}")

                items = self.stac_searcher.search(area.search_bbox, datetime_range)
                num_items = len(items)
                total_found += num_items
                print(f"    => Found {num_items} items.")

                if num_items > 0:
                    all_items[(area.name, datetime_range)] = items

        print("\n--- Discovery Summary ---")
        if not all_items:
            print("No STAC items found for any configuration.")
        else:
            for (area_name, dt_range), items in all_items.items():
                print(f"  - Area: '{area_name}', Window: {dt_range}: {len(items)} items")

        print(f"\nTotal items found across all searches: {total_found}")
        print("---------------------------\n")
        return all_items
