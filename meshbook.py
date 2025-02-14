#!/bin/python3

import argparse
import asyncio
from base64 import b64encode
from colorama import just_fix_windows_console
from configparser import ConfigParser
import json
import meshctrl
import os
import yaml

grace_period = 3 # Grace period will last for x (by default 3) second(s).

'''
Script utilities are handled in the following section.
'''

class ScriptEndTrigger(Exception):
    pass

class text_color:
        black = "\033[30m"
        red = "\033[31m"
        green = "\033[32m"
        yellow = "\033[33m"
        blue = "\033[34m"
        magenta = "\033[35m"
        cyan = "\033[36m"
        white = "\033[37m"
        italic = "\x1B[3m"
        reset = "\x1B[0m"

def console(message: str, required: bool=False):
    '''
    Helper function for terminal output, with a couple variables for the silent flag. Also clears terminal color each time.
    '''
    if required:
        print(message + text_color.reset)
    elif not args.silent:
        print(message + text_color.reset)

async def load_config(segment: str = 'meshcentral-account') -> dict:
    '''
    Function that loads the segment from the meshcentral.conf (by default) file and returns the it in a dict.
    '''

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
    '''
    Use the libmeshctrl library to initiate a Secure Websocket (wss) connection to the MeshCentral instance.
    '''

    session = meshctrl.Session(
        credentials['websocket_url'],
        user=credentials['username'],
        password=credentials['password']
    )
    await session.initialized.wait()
    return session

async def translate_nodeid_to_name(target_id: str, group_list: dict) -> str:
    '''
    Simple function that looks up nodeid to the human-readable name if existent - otherwise return None.
    '''

    for group in group_list:
        for device in group_list[group]:
            if device["device_id"] == target_id:
                return device["device_name"]
    return None

'''
Creation and compilation happends in the following section, where the yaml gets read in, and edited accordingly.
'''

async def compile_book(meshbook_file: dict) -> dict:
    '''
    Simple function that opens the file and replaces placeholders through the next function. After that just return it.
    '''

    meshbook = open(meshbook_file, 'r')
    meshbook = await replace_placeholders(yaml.safe_load(meshbook))
    return meshbook

async def replace_placeholders(meshbook: dict) -> dict:
    '''
    Replace the placeholders in both name and command fields of the tasks. According to the variables defined in the variables list.
    '''

    variables = {var["name"]: var["value"] for var in meshbook.get("variables", [])}

    for task in meshbook.get("tasks", []):
        task_name = task.get("name")
        for var_name, var_value in variables.items():
            placeholder = f"{{{{ {var_name} }}}}"
            task_name = task_name.replace(placeholder, var_value)
        task["name"] = task_name

        command = task.get("command")
        for var_name, var_value in variables.items():
            placeholder = f"{{{{ {var_name} }}}}"  # Create the placeholder string like "{{ host1 }}"
            command = command.replace(placeholder, var_value)
        task["command"] = command

    return meshbook

'''
Creation and compilation of the MeshCentral nodes list (list of all nodes available to the user in the configuration) is handled in the following section.
'''

async def compile_group_list(session: meshctrl.Session) -> dict:
    '''
    Function that retrieves the devices from MeshCentral and compiles it into a efficient list.
    '''

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

async def filter_targets(devices: list[dict], os_categories: dict, target_os: str = None) -> list[str]:
    '''
    Filters devices based on reachability and optional OS criteria, supporting nested OS categories.
    '''

    valid_devices = []

    def get_os_variants(category: str, os_map: dict) -> set:
        '''
        Extracts all OS names under a given category if it exists.
        '''

        for key, value in os_map.items():
            if key == category:
                if isinstance(value, dict):  # Expand nested categories
                    os_set = set()
                    for subcat in value:
                        os_set.update(get_os_variants(subcat, value))
                    return os_set
                elif isinstance(value, list):  # Direct OS list
                    return set(value)
        return set()

    allowed_os = set()

    # Identify correct OS filtering scope
    for key in os_categories:
        if key == target_os:
            allowed_os = get_os_variants(target_os, os_categories)
            break  # Stop searching once a match is found

        if isinstance(os_categories[key], dict) and target_os in os_categories[key]:
            allowed_os = get_os_variants(target_os, os_categories[key])
            break  # Stop searching once a match is found

    # Filter out unreachable devices
    for device in devices:
        if not device["reachable"]:
            continue  # Skip unreachable devices.

        if not target_os or device["device_os"] in allowed_os:
            valid_devices.append(device["device_id"])

    return valid_devices

async def gather_targets(meshbook: dict, group_list: dict[str, list[dict]], os_categories: dict) -> list[str]:
    '''
    Finds target devices based on meshbook criteria (device or group).
    '''

    target_list = []
    target_os = meshbook.get("target_os")

    async def process_device_or_group(pseudo_target, group_list, os_categories, target_os) -> list[str]:
        '''
        Helper function to process devices or groups.
        '''

        matched_devices = []
        for group in group_list:
            for device in group_list[group]:
                if device["device_name"] == pseudo_target:
                    matched_devices.append(device)

        if matched_devices:
            return await filter_targets(matched_devices, os_categories, target_os)
        return []

    match meshbook:
        case {"device": pseudo_target}:  # Single device target
            if isinstance(pseudo_target, str):
                matched_devices = await process_device_or_group(pseudo_target, group_list, os_categories, target_os)
                target_list.extend(matched_devices)

            else:
                console(text_color.yellow + "Please use devices (Notice the 'S') for multiple devices.", True)

        case {"devices": pseudo_target}:  # List of devices
            if isinstance(pseudo_target, list):
                for sub_pseudo_device in pseudo_target:
                    matched_devices = await process_device_or_group(sub_pseudo_device, group_list, os_categories, target_os)
                    target_list.extend(matched_devices)

            else:
                console(text_color.yellow + "The 'devices' method is being used, but only one string is given. Did you mean 'device'?", True)

        case {"group": pseudo_target}:  # Single group target
            if isinstance(pseudo_target, str) and pseudo_target in group_list:
                matched_devices = await filter_targets(group_list[pseudo_target], os_categories, target_os)
                target_list.extend(matched_devices)

            else:
                console(text_color.yellow + "Please use groups (Notice the 'S') for multiple groups.", True)

        case {"groups": pseudo_target}:  # List of groups
            if isinstance(pseudo_target, list):
                for sub_pseudo_target in pseudo_target:
                    if sub_pseudo_target in group_list:
                        matched_devices = await filter_targets(group_list[sub_pseudo_target], os_categories, target_os)
                        target_list.extend(matched_devices)
            else:
                console(text_color.yellow + "The 'groups' method is being used, but only one string is given. Did you mean 'group'?", True)

    return target_list

async def execute_meshbook(session: meshctrl.Session, targets: dict, meshbook: dict, group_list: dict) -> None:
    '''
    Actual function that handles meshbook execution, also responsible for formatting the resulting JSON.
    '''

    responses_list = {}
    round = 1

    for task in meshbook["tasks"]:
        console(text_color.green + str(round) + ". Running: " + task["name"])
        response = await session.run_command(nodeids=targets, command=task["command"],ignore_output=False,timeout=900)

        task_batch = []
        for device in response:
            device_result = response[device]["result"]
            response[device]["result"] = device_result.replace("Run commands completed.", "")
            response[device]["device_id"] = device
            response[device]["device_name"] = await translate_nodeid_to_name(device, group_list)
            task_batch.append(response[device])

        responses_list["Task " + str(round)] = {
            "task_name": task["name"],
            "data": task_batch
        }
        round += 1

    console(("-" * 40))
    if args.indent:
        console((json.dumps(responses_list,indent=4)), True)

    else:
        console(json.dumps(responses_list), True)

async def main():
    just_fix_windows_console()
    '''
    Main function where the program starts. Place from which all comands originate (eventually).
    '''

    parser = argparse.ArgumentParser(description="Process command-line arguments")
    parser.add_argument("-pb", "--meshbook", type=str, help="Path to the meshbook yaml file.", required=True)

    parser.add_argument("-oc", "--oscategories", type=str, help="Path to the Operating System categories JSON file.", required=False, default="./os_categories.json")
    parser.add_argument("--conf", type=str, help="Path for the API configuration file (default: ./meshcentral.conf).", required=False, default="./meshcentral.conf")
    parser.add_argument("--nograce", action="store_true", help="Disable the grace 3 seconds before running the meshbook.", required=False)
    parser.add_argument("-i", "--indent", action="store_true", help="Use an JSON indentation of 4 when this flag is passed.", required=False)
    parser.add_argument("-s", "--silent", action="store_true", help="Suppress terminal output", required=False)

    global args
    args = parser.parse_args()
    local_categories_file = "./os_categories.json"

    try:
        with open(local_categories_file, "r") as file:
            os_categories = json.load(file)

        credentials, meshbook = await asyncio.gather(
            (load_config()),
            (compile_book(args.meshbook))
        )

        '''
        The following section mainly displays used variables and first steps of the program to the console.
        '''

        console(("-" * 40))
        console("meshbook: " + text_color.yellow + args.meshbook)
        console("Operating System Categorisation file: " + text_color.yellow + args.oscategories)
        console("Configuration file: " + text_color.yellow + args.conf)
        console("Target Operating System category given: " + text_color.yellow + meshbook["target_os"])
        if "device" in meshbook:
            console("Target device: " + text_color.yellow + str(meshbook["device"]))

        elif "group" in meshbook:
            console("Target group: " + text_color.yellow + str(meshbook["group"]))

        console("Grace: " + text_color.yellow + str((not args.nograce))) # Negation of bool for correct explanation
        console("Silent: " + text_color.yellow + "False") # Can be pre-defined because if silent flag was passed then none of this would be printed.

        session = await init_connection(credentials)
        console(("-" * 40))
        console(text_color.italic + "Trying to load the MeshCentral account credential file...")
        console(text_color.italic + "Trying to load the meshbook yaml file and compile it into something workable...")
        console(text_color.italic + "Trying to load the Operating System categorisation JSON file...")
        console(text_color.italic + "Connecting to MeshCentral and establish a session using variables from previous credential file.")
        console(text_color.italic + "Generating group list with nodes and reference the targets from that.")

        '''
        End of the main information displaying section.
        '''

        group_list = await compile_group_list(session)
        targets_list = await gather_targets(meshbook, group_list, os_categories)

        if len(targets_list) == 0:
            console(text_color.red + "No targets found or targets unreachable, quitting.", True)
            console(("-" * 40), True)

        else:
            console(("-" * 40))

            match meshbook:
                case {"group": candidate_target_name}:
                    target_name = candidate_target_name

                case {"groups": candidate_target_name}:
                    target_name = str(candidate_target_name)

                case {"device": candidate_target_name}:
                    target_name = candidate_target_name

                case {"devices": candidate_target_name}:
                    target_name = str(candidate_target_name)

            console(text_color.yellow + "Executing meshbook on the target(s): " + text_color.green + target_name + ".")

            if not args.nograce:
                console(text_color.yellow + "Initiating grace-period...")

                for x in range(grace_period):
                    console(text_color.yellow + "{}...".format(x+1)) # Countdown!
                    await asyncio.sleep(1)

            console(("-" * 40))
            await execute_meshbook(session, targets_list, meshbook, group_list)

        await session.close()

    except OSError as message:
        console(text_color.red + message, True)

if __name__ == "__main__":
    asyncio.run(main())
