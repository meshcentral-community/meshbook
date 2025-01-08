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

'''
Script utilities are handled in the following section.
'''

class ScriptEndTrigger(Exception):
    pass

async def load_config(conf_file: str = './api.conf', segment: str = 'meshcentral-account') -> ConfigParser:
    if not os.path.exists(conf_file):
        raise ScriptEndTrigger(f'Missing config file {conf_file}. Provide an alternative path.')

    config = ConfigParser()
    try:
        config.read(conf_file)
    except Exception as err:
        raise ScriptEndTrigger(f"Error reading configuration file '{conf_file}': {err}")
    
    if segment not in config:
        raise ScriptEndTrigger(f'Segment "{segment}" not found in config file {conf_file}.')

    return config[segment]

async def init_connection(credentials: dict) -> meshctrl.Session:
    session = meshctrl.Session(
        credentials['websocket_url'],
        user=credentials['username'],
        password=credentials['password']
    )
    await session.initialized.wait()
    return session

def output(args: argparse.Namespace, message: str):
    if not args.silent or args.information:
        print(message)

'''
Creation and compilation happends in the following section, where the yaml gets read in, and edited accordingly.
'''

async def compile_book(playbook_file: dict) -> dict:
    playbook = open(playbook_file, 'r')
    playbook = await replace_placeholders(yaml.safe_load(playbook))
    return playbook

async def replace_placeholders(playbook: dict) -> dict:
    variables = {var["name"]: var["value"] for var in playbook.get("variables", [])}

    for task in playbook.get("tasks", []):
        command = task.get("command", "")
        for var_name, var_value in variables.items():
            placeholder = f"{{{{ {var_name} }}}}"  # Create the placeholder string like "{{ host1 }}"
            command = command.replace(placeholder, var_value)
        task["command"] = command
    return playbook

'''
Creation and compilation of the MeshCentral nodes list (list of all nodes available to the user in the configuration) is handled in the following section.
'''

async def compile_group_list(session: meshctrl.Session) -> dict:
    devices_response = await session.list_devices(details=False, timeout=10)
    
    local_device_list = {}
    for device in devices_response:
        if device.meshname not in local_device_list:
            local_device_list[device.meshname] = []
    
        local_device_list[device.meshname].append({
            "device_id": device.nodeid,
            "device_name": device.name,
            "device_os": device.os_description,
            "device_tags": device.tags,
            "reachable": device.connected
        })

    return local_device_list

async def gather_targets(group_list: dict, playbook: dict) -> dict:
    target_list = []

    if "device" in playbook and "group" not in playbook:
        pseudo_target = playbook["device"]

        for group in group_list:
            for device in group_list[group]:
                if device["reachable"] and pseudo_target == device["device_name"]:
                    target_list.append(device["device_id"])

    elif "group" in playbook and "device" not in playbook:
        pseudo_target = playbook["group"]

        for group in group_list:
            if pseudo_target == group:
                for device in group_list[group]:
                    if device["reachable"]:
                        target_list.append(device["device_id"])
    
    return target_list

async def execute_playbook(session: meshctrl.Session, targets: dict, playbook: dict):
    
    for task in playbook["tasks"]:
        print("Running:", task["name"])
        response = await session.run_command(nodeids=targets, command=task["command"], timeout=300)
        
        print(json.dumps(response,indent=4))
        for device in response:
            device_result = str(response[device]["result"])
            device_result = device_result.replace("Run commands completed.", "")
            print("AFTER", device_result)

async def main():
    parser = argparse.ArgumentParser(description="Process command-line arguments")
    parser.add_argument("-pb", "--playbook", type=str, help="Path to the playbook file.", required=True)
    parser.add_argument("--conf", type=str, help="Path for the API configuration file (default: ./api.conf).", required=False)
    parser.add_argument("--noout", action="store_true", help="Makes the program not output response data.", required=False)
    parser.add_argument("-s", "--silent", action="store_true", help="Suppress terminal output.", required=False)
    parser.add_argument("-i", "--information", action="store_true", help="Add the calculations and other informational data to the output.", required=False)

    args = parser.parse_args()

    try:
        output(args, "Trying to load the MeshCentral account credential file...")
        output(args, "Trying to load the Playbook yaml file and compile it into something workable...")

        credentials, playbook = await asyncio.gather(
            (load_config() if args.conf is None else load_config(args.conf)),
            (compile_book(args.playbook))
        )

        output(args, "Connecting to MeshCentral and establish a session using variables from previous credential file.")
        session = await init_connection(credentials)
    
        output(args, "Generating group list with nodes and reference the targets from that.")
        group_list = await compile_group_list(session)
        targets_list = await gather_targets(group_list, playbook)

        if len(targets_list) == 0:
            output(args, "No targets found or targets unreachable, quitting.")
        else:
            output(args, "Executing playbook on the targets.")
            output(args, json.dumps(targets_list,indent=4))
            await execute_playbook(session, targets_list, playbook)

        await session.close()

    except ScriptEndTrigger as message:
        output(args, message)


if __name__ == "__main__":
    asyncio.run(main())