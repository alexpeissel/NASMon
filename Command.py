import logging
import re
import subprocess

from loguru import logger


class Command():
    def __init__(self, name, command, run_once=False, numeric=False):
        self.name = name
        self.command = command
        self.run_once = run_once
        self.numeric = numeric

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

            try:
                execution = subprocess.run(
                    self.command, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=5)
            except subprocess.CalledProcessError as e:
                raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
    
            command_output = execution.stdout.rstrip().encode(
                "unicode_escape").decode("utf-8")

            if self.numeric:
                logger.debug("numeric flag is set, stripping all non-numeric characters")
                command_output = self._extract_first_number(command_output)

            result = {
                self.name: command_output
            }
            logger.debug(f"Command returned: {command_output}")
            self.last_execution = result

        return result

    def _extract_first_number(self, string):
        return re.findall('\d+', str(string))[0]
