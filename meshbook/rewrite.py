#!/bin/python3

import argparse
import asyncio
from base64 import b64encode
from configparser import ConfigParser
import json
import math
import meshctrl
import os
import yaml

class ScriptEndTrigger(Exception):
    """Custom Exception to handle script termination events."""
    pass

def load_config(conffile: str = None, segment: str = 'meshcentral-account') -> ConfigParser:
    conffile = conffile or './api.conf'
    
    if not os.path.exists(conffile):
        raise ScriptEndTrigger(f'Missing config file {conffile}. Provide an alternative path.')

    config = ConfigParser()
    try:
        config.read(conffile)
    except Exception as err:
        raise ConfigError(f"Error reading configuration file '{conffile}': {err}")
    
    if segment not in config:
        raise ScriptEndTrigger(f'Segment "{segment}" not found in config file {conffile}.')

    return config[segment]

class meshbook():
    @staticmethod
    def compile_book(pb_path) -> dict:
        playbook = meshbook.read_yaml(pb_path)
        playbook = meshbook.replace_placeholders(playbook)
        return playbook

    @staticmethod
    def read_yaml(file_path: str) -> dict:
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)

    @staticmethod
    def replace_placeholders(playbook: dict) -> dict:
        variables = {var["name"]: var["value"] for var in playbook.get("variables", [])}

        for task in playbook.get("tasks", []):
            command = task.get("command", "")
            for var_name, var_value in variables.items():
                placeholder = f"{{{{ {var_name} }}}}"  # Create the placeholder string like "{{ host1 }}"
                command = command.replace(placeholder, var_value)
            task["command"] = command
        return playbook

async def run_book(creds):
    print(creds)

async def main():
    parser = argparse.ArgumentParser(description="Process command-line arguments")
    parser.add_argument("-pb", "--playbook", type=str, help="Path to the playbook file.", required=True)

    parser.add_argument("--conf", type=str, help="Path for the API configuration file (default: ./api.conf).")
    parser.add_argument("--nojson", action="store_true", help="Makes the program not output the JSON response data.")
    parser.add_argument("-s", "--silent", action="store_true", help="Suppress terminal output.")
    parser.add_argument("-i", "--information", action="store_true", help="Add the calculations and other informational data to the output.")

    args = parser.parse_args()

    try:
        credentials = load_config(args.conf)
        playbook = meshbook.compile_book(args.playbook)

        session = meshctrl.Session(
            credentials['websocket_url'],
            user=credentials['username'],
            password=credentials['password']
        )
        await session.initialized.wait()
        raw_device_list = await session.list_devices(timeout=10)
        device_list = raw_device_list

        print(device_list)

        await session.close()

    except ScriptEndTrigger as e:
        if not args.silent or args.information:
            print(e)


if __name__ == "__main__":
    asyncio.run(main())
