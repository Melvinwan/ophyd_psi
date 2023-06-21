import xml.etree.ElementTree as ET

# Create XML config file
def create_xml_file(filename):
    # Create the root element
    root = ET.Element("config")

    # Create the tree and write it to the file
    tree = ET.ElementTree(root)
    tree.write(filename)

def read_xml_config(filename):
    tree = ET.parse(filename)
    root = tree.getroot()

    # Iterate over all elements in the XML tree
    for element in root.iter():
        # Extract the element tag and value
        tag = element.tag
        value = element.text

        # Skip elements with no value
        if value is None:
            continue

        # Print the tag and value
        print(f"{tag}: {value}")

def xml_to_dict(element):
    # Create an empty dictionary
    result = {}

    # Process attributes
    result.update(element.attrib)

    # Process child elements
    for child in element:
        child_dict = xml_to_dict(child)
        if child.tag in result:
            # If the tag already exists, convert it to a list
            if not isinstance(result[child.tag], list):
                result[child.tag] = [result[child.tag]]
            result[child.tag].append(child_dict)
        else:
            result[child.tag] = child_dict

    # Process text content
    if element.text:
        result['text'] = element.text.strip()

    return result

def xml_config_to_dict(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    return xml_to_dict(root)

def add_value_to_xml(filename, parent_element, element_name, value=None,nested_element=None):
    tree = ET.parse(filename)
    root = tree.getroot()

    # Find the parent element where the new value will be added
    parent = root.find(parent_element)

    # If parent element doesn't exist, create it
    if parent is None:
        parent = ET.SubElement(root, parent_element)

    # Create and append the new element with its value
    new_element = parent.find(element_name)
    if new_element is None:
        new_element = ET.SubElement(parent, element_name)
    if nested_element == None:
        new_element.text = str(value)

    if nested_element != None:
        nested_child = new_element.find(nested_element)
        if nested_child == None:
            nested_child = ET.SubElement(new_element, nested_element)
        nested_child.text = str(value)

    # Write the updated tree to the file
    tree.write(filename)
