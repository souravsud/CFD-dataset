# GenerateInput/download_config.py
from dataclasses import dataclass
from pathlib import Path

@dataclass
class DownloadConfig:
    # Download parameters
    dem_name: str = "glo_30"
    dst_ellipsoidal_height: bool = False
    dst_area_or_point: str = "Point"
    side_length_km: float = 50.0
    include_roughness_map: bool = False
    
    # Debug options
    verbose: bool = True
    show_plots: bool = False
    save_raw_files: bool = True