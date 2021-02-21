import logging
import os
import random
import string
import time
import yaml

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
        self.page_list = self._build_page_list(page_dir)
        self.summed_modified_time = self._get_summed_file_modification_time(page_dir)
        self.page_list_index = 0

    def generate_random_bargraph(self):
        random_graph = ""
        for i in range(0, 23):
            random_graph += (random.choice(['r', 'y', 'g', 'o']))

        return random_graph

    def generate_random_text(self, length):
        return ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=length))

    def _build_page_list(self, page_dir):
        page_list = []

        for entry in os.scandir(page_dir):
            if entry.path.endswith((".yaml", ".yml")) and entry.is_file():
                page_list.append(entry.path)
                self.logger.debug(f"Found page file: {entry.path}")
        
        self.logger.debug(f"Number of pages: {len(page_list)}")
        return page_list

    def _get_summed_file_modification_time(self, page_dir):
        summed_modified_time = 0

        for entry in os.scandir(page_dir):
            if entry.path.endswith((".yaml", ".yml")) and entry.is_file():
                summed_modified_time += os.path.getmtime(entry.path)
        
        return summed_modified_time
            
    def start(self):
        while True:
            sum_mod_time = self._get_summed_file_modification_time(self.page_dir)
            if sum_mod_time != self.summed_modified_time:
                self.logger.info(f"Found changes in page directory: {self.page_dir}, reloading page list...")
                self.page_list = self._build_page_list(self.page_dir)
                self.summed_modified_time = sum_mod_time
                self.logger.info("Page list reloaded.")
            
            if self._microcontroller.is_requesting_data():
                self._microcontroller.clear_displays()
                self._microcontroller.display_text(random.randint(0, 128), random.randint(0, 32), 1, bytes(self.generate_random_text(random.randint(1, 128)), "utf-8"))
                self._microcontroller.display_bargraph(bytes(self.generate_random_bargraph(), "utf-8"))
                time.sleep(1)

    def stop(self):
        self._microcontroller.stop()