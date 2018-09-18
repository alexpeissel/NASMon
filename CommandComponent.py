# -*- coding: utf-8 -*-
"""
CommandComponent
Describes a set of values that can be displayed on a bargraph
"""

__author__ = "Alexander Peissel"
__version__ = "0.1.0"
__license__ = "MIT"

from logzero import logger
import subprocess


class CommandComponent:
    def __init__(self, command, variable_identifier):
        """
        Loads pages from page_directory and connects to microcontroller.
        Args:
            command: The directory containing pages in .yml format.
            variable_identifier: The serial port or path to a serial device.
        """

        self.command = command
        self.variable_identifier = variable_identifier

        self.return_code = None
        self.result = None

        if self.variable_identifier.startswith("$"):
            logger.warn("Starting variable names with $ is not required!")
            self.variable_identifier = variable_identifier.replace("$", "")

    def update(self):
        """ Run command and return t result for the variable_identifier"""
        logger.debug("Updating var: %s", self.variable_identifier)
        self.result = self._run_command(self.command)

        logger.debug("Updating result to: %s", self.result)

    def _run_command(self, command):
        """ Creates a sub-process to run command and returns the result as string """
        logger.debug("Running command: %s", command)
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        return_code = p.wait()
        result = ""

        if return_code is 0:
            result = "".join(p.stdout.readlines()).rstrip()
            logger.debug("Command result: %s", result)
        else:
            logger.warn("Command returned a non 0 value")

        return result
