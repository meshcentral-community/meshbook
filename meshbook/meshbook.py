#!/bin/python3

import argparse
import asyncio
from base64 import b64encode
from configparser import ConfigParser
import json
import os
import yaml
import websockets

sequence = 0
response_counter = 0
expected_responses = 0
basic_ready_state = asyncio.Event()
ready_for_next = asyncio.Event()
global_list = []


class ScriptEndTrigger(Exception):
    """Custom Exception to handle script termination events."""
    pass


class MeshcallerUtilities:
    """Helper utility functions for the Meshcaller application."""
    
    @staticmethod
    def base64_encode(string: str) -> str:
        """Encode a string in Base64 format."""
        return b64encode(string.encode('utf-8')).decode()
    
    @staticmethod
    def read_yaml(file_path: str) -> dict:
        """Read a YAML file and return its content as a dictionary."""
        with open(file_path, 'r') as file:
            return yaml.safe_load(file)
    
    @staticmethod
    def get_target_ids(company: str = None, device: str = None) -> list:
        """Retrieve target IDs based on company or device."""
        ids = []

        for entry in global_list:
            nodes = entry.get('nodes', [])
            if company and not device:
                if entry.get('mesh_name') == company:
                    ids.extend(node['node_id'] for node in nodes if node.get('powered_on'))
            elif device and not company:
                for node in nodes:
                    if node['node_name'] == device and node.get('powered_on'):
                        return [node['node_id']]  # Immediate return for single device
            elif not company and not device:
                ids.extend(node['node_id'] for node in nodes if node.get('powered_on'))

        return ids

    @staticmethod
    def load_config(conffile: str = None, segment: str = 'meshcentral-service') -> ConfigParser:
        """Load and return the configuration from a file."""
        conffile = conffile or './api.conf'
        if not os.path.exists(conffile):
            raise ScriptEndTrigger(f'Missing config file {conffile}. Provide an alternative path.')

        try:
            my_config = ConfigParser()
            my_config.read(conffile)
        except Exception as err:
            raise ScriptEndTrigger(f'Error reading config file {conffile}: {err}')
        
        if segment not in my_config:
            raise ScriptEndTrigger(f'Segment "{segment}" not found in config file {conffile}.')

        return my_config[segment]


class MeshcallerWebSocket:
    """Handles WebSocket connections and interactions."""
    
    def __init__(self):
        self.meshsocket = None
        self.received_response_queue = asyncio.Queue()

    async def ws_on_open(self):
        """Called when WebSocket connection is established."""
        if not args.silent:
            print('Connection established.')

    async def ws_on_close(self):
        """Called when WebSocket connection is closed."""
        print('Connection closed by remote host.')
        raise ScriptEndTrigger("WebSocket connection closed.")

    async def ws_on_message(self, message: str):
        """Processes incoming WebSocket messages."""
        try:
            received_response = json.loads(message)
            await self.received_response_queue.put(received_response)
        except json.JSONDecodeError:
            print("Error processing:", message)
            raise ScriptEndTrigger("Failed to decode JSON message.")

    async def ws_send_data(self, message: str):
        """Send data to the WebSocket server."""
        if not self.meshsocket:
            raise ScriptEndTrigger("WebSocket connection not established. Unable to send data.")
        if not args.silent:
            print('Sending data to the server.')
        await self.meshsocket.send(message)

    async def gen_simple_list(self):
        """Send requests to retrieve mesh and node lists."""
        await self.ws_send_data(json.dumps({'action': 'meshes', 'responseid': 'meshctrl'}))
        await self.ws_send_data(json.dumps({'action': 'nodes', 'responseid': 'meshctrl'}))

    async def ws_handler(self, uri: str, username: str, password: str):
        """Main WebSocket connection handler."""
        login_string = f'{MeshcallerUtilities.base64_encode(username)},{MeshcallerUtilities.base64_encode(password)}'
        ws_headers = {
            'User-Agent': 'MeshCentral API client',
            'x-meshauth': login_string
        }
        if not args.silent:
            print("Attempting WebSocket connection...")

        try:
            async with websockets.connect(uri, additional_headers=ws_headers) as meshsocket:
                self.meshsocket = meshsocket
                await self.ws_on_open()
                await self.gen_simple_list()

                while True:
                    try:
                        message = await meshsocket.recv()
                        await self.ws_on_message(message)
                    except websockets.ConnectionClosed:
                        await self.ws_on_close()
                        break
        except ScriptEndTrigger as e:
            print(f"WebSocket handler terminated: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")


class MeshcallerProcessor:
    """Processes data received from the WebSocket."""
    
    def __init__(self):
        self.basic_temp_list = []

    def handle_basic_data(self, data):
        """Handles basic data from the server."""
        if not args.silent:
            print("Processing received basic data...")
        
        self.basic_temp_list.append(data)
        if len(self.basic_temp_list) < 2:
            return

        temp_dict = {}
        for entry in self.basic_temp_list:
            if isinstance(entry, list):
                for mesh in entry:
                    if mesh.get("type") == "mesh":
                        mesh_id = mesh["_id"]
                        temp_dict[mesh_id] = {
                            "mesh_name": mesh.get("name", "Unknown Mesh"),
                            "mesh_desc": mesh.get("desc", "No description"),
                            "nodes": []
                        }
            elif isinstance(entry, dict):
                for mesh_id, nodes in entry.items():
                    if mesh_id in temp_dict:
                        temp_dict[mesh_id]["nodes"].extend(nodes)
                    else:
                        temp_dict[mesh_id] = {
                            "mesh_name": "Unknown Mesh",
                            "mesh_desc": "No description",
                            "nodes": nodes
                        }

        for mesh_id, details in temp_dict.items():
            global_list.append({
                "mesh_name": details["mesh_name"],
                "mesh_id": mesh_id,
                "nodes": [
                    {
                        "node_id": node["_id"],
                        "node_name": node.get("name", "Unknown Node"),
                        "powered_on": node.get("pwr") == 1
                    }
                    for node in details["nodes"]
                ]
            })
        basic_ready_state.set()
        ready_for_next.set()

    async def receive_processor(self, python_client: MeshcallerWebSocket):
        """Processes messages received from the WebSocket."""
        global response_counter
        while True:
            message = await python_client.received_response_queue.get()
            action_type = message.get('action')
            if action_type in ('meshes', 'nodes'):
                self.handle_basic_data(message[action_type])
            elif action_type == 'msg':
                print(json.dumps(message, indent=4))
                response_counter += 1  # Increment response counter

                print(response_counter % len(target_ids))
                if response_counter % len(target_ids) == 0:
                    ready_for_next.set()
            elif action_type == 'close':
                print(message)
            elif not args.silent:
                print("Ignored action:", action_type)


class MeshcallerActions:
    """Processes playbook actions."""
    
    @staticmethod
    async def process_arguments(python_client: MeshcallerWebSocket, playbook_path: str):
        """Executes tasks defined in the playbook."""
        global response_counter, expected_responses, target_ids

        await basic_ready_state.wait()  # Wait for the basic data to be ready

        playbook_yaml = MeshcallerUtilities.read_yaml(playbook_path)
        target_ids = MeshcallerUtilities.get_target_ids(
            company=playbook_yaml.get('company'),
            device=playbook_yaml.get('device')
        )
        if not target_ids:
            raise ScriptEndTrigger("No targets found.")

        run_command_template = {
            'action': 'runcommands',
            'nodeids': target_ids,
            'type': 0,
            'cmds': None,
            'runAsUser': 0,
            'responseid': 'meshctrl',
            'reply': True
        }

        # Calculate the total expected responses: tasks x target nodes
        expected_responses = len(playbook_yaml['tasks']) * len(target_ids)

        print(expected_responses)

        # Send commands for all nodes at once
        for task in playbook_yaml['tasks']:
            await ready_for_next.wait()
            run_command_template["cmds"] = task['command']
            run_command_template["nodeids"] = target_ids  # Send to all target IDs at once
            print("Running task:", task)
            print("-=-" * 40)

            # Send the command to all nodes in one go
            await python_client.ws_send_data(json.dumps(run_command_template))
            ready_for_next.clear()

        # Wait until all expected responses are received
        while response_counter < expected_responses:
            await asyncio.sleep(1)

        # Exit gracefully
        raise ScriptEndTrigger("All tasks completed successfully.")


async def main():
    parser = argparse.ArgumentParser(description="Process command-line arguments")
    parser.add_argument("--conf", type=str, help="Path for the API configuration file (default: ./api.conf).")
    parser.add_argument("-pb", "--playbook", type=str, help="Path to the playbook file.", required=True)
    parser.add_argument("-s", "--silent", action="store_true", help="Suppress terminal output.")

    global args
    args = parser.parse_args()

    try:
        credentials = MeshcallerUtilities.load_config(args.conf)
        python_client = MeshcallerWebSocket()
        processor = MeshcallerProcessor()

        websocket_task = asyncio.create_task(python_client.ws_handler(
            credentials['websocket_url'],
            credentials['username'],
            credentials['password']
        ))
        processor_task = asyncio.create_task(processor.receive_processor(python_client))
        await MeshcallerActions.process_arguments(python_client, args.playbook)
        await asyncio.gather(websocket_task, processor_task)
        
    except ScriptEndTrigger as e:
        if not args.silent:
            print(e)


if __name__ == "__main__":
    asyncio.run(main())
