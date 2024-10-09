import ezdxf
import json

dxf_file = "/Users/peter/Projects/AWV/arch-313-AI-assistent-iVRI/docs/kruispunten/799C8-V016028-Meise/V016028v07_GPL_R12.dxf"

def get_distinct_entity_types_count(dxf_file):
    doc = ezdxf.readfile(dxf_file)
    msp = doc.modelspace()
    
    entity_counts = {}
    layers = []
    
    for block in doc.blocks:
        print(block.name)
        # print(f"Block '{block.name}' contains the following entities:")
        for block_entity in block:
            entity_type = block_entity.dxftype()
            if entity_type in entity_counts:
                entity_counts[entity_type] += 1
            else:
                entity_counts[entity_type] = 1   
            if block_entity.dxftype() == "ATTDEF":
                print(f" - {block_entity.dxf.tag}")
            layer = block_entity.dxf.layer
            if not layer in layers:
                layers.append(layer)

    for entity in msp:
        entity_type = entity.dxftype()
        if entity_type in entity_counts:
            entity_counts[entity_type] += 1
        else:
            entity_counts[entity_type] = 1
        layer = entity.dxf.layer
        if not layer in layers:
            layers.append(layer)

    return entity_counts, layers

entity_counts, layers = get_distinct_entity_types_count(dxf_file)

print()
print("Distinct entity types and their counts:")
for entity_type, count in entity_counts.items():
    print(f"{entity_type}: {count}")

print()
print("Distinct layers:")
for layer in layers:
    print(f"{layer}")
