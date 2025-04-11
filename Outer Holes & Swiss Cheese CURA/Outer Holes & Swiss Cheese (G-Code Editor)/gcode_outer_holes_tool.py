
import os
import re
import random
import math

INPUT_FOLDER = "input"
OUTPUT_FOLDER = "output"

def list_gcode_files():
    if not os.path.exists(INPUT_FOLDER):
        os.makedirs(INPUT_FOLDER)
    return [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(".gcode")]

def prompt_user_choice(prompt, options):
    print(f"\n{prompt}")
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    while True:
        choice = input("Enter choice number: ")
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        else:
            print("Invalid choice, try again.")

def get_int_input(prompt, default):
    print(f"{prompt} [Default: {default}]")
    user_input = input("Enter a value or press Enter to use default: ")
    try:
        return int(user_input) if user_input else default
    except ValueError:
        print("Invalid input, using default.")
        return default

def get_float_input(prompt, default):
    print(f"{prompt} [Default: {default}]")
    user_input = input("Enter a value or press Enter to use default: ")
    try:
        return float(user_input) if user_input else default
    except ValueError:
        print("Invalid input, using default.")
        return default

def parse_move(line):
    match = re.match(r"^G1 .*X([\d\.\-]+) Y([\d\.\-]+)(?: .*Z([\d\.\-]+))?", line)
    if match:
        x = float(match.group(1))
        y = float(match.group(2))
        z = float(match.group(3)) if match.group(3) else None
        return x, y, z
    return None

def calculate_bounds(lines):
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    for line in lines:
        coords = parse_move(line)
        if coords:
            x, y, _ = coords
            min_x, max_x = min(min_x, x), max(max_x, x)
            min_y, max_y = min(min_y, y), max(max_y, y)
    return (min_x, max_x), (min_y, max_y)

def generate_random_vectors(bounds, count, seed):
    (min_x, max_x), (min_y, max_y) = bounds
    random.seed(seed)
    vectors = []
    for _ in range(count):
        x, y = random.uniform(min_x, max_x), random.uniform(min_y, max_y)
        angle = random.uniform(0, 2 * math.pi)
        dx = math.cos(angle)
        dy = math.sin(angle)
        vectors.append(((x, y), (dx, dy)))
    return vectors

def point_line_distance_2d(px, py, x0, y0, dx, dy):
    # Distance from (px, py) to line (x0, y0) + t*(dx, dy)
    t = ((px - x0) * dx + (py - y0) * dy) / (dx**2 + dy**2)
    nearest_x = x0 + t * dx
    nearest_y = y0 + t * dy
    distance = ((px - nearest_x)**2 + (py - nearest_y)**2)**0.5
    return distance

def inject_angled_holes(lines, count, radius, seed):
    bounds = calculate_bounds(lines)
    lines_to_cut = generate_random_vectors(bounds, count, seed)
    modified = []
    removed = 0
    extrusion_move_re = re.compile(r"^G1 .*E[\d\.\-]+.*")

    for line in lines:
        coords = parse_move(line)
        if coords and extrusion_move_re.match(line):
            x, y, _ = coords
            for origin, direction in lines_to_cut:
                dist = point_line_distance_2d(x, y, origin[0], origin[1], direction[0], direction[1])
                if dist <= radius:
                    modified.append(f"; Removed by angled Swiss cheese hole at X{x:.1f} Y{y:.1f}\n")
                    removed += 1
                    break
            else:
                modified.append(line)
        else:
            modified.append(line)

    modified.append(f"; Total moves removed by angled Swiss cheese holes: {removed}\n")
    return modified

def main():
    print("🧀 Angled Swiss Cheese G-code Modifier")
    print("Simulates full-depth diagonal holes through model at random XY angles.\n")

    gcode_files = list_gcode_files()
    if not gcode_files:
        print("❗ No G-code files found in the 'input' folder. Please add a .gcode file there and re-run.")
        return

    file_name = prompt_user_choice("Choose a G-code file to modify:", gcode_files)

    line_count = get_int_input("Number of angled lines for holes", 20)
    radius = get_float_input("Hole radius (tolerance in mm)", 1.0)
    seed = get_int_input("Random seed", 42)

    input_path = os.path.join(INPUT_FOLDER, file_name)
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
    output_path = os.path.join(OUTPUT_FOLDER, f"angledholes_{file_name}")

    with open(input_path, "r") as f:
        gcode_lines = f.readlines()

    modified_lines = inject_angled_holes(gcode_lines, line_count, radius, seed)

    with open(output_path, "w") as f:
        f.writelines(modified_lines)

    print(f"✅ Angled-hole-modified G-code saved to: {output_path}")
    print("📌 Holes run diagonally through the entire model like classic Swiss cheese.")

if __name__ == "__main__":
    main()
