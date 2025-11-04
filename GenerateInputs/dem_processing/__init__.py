# dem_processing/__init__.py
import os
from .dem_processor import process_dem
from .process_config import ProcessConfig
from .randomDirections import generate_directions
from .csv_utils import get_coordinate_by_index

def process_dem_files(dem_file, csv_path, row_index, **kwargs):
    """Simple API for DEM processing - matches download API style"""
    
    # Get coordinates from CSV
    #lat, lon = get_coordinate_by_index(csv_path, row_index, verbose=kwargs.get('verbose', False))
    
    # Create and configure processing config
    config = ProcessConfig(csv_path=csv_path, row_index=row_index, verbose=kwargs.get('verbose', True))
    
    if "rotation_deg" in kwargs:
        config.rotation_deg = kwargs["rotation_deg"]
    if "crop_size_km" in kwargs:
        config.final_crop_km = kwargs["crop_size_km"]
    if "debug_mode" in kwargs:
        config.debug_mode = kwargs["debug_mode"]
    if "verbose" in kwargs:
        config.verbose = kwargs["verbose"]
    
    # Set paths
    
    output_dir = kwargs.get('output_dir', 'output')
    script_dir = os.path.dirname(os.path.abspath(dem_file))
    full_output_dir = os.path.join(script_dir, output_dir)
    config.set_paths(dem_file, full_output_dir)
    
    # Process and return result
    return process_dem(config)

__all__ = ['process_dem', 'Config', 'process_dem_files', 'generate_directions']
