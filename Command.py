import logging
import subprocess

from loguru import logger


class Command():
    def __init__(self, name, command, run_once=False):
        self.name = name
        self.command = command
        self.run_once = run_once
        self.last_execution = None

        if self.run_once:
            logger.debug(f"Storing value in cache for command: {self.name}")
            self.last_execution = self.execute()

    def execute(self):
        if self.run_once and (self.last_execution is not None):
            logger.debug(f"Returning cached value: {self.last_execution}")
            result = self.last_execution
        else:
            logger.debug(f"Executing command: {self.command}")
            command_line = self.command.split()
            execution = subprocess.run(
                command_line, check=True, shell=True, stdout=subprocess.PIPE, text=True, timeout=5)

            result = {
                self.name: execution.stdout.rstrip().encode(
                "unicode_escape").decode("utf-8")
            }

            self.last_execution = result

        return result
