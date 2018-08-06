# -*- coding: utf-8 -*-
"""
Pages
A page is a collection of data that will be displayed on the screen and bargraph of the monitor.
Pages have the following attributes:
- name: the name of the page
- text: static or interpolated text that can be shown on the display
- bmp: 1 bit bitmaps
- bargraph: a static or interpolated 0-100 value that is shown on the bargraph, with definable thresholds for colour
- commands
"""

__author__ = "Alexander Peissel"
__version__ = "0.1.0"
__license__ = "MIT"

import yaml
import subprocess
from string import Template
from logzero import logger


class Page:
    def __init__(self, page_file):
        self.name = "NASMon page"
        self.text_components = []
        self.bmp_components = []
        self.bargraph_components = []
        self._command_components = []
        self._command_outputs = {}
        self._parse_page_file(page_file)

    def get_text_components(self):
        return self._get_interpolated_components("text", self.text_components, "text")

    def get_bmp_components(self):
        return self.bmp_components

    def get_bargraph_components(self):
        return self._get_interpolated_components("bargraph", self.bargraph_components, "graph_value")

    def _update(self):
        for command_component in self._command_components:
            logger.debug("Updating var: %s", command_component.get("variable_identifier"))
            result = self._run_command(command_component.get("command"))
            logger.debug("Updating result to: %s", result)
            self._command_outputs[command_component.get("variable_identifier")] = result

    def _get_interpolated_components(self, component_type, source_component_list, field_to_update):
        self._update()
        interpolated_components = []
        for component in source_component_list:
            updated_component = {}
            updated_component.update(component)

            interpolated_value = ""

            if component_type == "text":
                interpolated_value = Template(updated_component.get(field_to_update)).safe_substitute(
                    self._command_outputs)
            elif component_type == "bmp":
                # Nothing to interpolate yet
                pass
            elif component_type == "bargraph":
                interpolated_value = self._convert_int_to_bargraph(
                    Template(updated_component.get("graph_value")).safe_substitute(self._command_outputs))
            else:
                logger.error("component_type is invalid, returning empty string")

            updated_component[field_to_update] = interpolated_value
            interpolated_components.append(updated_component)
        return interpolated_components

    def _convert_bitmap_to_1_bit(self):
        pass

    def _convert_int_to_bargraph(self, value, green_threshold=0, yellow_threshold=50, red_threshold=75):
        bargraph_data = ["o"] * 24
        for i in xrange(0, len(bargraph_data)):
            if int(float(value)) > ((i + 1) * (100.0 / 24)):
                if (i + 1) * (100.0 / 24) >= red_threshold:
                    bargraph_data[i] = 'r'
                elif (i + 1) * (100.0 / 24) >= yellow_threshold:
                    bargraph_data[i] = 'y'
                elif (i + 1) * (100.0 / 24) >= green_threshold:
                    bargraph_data[i] = 'g'
                else:
                    bargraph_data[i] = 'o'

        return "".join(reversed(bargraph_data))

    def _parse_page_file(self, page_file):
        with open(page_file) as stream:
            try:
                page_file_data = yaml.safe_load(stream)
                self._parse_page_data(page_file_data)
            except yaml.YAMLError as exc:
                logger.error(exc)

    def _parse_page_data(self, data):
        self.name = data.get("name")

        for text_component in data.get("text"):
            self.text_components.append(text_component)

        for bmp_component in data.get("bmp"):
            self.bmp_components.append(bmp_component)

        if len(data.get("graph")) > 1:
            logger.warn("Only 1 graph value is allowed, taking the first value only.")

        bargraph_data = data.get("graph")[0]
        output = {
            'graph_value': bargraph_data.get("graph_value"),
            'green_threshold': bargraph_data.get("green_threshold"),
            'yellow_threshold': bargraph_data.get("yellow_threshold"),
            'red_threshold': bargraph_data.get("red_threshold")
        }

        self.bargraph_components.append(output)

        for command_component in data.get("commands"):
            self._command_components.append({
                'variable_identifier': command_component.get("variable_identifier").replace("$", ""),
                'command': command_component.get("command"),
                'update': True,
            })

            self._command_outputs[command_component.get("variable_identifier").replace("$", "")] = None

    def _run_command(self, command):
        logger.debug("Running command: %s", command)
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return_value = p.wait()
        result = None
        if return_value is 0:
            result = "".join(p.stdout.readlines()).rstrip()
            logger.debug("Command result: %s", result)
        else:
            logger.warn("Command returned a non 0 value")
        return result
