#!/bin/python3

# Public Python libraries
import argparse
import asyncio
from colorama import just_fix_windows_console
import pyotp
import json
import meshctrl

# Local Python libraries/modules
from modules.console import *
from modules.executor import *
from modules.utilities import *

meshbook_version = "1.3.1"
grace_period = 3 # Grace period will last for x (by default 3) second(s).

async def init_connection(credentials: dict) -> meshctrl.Session:
    '''
    Use the libmeshctrl library to initiate a Secure Websocket (wss) connection to the MeshCentral instance.
    '''

    if "totp_secret" in credentials:
        totp = pyotp.TOTP(credentials["totp_secret"])
        otp = totp.now()

        session = meshctrl.Session(
            credentials['hostname'],
            user=credentials['username'],
            password=credentials['password'],
            token=otp
        )
    else:
        session = meshctrl.Session(
            credentials['hostname'],
            user=credentials['username'],
            password=credentials['password']
        )
    await session.initialized.wait()
    return session

async def gather_targets(args: argparse.Namespace,
                         meshbook: dict,
                         group_list: dict[str, list[dict]],
                         os_categories: dict) -> dict:
    """
    Finds target devices based on meshbook criteria (device, devices, group or groups).
    """

    group_list = {k.lower(): v for k, v in group_list.items()}  # Normalize keys
    target_list = []
    offline_list = []

    target_os = meshbook.get("target_os")
    target_tag = meshbook.get("target_tag")
    ignore_categorisation = meshbook.get("ignore_categorisation", False)

    async def add_processed_devices(processed):
        """Helper to update target and offline lists."""
        if processed:
            target_list.extend(processed.get("valid_devices", []))
            offline_list.extend(processed.get("offline_devices", []))

    async def process_device_helper(device):
        processed = await utilities.process_device(
            device,
            group_list,
            os_categories,
            target_os,
            ignore_categorisation,
            target_tag
        )
        await add_processed_devices(processed)

    async def process_group_helper(group):
        processed = await utilities.filter_targets(
            group, os_categories, target_os, ignore_categorisation, target_tag
        )
        await add_processed_devices(processed)

    '''
    Groups receive the first priority, then device targets.
    '''
    match meshbook:
        case {"group": pseudo_target}:
            if isinstance(pseudo_target, str):
                pseudo_target = pseudo_target.lower()

                if pseudo_target in group_list:
                    await process_group_helper(group_list[pseudo_target])

                elif pseudo_target not in group_list:
                    console.nice_print(
                        args,
                        console.text_color.yellow + "Targeted group not found on the MeshCentral server.",
                        True
                    )
            elif isinstance(pseudo_target, list):
                console.nice_print(
                    args,
                    console.text_color.yellow + "Please use groups (Notice the plural with 'S') for multiple groups.",
                    True
                )
            else:
                console.nice_print(
                    args,
                    console.text_color.yellow + "The 'group' key is being used, but an unknown data type was found, please check your values.",
                    True
                )

        case {"groups": pseudo_target}:
            if isinstance(pseudo_target, list):
                for sub_group in pseudo_target:
                    sub_group = sub_group.lower()
                    if sub_group in group_list:
                        await process_group_helper(group_list[sub_group])
            elif isinstance(pseudo_target, str) and pseudo_target.lower() == "all":
                for group in group_list.values():
                    await process_group_helper(group)
            elif isinstance(pseudo_target, str):
                console.nice_print(
                    args,
                    console.text_color.yellow + "The 'groups' key is being used, but only one string is given. Did you mean 'group'?",
                    True
                )
            else:
                console.nice_print(
                    args,
                    console.text_color.yellow + "The 'groups' key is being used, but an unknown data type was found, please check your values.",
                    True
                )

        case {"device": pseudo_target}:
            if isinstance(pseudo_target, str):
                await process_device_helper(pseudo_target)
            elif isinstance(pseudo_target, list):
                console.nice_print(
                    args,
                    console.text_color.yellow + "Please use devices (Notice the plural with 'S') for multiple devices.",
                    True
                )
            else:
                console.nice_print(
                    args,
                    console.text_color.yellow + "The 'device' key is being used, but an unknown data type was found, please check your values.",
                    True
                )

        case {"devices": pseudo_target}:
            if isinstance(pseudo_target, list):
                for sub_device in pseudo_target:
                    await process_device_helper(sub_device)
            elif isinstance(pseudo_target, str):
                console.nice_print(
                    args,
                    console.text_color.yellow + "The 'devices' key is being used, but only one string is given. Did you mean 'device'?",
                    True
                )
            else:
                console.nice_print(
                    args,
                    console.text_color.yellow + "The 'devices' key is being used, but an unknown data type was found, please check your values.",
                    True
                )

    return {"target_list": target_list, "offline_list": offline_list}

async def main():
    just_fix_windows_console()
    '''
    Main function where the program starts. Place from which all comands originate (eventually).
    '''

    parser = argparse.ArgumentParser(description="Process command-line arguments")
    parser.add_argument("-mb", "--meshbook", type=str, help="Path to the meshbook yaml file.")

    parser.add_argument("-oc", "--oscategories", type=str, help="Path to the Operating System categories JSON file.", default="./os_categories.json")
    parser.add_argument("--conf", type=str, help="Path for the API configuration file (default: ./config.conf).", default="./api.conf")
    parser.add_argument("--nograce", action="store_true", help="Disable the grace 3 seconds before running the meshbook.")
    parser.add_argument("-g", "--group", type=str, help="Specify a manual override for the group.", default="")
    parser.add_argument("-d", "--device", type=str, help="Specify a manual override for a device", default="")
    parser.add_argument("-i", "--indent", action="store_true", help="Use an JSON indentation of 4 when this flag is passed.", default=False)
    parser.add_argument("-r", "--raw-result", action="store_true", help="Print the raw result.", default=False)
    parser.add_argument("-s", "--silent", action="store_true", help="Suppress terminal output.", default=False)
    parser.add_argument("--shlex", action="store_true", help="Shlex the lines.", default=False)

    parser.add_argument("--version", action="store_true", help="Show the Meshbook version.")

    args = parser.parse_args()
    local_categories_file = "./os_categories.json"

    if args.version:
        console.nice_print(args,
                           console.text_color.reset + "MeshBook Version: " + console.text_color.yellow + str(meshbook_version))
        return

    if not args.meshbook:
        parser.print_help()
        return

    try:
        with open(local_categories_file, "r") as file:
            os_categories = json.load(file)

        credentials, meshbook = await asyncio.gather(
            (utilities.load_config(args)),
            (utilities.compile_book(args.meshbook))
        )

        if args.group != "":
            meshbook["group"] = args.group
            if "device" in meshbook:
              del meshbook["device"]
        elif args.device != "":
            meshbook["device"] = args.device
            if "group" in meshbook:
              del meshbook["group"]

        '''
        The following section mainly displays used variables and first steps of the program to the console.
        '''

        # INIT ARGUMENTS PRINTING
        console.nice_print(args,
                           console.text_color.reset + ("-" * 40))
        console.nice_print(args,
                           "meshbook: " + console.text_color.yellow + args.meshbook + console.text_color.reset + ".")
        console.nice_print(args,
                           "Operating System Categorisation file: " + console.text_color.yellow + args.oscategories + console.text_color.reset + ".")
        console.nice_print(args,
                           "Configuration file: " + console.text_color.yellow + args.conf + console.text_color.reset + ".")

        # TARGET OS PRINTING
        if "target_os" in meshbook:
            console.nice_print(args,
                               "Target Operating System category given: " + console.text_color.yellow + meshbook["target_os"] + console.text_color.reset + ".")
        else:
            console.nice_print(args,
                               "Target Operating System category given: " + console.text_color.yellow + "All" + console.text_color.reset + ".")

        # Should Meshbook ignore categorisation?
        if "ignore_categorisation" in meshbook:
            console.nice_print(args,
                                "Ignore the OS Categorisation file: " + console.text_color.yellow + str(meshbook["ignore_categorisation"]) + console.text_color.reset + ".")
            if meshbook["ignore_categorisation"]:
                console.nice_print(args,
                                console.text_color.red + "!!!!\n" +
                                console.text_color.yellow + 
                                "Ignore categorisation is True.\nThis means that the program checks if the target Operating System is somewhere in the reported device Operating System." + 
                                console.text_color.red + "\n!!!!")
        else:
            console.nice_print(args,
                                "Ignore the OS Categorisation file: " + console.text_color.yellow + "False" + console.text_color.reset + ".")

        # TARGET TAG PRINTING
        if "target_tag" in meshbook:
            console.nice_print(args,
                               "Target Device tag given: " + console.text_color.yellow + meshbook["target_tag"] + console.text_color.reset + ".")
        else:
            console.nice_print(args,
                               "Target Device tag given: " + console.text_color.yellow + "All" + console.text_color.reset + ".")

        # TARGET PRINTING
        if "device" in meshbook:
            console.nice_print(args,
                               "Target device: " + console.text_color.yellow + str(meshbook["device"]) + console.text_color.reset + ".")
        elif "devices" in meshbook:
            console.nice_print(args,
                               "Target devices: " + console.text_color.yellow + str(meshbook["devices"]) + console.text_color.reset + ".")
        elif "group" in meshbook:
            console.nice_print(args,
                               "Target group: " + console.text_color.yellow + str(meshbook["group"]) + console.text_color.reset + ".")
        elif "groups" in meshbook:
            console.nice_print(args,
                               "Target groups: " + console.text_color.yellow + str(meshbook["groups"]) + console.text_color.reset + ".")

        # RUNNING PARAMETERS PRINTING
        console.nice_print(args, "Grace: " + console.text_color.yellow + str((not args.nograce))) # Negation of bool for correct explanation
        console.nice_print(args, "Silent: " + console.text_color.yellow + "False") # Can be pre-defined because if silent flag was passed then none of this would be printed.

        session = await init_connection(credentials)

        # PROCESS PRINTING aka what its doing in the moment...
        console.nice_print(args,
                           console.text_color.reset + ("-" * 40))
        console.nice_print(args,
                           console.text_color.italic + "Trying to load the MeshCentral account credential file...")
        console.nice_print(args,
                           console.text_color.italic + "Trying to load the meshbook yaml file and compile it into something workable...")
        console.nice_print(args,
                           console.text_color.italic + "Trying to load the Operating System categorisation JSON file...")
        console.nice_print(args,
                           console.text_color.italic + "Connecting to MeshCentral and establish a session using variables from previous credential file.")
        console.nice_print(args,
                           console.text_color.italic + "Generating group list with nodes and reference the targets from that.")

        '''
        End of the main information displaying section.
        '''

        group_list = await transform.compile_group_list(session)
        compiled_device_list = await gather_targets(args, meshbook, group_list, os_categories)

        if "target_list" not in compiled_device_list or len(compiled_device_list["target_list"]) == 0:
            console.nice_print(args,
                               console.text_color.red + "No targets found or targets unreachable, quitting.", True)

            console.nice_print(args,
                               console.text_color.reset + ("-" * 40), True)

        else:
            console.nice_print(args,
                               console.text_color.reset + ("-" * 40))

            match meshbook:
                case {"group": candidate_target_name}:
                    target_name = candidate_target_name

                case {"groups": candidate_target_name}:
                    target_name = str(candidate_target_name)

                case {"device": candidate_target_name}:
                    target_name = candidate_target_name

                case {"devices": candidate_target_name}:
                    target_name = str(candidate_target_name)

                case _:
                    target_name = ""


            console.nice_print(args,
                               console.text_color.yellow + "Executing meshbook on the target(s): " + console.text_color.green + target_name + console.text_color.yellow + ".")

            if not args.nograce:
                console.nice_print(args,
                                   console.text_color.yellow + "Initiating grace-period...")

                for x in range(grace_period):
                    console.nice_print(args,
                                       console.text_color.yellow + "{}...".format(x+1)) # Countdown!
                    await asyncio.sleep(1)

            console.nice_print(args, console.text_color.reset + ("-" * 40))
            await executor.execute_meshbook(args,
                                            session,
                                            compiled_device_list,
                                            meshbook,
                                            group_list)

        await session.close()

    except OSError as message:
        console.nice_print(args,
                           console.text_color.red + f'{message}', True)

if __name__ == "__main__":
    asyncio.run(main())
