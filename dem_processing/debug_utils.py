# debug_utils.py
import numpy as np
import os
import matplotlib.pyplot as plt
import pyvista as pv
from scipy.interpolate import griddata
import rasterio
from pyproj import Transformer
from geo_utils import reproject_to_utm, latlon_to_utm
from rasterio.crs import CRS

def print_debug(message, debug=False):
    if debug:
        print(message)
    
def test_orientation(elevation_data, mesh):
    """Quick test to verify mesh orientation matches elevation data"""
    print("\n=== Orientation Test ===")
    
    # Find highest point in elevation data
    max_row, max_col = np.unravel_index(np.nanargmax(elevation_data), elevation_data.shape)
    print(f"Highest point in elevation data at row {max_row}, col {max_col}")
    print(f"Elevation value: {elevation_data[max_row, max_col]}")
    
    # Find highest point in mesh
    max_z_idx = np.argmax(mesh.points[:, 2])
    max_point = mesh.points[max_z_idx]
    print(f"Highest point in mesh: {max_point}")
    
    # Check if relative positions match expectations
    nrows, ncols = elevation_data.shape
    print(f"Data shape: {nrows} rows x {ncols} cols")
    print(f"Row {max_row} is {'near top' if max_row < nrows/2 else 'near bottom'} of image")
    print(f"Y coordinate {max_point[1]} is {'positive' if max_point[1] > 0 else 'negative'}")
    
    # Additional checks for corners
    print(f"\nCorner elevations:")
    print(f"Top-left (0,0): {elevation_data[0, 0] if not np.isnan(elevation_data[0, 0]) else 'NaN'}")
    print(f"Top-right (0,-1): {elevation_data[0, -1] if not np.isnan(elevation_data[0, -1]) else 'NaN'}")
    print(f"Bottom-left (-1,0): {elevation_data[-1, 0] if not np.isnan(elevation_data[-1, 0]) else 'NaN'}")
    print(f"Bottom-right (-1,-1): {elevation_data[-1, -1] if not np.isnan(elevation_data[-1, -1]) else 'NaN'}")
    print("=========================\n")
    
def debug_coordinate_alignment(elevation_data, mesh, stl_file_path):
    """Debug coordinate alignment between elevation data and mesh"""
    print("\n=== Coordinate Alignment Debug ===")
    
    # Find a distinctive feature in elevation data
    max_row, max_col = np.unravel_index(np.nanargmax(elevation_data), elevation_data.shape)
    print(f"Highest point in elevation data: row {max_row}, col {max_col}")
    print(f"Value: {elevation_data[max_row, max_col]}")
    
    # Find corresponding point in mesh
    max_z_idx = np.argmax(mesh.points[:, 2])
    max_mesh_point = mesh.points[max_z_idx]
    print(f"Highest point in mesh: {max_mesh_point}")
    
    # Load STL and check
    stl_mesh = pv.read(stl_file_path)
    stl_max_idx = np.argmax(stl_mesh.points[:, 2])
    stl_max_point = stl_mesh.points[stl_max_idx]
    print(f"Highest point in STL: {stl_max_point}")
    
    # Check if they represent the same feature
    print(f"Do they have the same elevation? {np.isclose(max_mesh_point[2], stl_max_point[2], rtol=1e-3)}")
    print("=====================================\n")

def visualize_dem_and_stl_2d_with_towers(original_tiff_path, stl_file_path, center_lat, center_lon, 
                                        crop_size_km, rotation_deg, tower_latlons=None, tower_labels=None, stl_is_y_flipped=False):
    """
    Simple 2D visualization:
    1) Original DEM with crop area marked (left)
    2) STL data as 2D elevation map (right)
    """
    print("Creating 2D visualization of DEM and STL...")
    
    # Read original DEM (left plot)
    with rasterio.open(original_tiff_path) as src:
        full_terrain = src.read(1)
        transform = src.transform
        crs = src.crs
        bounds = src.bounds
        res = src.res
    
    # Handle coordinate conversion if needed
    if crs != CRS.from_epsg(4326):
        center_utm_x, center_utm_y = latlon_to_utm(center_lat, center_lon, crs)
    else:
        utm_path, utm_crs = reproject_to_utm(original_tiff_path)
        return visualize_dem_and_stl_2d_with_towers(utm_path, stl_file_path, center_lat, center_lon, 
                                                   crop_size_km, rotation_deg, tower_latlons, tower_labels, stl_is_y_flipped)
    
    # Create side-by-side plots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Left plot: Full terrain with crop outline
    im1 = ax1.imshow(full_terrain, 
                     extent=[bounds.left, bounds.right, bounds.bottom, bounds.top], 
                     cmap='terrain', origin='upper')
    
    # Draw crop rectangle
    crop_size_m = crop_size_km * 1000
    half_size = crop_size_m / 2
    angle_rad = np.deg2rad(rotation_deg)
    
    corners = np.array([
        [-half_size, -half_size], [half_size, -half_size], 
        [half_size, half_size], [-half_size, half_size], 
        [-half_size, -half_size]
    ])
    
    cos_theta, sin_theta = np.cos(angle_rad), np.sin(angle_rad)
    rotated_corners = np.zeros_like(corners)
    rotated_corners[:, 0] = corners[:, 0] * cos_theta - corners[:, 1] * sin_theta + center_utm_x
    rotated_corners[:, 1] = corners[:, 0] * sin_theta + corners[:, 1] * cos_theta + center_utm_y
    
    ax1.plot(rotated_corners[:, 0], rotated_corners[:, 1], 'red', linewidth=3, label=f'Crop Area ({crop_size_km}km)')
    ax1.plot(center_utm_x, center_utm_y, 'r+', markersize=12, markeredgewidth=3, label='Center')
    
    arrow_length = half_size * 0.5  # Length of the arrow
    arrow_end_x = center_utm_x + (0 * cos_theta - arrow_length * sin_theta)
    arrow_end_y = center_utm_y + (0 * sin_theta + arrow_length * cos_theta)
    
    # Draw arrow from center pointing to top
    ax1.annotate('', xy=(arrow_end_x, arrow_end_y), xytext=(center_utm_x, center_utm_y),
                arrowprops=dict(arrowstyle='->', color='red', lw=2, alpha=0.8))

    if tower_latlons is not None:
        # Convert towers to UTM coordinates for left plot
        transformer = Transformer.from_crs('EPSG:4326', crs, always_xy=True)
        
        for i, (lat, lon) in enumerate(tower_latlons):
            utm_x, utm_y = transformer.transform(lon, lat)
            label = tower_labels[i] if tower_labels and i < len(tower_labels) else f'Tower{i+1}'
            
            # Plot tower on left (DEM) plot
            ax1.plot(utm_x, utm_y, 'ko', markersize=8, markerfacecolor='yellow', 
                    markeredgewidth=2, label=label if i == 0 else "")
            ax1.text(utm_x + 200, utm_y + 200, label, fontsize=9, fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.8))

    ax1.set_title(f'Original DEM with Crop Area\n(Rotation: {rotation_deg}°)')
    ax1.set_xlabel('Easting (m)')
    ax1.set_ylabel('Northing (m)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_aspect('equal')
    
    try:
        stl_mesh = pv.read(stl_file_path)
        points = stl_mesh.points
        
        # Create regular grid for interpolation
        x_min, x_max = points[:, 0].min(), points[:, 0].max()
        y_min, y_max = points[:, 1].min(), points[:, 1].max()
        
        # Create grid with similar resolution to original TIFF
        grid_size = 200  # Adjust for desired resolution
        xi = np.linspace(x_min, x_max, grid_size)
        yi = np.linspace(y_min, y_max, grid_size)
        xi_grid, yi_grid = np.meshgrid(xi, yi)
        
        # Interpolate STL points to regular grid
        zi_grid = griddata((points[:, 0], points[:, 1]), points[:, 2], 
                          (xi_grid, yi_grid), method='cubic')
        
        # Plot as image like the TIFF
        origin_setting = 'lower' if stl_is_y_flipped else 'upper'
        im2 = ax2.imshow(zi_grid, extent=[x_min, x_max, y_min, y_max], 
                cmap='terrain', origin=origin_setting)  # Same as TIFF
        
        if tower_latlons is not None:
            tower_stl_coords = convert_towers_to_stl_coords(tower_latlons, center_lat, center_lon, 
                                                           crop_size_km, rotation_deg, crs)
            print("Tower coordinates in STL crop area:")
            print(tower_stl_coords)
            
            for i, (stl_x, stl_y) in enumerate(tower_stl_coords):
                label = tower_labels[i] if tower_labels and i < len(tower_labels) else f'Tower{i+1}'
                
                # Check if tower is within plot bounds
                if x_min <= stl_x <= x_max and y_min <= stl_y <= y_max:
                    ax2.plot(stl_x, stl_y, 'ko', markersize=8, markerfacecolor='yellow', markeredgewidth=2)
                    ax2.text(stl_x + 100, stl_y + 100, label, fontsize=9, fontweight='bold',
                            bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.8))
                else:
                    print(f"{label} is outside the STL crop area")
        
        ax2.set_title(f'Cropped Content \nInterpolated to Grid')
        plt.colorbar(im2, ax=ax2, shrink=0.8, label='Elevation (m)')
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Add colorbar for DEM
    plt.colorbar(im1, ax=ax1, shrink=0.8, label='Elevation (m)')
    
    plt.tight_layout()
    output_dir = os.path.dirname(stl_file_path)
    plt.savefig(output_dir)
    
    return fig

def convert_towers_to_stl_coords(tower_latlons, center_lat, center_lon, crop_size_km, rotation_deg, dem_crs):
    """
    Convert tower lat/lon coordinates to STL mesh coordinate system.
    """
    
    transformer = Transformer.from_crs("EPSG:4326", dem_crs, always_xy=True)
    
    # Convert center to UTM
    center_utm_x, center_utm_y = transformer.transform(center_lon, center_lat)
    
    # Convert towers to STL coordinates (centered at origin, rotated)
    tower_stl_coords = []
    angle_rad = np.deg2rad(-rotation_deg)  # Negative for inverse rotation
    cos_theta, sin_theta = np.cos(angle_rad), np.sin(angle_rad)
    
    for lat, lon in tower_latlons:
        # Convert to UTM first
        utm_x, utm_y = transformer.transform(lon, lat)
        
        # Shift to center at origin
        rel_x = utm_x - center_utm_x
        rel_y = utm_y - center_utm_y
        
        # Apply inverse rotation to match STL coordinate system
        stl_x = rel_x * cos_theta - rel_y * sin_theta
        stl_y = rel_x * sin_theta + rel_y * cos_theta
        
        tower_stl_coords.append((stl_x, stl_y))
    
    return tower_stl_coords
