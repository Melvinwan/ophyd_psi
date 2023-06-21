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

import ast

def xml_to_dict(element):
    result = {}
    result.update(element.attrib)

    for child in element:
        child_dict = xml_to_dict(child)
        if child.tag in result:
            if not isinstance(result[child.tag], list):
                result[child.tag] = [result[child.tag]]
            result[child.tag].append(child_dict)
        else:
            if isinstance(child_dict, str) and child_dict.isdigit():
                result[child.tag] = int(child_dict)
            elif isinstance(child_dict, str) and is_float(child_dict):
                result[child.tag] = float(child_dict)
            elif isinstance(child_dict, str) and is_list(child_dict):
                result[child.tag] = ast.literal_eval(child_dict)
            elif isinstance(child_dict, list):
                result[child.tag] = child_dict
            else:
                result[child.tag] = child_dict

    # Process text content
    if element.text and element.text.strip():
        text_content = element.text.strip()
        if text_content.isdigit():
            result = int(text_content)
        elif is_float(text_content):
            result = float(text_content)
        else:
            result = text_content

    # Convert key to int if possible
    if isinstance(result, dict):
        for key, value in list(result.items()):
            if isinstance(key, str) and key.isdigit():
                result[int(key)] = result.pop(key)

    return result

def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def is_list(value):
    try:
        ast.literal_eval(value)
        return isinstance(ast.literal_eval(value), list)
    except (SyntaxError, ValueError):
        return False


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

def dict_to_xml(dictionary, parent):
    for key, value in dictionary.items():
        if isinstance(value, dict):
            element = ET.SubElement(parent, key)
            dict_to_xml(value, element)
        else:
            element = ET.SubElement(parent, key)
            element.text = str(value)

def dict_to_xml_string(dictionary, root_element_name):
    root = ET.Element(root_element_name)
    dict_to_xml(dictionary, root)
    xml_string = ET.tostring(root, encoding='utf-8', method='xml')
    return xml_string

def dict_to_xml_file(dictionary, file_name):
    xml_string = dict_to_xml_string(dictionary, 'data')

    # Save the XML to a file
    with open(file_name, 'wb') as f:
        f.write(xml_string)