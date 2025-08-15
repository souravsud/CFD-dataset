# GenerateInput/config.py
from dataclasses import dataclass
from pathlib import Path

@dataclass
class DownloadConfig:
    # DEM download parameters
    dem_name: str = "glo_30"
    dst_ellipsoidal_height: bool = False
    dst_area_or_point: str = "Point"
    side_length_km: float = 50.0
    
    # Paths
    out_dir: str = "Data/downloads"
    
    # Debug options
    verbose: bool = False
    show_plots: bool = False  # Separate from verbose for plotting
    
    def __post_init__(self):
        """Create output directory"""
        Path(self.out_dir).mkdir(exist_ok=True, parents=True)
