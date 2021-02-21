import logging
import os
import random
import string
import time
import yaml

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from Microcontroller import Microcontroller
from Page import Page

class Monitor():
    def __init__(self, port, baudrate, timeout, page_dir, logger):
        self.logger = logger
        
        self._microcontroller = Microcontroller(port, baudrate, timeout, logger)
        self.logger.info(f"NASMon running, connected to device at port: {port}")

        self._page_directory = page_dir
        self.logger.debug(f'Page directory: {page_dir}')

        self.page_dir = page_dir
        self._page_list = []
        self._page_list_index = 0
        self._build_page_list(page_dir)

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

    def _generate_random_bargraph(self):
        random_graph = ""
        for i in range(0, 23):
            random_graph += (random.choice(['r', 'y', 'g', 'o']))

        return random_graph

    def _generate_random_text(self, length):
        return ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=length))

    def _build_page_list(self, page_dir):
        page_list = []

        for entry in os.scandir(page_dir):
            if entry.path.endswith((".yaml", ".yml")) and entry.is_file():
                page_list.append(entry.path)
                self.logger.debug(f"Found page file: {entry.path}")
        
        self.logger.debug(f"Number of pages: {len(page_list)}")
        return page_list

    def _handle_page_file_change_events(self, event):
        self.logger.info(f"Page file {event.src_path} {event.event_type}, reloading page list...")
        self._page_list = self._build_page_list(self.page_dir)
        self.logger.info("Reload complete")

    def start(self):
        self._observer.start()
        try:
            while True:
                # self.logger.info(f"Found changes in page directory: {self.page_dir}, reloading page list...")
                # self.logger.info("Page list reloaded.")
            
                if self._microcontroller.is_requesting_data():
                    self._microcontroller.clear_displays()
                    self._microcontroller.display_text(random.randint(0, 128), random.randint(0, 32), 1, bytes(self._generate_random_text(random.randint(1, 128)), "utf-8"))
                    self._microcontroller.display_bargraph(bytes(self._generate_random_bargraph(), "utf-8"))
                    time.sleep(1)
        except KeyboardInterrupt:
            self._observer.stop()
            self._observer.join()
            self.stop()

    def stop(self):
        self._microcontroller.stop()