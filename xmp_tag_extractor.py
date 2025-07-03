import xml.etree.ElementTree as ET
import sys

def extract_xmp_tags(xmp_file_path):
    ns = {
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'dc': 'http://purl.org/dc/elements/1.1/'
    }

    try:
        tree = ET.parse(xmp_file_path)
        root = tree.getroot()

        # XPath to find tag elements inside dc:subject/rdf:Bag/rdf:li
        subjects = root.findall(".//rdf:Description/dc:subject/rdf:Bag/rdf:li", ns)

        if not subjects:
            print(f"No tags found in {xmp_file_path}")
            return

        tags = [elem.text.strip().lower() for elem in subjects if elem.text]

        print(f"Tags found in {xmp_file_path}:")
        for tag in tags:
            print(f"- {tag}")

    except Exception as e:
        print(f"Error parsing {xmp_file_path}: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python xmp_tag_extractor.py <path_to_xmp_file>")
    else:
        xmp_path = sys.argv[1]
        extract_xmp_tags(xmp_path)
