import json
import svgwrite
import math  # Import math for trigonometric functions like cos and sin
from collections import defaultdict

DEFAULT_STROKE_WIDTH = 0.1

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
        if entity['type'] in ['POINT', 'LINE', 'POLYLINE', 'SOLID', 'CIRCLE', 'ARC', 'TEXT']:
            if entity['type'] in ['POINT', 'CIRCLE', 'ARC', 'TEXT']:
                update_min_max([entity['coordinates']])
            elif entity['type'] in ['LINE', 'POLYLINE', 'SOLID']:
                update_min_max(entity['coordinates'])

    # Check if min_x or max_x are still at inf or -inf
    if min_x == float('inf') or max_x == float('-inf'):
        # Fallback to default values if no valid coordinates were found
        min_x, min_y, max_x, max_y = 0, 0, 100, 100

    return min_x, min_y, max_x, max_y


def draw_entities(entities, svg_group, blocks, dwg):
    """Draws entities (points, lines, polylines, etc.) onto the SVG group."""
    
    for entity in entities:
        if entity['type'] == 'POINT':
            draw_point(entity, svg_group, dwg)
        elif entity['type'] == 'LINE':
            draw_line(entity, svg_group, dwg)
        elif entity['type'] == 'POLYLINE':
            draw_polyline(entity, svg_group, dwg)
        elif entity['type'] == 'SOLID':
            draw_solid(entity, svg_group, dwg)
        elif entity['type'] == 'CIRCLE':
            draw_circle(entity, svg_group, dwg)
        elif entity['type'] == 'ARC':
            draw_arc(entity, svg_group, dwg)
        elif entity['type'] == 'TEXT':
            draw_text(entity, svg_group, dwg)
        elif entity['type'] == 'INSERT':
            draw_insert(entity, svg_group, blocks, dwg)

def draw_point(entity, svg_group, dwg):
    x, y = entity['coordinates']
    svg_group.add(dwg.circle(center=(x, y), r=2, fill="black", stroke_width=DEFAULT_STROKE_WIDTH))

def draw_line(entity, svg_group, dwg):
    (x1, y1), (x2, y2) = entity['coordinates']
    svg_group.add(dwg.line(start=(x1, y1), end=(x2, y2), stroke="black", stroke_width=DEFAULT_STROKE_WIDTH))

def draw_polyline(entity, svg_group, dwg):
    points = [(x, y) for x, y in entity['coordinates']]
    svg_group.add(dwg.polyline(points=points, stroke="black", fill="none", stroke_width=DEFAULT_STROKE_WIDTH))

def draw_solid(entity, svg_group, dwg):
    points = [(x, y) for x, y in entity['coordinates']]
    svg_group.add(dwg.polygon(points=points, fill="gray", stroke_width=DEFAULT_STROKE_WIDTH))

def draw_circle(entity, svg_group, dwg):
    x, y = entity['coordinates']
    radius = entity['radius']
    svg_group.add(dwg.circle(center=(x, y), r=radius, stroke="black", fill="none", stroke_width=DEFAULT_STROKE_WIDTH))

def draw_arc(entity, svg_group, dwg):
    x, y = [n for n in entity['coordinates']]
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
                           stroke="black", fill="none", stroke_width=DEFAULT_STROKE_WIDTH))

def draw_text(entity, svg_group, dwg):
    x, y = entity['coordinates']
    text = entity['text']
    rotation = entity.get('rotation', 0) 
    # in de transformatie hieronder is de volgorde van de rotate, scale en translate belangrijk!
    svg_group.add(dwg.text(text, insert=(x, y), font_size=entity['height'], fill="black", transform=f'rotate({rotation}, {x}, {y}) scale(1, -1) translate(0, {-2 * y})'))


def transform_point(point, scale, rotation, translation):
    """Transforms a point by scaling, rotating, and translating."""
    # Apply scaling
    x, y = point[0] * scale[0], point[1] * scale[1]

    # Apply rotation
    angle_rad = math.radians(rotation)
    x_rot = x * math.cos(angle_rad) - y * math.sin(angle_rad)
    y_rot = x * math.sin(angle_rad) + y * math.cos(angle_rad)

    # Apply translation
    x_trans = x_rot + translation[0]
    y_trans = y_rot + translation[1]

    return [x_trans, y_trans]


def draw_insert(entity, svg_group, blocks, dwg):
    """Draws an INSERT entity with its attributes."""
    name = entity['name']
    if name not in blocks:
        return  # Block definition not found

    block_entities = blocks[name]
    transform = {
        'scale': (entity.get('xscale', 1.0), entity.get('yscale', 1.0)),
        'rotation': entity.get('rotation', 0),
        'translation': entity['coordinates']
    }

    # Draw each entity in the block
    for block_entity in block_entities:
        if block_entity['type'] == 'ATTDEF':
            # Find the corresponding ATTRIB from the insert
            attrib = next((a for a in entity.get('attribs', []) if a['tag'] == block_entity['tag']), None)
            if attrib:
                attrib_text = attrib.get('text', block_entity.get('text', ''))
                # Draw the text attribute
                text_position = transform_point(attrib['coordinates'], transform['scale'], 
                                                transform['rotation'], transform['translation'])
                text_rotation = attrib.get('rotation', 0) 
                svg_group.add(dwg.text(attrib_text, insert=text_position, 
                                 transform=f'rotate({text_rotation},{text_position[0]},{text_position[1]}) scale(1, -1) translate(0, {-2 * text_position[1]})',
                                 font_size=block_entity.get('height', 10)))

        elif block_entity['type'] == 'LINE':
            start = transform_point(block_entity['coordinates'][0], transform['scale'], 
                                    transform['rotation'], transform['translation'])
            end = transform_point(block_entity['coordinates'][1], transform['scale'], 
                                  transform['rotation'], transform['translation'])
            svg_group.add(dwg.line(start=start, end=end, stroke='black', stroke_width=DEFAULT_STROKE_WIDTH))

        elif block_entity['type'] == 'CIRCLE':
            center = transform_point(block_entity['coordinates'], transform['scale'], 
                                     transform['rotation'], transform['translation'])
            radius = block_entity['radius'] * transform['scale'][0]  # Assuming uniform scaling
            svg_group.add(dwg.circle(center=center, r=radius, stroke='black', fill='none', stroke_width=DEFAULT_STROKE_WIDTH))

        elif block_entity['type'] == 'TEXT':
            position = transform_point(block_entity['coordinates'], transform['scale'], 
                                       transform['rotation'], transform['translation'])
            rotation = block_entity.get('rotation', 0) 
            svg_group.add(dwg.text(block_entity['text'], insert=position, 
                             transform=f'rotate({rotation},{position[0]},{position[1]}) scale(1, -1) translate(0, {-2 * position[1]})',
                             font_size=block_entity.get('height', 10), stroke_width=DEFAULT_STROKE_WIDTH))
        elif block_entity['type'] == 'SOLID':
            positions = [transform_point(coords, transform['scale'],  transform['rotation'], transform['translation']) for coords in block_entity['coordinates']]
            points = [(x, y) for x, y in positions]
            svg_group.add(dwg.polygon(points=points, fill="gray", stroke_width=DEFAULT_STROKE_WIDTH))
        elif block_entity['type'] == 'POLYLINE':
            positions = [transform_point(coords, transform['scale'],  transform['rotation'], transform['translation']) for coords in block_entity['coordinates']]
            points = [(x, y) for x, y in positions]
            svg_group.add(dwg.polyline(points=points, stroke="black", fill="none", stroke_width=DEFAULT_STROKE_WIDTH))
        # Add handling for other block_entity types as needed


def main(input_file, output_file):
    blocks = {}
    entities = []
    
    with open(input_file, 'r') as f:
        json_data = json.load(f)
    
    for item in json_data:
        if item['type'] == 'BLOCK':
            blocks[item['block_name']] = item['entities']
        else:
            entities.append(item)

    # Estimate viewport size
    min_x, min_y, max_x, max_y = get_min_max_coordinates(entities)
    width = max_x - min_x
    height = max_y - min_y

    # Create the SVG drawing with full SVG 1.1 profile
    dwg = svgwrite.Drawing(output_file, profile='full', viewBox=f"{min_x} {-min_y} {width} {height}")
    transform_group = dwg.g(transform=f'translate(0, {height}) scale(1, -1)')
    
    # Define block symbols
    for block_id, block_entities in blocks.items():
        symbol = dwg.symbol(id=block_id, viewBox=f"{min_x} {-min_y} {width} {height}")
        dwg.defs.add(symbol)

    # Draw main entities
    draw_entities(entities, transform_group, blocks, dwg)
    dwg.add(transform_group)

    # Save SVG file
    dwg.save()
    
    

# if __name__ == '__main__':
#     import sys
#     if len(sys.argv) != 3:
#         print("Usage: python data2svg.py <input_file.json> <output_file.svg>")
#         sys.exit(1)

#     main(sys.argv[1], sys.argv[2])


main("./output/dxf_entities.json", "output/output.svg")
