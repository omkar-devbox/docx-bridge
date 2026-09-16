import math
from datetime import datetime, timezone
from formats.doc.cfbf import *

def build_tree(paths, stream_data):
    # This logic creates the DirectoryEntry tree
    nodes = {}
    class Node:
        def __init__(self, name, type_):
            self.name = name
            self.type = type_
            self.children = {}
            self.data = None
            self.entry = None
            self.clsid = b"\x00"*16

    root = Node("Root Entry", STGTY_ROOT)
    for path, data in stream_data.items():
        parts = path.split("/")
        curr = root
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                if part not in curr.children:
                    curr.children[part] = Node(part, STGTY_STREAM)
                curr.children[part].data = data
            else:
                if part not in curr.children:
                    curr.children[part] = Node(part, STGTY_STORAGE)
                curr = curr.children[part]

    # Assign CLSIDs if they are known, e.g. from a separate map in CFBWriter
    return root

