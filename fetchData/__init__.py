# GenerateInput/__init__.py
from .download_raster import DEMDownloader, create_output_dir
from .download_config import DownloadConfig

def download_raster_data(lat, lon, index, out_dir, config):
    """Simple API - takes coordinates and config object"""
    downloader = DEMDownloader(config)
    return downloader.download_single_location(lat, lon, index, out_dir)

__all__ = ['DEMDownloader', 'DownloadConfig', 'download_dem']