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
import string
from string import Template
from logzero import logger


class Page:
    def __init__(self, page_file):
        self.name = "NASMon page"
        self.text_components = []
        self.bmp_components = []
        self.bargraph_components = []
        self.command_components = []
        self.command_outputs = []
        self._parse_page_file(page_file)

    def get_text_components(self):
        s = Template('$who likes $what')
        s.substitute(who='tim', what='kung pao')
        self._update()
        for command_output in self.command_outputs:
            variable_identifier = command_output['variable_identifier']
            for i, searchable_text in enumerate(self.text_components):
                if variable_identifier in searchable_text['text']:
                    logger.debug("Replacing " + str(variable_identifier) + " with " + command_output['result'])
                    self.text_components[i]['text'] = searchable_text['text'].replace(variable_identifier,
                                                                                      command_output['result']
                                                                                      )

        return self.text_components

    def get_bmp_components(self):
        return self.bmp_components

    def get_bargraph_components(self):
        self._update()
        for command_output in self.command_outputs:
            variable_identifier = command_output['variable_identifier']
            for i, bargraph_component in enumerate(self.bargraph_components):
                if variable_identifier == bargraph_component['graph_value']:
                    logger.debug("Setting graph value to " + str(command_output['result']) + "%")
                    self.bargraph_components[i]['graph_value'] = self._convert_int_to_bargraph(
                        command_output['result']

                    )
        return self.bargraph_components

    def _update(self):
        for i, command_output in enumerate(self.command_outputs):
            logger.debug("Updating output: %s", command_output)
            if command_output['update']:
                result = self._run_command(command_output['command'])
                logger.debug("Updating result to: %s", result)
                self.command_outputs[i]['result'] = result

    def _convert_bitmap_to_1_bit(self):
        pass

    def _convert_int_to_bargraph(self, value, green_threshold=0, yellow_threshold=50, red_threshold=75):
        bargraph_data = ['o'] * 24
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
        self.name = data['name']

        for text_component in data['text']:
            self.text_components.append(text_component)

        for bmp_component in data['bmp']:
            self.bmp_components.append(bmp_component)

        if len(data['graph']) > 1:
            logger.warn("Only 1 graph value is allowed, taking the first value only.")

        bargraph_data = data['graph'][0]
        output = {
            'graph_value': bargraph_data['graph_value'],
            'green_threshold': bargraph_data['green_threshold'],
            'yellow_threshold': bargraph_data['yellow_threshold'],
            'red_threshold': bargraph_data['red_threshold']
        }

        self.bargraph_components.append(output)

        for command_component in data['commands']:
            output = {}
            if command_component['update_when_displayed']:
                output = {
                    'variable_identifier': command_component['variable_identifier'],
                    'command': command_component['command'],
                    'update': True,
                    'result': None
                }
            else:
                command_result = self._run_command(command_component['command'])
                output = {
                    'variable_identifier': command_component['variable_identifier'],
                    'command': command_component['command'],
                    'update': True,
                    'result': command_result
                }

            self.command_outputs.append(output)

    def _run_command(self, command):
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        retval = p.wait()
        result = None
        if retval is 0:
            result = "".join(p.stdout.readlines()).rstrip()
        else:
            logger.warn("Command returned a non 0 value")
        return result