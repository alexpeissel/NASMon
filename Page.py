import chevron
import json
import logging
import yaml

from loguru import logger

from Command import Command
from Components import TextComponent, ImageComponent, BargraphComponent

class Page():
    def __init__(self, page_file):
        # Parse the page config yaml
        _parsed_page_config = self._read_config(page_file)

        # Define command runners and cache
        self.command_runners = self._build_commands_lookup(
            _parsed_page_config.get("commands", []))
        self.command_cache = {}
        self.update()

        # Page config components
        logger.debug("Creating components from config")
        self.text_components = [TextComponent(definition) for definition in _parsed_page_config.get("text", [])]
        self.image_components = [ImageComponent(definition) for definition in _parsed_page_config.get("images", [])]
        self.bargraph_component = [BargraphComponent(definition) for definition in _parsed_page_config.get("bargraph", [])]

    @property
    def text(self):
        return self._get_rendered_components(self.text_components)

    @property
    def images(self):
        return self._get_rendered_components(self.image_components)
    
    @property
    def bargraph(self):
        return self._get_rendered_components(self.bargraph_component)

    def update(self):
        logger.debug("Updating command cache for page")
        for name, command in self.command_runners.items():
            logger.debug(f"Updating command for key: {name}")
            self.command_cache.update(command.execute())

    def _get_rendered_components(self, component_list):
        components = []
        for component in component_list:
            components.append(component.render(self.command_cache))

        return components

    def _read_config(self, page_file):
        with open(page_file, "r") as f:
            return yaml.safe_load(f)
    
    def _build_commands_lookup(self, commands):
        command_runners = {}

        for command_definition in commands:
            run_once = command_definition.get("run_once", False)
            command_definition.pop("run_once", None)

            numeric = command_definition.get("numeric", False)
            command_definition.pop("numeric", None)

            for name, command in command_definition.items():
                runner = {}
                runner[name] = Command(name, command, run_once=run_once, numeric=numeric)
                command_runners.update(runner)

        return command_runners
