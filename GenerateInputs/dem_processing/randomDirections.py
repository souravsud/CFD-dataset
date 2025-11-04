import random

def generate_directions(absolute_random=False):
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
    if absolute_random:
        # Generate four entirely random directions from 0 to 360
        return [random.randint(0, 360) for _ in range(4)]
    else:
        # Generate one random direction per 90-degree sector
        directions = []
        for i in range(4):
            lower_bound = i * 90
            upper_bound = (i + 1) * 90
            directions.append(random.randint(lower_bound, upper_bound))
        return directions