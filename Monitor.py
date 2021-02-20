import random
import string
import time
import yaml

from Microcontroller import Microcontroller
from Page import Page

class Monitor():
    def __init__(self, port, baudrate, timeout, page_dir):
        self._page_directory = page_dir

        self._microcontroller = Microcontroller(port, baudrate, timeout)

    def generate_random_bargraph(self):
        random_graph = ""
        for i in range(0, 23):
            random_graph += (random.choice(['r', 'y', 'g', 'o']))

        return random_graph

    def generate_random_text(self, length):
        return ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=length))

    def start(self):
        while True:
            if self._microcontroller.is_requesting_data():
                self._microcontroller.clear_displays()
                self._microcontroller.display_text(random.randint(0, 128), random.randint(0, 32), 1, bytes(self.generate_random_text(random.randint(1, 128)), "utf-8"))
                self._microcontroller.display_bargraph(bytes(self.generate_random_bargraph(), "utf-8"))
                time.sleep(1)

    def stop(self):
        self._microcontroller.stop()