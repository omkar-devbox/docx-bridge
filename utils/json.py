import json
import os


# -------------------------------------------------
# Load JSON File
# -------------------------------------------------
def load_json(filepath):

    # Check whether the file exists.
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    # Read and return the JSON data.
    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)


def _json_default(obj):
    if isinstance(obj, (bytes, bytearray)):
        import base64
        return base64.b64encode(obj).decode("ascii")
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def save_json(data, filepath):

    # Create the parent directory if it does not exist.
    directory = os.path.dirname(filepath)

    if directory:
        os.makedirs(directory, exist_ok=True)

    # Write the JSON data to the file.
    # ensure_ascii=False keeps Unicode characters readable.
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
            default=_json_default,
        )


# Alias dump_json to save_json for compatibility
dump_json = save_json