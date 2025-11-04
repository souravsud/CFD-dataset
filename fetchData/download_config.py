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
    include_roughness_map: bool = False  # Changed to False by default for backward compatibility
    
    # Paths
    out_dir: str = "Data/downloads"
    
    # Debug options
    verbose: bool = True
    show_plots: bool = False  # Changed to False by default
    
    def __post_init__(self):
        """Create output directory"""
        Path(self.out_dir).mkdir(exist_ok=True, parents=True)