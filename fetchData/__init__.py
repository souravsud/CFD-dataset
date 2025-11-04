# GenerateInput/__init__.py
from .download_raster import DEMDownloader
from .download_config import DownloadConfig

def download_raster_data(lat, lon, index, config):
    """Simple API - takes coordinates and config object"""
    downloader = DEMDownloader(config)
    return downloader.download_single_location(lat, lon, index)

__all__ = ['DEMDownloader', 'DownloadConfig', 'download_dem']