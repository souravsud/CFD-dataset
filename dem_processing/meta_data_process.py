import functools
import time
import json

def capture_metadata(func):
    """Decorator to capture metadata from DEM processing functions"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Handle both positional and keyword arguments
        if len(args) >= 6:
            # Called with positional arguments
            dem_path, output_stl, crop_km, rotation_deg, center_lat, center_lon = args[:6]
        else:
            # Called with keyword arguments (or mixed)
            dem_path = args[0] if len(args) > 0 else kwargs.get('dem_path')
            output_stl = args[1] if len(args) > 1 else kwargs.get('output_stl')
            crop_km = args[2] if len(args) > 2 else kwargs.get('crop_km')
            rotation_deg = args[3] if len(args) > 3 else kwargs.get('rotation_deg')
            center_lat = args[4] if len(args) > 4 else kwargs.get('center_lat')
            center_lon = args[5] if len(args) > 5 else kwargs.get('center_lon')
        
        start_time = time.time()
        metadata = {
            "sample_info": {
                "created_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
            "input_parameters": {
                "dem_path": dem_path,
                "output_stl": output_stl,
                "crop_km": crop_km,
                "rotation_deg": rotation_deg,
                "center_coordinates": {"lat": center_lat, "lon": center_lon},
                "smooth_terrain": kwargs.get('smooth_terrain', True),
            },
            "status": "processing"
        }
        
        try:
            # Call your original function unchanged
            result = func(*args, **kwargs)
            
            # Add completion metadata
            metadata["status"] = "completed"
            metadata["processing_time_seconds"] = round(time.time() - start_time, 2)
            
            # Auto-save metadata next to STL
            metadata_path = output_stl.replace('.stl', '_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return result
            
        except Exception as e:
            metadata["status"] = "failed"
            metadata["error"] = str(e)
            metadata["processing_time_seconds"] = round(time.time() - start_time, 2)
            
            # Save error metadata
            metadata_path = output_stl.replace('.stl', '_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            raise
    
    return wrapper
