# -*- coding: utf-8 -*-
"""
Monitor
Main loop for NASMon
"""

__author__ = "Alex Peissel"
__version__ = "0.1.0"
__license__ = "MIT"

import glob

from logzero import logger

from Microcontroller import Microcontroller
from Page import Page


class Monitor:
    """ Main class """

    def __init__(self, page_directory, serial_port, baud_rate):
        """Loads pages from page_directory and connects to microcontroller.
        Args:
            page_directory: The directory containing pages in .yml format.
            serial_port: The serial port or path to a serial device.
            baud_rate: The bit rate for serial communication.
        """
        # Index of page to display
        self.current_page_index = 0

        # Where the program will look to find pages
        self.page_directory = page_directory

        # A list of parsed pages
        self.pages = self._build_page_list(self.page_directory)

        # Instantiate a microcontroller
        self.mc = Microcontroller(serial_port, baud_rate)

    def start(self):
        """ Check the microcontroller is up and run the test routines.  After that, start looping forever, querying the
        microcontroller for whether the sensor is activated.  If the sensor is active, clear the displays and cycle
        through the page list, displaying the current page.

        """
        if self.mc.is_up():
            logger.info("Microcontroller ready")
        else:
            logger.error("Microcontroller did not respond")
            logger.error("Exiting")
            exit(1)

        # Main loop
        while True:
            if self.mc.is_requesting_data():
                # Clear display and bargraph
                self.mc.clear_displays()

                # Get the current page and store in current_page
                current_page = self.pages[self.current_page_index]
                logger.info("Displaying page: %s", current_page.name)

                # Show the page at index current_page_index
                self._show_page(self.pages[self.current_page_index])

                # Check if it is time to cycle back to the start of the page list
                if self.current_page_index == len(self.pages) - 1:
                    self.current_page_index = 0
                else:
                    self.current_page_index += 1

    def stop(self):
        """ Stop the microcontroller and quit """
        logger.info("Stopping application")
        self.mc.stop()

        logger.info("Exiting")
        exit(0)

    def _build_page_list(self, page_directory):
        """ For each page file, (*.yml file in page_directory) create a Page object, append to list and return """
        logger.info("Building page list from directory: %s", page_directory)

        parsed_pages = []

        # Look for all files that match *.yml inside of the page_directory
        matching_files = glob.glob(page_directory + "/*.yml")
        logger.debug("Found files: %s", matching_files)

        # Loop through each file and create a page object
        for page_file in matching_files:
            logger.info("Found page file: %s, parsing...", page_file)

            # Create a new page and append to the parsed_pages list
            page = Page(page_file)
            parsed_pages.append(page)
            logger.info("Added page: %s", page.name)

        logger.info("Finished parsing %i pages", len(matching_files))
        return parsed_pages

    def _show_page(self, page):
        """ Loop through the page components, (text, bitmaps and bargraph) and send to the microcontroller """
        logger.debug("Updating command output table")

        # Run all commands components for a page and store the result for reference later
        page.update_command_outputs()

        # Loop through all components and package result as keyworded arguments to the microcontroller
        for text_data in page.get_text_components():
            logger.debug("Displaying text component: %s", text_data.get_as_dict())
            self.mc.display_text(**text_data.get_as_dict())

        for bmp_data in page.get_bmp_components():
            logger.debug("Displaying text component: %s", bmp_data.get_as_dict())
            self.mc.display_bmp(**bmp_data.get_as_dict())

        for bargraph_data in page.get_bargraph_components():
            logger.debug("Displaying bargraph component: %s", bargraph_data.get_as_dict())
            self.mc.display_bargraph(**bargraph_data.get_as_dict())
