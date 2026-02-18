# dem_processing/__init__.py
import os
from .dem_processor import process_dem
from .process_config import ProcessConfig
from .randomDirections import generate_directions

def process_dem_files(dem_file, csv_path, row_index, **kwargs):
    """Process DEM file to create STL mesh for CFD simulation.
    
    Args:
        dem_file (str): Path to the DEM file to process
        csv_path (str): Path to CSV file containing coordinates
        row_index (int): Row index in CSV file for this location
        **kwargs: Additional processing parameters:
            - rotation_deg (float): Rotation angle in degrees (default: 0)
            - crop_size_km (float): Final terrain size in km (default: from config)
            - output_dir (str): Output directory path (default: 'output')
            - debug_mode (bool): Enable debug visualizations (default: False)
            - verbose (bool): Enable verbose output (default: True)
    
    Returns:
        str: Path to the generated STL file
    
    Raises:
        FileNotFoundError: If dem_file or csv_path doesn't exist
        ValueError: If row_index is out of range
        Exception: For processing errors during DEM conversion
    """
    
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
