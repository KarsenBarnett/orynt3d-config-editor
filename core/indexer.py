import xml.etree.ElementTree as ET
import logging

def get_tags_from_xmp(xmp_path):
    """
    Parse the given .xmp sidecar file to extract tags under dc:subject.
    Returns list of lowercase tags.
    """
    try:
        tree = ET.parse(xmp_path)
        root = tree.getroot()
        ns = {
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }

        tags = []
        for description in root.findall('.//rdf:Description', ns):
            subject = description.find('dc:subject', ns)
            if subject is not None:
                bag = subject.find('rdf:Bag', ns)
                if bag is not None:
                    for li in bag.findall('rdf:li', ns):
                        if li.text:
                            tags.append(li.text.lower())
        return tags

    except ET.ParseError as e:
        logging.error(f"Failed to parse XML {xmp_path}: {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error reading {xmp_path}: {e}")
        return []
