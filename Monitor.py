#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Monitor
"""

__author__ = "Alex Peissel"
__version__ = "0.1.0"
__license__ = "MIT"

###############################
# Imports
###############################
import string
import glob
import random
from logzero import logger
from Microcontroller import Microcontroller
from Page import Page


class Monitor:
    """Main class"""

    def __init__(self, page_directory, serial_port, baud_rate):
        """Loads pages from page_directory and connects to microcontroller.
        Args:
            page_directory: The directory containing pages in .yml format.
            serial_port: The serial port or path to a serial device.
            baud_rate: The bit rate for serial communication.
        """
        self.current_page_index = 0
        self.page_directory = page_directory
        self.pages = self._build_page_list(self.page_directory)

        self.mc = Microcontroller(serial_port, baud_rate)

    def start(self):
        if self.mc.is_up():
            logger.info("Microcontroller ready")
        else:
            logger.error("Microcontroller did not respond")
            logger.error("Exiting")
            exit(1)

        self._test_displays(5)
        self.mc.clear_displays()

        while True:
            if self.mc.is_requesting_data():
                self.mc.clear_displays()

                current_page = self.pages[self.current_page_index]
                logger.info("Displaying page: %s", current_page.name)
                self._show_page(self.pages[self.current_page_index])

                if self.current_page_index == len(self.pages) - 1:
                    self.current_page_index = 0
                else:
                    self.current_page_index += 1

    def stop(self):
        self.mc.stop()

    def _build_page_list(self, page_directory):
        logger.info("Building page list from directory: %s", page_directory)

        parsed_pages = []
        matching_files = glob.glob(page_directory + "/*.yml")
        logger.debug("Found files: %s", matching_files)

        for page_file in matching_files:
            logger.info("Found page file: %s, parsing...", page_file)
            page = Page(page_file)
            parsed_pages.append(page)
            logger.info("Added page: %s...", page.name)

        logger.info("Finished parsing %i pages", len(matching_files))
        return parsed_pages

    def _show_page(self, page):
        logger.debug("Page data: %s", page.get_text_components())
        for text_data in page.get_text_components():
            self.mc.display_text(text_data.get("text"),
                                 text_data.get("x"),
                                 text_data.get("y"),
                                 text_data.get("size")
                                 )

        # # TODO: handle bitmaps
        # for bmp_data in page.get_bmp_components():
        #     bmp = bytes([0b11111111])
        #     print bmp
        #     self.mc.display_bmp(bmp,
        #                         1,
        #                         1,
        #                         8,
        #                         2
        #                         )

        for bargraph_data in page.get_bargraph_components():
            self.mc.display_bargraph(bargraph_data.get("graph_value"))

    def _generate_random_text_component(self, length):
        text_component = {
            "text": ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length)),
            "x": 0,
            "y": 0,
            "size": 1
        }

        return text_component

    def _generate_random_graph_component(self):
        return ''.join(random.choice('rgyo') for _ in range(24))

    def _test_displays(self, number_of_text_components):
        for i in xrange(number_of_text_components):
            random_text_component = self._generate_random_text_component(10)
            self.mc.clear_displays()
            self.mc.display_text(random_text_component.get("text"),
                                 random_text_component.get("x"),
                                 random_text_component.get("y"),
                                 random_text_component.get("size")
                                 )
            self.mc.display_bargraph(self._generate_random_graph_component())
