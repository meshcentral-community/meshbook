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

def output_text(message: str, required=False):
    if required:
        print(message)
    elif not args.silent:
        print(message)

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

async def translate_id_to_name(target_id: str) -> str:
    for group in group_list:
        for device in group_list[group]:
            if device["device_id"] == target_id:
                return device["device_name"]

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

async def gather_targets(playbook: dict) -> dict:
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
    responses_list = {}
    round = 1
    for task in playbook["tasks"]:
        output_text(("\033[1m\033[92m" + str(round) + ". Running: " + task["name"] + "\033[0m"), False)
        response = await session.run_command(nodeids=targets, command=task["command"], timeout=300)
        
        task_batch = []
        for device in response:
            device_result = response[device]["result"]
            response[device]["result"] = device_result.replace("Run commands completed.", "")
            response[device]["device_id"] = device
            response[device]["device_name"] = await translate_id_to_name(device)
            task_batch.append(response[device])

        responses_list["Task " + str(round)] = task_batch
        round += 1
    
    output_text(("-" * 40), False)
    output_text((json.dumps(responses_list,indent=4)), True)

async def main():
    parser = argparse.ArgumentParser(description="Process command-line arguments")
    parser.add_argument("-pb", "--playbook", type=str, help="Path to the playbook file.", required=True)
    parser.add_argument("--conf", type=str, help="Path for the API configuration file (default: ./api.conf).", required=False)
    parser.add_argument("--noout", action="store_true", help="Makes the program not output response data.", required=False)
    parser.add_argument("-s", "--silent", action="store_true", help="Suppress terminal output", required=False)

    global args
    args = parser.parse_args()

    try:
        output_text(("-" * 40), False)
        output_text(("\x1B[3mTrying to load the MeshCentral account credential file...\x1B[0m"), False)
        output_text(("\x1B[3mTrying to load the Playbook yaml file and compile it into something workable...\x1B[0m"), False)

        credentials, playbook = await asyncio.gather(
            (load_config() if args.conf is None else load_config(args.conf)),
            (compile_book(args.playbook))
        )

        output_text(("\x1B[3mConnecting to MeshCentral and establish a session using variables from previous credential file.\x1B[0m"), False)
        session = await init_connection(credentials)
    
        output_text(("\x1B[3mGenerating group list with nodes and reference the targets from that.\x1B[0m"), False)
        global group_list
        group_list = await compile_group_list(session)
        targets_list = await gather_targets(playbook)

        output_text(("-" * 40), False)
        if len(targets_list) == 0:
            output_text(("\033[91mNo targets found or targets unreachable, quitting.\x1B[0m"), True)
        else:
            output_text(("\033[91mExecuting playbook on the targets.\x1B[0m"), False)
            await execute_playbook(session, targets_list, playbook)

        await session.close()

    except OSError as message:
        output_text(message, True)


if __name__ == "__main__":
    asyncio.run(main())