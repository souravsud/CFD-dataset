import random

def generate_directions(sectors, absolute_random=False):
    """
    Generates four random directions.
    
    Args:
        absolute_random (bool): If True, generates four completely random
                                directions between 0 and 360.
                                If False, generates one random direction from
                                each of the four 90-degree sectors.
                                
    Returns:
        list: A list of four random direction angles in degrees.
    """
    sector_size = 360 // sectors
    
    if absolute_random:
        # Generate four entirely random directions from 0 to 360
        return [random.randint(0, 360) for _ in range(sectors)]
    else:
        # Generate one random direction per 90-degree sector
        directions = []
        for i in range(sectors):
            lower_bound = i * sector_size
            upper_bound = (i + 1) * sector_size
            directions.append(random.randint(lower_bound, upper_bound))
        return directions
    
if __name__ == "__main__":
    # Example usage
    print("Random directions (sector-based):", generate_directions(4, absolute_random=False))
    print("Random directions (absolute):", generate_directions(16, absolute_random=False))