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
doc = ezdxf.readfile("799C8-V016028-Meise/V016028v07_GPL_R12.dxf")
msp = doc.modelspace()  # Access the modelspace

# List to store all entities' attributes
entities_data = []

# Iterate over all entities in the modelspace
def process_entities(entities, block_name = None):
    for entity in entities:
        # Dictionary to hold this entity's attributes
        entity_data = {
            "type": entity.dxftype(),
            "attributes": {}
        }
        
        if (block_name):
            entity_data["attributes"]["block_naam"] = block_name
        
        # Collect common DXF attributes dynamically
        for key, value in vars(entity.dxf).items():
            if (key not in ["location", "vtx0", "vtx1", "vtx2", "vtx3"]): # location and vtxX are part the coordinates
                entity_data["attributes"][key] = convert_value(value)

        # Some entities have additional attributes; store those as well
        if entity.dxftype() == "LINE":
            entity_data["attributes"]["coordinates"] = [convert_value(entity.dxf.start), convert_value(entity.dxf.end)]
        elif entity.dxftype() == "CIRCLE":
            entity_data["attributes"]["center"] = convert_value(entity.dxf.center)
            entity_data["attributes"]["radius"] = convert_value(entity.dxf.radius)
        elif entity.dxftype() == "TEXT":
            entity_data["attributes"]["text"] = entity.dxf.text
            entity_data["attributes"]["coordinates"] = convert_value(entity.dxf.insert)
        elif entity.dxftype() == "ARC":
            ""
        elif entity.dxftype() == "POLYLINE":
            points = []
            # Iterate through all vertices in the POLYLINE entity
            for vertex in entity.vertices:
                points.append([vertex.dxf.location.x, vertex.dxf.location.y])
            entity_data["attributes"]["coordinates"] = points
            entity_data["attributes"]["is_closed"] = entity.is_closed # or entity.dxf.flags & ezdxf.lldxfconst.POLYLINE_CLOSED
        elif entity.dxftype() == "POINT":
            entity_data["attributes"]["coordinates"] = convert_value(entity.dxf.location)
        elif entity.dxftype() == "SOLID":
            entity_data["attributes"]["coordinates"] = [convert_value(entity.dxf.vtx0), convert_value(entity.dxf.vtx1), convert_value(entity.dxf.vtx2), convert_value(entity.dxf.vtx3)]
        elif entity.dxftype() == "LWPOLYLINE":
            entity_data["attributes"]["coordinates"] = [[point[0], point[1]] for point in entity]
            entity_data["attributes"]["is_closed"] = entity.is_closed 
    
        # Append this entity's data to the main list
        entities_data.append(entity_data)

process_entities(msp)
for block in doc.blocks:
    process_entities(block, block.name)

# Write the collected data to a JSON file
with open("dxf_entities.json", "w") as json_file:
    json.dump(entities_data, json_file, indent=4)
