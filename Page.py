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
from logzero import logger

from TextComponent import TextComponent
from ImageComponent import ImageComponent
from BargraphComponent import BargraphComponent
from CommandComponent import CommandComponent


class Page:
    def __init__(self, page_file):
        self.name = ""
        self.text_components = []
        self.bmp_components = []
        self.bargraph_components = []
        self._command_components = []
        self._command_outputs = {}

        self._parse_page_file(page_file)

    def get_text_components(self):
        """ Return a list of interpolated text dicts """
        self._update_components(self.text_components)
        return self.text_components

    def get_bmp_components(self):
        """ Return a list of interpolated bmp dicts """
        # TODO: fix the update_components method for images
        #self._update_components(self.bmp_components)
        return self.bmp_components

    def get_bargraph_components(self):
        """ Return a list of interpolated bargraph dicts """
        self._update_components(self.bargraph_components)
        return self.bargraph_components

    def update_command_outputs(self):
        """ Runs each command component and adds the result to the self._command_outputs dict, e.g. {'cpu': '32'} """
        for component in self._command_components:
            component.update()
            self._command_outputs[component.variable_identifier] = component.result

    def _update_components(self, component_list):
        """ Call update method on any list of components """
        for component in component_list:
            component.update(self._command_outputs)

    def _parse_page_file(self, page_file):
        """ Parse YAML page files and set public attributes """
        # Parse YAML
        with open(page_file) as stream:
            try:
                data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                logger.error(exc)

        # Set the page name
        self.name = data.get("name", "NASMon page")

        # Create TextComponents
        for text_component in data.get("text", []):
            self.text_components.append(TextComponent(**text_component))

        # Create BMPComponents
        for bmp_component in data.get("bmp", []):
            logger.debug("Creating initial image component")
            initial_component = ImageComponent(**bmp_component)

            logger.debug("Appending %i sub-images to image component list", len(initial_component.sub_image_components))
            for image_component in initial_component.sub_image_components:
                self.bmp_components.append(image_component)

        # Create one BargraphComponent
        for bargraph_component in data.get("bargraph", []):
            if len(data.get("bargraph", [])) > 1:
                logger.warn("Only 1 graph value is allowed, taking the first value only.")

            self.bargraph_components.append(BargraphComponent(**bargraph_component))
            break

        # Create CommandComponents
        for command_component in data.get("commands"):
            self._command_components.append(CommandComponent(**command_component))
