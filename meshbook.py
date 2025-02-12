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

def console(message: str, required: bool=False):
    if required:
        print(message)
    elif not args.silent:
        print(message)

async def load_config(segment: str = 'meshcentral-account') -> ConfigParser:
    conf_file = args.conf
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

async def translate_id_to_name(target_id: str, group_list: dict) -> str:
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

async def filter_devices(devices: list[dict], os_categories: dict, target_os: str = None) -> list[str]:
    """Filters devices based on reachability and optional OS criteria."""
    valid_devices = []

    for device in devices:
        if not device["reachable"]:
            continue  # Skip unreachable devices

        if target_os:
            if target_os in os_categories:
                if device["device_os"] not in os_categories[target_os]:
                    continue  # Skip if the device's OS is not in the allowed OS category

        valid_devices.append(device["device_id"])

    return valid_devices

async def gather_targets(playbook: dict, group_list: dict[str, list[dict]], os_categories: dict) -> list[str]:
    """Finds target devices based on playbook criteria (device or group)."""

    target_list = []
    target_os = playbook.get("target_os")

    if "device" in playbook:
        pseudo_target = playbook["device"]

        for group in group_list:
            for device in group_list[group]:
                if device["device_name"] == pseudo_target:
                    matched_devices = await filter_devices([device], os_categories, target_os)
                    target_list.extend(matched_devices)

    elif "group" in playbook:
        pseudo_target = playbook["group"]

        if pseudo_target in group_list:
            matched_devices = await filter_devices(group_list[pseudo_target], os_categories, target_os)
            target_list.extend(matched_devices)

    return target_list

async def execute_playbook(session: meshctrl.Session, targets: dict, playbook: dict, group_list: dict) -> None:
    responses_list = {}
    round = 1
    for task in playbook["tasks"]:
        console(("\033[1m\033[92m" + str(round) + ". Running: " + task["name"] + "\033[0m"))
        response = await session.run_command(nodeids=targets, command=task["command"],ignore_output=False,timeout=900)

        task_batch = []
        for device in response:
            device_result = response[device]["result"]
            response[device]["result"] = device_result.replace("Run commands completed.", "")
            response[device]["device_id"] = device
            response[device]["device_name"] = await translate_id_to_name(device, group_list)
            task_batch.append(response[device])

        responses_list["Task " + str(round)] = {
            "task_name": task["name"],
            "data": task_batch
        }
        round += 1

    console(("-" * 40))
    console((json.dumps(responses_list,indent=4)), True)

async def main():
    parser = argparse.ArgumentParser(description="Process command-line arguments")
    parser.add_argument("-pb", "--playbook", type=str, help="Path to the playbook yaml file.", required=True)

    parser.add_argument("-oc", "--oscategories", type=str, help="Path to the Operating System categories JSON file.", required=False, default="./os_categories.json")
    parser.add_argument("--conf", type=str, help="Path for the API configuration file (default: ./meshcentral.conf).", required=False, default="./meshcentral.conf")
    parser.add_argument("--nograce", action="store_true", help="Disable the grace 3 seconds before running the playbook.", required=False)
    parser.add_argument("-s", "--silent", action="store_true", help="Suppress terminal output", required=False)

    global args
    args = parser.parse_args()
    local_categories_file = "./os_categories.json"

    console(("-" * 40))
    console("Playbook: " + args.playbook)
    console("Operating System Categorisation file: " + args.oscategories)
    console("Congiguration file: " + args.conf)
    console("Grace: " + str((not args.nograce))) # Negation of bool for correct explanation
    console("Silent: False") # Can be pre-defined because if silent flag was passed then none of this would be printed.

    console(("-" * 40))
    console(("\x1B[3mTrying to load the MeshCentral account credential file...\x1B[0m"))
    console(("\x1B[3mTrying to load the Playbook yaml file and compile it into something workable...\x1B[0m"))
    console(("\x1B[3mTrying to load the Operating System categorisation JSON file...\x1B[0m"))
    try:
        with open(local_categories_file, "r") as file:
            os_categories = json.load(file)

        credentials, playbook = await asyncio.gather(
            (load_config()),
            (compile_book(args.playbook))
        )

        console(("\x1B[3mConnecting to MeshCentral and establish a session using variables from previous credential file.\x1B[0m"))
        session = await init_connection(credentials)

        console(("\x1B[3mGenerating group list with nodes and reference the targets from that.\x1B[0m"))
        group_list = await compile_group_list(session)
        targets_list = await gather_targets(playbook, group_list, os_categories)

        if len(targets_list) == 0:
            console(("\033[91mNo targets found or targets unreachable, quitting.\x1B[0m"), True)
        else:
            console(("-" * 40))
            target_name = playbook["group"] if "group" in playbook else playbook["device"] # Quickly get the name.
            console(("\033[91mExecuting playbook on the target(s): " + target_name + ".\x1B[0m"))

            if not args.nograce:
                console(("\033[91mInitiating grace-period...\x1B[0m"))
                for x in range(3):
                    console(("\033[91m{}...\x1B[0m".format(x+1)))
                    await asyncio.sleep(1)
            console(("-" * 40))
            await execute_playbook(session, targets_list, playbook, group_list)

        await session.close()

    except OSError as message:
        console(message, True)

if __name__ == "__main__":
    asyncio.run(main())
