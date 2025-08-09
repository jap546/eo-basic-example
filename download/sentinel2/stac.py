from __future__ import annotations

from typing import TYPE_CHECKING

import planetary_computer
import pystac_client
from pystac import ItemCollection

if TYPE_CHECKING:
    from download.sentinel2.config import Sentinel2Config
    from download.sentinel2.model import BoundingBox


class StacSearcher:
    """Performs searches against a STAC API."""

    STAC_API_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"

    def __init__(self, config: Sentinel2Config):
        self.config = config
        self.client = pystac_client.Client.open(
            self.STAC_API_URL, modifier=planetary_computer.sign_inplace
        )

    def search(self, search_bbox: BoundingBox, datetime_range: str) -> ItemCollection:
        """Performs a STAC search for a specific time window."""
        search = self.client.search(
            collections=[self.config.collection],
            bbox=search_bbox.as_tuple(),
            datetime=datetime_range,
            query={"eo:cloud_cover": {"lt": self.config.max_cloud_cover}},
        )
        return search.item_collection()
