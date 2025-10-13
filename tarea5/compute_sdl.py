import math
import os

# Given city coordinates (x, y)
locations = dict(
    Arad=(91, 492), Bucharest=(400, 327), Craiova=(253, 288),
    Drobeta=(165, 299), Eforie=(562, 293), Fagaras=(305, 449),
    Giurgiu=(375, 270), Hirsova=(534, 350), Iasi=(473, 506),
    Lugoj=(165, 379), Mehadia=(168, 339), Neamt=(406, 537),
    Oradea=(131, 571), Pitesti=(320, 368), Rimnicu=(233, 410),
    Sibiu=(207, 457), Timisoara=(94, 410), Urziceni=(456, 350),
    Vaslui=(509, 444), Zerind=(108, 531), Ganeasa=(275, 350)
)

# Target city for distance calculation
TARGET_CITY = "Fagaras"
OUTPUT_FILENAME = "distance_to_fagaras.txt"

def calculate_straight_line_distance(loc1, loc2):
    """
    Calculates the Euclidean distance between two points (loc1 and loc2).
    loc1 and loc2 should be tuples of (x, y) coordinates.
    """
    x1, y1 = loc1
    x2, y2 = loc2
    # Euclidean distance formula: sqrt((x2 - x1)^2 + (y2 - y1)^2)
    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return distance

def generate_distance_file():
    """
    Calculates the distance from all cities to the TARGET_CITY and 
    writes the result to a file in the required format.
    """
    try:
        fagaras_coords = locations[TARGET_CITY]
    except KeyError:
        print(f"Error: Target city '{TARGET_CITY}' not found in locations dictionary.")
        return

    # A list to hold the formatted lines
    output_lines = []

    # Iterate through all cities to calculate the distance to Fagaras
    for city, coords in locations.items():
        # Calculate the distance
        distance = calculate_straight_line_distance(coords, fagaras_coords)
        
        # Take only the integer part of the distance
        integer_distance = int(distance)
        
        # Format the line as required: h(city_name_lowercase, distance_integer).
        # Note: The example uses lowercase city names like 'drobeta', 
        # so we convert the city name to lowercase for consistency.
        formatted_line = f"h({city.lower()}, {integer_distance})."
        output_lines.append(formatted_line)

    # Write all lines to the output file
    try:
        with open(OUTPUT_FILENAME, 'w') as f:
            for line in output_lines:
                f.write(line + '\n')

        print(f"✅ Success! Distances have been calculated and saved to **{OUTPUT_FILENAME}**.")
        print("-" * 50)
        print("Example content of the file:")
        # Print the first few lines as a preview
        for line in output_lines[:5]: 
            print(line)
        if len(output_lines) > 5:
             print("...")
        print("-" * 50)

    except IOError as e:
        print(f"Error writing to file {OUTPUT_FILENAME}: {e}")
        
# Execute the function
if __name__ == "__main__":
    generate_distance_file()