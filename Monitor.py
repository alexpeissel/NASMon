import os
import random
import string
import time
import yaml

from loguru import logger

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from Microcontroller import Microcontroller
from Page import Page

class Monitor():
    def __init__(self, port, baudrate, timeout, page_dir):        
        self._microcontroller = Microcontroller(port, baudrate, timeout)
        logger.info(f"NASMon running, connected to device at port: {port}")

        self._page_directory = page_dir
        logger.debug(f'Page directory: {page_dir}')

        self.page_dir = page_dir
        self._page_list = self._build_page_list(page_dir)
        self._page_list_index = 0

        self._page_file_update_handler = PatternMatchingEventHandler(
            patterns=["*.yml", "*.yaml"], 
            ignore_directories=True, 
            case_sensitive=False
            )

        self._page_file_update_handler.on_created = self._handle_page_file_change_events
        self._page_file_update_handler.on_modified = self._handle_page_file_change_events
        self._page_file_update_handler.on_deleted = self._handle_page_file_change_events

        self._observer = Observer()
        self._observer.schedule(self._page_file_update_handler, page_dir, recursive=False)

    def _build_page_list(self, page_dir):
        page_list = []

        for entry in os.scandir(page_dir):
            if entry.path.endswith((".yaml", ".yml")) and entry.is_file():
                page_list.append(Page(entry.path))
                logger.debug(f"Found page file: {entry.path}")
        
        logger.debug(f"Number of pages: {len(page_list)}")
        return page_list

    def _handle_page_file_change_events(self, event):
        logger.info(f"Page file {event.src_path} {event.event_type}, reloading page list...")
        self._page_list = self._build_page_list(self.page_dir)
        logger.info("Reload complete")

    def start(self):
        logger.info("Starting listening for file updates")
        self._observer.start()
        
        self._microcontroller.clear_displays()

        logger.info("Ready to send pages.")
        while True:
            if self._microcontroller.is_requesting_data():
                current_page = self._page_list[self._page_list_index]
                current_page.update()

                self._microcontroller.clear_displays()

                for text in current_page.text:
                    logger.trace(f"Rendered text component: {text}")
                    self._microcontroller.display_text(**text)
                
                for image in current_page.images:
                    logger.trace(f"Rendered image component: {image}")
                    self._microcontroller.display_image(**image)
                
                for bargraph in current_page.bargraph:
                    logger.trace(f"Rendered bargraph component: {bargraph}")
                    self._microcontroller.display_bargraph(**bargraph)

                if self._page_list_index == len(self._page_list) - 1:
                    self._page_list_index = 0
                else:
                    self._page_list_index += 1

    def stop(self):
        self._microcontroller.stop()
        self._observer.stop()
        self._observer.join()
