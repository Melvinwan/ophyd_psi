import json
import numpy as np

def create_json(config):
        # Write the configuration to a JSON file
        with open('config.json', 'w') as config_file:
                json.dump(config, config_file)
def import_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def save_list_to_json_file(list_data, file_path):
    if isinstance(list_data, np.ndarray):
        list_data = list_data.tolist()
    with open(file_path, 'w') as file:
        json.dump(list_data, file)
