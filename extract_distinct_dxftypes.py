import ezdxf
import json

dxf_file = "/Users/peter/Projects/AWV/arch-313-AI-assistent-iVRI/docs/kruispunten/799C8-V016028-Meise/V016028v07_GPL_R12.dxf"

def get_distinct_entity_types_count(dxf_file):
    doc = ezdxf.readfile(dxf_file)
    msp = doc.modelspace()
    
    entity_counts = {}
    
    for block in doc.blocks:
        print(block.name)
        # print(f"Block '{block.name}' contains the following entities:")
        for block_entity in block:
            entity_type = block_entity.dxftype()
            if entity_type in entity_counts:
                entity_counts[entity_type] += 1
            else:
                entity_counts[entity_type] = 1    

    for entity in msp:
        entity_type = entity.dxftype()
        if entity_type in entity_counts:
            entity_counts[entity_type] += 1
        else:
            entity_counts[entity_type] = 1

    return entity_counts

entity_counts = get_distinct_entity_types_count(dxf_file)

print("Distinct entity types and their counts:")
for entity_type, count in entity_counts.items():
    print(f"{entity_type}: {count}")