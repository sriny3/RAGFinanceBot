import sys
import os
import logging

# Add backend to path
sys.path.insert(0, os.path.abspath('.'))

from ingestion.docling_parser import DoclingParser

logging.basicConfig(level=logging.INFO)

def test_parser():
    parser = DoclingParser()
    test_file = "../../data/general/employee_handbook.pdf"
    
    if not os.path.exists(test_file):
        print(f"File not found: {test_file}")
        return
        
    print(f"Parsing {test_file}...")
    doc_dict = parser.parse_document(test_file)
    
    if doc_dict:
        print(f"Parsing successful! Extracted {len(doc_dict['text'])} characters.")
        print(f"Filename: {doc_dict['filename']}")
        
        hierarchy = parser.extract_hierarchy(doc_dict)
        print(f"Extracted {len(hierarchy)} hierarchical elements.")
        
        if hierarchy:
            print("Sample hierarchy entries (depth, title):")
            for depth, info, parent_id in hierarchy[:5]:
                print(f"  {'  ' * depth} {info.get('parent_title', 'Root')} -> {info.get('text', '')[:30]}...")
    else:
        print("Parsing failed.")

if __name__ == "__main__":
    test_parser()
