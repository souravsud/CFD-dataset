# config.py
class Config:
    # CSV and folders
    CSV_FILENAME = "coords.csv"
    DATA_FOLDER = "Data" 
    DOWNLOAD_FOLDER = "downloads"
    TERRAIN_SAVE_FOLDER = "terrain_input"
    
    # Download params
    DEM_NAME = "glo_30"
    DST_ELLIPSOIDAL_HEIGHT = False
    DST_AREA_OR_POINT = "Point"
    DOWNLOAD_SIDE_LENGTH_KM = 50
    VERBOSE_DOWNLOAD = True
    SHOW_PLOTS_DOWNLOAD = False
    
    # Processing params  
    PROCESS_CROP_SIZE_KM = 31
    DEBUG_PROCESS = True
    VERBOSE_PROCESS = True
