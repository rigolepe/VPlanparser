import json
import svgwrite
import math  # Import math for trigonometric functions like cos and sin
from collections import defaultdict

def get_min_max_coordinates(entities):
    """Helper function to calculate the min and max coordinates for estimating viewport size."""
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')

    def update_min_max(coords):
        nonlocal min_x, min_y, max_x, max_y
        for x, y in coords:
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)

    for entity in entities:
        if entity['type'] in ['Point', 'Line', 'Polyline', 'Solid', 'Circle', 'Arc', 'Text']:
            if entity['type'] in ['Point', 'Circle', 'Arc', 'Text']:
                update_min_max([entity['coordinates']])
            elif entity['type'] == 'Line':
                update_min_max(entity['coordinates'])
            elif entity['type'] in ['Polyline', 'Solid']:
                update_min_max(entity['coordinates'])

    # Check if min_x or max_x are still at inf or -inf
    if min_x == float('inf') or max_x == float('-inf'):
        # Fallback to default values if no valid coordinates were found
        min_x, min_y, max_x, max_y = 0, 0, 100, 100

    return min_x, min_y, max_x, max_y

def create_svg(json_data, output_file):
    """Function to create SVG based on JSON input."""
    
    # Group block definitions by id
    blocks = {}
    entities = []
    
    for item in json_data:
        if item['type'] == 'Block':
            blocks[item['id']] = item['entities']
        else:
            entities.append(item)

    # Estimate viewport size
    min_x, min_y, max_x, max_y = get_min_max_coordinates(entities)
    width = max_x - min_x
    height = max_y - min_y

    # Create the SVG drawing with full SVG 1.1 profile
    dwg = svgwrite.Drawing(output_file, profile='full', viewBox=f"{min_x} {min_y} {width} {height}")

    # Define block symbols
    for block_id, block_entities in blocks.items():
        symbol = dwg.symbol(id=block_id, viewBox=f"{min_x} {min_y} {width} {height}")
        draw_entities(block_entities, symbol, blocks, dwg)
        dwg.defs.add(symbol)

    # Draw main entities
    draw_entities(entities, dwg, blocks, dwg)

    # Save SVG file
    dwg.save()

def draw_entities(entities, svg_group, blocks, dwg):
    """Draws entities (points, lines, polylines, etc.) onto the SVG group."""
    
    for entity in entities:
        if entity['type'] == 'Point':
            draw_point(entity, svg_group, dwg)
        elif entity['type'] == 'Line':
            draw_line(entity, svg_group, dwg)
        elif entity['type'] == 'Polyline':
            draw_polyline(entity, svg_group, dwg)
        elif entity['type'] == 'Solid':
            draw_solid(entity, svg_group, dwg)
        elif entity['type'] == 'Circle':
            draw_circle(entity, svg_group, dwg)
        elif entity['type'] == 'Arc':
            draw_arc(entity, svg_group, dwg)
        elif entity['type'] == 'Text':
            draw_text(entity, svg_group, dwg)
        elif entity['type'] == 'Insert':
            draw_insert(entity, svg_group, blocks, dwg)

def draw_point(entity, svg_group, dwg):
    x, y = entity['coordinates']
    svg_group.add(dwg.circle(center=(x, y), r=2, fill="black"))

def draw_line(entity, svg_group, dwg):
    (x1, y1), (x2, y2) = entity['coordinates']
    svg_group.add(dwg.line(start=(x1, y1), end=(x2, y2), stroke="black", stroke_width=1))

def draw_polyline(entity, svg_group, dwg):
    points = [(x, y) for x, y in entity['coordinates']]
    svg_group.add(dwg.polyline(points=points, stroke="black", fill="none", stroke_width=1))

def draw_solid(entity, svg_group, dwg):
    points = [(x, y) for x, y in entity['coordinates']]
    svg_group.add(dwg.polygon(points=points, fill="gray"))

def draw_circle(entity, svg_group, dwg):
    x, y = entity['center']
    radius = entity['radius']
    svg_group.add(dwg.circle(center=(x, y), r=radius, stroke="black", fill="none"))

def draw_arc(entity, svg_group, dwg):
    x, y = entity['center']
    radius = entity['radius']
    start_angle = entity['start_angle']
    end_angle = entity['end_angle']
    
    # Approximate arc using path
    start_x = x + radius * math.cos(math.radians(start_angle))
    start_y = y + radius * math.sin(math.radians(start_angle))
    end_x = x + radius * math.cos(math.radians(end_angle))
    end_y = y + radius * math.sin(math.radians(end_angle))
    
    large_arc_flag = 1 if (end_angle - start_angle) > 180 else 0
    
    svg_group.add(dwg.path(d=f"M {start_x},{start_y} A {radius},{radius} 0 {large_arc_flag},1 {end_x},{end_y}",
                           stroke="black", fill="none"))

def draw_text(entity, svg_group, dwg):
    x, y = entity['coordinates']
    text = entity['text']
    svg_group.add(dwg.text(text, insert=(x, y), font_size=entity['height'], fill="black"))

def draw_insert(entity, svg_group, blocks, dwg):
    block_id = entity['name']
    if block_id in blocks:
        x, y = entity['coordinates']
        xscale = entity.get('xscale', 1)
        yscale = entity.get('yscale', 1)
        rotation = entity.get('rotation', 0)
        
        # Insert block reference
        svg_group.add(dwg.use(f"#{block_id}", insert=(x, y), transform=f"scale({xscale}, {yscale}) rotate({rotation}, {x}, {y})"))

# Example usage
json_input = '''[
    {
        "type": "Block",
        "id": "block1",
        "entities": [
            {"type": "Line", "id": "1", "layer": "0", "coordinates": [[0, 0], [100, 0]]},
            {"type": "Line", "id": "2", "layer": "0", "coordinates": [[100, 0], [100, 100]]}
        ]
    },
    {
        "type": "Insert",
        "id": "3",
        "layer": "0",
        "name": "block1",
        "coordinates": [200, 200],
        "xscale": 1,
        "yscale": 1,
        "rotation": 45
    }
]'''

json_data = json.loads(json_input)
create_svg(json_data, "output/output.svg")
