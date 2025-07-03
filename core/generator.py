
# core/generator.py
import json
import os

def generate_config(folder, attributes):
    config = {
        "version": 5,
        "scancfg": {
            "fileMode": 0,
            "modelMode": 0,
            "ifLeaf": False,
            "filetypes": [1],
            "autotags": 1,
            "archives": 0,
            "thumbnails": 0,
            "propagation": 0,
            "tags": {
                "include": [],
                "exclude": [],
                "clear": False
            },
            "attributes": {
                "include": [],
                "exclude": [],
                "clear": False
            }
        },
        "modelmeta": {
            "name": None,
            "notes": "",
            "tags": [],
            "cover": None,
            "collections": [],
	"attributes": [
	    {"key": k, "value": val}
	    for k, v in attributes.items() 
	    for val in (v if isinstance(v, list) else [v])
	]
        }
    }

    output_path = os.path.join(folder, "config.orynt3d")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

