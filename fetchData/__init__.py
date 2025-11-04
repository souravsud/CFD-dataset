# GenerateInput/__init__.py
from .download_raster import DEMDownloader
from .download_config import DownloadConfig

def download_dem(lat, lon, index, **kwargs):
    """Simple API for external scripts - takes coordinates directly"""
    config = DownloadConfig(**kwargs)
    downloader = DEMDownloader(config)
    return downloader.download_single_location(lat, lon, index)

__all__ = ['DEMDownloader', 'DownloadConfig', 'download_dem']