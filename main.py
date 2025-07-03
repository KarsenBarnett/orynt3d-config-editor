# main.py
from core import scanner, indexer, mapper, editor, generator, logger
import os
import json

import openai
from sentence_transformers import SentenceTransformer, util

# Load the embedding model once
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Build attribute index for semantic search
attribute_index = {}
attribute_phrases = []
attribute_lookup = []

attribute_yaml = mapper.load_attribute_yaml()
for key, values in attribute_yaml.items():
    for v in values:
        phrase = f"{key}: {v}"
        attribute_phrases.append(phrase)
        attribute_lookup.append((key, v))

attribute_embeddings = embedding_model.encode(attribute_phrases, convert_to_tensor=True)

def semantic_map(raw_tags):
    enriched = {}
    for tag in raw_tags:
        tag_embedding = embedding_model.encode(tag, convert_to_tensor=True)
        cosine_scores = util.pytorch_cos_sim(tag_embedding, attribute_embeddings)[0]
        top_score, top_idx = cosine_scores.max(0)
        if top_score.item() > 0.55:
            k, v = attribute_lookup[top_idx.item()]
            enriched.setdefault(k, []).append(v)
    return enriched

def load_existing_attributes(folder):
    config_path = os.path.join(folder, "config.orynt3d")
    if not os.path.isfile(config_path):
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        attr_list = data.get("modelmeta", {}).get("attributes", [])
        attr_dict = {}
        for item in attr_list:
            k = item.get("key")
            v = item.get("value")
            if k and v:
                attr_dict.setdefault(k, []).append(v)
        return attr_dict
    except Exception as e:
        logger.log(f"Failed to load existing config attributes: {e}")
        return {}

def process_folder(xmp_file):
    folder = os.path.dirname(xmp_file)
    logger.log(f"Processing folder: {folder}")
    raw_tags = indexer.get_tags_from_xmp(xmp_file)
    logger.log(f"Raw tags from sidecar: {raw_tags}")

    # Map raw tags using both hard mapping and semantic mapping
    mapped_tags = mapper.map_tags(raw_tags)
    semantic_tags = semantic_map(raw_tags)
    for k, vlist in semantic_tags.items():
        for v in vlist:
            mapped_tags.setdefault(k, []).append(v)
    logger.log(f"Mapped attributes before merging existing config: {mapped_tags}")

    # Load existing config attributes and overwrite raw tag mapping with them
    existing_attrs = load_existing_attributes(folder)
    logger.log(f"Existing config attributes: {existing_attrs}")
    mapped_tags.update(existing_attrs)
    logger.log(f"Mapped attributes after merging with priority to existing config: {mapped_tags}")

    required_keys = mapper.get_required_keys()

    for key in required_keys:
        current_value = mapped_tags.get(key)
        if current_value:
            print(f"\nExisting value(s) for '{key}': {current_value}")
            new_value = input(f"Edit '{key}'? Enter new value(s) comma-separated, leave blank to keep, type '-' to clear: ").strip()
            if new_value == '-':
                mapped_tags.pop(key, None)
            elif new_value:
                mapped_tags[key] = [v.strip() for v in new_value.split(",") if v.strip()]
        else:
            new_value = input(f"\nMissing attribute '{key}'. Enter value(s) comma-separated, or press Enter to skip: ").strip()
            if new_value:
                mapped_tags[key] = [v.strip() for v in new_value.split(",") if v.strip()]

    edited_tags = editor.edit_tags(mapped_tags)
    logger.log(f"Edited attributes: {edited_tags}")

    generator.generate_config(folder, edited_tags)
    logger.log("Config file generated.")

def main():
    root = "K:/Model Repo/Loot Studios"
    xmp_files = scanner.find_xmp_files(root)
    for xmp_file in xmp_files:
        process_folder(xmp_file)

if __name__ == "__main__":
    main()
