# dem_processing/__init__.py
import os
from .dem_processor_original import process_dem
from .process_config import ProcessConfig
from .randomDirections import generate_directions
from .csv_utils import get_coordinate_by_index

def process_dem_files(dem_file, csv_path, row_index, **kwargs):
    """Simple API for DEM processing - matches download API style"""
    
    # Get coordinates from CSV
    lat, lon = get_coordinate_by_index(csv_path, row_index, verbose=kwargs.get('verbose', False))
    
    # Create and configure processing config
    config = ProcessConfig()
    config.center_lat = lat
    config.center_lon = lon
    
    # Apply any overrides from kwargs
    config.rotation_deg = kwargs.get('rotation_deg', 45)
    config.final_crop_km = kwargs.get('crop_size_km', 31)
    config.debug_mode = kwargs.get('debug_mode', False)
    config.verbose = kwargs.get('verbose', False)
    
    # Set paths
    
    output_dir = kwargs.get('output_dir', 'output')
    script_dir = os.path.dirname(os.path.abspath(dem_file))
    full_output_dir = os.path.join(script_dir, output_dir)
    config.set_paths(dem_file, full_output_dir)
    
    # Process and return result
    return process_dem(config)

__all__ = ['process_dem', 'Config', 'process_dem_files', 'generate_directions']
