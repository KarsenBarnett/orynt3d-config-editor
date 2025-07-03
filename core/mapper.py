# core/mapper.py

import yaml
import os

class TagMapper:
    def __init__(self, yaml_path="attributes.yaml"):
        self.yaml_path = yaml_path
        self.attributes_map = {}
        self.phrase_map = {}
        self.required_keys = [
            "age", "armor", "class", "clothing", "element", "faction", "gender",
            "held", "holding", "mount", "pose", "race", "racegroup", "role",
            "setting", "size", "theme", "type", "weapon"
        ]
        self.load_yaml()

    def load_yaml(self):
        if not os.path.isfile(self.yaml_path):
            print(f"[mapper] YAML file not found: {self.yaml_path}")
            return

        with open(self.yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            print("[mapper] YAML file format invalid")
            return

        self.attributes_map = {k: v for k, v in data.items() if k != "phrase_map"}
        self.phrase_map = data.get("phrase_map", {})

    def map_tags(self, tags):
        result = {}
        lower_tags = [t.lower() for t in tags]

        # Direct value match
        for key, values in self.attributes_map.items():
            for val in values:
                if val.lower() in lower_tags:
                    result.setdefault(key, []).append(val)

        # Phrase-based fuzzy mapping
        for tag in lower_tags:
            for phrase, mapping in self.phrase_map.items():
                if phrase in tag:
                    key = mapping.get("key")
                    value = mapping.get("value")
                    if key and value:
                        result.setdefault(key, []).append(value)

        return result

    def get_required_keys(self):
        return self.required_keys

    def load_attribute_yaml(self):
        return self.attributes_map


# Singleton instance
tag_mapper = TagMapper()

def map_tags(tags):
    return tag_mapper.map_tags(tags)

def get_required_keys():
    return tag_mapper.get_required_keys()

def load_attribute_yaml():
    return tag_mapper.load_attribute_yaml()
