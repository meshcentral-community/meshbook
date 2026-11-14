import json
import os
from datetime import datetime
from typing import Union

from modules.console import Console

class History():
    def __init__(self, silent: bool, history_directory: str, flush_history: bool) -> None:
        '''
        Init function to declare some stuff and make sure we are good to go, mostly the directory.
        '''
        self.silent = silent
        self.history_directory = history_directory

        if not os.path.exists(history_directory):
            Console.print_text(silent, "Directory absent, trying to create it now...")

            try:
                os.makedirs(history_directory, exist_ok=True)

            except (PermissionError, OSError) as err:
                Console.print_text(silent, Console.text_color.red + f"Failed to create directory ({err}).")
                return

        try:
            history_items = os.listdir(history_directory)
        except OSError as err:
            Console.print_text(silent, Console.text_color.red + f"Failed to read history directory ({err}).")
            return

        if len(history_items) == 1:
            Console.print_text(silent, f"There is {len(history_items)} history item.")
        else:
            Console.print_text(silent, f"There are {len(history_items)} history items.")

        if flush_history:
            self.remove_history(history_items)

    def remove_history(self, history_items: list[str]) -> None:
        if not os.access(self.history_directory, os.W_OK):
            Console.print_text(self.silent, Console.text_color.red + "Unable to flush history logs, no write access.")
            return

        for item in history_items:
            stitched_path = f"{self.history_directory}/{item}"

            if os.path.isfile(stitched_path):
                Console.print_text(self.silent, f"Removing: {item}.")
                try:
                    os.remove(stitched_path)
                except OSError as err:
                    Console.print_text(self.silent, Console.text_color.red + f"Failed to remove {item}: {err}")

    def write_history(self, history: Union[dict, list, str]) -> bool:
        try:
            os.makedirs(self.history_directory, exist_ok=True)
            stitched_file = f"{self.history_directory}/meshbook_run_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.log"

            if isinstance(history, (dict, list)):
                content = json.dumps(history, indent=4)
            else:
                content = str(history)

            with open(stitched_file, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except OSError as err:
            Console.print_text(self.silent, Console.text_color.red + f"Failed to write history file: {err}")
            return False
