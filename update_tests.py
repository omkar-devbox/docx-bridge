import os
import re

files_to_update = [
    'tests/doc/test_doc_roundtrip.py',
    'tests/doc/test_doc_pipeline.py'
]

for filepath in files_to_update:
    with open(filepath, 'r') as f:
        content = f.read()
    
    if 'BinaryToJsonParser' not in content:
        content = content.replace('from formats.doc.reader import DocReader', 'from formats.doc.reader import DocReader\nfrom parser.doc.binary_to_json import BinaryToJsonParser')
    
    if 'JsonToBinaryParser' not in content:
        content = content.replace('from formats.doc.writer import DocWriter', 'from formats.doc.writer import DocWriter\nfrom parser.doc.json_to_binary import JsonToBinaryParser')
    
    content = re.sub(r'(\w+)\.parse_document\(\)', r'BinaryToJsonParser(\1).parse_document()', content)
    content = re.sub(r'(\w+)\.build_document\(([^)]+)\)', r'JsonToBinaryParser().build_document(\2, \1)', content)
    
    with open(filepath, 'w') as f:
        f.write(content)
