import ezdxf
import json

# Helper function to convert non-serializable objects into serializable data
def convert_value(value):
    if isinstance(value, ezdxf.math.Vec3):  # Convert Vec3 objects (e.g., points) to lists
        return [value.x, value.y] # , value.z omitted
    elif isinstance(value, tuple):  # Convert tuples (like RGB colors or points) to lists
        return list(value)
    elif hasattr(value, 'x') and hasattr(value, 'y'): # and hasattr(value, 'z') omitted
        # Catch any custom point object with x, y, z attributes (like Insert types)
        return [value.x, value.y] # , value.z omitted
    else:
        return str(value)  # As a last resort, convert to string

# Load the DXF file
doc = ezdxf.readfile("/Users/peter/Projects/AWV/arch-313-AI-assistent-iVRI/docs/kruispunten/799C8-V016028-Meise/V016028v07_GPL_R12.dxf")
msp = doc.modelspace()  # Access the modelspace

# Iterate over all entities in the modelspace
def process_entities(entities, empty_block_names):
    # List to store all entities' attributes
    entities_data = []
    for entity in entities:
        # Dictionary to hold this entity's attributes
        entity_data = {
            "type": entity.dxftype(),
            "id": entity.dxf.handle
        }
        
        # Collect common DXF attributes dynamically
        skip_keys = ["location", "vtx0", "vtx1", "vtx2", "vtx3", "start", "end", "insert", "_entity", "owner", "handle", "center"] # location and vtxX are part the coordinates
        for key, value in vars(entity.dxf).items():
            if (key not in skip_keys): 
                if (key in ['rotation', 'xscale', 'yscale', 'radius', 'start_angle', 'end_angle', 'color']):
                    entity_data[key] = float(value)
                else:
                    entity_data[key] = convert_value(value)

        if entity.dxftype() == "POINT":
            entity_data["coordinates"] = convert_value(entity.dxf.location)
        elif entity.dxftype() == "LINE":
            entity_data["coordinates"] = [convert_value(entity.dxf.start), convert_value(entity.dxf.end)]
        elif entity.dxftype() == "CIRCLE":
            entity_data["coordinates"] = convert_value(entity.dxf.center)
            entity_data["radius"] = float(entity.dxf.radius)
        elif entity.dxftype() == "TEXT":
            entity_data["text"] = entity.dxf.text
            entity_data["coordinates"] = convert_value(entity.dxf.insert)
        elif entity.dxftype() == "ARC":
            entity_data["coordinates"] = convert_value(entity.dxf.center)
        elif entity.dxftype() == "POLYLINE":
            points = []
            # Iterate through all vertices in the POLYLINE entity
            for vertex in entity.vertices:
                points.append([vertex.dxf.location.x, vertex.dxf.location.y])
            entity_data["coordinates"] = points
            entity_data["is_closed"] = entity.is_closed # or entity.dxf.flags & ezdxf.lldxfconst.POLYLINE_CLOSED
        elif entity.dxftype() == "SOLID":
            entity_data["coordinates"] = [convert_value(entity.dxf.vtx0), convert_value(entity.dxf.vtx1), convert_value(entity.dxf.vtx2), convert_value(entity.dxf.vtx3)]
        elif entity.dxftype() == "LWPOLYLINE":
            entity_data["coordinates"] = [[point[0], point[1]] for point in entity]
            entity_data["is_closed"] = entity.is_closed 
        elif entity.dxftype() == "ATTDEF": # only part of BLOCK entities
            ""
        elif entity.dxftype() == "INSERT": 
            attribs = entity.attribs
            attribs_data_list = []
            for attrib in attribs:
                attrib_data = {
                    "type": attrib.dxftype(),
                    "id": attrib.dxf.handle
                }
                for key, value in vars(attrib.dxf).items():
                    if (key not in ["insert", "_entity", "handle"]): 
                        if (key in ['rotation', 'xscale', 'yscale', 'radius', 'start_angle', 'end_angle', 'color']):
                            attrib_data[key] = float(value)
                        else:
                            attrib_data[key] = convert_value(value)
                attrib_data["coordinates"] = convert_value(attrib.dxf.insert)
                # hieronder veronderstellen we dat een attrib dat geen text heeft, niet ingevuld werd door de gebruiker en dus weinig zin heeft
                if attrib_data["text"]: 
                    attribs_data_list.append(attrib_data)
            entity_data["attribs"] = attribs_data_list
            entity_data["coordinates"] = convert_value(entity.dxf.insert)
        elif entity.dxftype() == "ATTRIB":
            "See entity.attribs in INSERT entities."
    
        # Append this entity's data to the main list
        if "name" in entity_data:
            if entity_data["name"] not in empty_block_names:
                entities_data.append(entity_data)
        else:
            entities_data.append(entity_data)
        
    return entities_data


def process_block(block, empty_block_names):
    block_list = []
    entities = process_entities(block, empty_block_names)
    if entities:
        block_list.append(
            {
                "type": "BLOCK",
                "id": block.dxf.handle,
                "block_name": block.name,
                "entities": entities
            }
        )
    return block_list


def find_empty_blocks(blocks):
    empty_block_names = []
    for block in blocks:
        if not block:
            empty_block_names.append(block.name)
    return empty_block_names


def find_unused_blocks(top_level_entities, blocks):
    """
    - BLOCK use can be recursive: INSERT entities can use a BLOCK inside a BLOCK definition
    - a BLOCK definition cannot contain another BLOCK definitions
    
    So: first find all BLOCK inserts in msp and then the recursive inserts inside these blocks
    """
    all_blocks = set()
    used_blocks = set()
    for entity in top_level_entities:
        if entity.dxftype() == "INSERT":
            used_blocks.add(entity.dxf.name)
    for block in blocks:
        all_blocks.add(block.name)
        if block.name in used_blocks:
            for block_entity in block:
                if block_entity.dxftype() == "INSERT":
                    used_blocks.add(block_entity.dxf.name)
    return all_blocks - used_blocks


empty_block_names = find_empty_blocks(doc.blocks)
print(f"Empty block names: {empty_block_names}")

unused_blocks = find_unused_blocks(msp, doc.blocks)
print(f"Unused blocks: {unused_blocks}")

data = []

for block in doc.blocks:
    if block.name not in unused_blocks:
        block_list = process_block(block, empty_block_names)
        data.extend(block_list)

data.extend(process_entities(msp, empty_block_names))

# Write the collected data to a JSON file
with open("output/dxf_entities.json", "w") as json_file:
    json.dump(data, json_file, indent=4)

with open("output/dxf_entities.jsonl", "w") as jsonl_file:
    for item in data:
        json.dump(item, jsonl_file)
        jsonl_file.write('\n')  # Write a newline after each JSON object
