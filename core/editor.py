def edit_tags(mapped_tags):
    print("Edit tags manually if needed (leave blank to keep):")
    for key, values in mapped_tags.items():
        current = ", ".join(values)
        updated = input(f"{key} [{current}]: ").strip()
        if updated:
            mapped_tags[key] = [tag.strip() for tag in updated.split(",")]
    return mapped_tags
