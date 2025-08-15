import os
import numpy as np
import rasterio
from rasterio.crs import CRS
import pyvista as pv
from scipy.ndimage import gaussian_filter
from scipy.spatial import Delaunay
import warnings
warnings.filterwarnings('ignore', category=rasterio.errors.NotGeoreferencedWarning)
from debug_utils import test_orientation, debug_coordinate_alignment, visualize_dem_and_stl_2d_with_towers, print_debug
from geo_utils import get_utm_crs, reproject_to_utm, latlon_to_utm
from meta_data_process import capture_metadata

def create_rotated_crop_mask(center_x, center_y, crop_size_m, rotation_deg, x_coords, y_coords):
    """
    Create a mask for a rotated rectangular crop.
    """
    # Convert rotation to radians
    rotation_rad = np.deg2rad(rotation_deg-90)
    
    # Half dimensions of the crop
    half_size = crop_size_m / 2
    
    # Create coordinate grids relative to center
    rel_x = x_coords - center_x
    rel_y = y_coords - center_y
    
    # Apply inverse rotation to coordinates (rotate coordinate system, not the crop)
    cos_theta = np.cos(-rotation_rad)
    sin_theta = np.sin(-rotation_rad)
    
    rotated_x = rel_x * cos_theta - rel_y * sin_theta
    rotated_y = rel_x * sin_theta + rel_y * cos_theta
    
    # Check if points fall within the rectangular bounds
    mask = ((np.abs(rotated_x) <= half_size) & (np.abs(rotated_y) <= half_size))
    
    return mask

def crop_dem_around_point_rotated(dem_path, center_lat, center_lon, crop_size_km, rotation_deg=0, utm_crs=None, debug=False):
    """
    Create a rotated crop of a DEM around a specified center point.
    """
    with rasterio.open(dem_path) as src:
        # If no UTM CRS provided, determine it
        if utm_crs is None:
            utm_crs = get_utm_crs(center_lon, center_lat)
        
        # Convert center point to UTM if the DEM is in UTM
        if src.crs != CRS.from_epsg(4326):
            # Assume DEM is already in UTM
            center_utm_x, center_utm_y = latlon_to_utm(center_lat, center_lon, src.crs)
        else:
            # DEM is in geographic coordinates, need to reproject first
            print_debug("DEM appears to be in geographic coordinates. Reprojecting...", debug)
            utm_dem_path, utm_crs = reproject_to_utm(debug, dem_path)
            return crop_dem_around_point_rotated(utm_dem_path, center_lat, center_lon, crop_size_km, rotation_deg, utm_crs, debug)
        
        crop_size_m = crop_size_km * 1000
        
        # Calculate expanded bounds to ensure we capture all rotated pixels
        # For a rotated square, the diagonal is sqrt(2) times the side length
        buffer_size = crop_size_m * np.sqrt(2) / 2
        
        expanded_bounds = [
            center_utm_x - buffer_size,  # left
            center_utm_y - buffer_size,  # bottom
            center_utm_x + buffer_size,  # right
            center_utm_y + buffer_size   # top
        ]
        
        print_debug(f"Expanded bounds for rotation (UTM): {expanded_bounds}", debug)
        
        # Convert bounds to pixel coordinates
        left_px = int((expanded_bounds[0] - src.bounds.left) / src.res[0])
        right_px = int((expanded_bounds[2] - src.bounds.left) / src.res[0])
        bottom_px = int((src.bounds.top - expanded_bounds[3]) / src.res[1])
        top_px = int((src.bounds.top - expanded_bounds[1]) / src.res[1])
        
        # Ensure we don't go outside the image bounds
        left_px = max(0, left_px)
        right_px = min(src.width, right_px)
        bottom_px = max(0, bottom_px)
        top_px = min(src.height, top_px)
        
        print_debug(f"Expanded pixel window: ({left_px}, {bottom_px}, {right_px}, {top_px})", debug)
        
        # Read the expanded data
        window = rasterio.windows.Window.from_slices((bottom_px, top_px), (left_px, right_px))
        expanded_data = src.read(1, window=window)
        
        if expanded_data.size == 0:
            raise ValueError("Expanded crop area is empty. Check your coordinates and crop size.")
        
        # Calculate transform for expanded data
        expanded_transform = rasterio.windows.transform(window, src.transform)
        
        # Create coordinate arrays for the expanded data
        nrows, ncols = expanded_data.shape
        
        # Create x, y coordinate arrays in UTM
        x_coords = np.arange(ncols) * src.res[0] + expanded_transform.c
        y_coords = np.arange(nrows) * (-src.res[1]) + expanded_transform.f  # Note: y resolution is typically negative
        
        # Create coordinate grids
        x_grid, y_grid = np.meshgrid(x_coords, y_coords)
        
        # Create the rotated crop mask
        print_debug(f"Creating rotated crop mask (rotation: {rotation_deg}°)...", debug)
        crop_mask = create_rotated_crop_mask(center_utm_x, center_utm_y, crop_size_m, rotation_deg, x_grid, y_grid)
        
        # Apply mask to elevation data
        cropped_data = expanded_data.copy()
        cropped_data[~crop_mask] = np.nan
        
        print_debug(f"Rotated crop completed. Valid pixels: {np.sum(crop_mask)} / {crop_mask.size}", debug)
        
        return cropped_data, expanded_transform, src.crs, src.res, crop_mask

def create_mesh_from_dem(elevation_data, transform, pixel_res, crop_mask=None, debug = False):
    """
    Create a PyVista mesh from elevation data with optional mask for rotated crops.
    """
    print_debug(f"Creating mesh from DEM data with shape: {elevation_data.shape}", debug)
    
    # Handle NaN values (these will be the areas outside our rotated crop)
    if np.any(np.isnan(elevation_data)):
        print_debug("Handling areas outside rotated crop (NaN values)...", debug)
        valid_mask = ~np.isnan(elevation_data)
        if not np.any(valid_mask):
            raise ValueError("No valid elevation data in the rotated crop area.")
    else:
        valid_mask = np.ones_like(elevation_data, dtype=bool)
    
    # Get dimensions
    nrows, ncols = elevation_data.shape
    
    # Create coordinate arrays
    pixel_width, pixel_height = pixel_res
    
    # Create x, y coordinate arrays
    x = np.arange(ncols) * pixel_width
    y = np.arange(nrows) * abs(pixel_height)  # Use abs since pixel_height might be negative
    
    # Center the coordinates
    x = x - np.mean(x)
    y = y - np.mean(y)
    
    # Create meshgrid
    X, Y = np.meshgrid(x, y)
    
    elevation_data_to_use = elevation_data
    valid_mask_to_use = valid_mask  
    
    # Only create points for valid (non-NaN) areas
    valid_indices = np.where(valid_mask_to_use)
    n_valid_points = len(valid_indices[0])
    
    if n_valid_points == 0:
        raise ValueError("No valid points found in the rotated crop.")
    
    print_debug(f"Valid points in rotated crop: {n_valid_points}", debug)
    
    # Create points array for valid data only
    valid_x = X[valid_indices]
    valid_y = Y[valid_indices]
    valid_z = elevation_data_to_use[valid_indices]
    
    # Create a point cloud first
    points = np.column_stack((valid_x, valid_y, valid_z))
    #points[:, 1] = -points[:, 1]
    point_cloud = pv.PolyData(points)
    
    # For irregularly distributed points (due to rotation), we need to create a surface
    # Using Delaunay triangulation on the XY plane
    print_debug("Creating Delaunay triangulation for rotated crop...", debug)
    
    # Project points to 2D for triangulation
    points_2d = points[:, :2]  # Just X, Y coordinates
    
    # Create 2D triangulation
    tri = Delaunay(points_2d)
    
    # Create faces for PyVista (triangles)
    faces = []
    for simplex in tri.simplices:
        faces.append([3, simplex[0], simplex[1], simplex[2]])  # 3 vertices per face
    faces = np.hstack(faces)
    
    # Create the mesh
    mesh = pv.PolyData(points, faces)
    
    # Add elevation data
    mesh.point_data['elevation'] = valid_z
    
    print_debug(f"Created triangulated mesh with {mesh.n_points} points and {mesh.n_cells} faces", debug)
    
    if debug:
        test_orientation(elevation_data, mesh)
    
    return mesh

@capture_metadata
def create_rotated_stl_from_dem(dem_path, output_stl, crop_km, rotation_deg, center_lat, center_lon,smooth_terrain=True, debug = False, intermediate_save=True,):
    """
    Main function to create a rotated STL file from a DEM.
    """
    print(f"Processing DEM: {dem_path}")
    print_debug(f"Crop size: {crop_km} km", debug)
    print_debug(f"Rotation: {rotation_deg} degrees", debug)
    print_debug(f"Center: {center_lat}, {center_lon}", debug)
    
    try:
        # Check if input file exists
        if not os.path.exists(dem_path):
            raise FileNotFoundError(f"DEM file not found: {dem_path}")
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_stl), exist_ok=True)
        
        # Step 1: Check if DEM needs reprojection to UTM
        with rasterio.open(dem_path) as src:
            print_debug(f"Original CRS: {src.crs}", debug)
            if src.crs == CRS.from_epsg(4326) or 'geographic' in str(src.crs).lower():
                print_debug("Reprojecting to UTM...", debug)
                if intermediate_save:
                    utm_path = dem_path.replace('.tif', '_utm.tif')
                    utm_dem_path, utm_crs = reproject_to_utm(debug, dem_path, utm_path)
                else:
                    utm_dem_path, utm_crs = reproject_to_utm(debug, dem_path)
            else:
                print_debug("DEM appears to already be in projected coordinates", debug)
                utm_dem_path = dem_path
                utm_crs = src.crs
        
        # Step 2: Create rotated crop of the DEM around the center point
        print_debug("Creating rotated crop of DEM...", debug)
        elevation_data, transform, crs, pixel_res, crop_mask = crop_dem_around_point_rotated(
            utm_dem_path, center_lat, center_lon, crop_km, rotation_deg, utm_crs, debug
        )
        
        if elevation_data.size == 0:
            raise ValueError("Cropped area is empty. Check your coordinates and crop size.")
        
        if smooth_terrain:
            print_debug("Smoothing terrain ...", debug)
            elevation_data = smooth_terrain_for_cfd(elevation_data, sigma=2.0)

        print_debug(f"Rotated crop elevation data shape: {elevation_data.shape}", debug)
        valid_elevations = elevation_data[~np.isnan(elevation_data)]
        if len(valid_elevations) > 0:
            print_debug(f"Elevation range: {np.min(valid_elevations):.1f} to {np.max(valid_elevations):.1f} meters", debug)
        else:
            raise ValueError("No valid elevation data in rotated crop area.")
        
        # Step 3: Create mesh from rotated crop (no additional rotation needed)
        print_debug("Creating 3D mesh from rotated crop...", debug)
        mesh = create_mesh_from_dem(elevation_data, transform, pixel_res, crop_mask, debug)
        
        # Step 4: Save as STL
        print_debug(f"Saving STL file: {output_stl}", debug)
        mesh.save(output_stl)

        if debug:
            debug_coordinate_alignment(elevation_data, mesh, output_stl)
        
        print_debug(f"Successfully created STL file: {output_stl}", debug)
        print_debug(f"Final mesh statistics:", debug)
        print_debug(f"  - Points: {mesh.n_points}", debug)
        print_debug(f"  - Faces: {mesh.n_cells}", debug)
        print_debug(f"  - Bounds: {mesh.bounds}", debug)
        
        return output_stl
        
    except Exception as e:
        print(f"Error processing DEM: {str(e)}")
        raise

def smooth_terrain_for_cfd(elevation_data, sigma=2.0, preserve_nan=True):
    """
    Smooth terrain data for better CFD mesh quality
    
    Parameters:
    - sigma: smoothing strength (higher = more smoothing)
    - preserve_nan: keep NaN areas (outside rotated crop) as NaN
    """
    if preserve_nan:
        valid_mask = ~np.isnan(elevation_data)
        smoothed = elevation_data.copy()
        
        # Only smooth valid areas
        valid_data = elevation_data[valid_mask]
        if len(valid_data) > 0:
            # Create temporary array for smoothing
            temp_array = np.zeros_like(elevation_data)
            temp_array[valid_mask] = valid_data
            temp_array[~valid_mask] = np.mean(valid_data)  # Fill NaN with mean for smoothing
            
            # Apply smoothing
            smoothed_temp = gaussian_filter(temp_array, sigma=sigma)
            
            # Restore only valid areas
            smoothed[valid_mask] = smoothed_temp[valid_mask]
    else:
        smoothed = gaussian_filter(elevation_data, sigma=sigma)
    
    return smoothed


def realign_rotated_stl(input_stl_path, output_stl_path, rotation_deg , flip_y=False, flip_x=False, debug = False):
    """
    Realign a rotated STL to axis-aligned coordinates
    Applies counter-rotation to make terrain features align with X/Y axes
    
    Parameters:
    - input_stl_path: your current rotated STL file
    - output_stl_path: output path for aligned STL
    - rotation_deg: original rotation angle applied to terrain (to reverse it)
    """
    
    print_debug(f"Loading rotated STL: {input_stl_path}", debug)
    mesh = pv.read(input_stl_path)
    
    print_debug(f"Original mesh bounds: {mesh.bounds}", debug)
    # DIAGNOSTIC: Find highest point before rotation
    max_z_idx_before = np.argmax(mesh.points[:, 2])
    highest_before = mesh.points[max_z_idx_before]
    print_debug(f"Highest point BEFORE realign: {highest_before}", debug)
    print_debug(f"Applying counter-rotation of {-rotation_deg}°...", debug)
    
    # Get current points
    points = mesh.points.copy()
    
    # Apply counter-rotation (negative of original rotation)
    theta = np.deg2rad(-rotation_deg)  # Negative to reverse rotation
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)
    
    # Rotate X,Y coordinates (Z stays the same)
    x_new = points[:, 0] * cos_theta - points[:, 1] * sin_theta
    y_new = points[:, 0] * sin_theta + points[:, 1] * cos_theta
    
    # Apply axis flips if requested
    if flip_x:
        print_debug("Applying X-axis flip...", debug)
        x_new = -x_new
    
    if flip_y:
        print_debug("Applying Y-axis flip...", debug)
        y_new = -y_new

    # Create new mesh with realigned coordinates
    new_mesh = mesh.copy()
    new_mesh.points[:, 0] = x_new
    new_mesh.points[:, 1] = y_new
    # Z coordinates unchanged
    
    # DIAGNOSTIC: Find highest point after rotation
    max_z_idx_after = np.argmax(new_mesh.points[:, 2])
    highest_after = new_mesh.points[max_z_idx_after]
    print_debug(f"Highest point AFTER realign: {highest_after}", debug)

    print_debug(f"Realigned mesh bounds: {new_mesh.bounds}", debug)
    
    # Save the realigned STL
    new_mesh.save(output_stl_path)
    print_debug(f"Axis-aligned STL saved: {output_stl_path}", debug)
    
    return output_stl_path


def process_dem(config_override=None):
    """Main processing function that can be called from other scripts"""
    
    # Use default config or override
    if config_override:
        config = config_override
    else:
        from dem_processing.process_config import Config
        config = Config()
    
    # Your exact processing logic here (copy from your __main__ section):
    output_stl = os.path.join(config.output_folder_final, f"original_crop{config.final_crop_km}km_{config.rotation_deg}deg.stl")
    #aligned_stl = os.path.join(config.output_folder_final, f"rotated_crop_{config.final_crop_km}km_{config.rotation_deg}deg_realigned.stl")
    aligned_stl = os.path.join(config.output_folder_final, "terrain.stl")

    create_rotated_stl_from_dem(
        dem_path=config.input_file,
        output_stl=output_stl,
        crop_km=config.final_crop_km,
        rotation_deg=config.rotation_deg,
        center_lat=config.center_lat,
        center_lon=config.center_lon,
        smooth_terrain=True,
        debug = config.debug_mode

    )

    realign_rotated_stl(
        input_stl_path=output_stl,
        output_stl_path=aligned_stl,
        rotation_deg=-config.rotation_deg,
        flip_y=True,
        flip_x=False,
        debug= config.debug_mode
    )

    if config.debug_mode:
        visualize_dem_and_stl_2d_with_towers(
            original_tiff_path=config.input_file,
            stl_file_path=aligned_stl,
            center_lat=config.center_lat, 
            center_lon=config.center_lon,
            crop_size_km=config.final_crop_km,
            rotation_deg=config.rotation_deg,
            tower_latlons=config.tower_locations,
            tower_labels=config.tower_names,
            stl_is_y_flipped=True
        )
    
    return aligned_stl

if __name__ == "__main__":
    # Now just call the function
    result_stl = process_dem()
    print(f"Finished! STL file: {result_stl}")