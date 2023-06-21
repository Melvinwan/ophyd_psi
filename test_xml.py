from XMLGenerator import add_value_to_xml,create_xml_file, xml_config_to_dict

# config_filename = "xilinx_host.xml"
# create_xml_file(config_filename)

config = xml_config_to_dict("xilinx_host.xml")
print(config)

# parent_element = "database"
# element_name = ["host","username","password"]
# value = ["129.129.131.153","xilinx","xilinx"]
# for i, cc in enumerate(element_name):
#     add_value_to_xml(config_filename, parent_element, cc, value[i])