# GenerateInput/__init__.py
from .download_raster import DEMDownloader
from .download_config import DownloadConfig

def download_dem(csv_path, row_index=0, **kwargs):
    """Simple API for external scripts"""
    config = DownloadConfig(**kwargs)
    downloader = DEMDownloader(config)
    return downloader.download_by_index(csv_path, row_index)

__all__ = ['DEMDownloader', 'DownloadConfig', 'download_dem']