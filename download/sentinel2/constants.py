import stackstac

S2_BANDS = {
    "blue": "B02",
    "green": "B03",
    "red": "B04",
    "nir": "B08",
    "swir16": "B11",
    "swir22": "B12",
}

SCL_GOOD_PIXELS = [4, 5, 6, 11]

TIME_PERIOD_LOOKUP = {
    "daily": "D",
    "weekly": "W",
    "monthly": "M",  # month end
    "month_start": "MS",  # month start
    "quarterly": "Q",  # Quarter end (default: Dec-31)
    "annual": "Y",  # Year end (default: Dec-31)
    "bi-annual": "2Q",  # 2 quarters / 6 months
    "10_day": "10D",
}

GDAL_ENV = stackstac.DEFAULT_GDAL_ENV.updated({
    "GDAL_HTTP_RETRY_COUNT": 5,
    "GDAL_HTTP_RETRY_DELAY": 2,
    "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
    "VSI_CACHE": True,
    "VSI_CACHE_SIZE": 50_000_000,
})
