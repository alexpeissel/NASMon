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
from cobs import cobs
import io
import select
import serial
import struct
import threading
import time
import string
import yaml
import glob
import subprocess
import array
import random
import argparse
from logzero import logger

###############################
# Classes
###############################
class Microcontroller(object):
    """interface to an on-board microcontroller"""

    # Modes
    SEND_CLEAR_MODE = 1
    SEND_PING_MODE = 2
    GET_WAVE_MODE = 3
    SEND_TEXT_MODE = 4
    SEND_BMP_MODE = 5
    SEND_BARGRAPH_MODE = 6
    DEBUG_ECHO_MODE = 7

    # Timeout for buffered serial I/O in seconds.
    IO_TIMEOUT_SEC = 2

    def __init__(self, port, baud_rate=115200):
        """Connects to the microcontroller on a serial port.
        Args:
            port: The serial port or path to a serial device.
            baud_rate: The bit rate for serial communication.
        Raises:
            ValueError: There is an error opening the port.
            SerialError: There is a configuration error.
        """
        # Build the serial wrapper.
        self._serial = serial.Serial(
            port=port,
            baudrate=baud_rate,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=self.IO_TIMEOUT_SEC)
        if not self._serial.isOpen():
            raise ValueError("Couldn't open %s" % port)

        # holds reads until we encounter a 0-byte (COBS!!!)
        self._read_buf = [None] * 256
        self._read_buf_pos = 0

        # How many commands we've sent to the microcontroller.
        self.commands_sent = 0

    def stop(self):
        """Shuts down communication to the microcontroller."""
        self._serial.close()

    def _send_command(self, data=None, binary_format=True):
        """Sends a command to the microcontroller.
          Args:
              command: An ASCII string which the controller will interpret.
          Returns:
              True if command was sent, False if something went wrong. Note
              this doesn't guarantee the command was actually received.
        """

        if data is None:
            data = []
        encoded = cobs.encode(str(bytearray(data)))

        print("Sending: " + encoded + '\x00')
        print((encoded + '\x00').encode("hex"))
        self._serial.write(encoded + '\x00')

        self.commands_sent += 1
        return True

    def _reset_read_buf(self):
        self._read_buf[0:self._read_buf_pos] = [None] * self._read_buf_pos
        self._read_buf_pos = 0

    def _recv_command(self):
        """Reads a full line from the microcontroller
        We expect to complete a read when this is invoked, so don't invoke unless
        you expect to get data from the microcontroller. we raise a timeout if we
        cannot read a command in the alloted timeout interval."""
        # we rely on the passed-in timeout
        while True:
            c = self._serial.read(1)
            if not c:
                break
                raise serial.SerialTimeoutException(
                    "Couldn't recv command in %d seconds" % self.IO_TIMEOUT_SEC)

            # finished reading an entire COBS structure
            if c == '\x00':
                # grab the data and reset the buffer
                data = self._read_buf[0:self._read_buf_pos]
                self._reset_read_buf()

                # return decoded data
                data_length = str(len(data))
                decoded = cobs.decode(str(bytearray(data)))
                decoded_length = "Sending " + str(len(decoded)) + " bytes"
                print "Data length: " + data_length + ", encoded length: " + decoded_length
                return decoded

            # still got reading to do
            else:
                self._read_buf[self._read_buf_pos] = c
                self._read_buf_pos += 1
                print self._read_buf[0:self._read_buf_pos]

                # ugh. buffer overflow. wat do?
                if self._read_buf_pos == len(self._read_buf):
                    print(cobs.decode(str(bytearray(self._read_buf))).encode("hex"))
                    # resetting the buffer likely means the next recv will fail, too (we lost the start bits)
                    self._reset_read_buf()
                    raise RuntimeError("IO read buffer overflow :(")

    def clear_displays(self):
        data = struct.pack('>B', self.SEND_CLEAR_MODE)
        self._send_command(data)
        recieved_data = self._recv_command()
        return recieved_data

    def display_text(self, text, x, y, size):
        data = struct.pack('>BBBB128s', self.SEND_TEXT_MODE, size, x, y, text)
        self._send_command(data)
        recieved_data = self._recv_command()
        return recieved_data

    def display_bmp(self, bmp, x, y, width, height):
        data = struct.pack('>BBBBB128s', self.SEND_BMP_MODE, x, y, width, height, bmp)
        self._send_command(data)
        recieved_data = self._recv_command()
        return recieved_data

    def display_bargraph(self, sequence):
        data = struct.pack('>B24s', self.SEND_BARGRAPH_MODE, sequence)
        self._send_command(data)
        recieved_data = self._recv_command()
        return recieved_data

    def is_requesting_data(self):
        requesting_data = False
        data = struct.pack('>B', self.GET_WAVE_MODE)
        self._send_command(data)
        recieved_data = self._recv_command()
        print recieved_data
        if ("wav_y" in recieved_data):
            requesting_data = True

        return requesting_data

    def ping(self, attempts = 5):
        status = False
        while attempts >= 0:
            print"pings left: " + str(attempts)
            self._send_command(struct.pack('>B', self.SEND_PING_MODE))
            data = self._recv_command()
            print "mc returned: " + str(data)
            if data:
                status = True
                break

            attempts -= 1
        return status


class Page:
    def __init__(self, page_file):
        self.text_components = []
        self.bmp_components = []
        self.bargraph_components = []
        self.command_components = []
        self.command_outputs = []
        self._parse_page_file(page_file)

    def get_text_components(self):
        self._update()
        for command_output in self.command_outputs:
            variable_identifier = command_output['variable_identifier']
            for i, searchable_text in enumerate(self.text_components):
                if variable_identifier in searchable_text['text']:
                    print("Replacing " + str(variable_identifier) + " with " + command_output['result'])
                    self.text_components[i]['text'] = searchable_text['text'].replace(variable_identifier, command_output['result'])

        return self.text_components

    def get_bmp_components(self):
        return self.bmp_components

    def get_bargraph_components(self):
        self._update()
        for command_output in self.command_outputs:
            variable_identifier = command_output['variable_identifier']
            for i, bargraph_component in enumerate(self.bargraph_components):
                if variable_identifier == bargraph_component['graph_value']:
                    print("Setting graph value to " + str(command_output['result']) + "%")
                    self.bargraph_components[i]['graph_value'] = self._convert_int_to_bargraph(
                        command_output['result']

                    )
        return self.bargraph_components

    def _update(self):
        for output in self.command_outputs:
            if output['update']:
                output['result'] = self._run_command(output['command'])

    def _convert_bitmap_to_1_bit(self):
        pass

    def _convert_int_to_bargraph(self, value, green_threshold=0, yellow_threshold=50, red_threshold=75):
        bargraph_data = ['o'] * 24
        for i in xrange(0, len(bargraph_data)):
            if int(value) > ((i + 1) * (100.0 / 24)):
                if (i + 1) * (100.0 / 24) >= red_threshold:
                    bargraph_data[i] = 'r'
                elif (i + 1) * (100.0 / 24) >= yellow_threshold:
                    bargraph_data[i] = 'y'
                elif (i + 1) * (100.0 / 24) >= green_threshold:
                    bargraph_data[i] = 'g'
                else:
                    bargraph_data[i] = 'o'

        return "".join(bargraph_data)

    def _parse_page_file(self, page_file):
        with open(page_file) as stream:
            try:
                page_file_data = yaml.safe_load(stream)
                self._parse_page_data(page_file_data)
            except yaml.YAMLError as exc:
                print(exc)

    def _parse_page_data(self, data):
        for text_component in data['text']:
            self.text_components.append(text_component)

        for bmp_component in data['bmp']:
            self.bmp_components.append(bmp_component)

        if len(data['graph']) > 1:
            print("Only 1 graph value is allowed, taking the first value only.")

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
            print "Command returned a non 0 value"
        return result


class Monitor:
    """Main class"""
    def __init__(self, page_directory, serial_port, baudrate):
        """Loads pages from page_directory and connects to microcontroller.
        Args:
            page_directory: The directory containing pages in .yml format.
            port: The serial port or path to a serial device.
            baud_rate: The bit rate for serial communication.
        """
        self.current_page_index = 0
        self.page_directory = page_directory
        self.pages = self._build_page_list(self.page_directory)

        self.mc = Microcontroller(serial_port, baudrate)

        if self.mc.ping():
            print "Microcontrolller ready!"
            print
        else:
            print "broke :("
            print
            exit(1)

        self.test_mc()
        #exit(0)

    def generate_random_string(self, length):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

    def generate_random_graph(self):
        return ''.join(random.choice('rgyo') for _ in range(24))

    def test_mc(self):

        #time.sleep(10)

        # Ping
        # print("sending ping")
        # test_string = struct.pack('>B', 128)
        # self.mc._send_command(test_string)
        # recieved_data = self.mc._recv_command()
        # print("Recieved: " + recieved_data)
        # print(recieved_data.encode("hex"))
        # print

        # Get status of wave
        # print("sending wave")
        # test_string = struct.pack('>B', self.mc.GET_WAVE_MODE)
        # self.mc.test_send(test_string)
        # recieved_data = self.mc.test_recieve()
        # print("Recieved: " + recieved_data)
        # print(recieved_data.encode("hex"))
        # print

        # while True:
        #     # Get status of wave
        #     test_string = struct.pack('>B', 3)
        #     self.mc._send_command(test_string)
        #     recieved_data = self.mc.test_recieve()
        #     print("Recieved: " + recieved_data)
        #     print(recieved_data.encode("hex"))
        #     print

        # # Send text (3)
        # print("sending text")
        # test_string = struct.pack('>BBBB128s', self.mc.SEND_TEXT_MODE, 1, 10, 255, self.generate_random_string(128))
        # self.mc.test_send(test_string)
        # recieved_data = self.mc.test_recieve()
        # print("Recieved: " + recieved_data)
        # print(recieved_data.encode("hex"))
        # print
        #
        # time.sleep(2)

        # Send bmp (4)
        # print("sending bmp")
        # origin_array = [1, 2, 4, 6, 8]
        # test_array = array.array('B', origin_array)
        # test_string = struct.pack('>BBBBB128s', self.mc.SEND_BMP_MODE, 1, 10, 255, 255, test_array.tostring())
        # self.mc.test_send(test_string)
        # recieved_data = self.mc.test_recieve()
        # print("Recieved: " + recieved_data)
        # print(recieved_data.encode("hex"))
        # print


        while True:
            # Send text (3)
            print("sending text")
            test_string = struct.pack('>BBBB128s', self.mc.SEND_TEXT_MODE, 1, 0, 0, self.generate_random_string(10))
            self.mc._send_command(test_string)
            recieved_data = self.mc._recv_command()
            print("Recieved: " + recieved_data)
            print(recieved_data.encode("hex"))
            print

            # Send text (3)
            print("sending text")
            test_string = struct.pack('>BBBB128s', self.mc.SEND_TEXT_MODE, 2, 0, 10, self.generate_random_string(10))
            self.mc._send_command(test_string)
            recieved_data = self.mc._recv_command()
            print("Recieved: " + recieved_data)
            print(recieved_data.encode("hex"))
            print

            print("sending text")
            test_string = struct.pack('>BBBB128s', self.mc.SEND_TEXT_MODE, 1, 0, 20, self.generate_random_string(10))
            self.mc._send_command(test_string)
            recieved_data = self.mc._recv_command()
            print("Recieved: " + recieved_data)
            print(recieved_data.encode("hex"))
            print

            # Send bargraph (5)
            print("sending bargraph")
            test_bargraph = self.generate_random_graph()
            test_string = struct.pack('>B24s', self.mc.SEND_BARGRAPH_MODE, test_bargraph)
            self.mc._send_command(test_string)
            recieved_data = self.mc._recv_command()
            print("Recieved: " + recieved_data)
            print(recieved_data.encode("hex"))
            print

            # Clear text (0)
            print("clearing text")
            test_string = struct.pack('>B', self.mc.SEND_CLEAR_MODE)
            self.mc._send_command(test_string)
            recieved_data = self.mc._recv_command()
            print("Recieved: " + recieved_data)
            print(recieved_data.encode("hex"))
            print

        # print(len(test_string))
        # self.mc.test_send(test_string)
        # recieved_data = self.mc.test_recieve()
        # print("Recieved: " + recieved_data)
        # print(recieved_data.encode("hex"))
        # print(ord(recieved_data))
        # print(bin(ord(recieved_data)))

    def start(self):
        while(True):
            time.sleep(2)
            if self.mc.is_requesting_data():
                self.mc.clear_displays()
                current_page = self.pages[self.current_page_index]
                print("Displaying page: " + str(self.current_page_index))
                self._show_page(current_page)
                if self.current_page_index == len(self.pages) - 1:
                    self.current_page_index = 0
                else:
                    self.current_page_index += 1
            else:
                print("-")

    def stop(self):
        self.mc.stop()

    def _build_page_list(self, page_directory):
        parsed_pages = []
        matching_files = glob.glob(page_directory + "/*.yml")

        for page_file in matching_files:
            print("Found page file" + page_file + ", parsing....")
            parsed_pages.append(Page(page_file))

        print("Finished parsing " + str(len(matching_files)) + " pages.")
        return parsed_pages

    def _show_page(self, page):
        print page.get_text_components()
        for text_data in page.get_text_components():
            self.mc.display_text(text_data['text'], text_data['x'], text_data['y'], text_data['size'])

        # for bmp_data in page.get_bmp_components():
        #     self.mc.display_bmp(bmp_data)
        #
        print page.get_bargraph_components()
        for bargraph_data in page.get_bargraph_components():
            self.mc.display_bargraph(bargraph_data)

###############################
# Functions
###############################
# def main(args):
#     """ Main entry point of the app """
#     logger.info("hello world")
#     mon = Monitor(page_directory="pages", baudrate=115200, serial_port='/dev/cu.wchusbserial1420')
#     mon.start()
#     mon.stop()

###############################
# Main
###############################
# if __name__ == "__main__":
#     """ This is executed when run from the command line """
#     parser = argparse.ArgumentParser()
#
#     # Required positional argument
#     #parser.add_argument("arg", help="Required positional argument")
#
#     # Optional argument flag which defaults to False
#     parser.add_argument("-f", "--flag", action="store_true", default=False)
#
#     # Optional argument which requires a parameter (eg. -d test)
#     parser.add_argument("-n", "--name", action="store", dest="name")
#
#     # Optional verbosity counter (eg. -v, -vv, -vvv, etc.)
#     parser.add_argument(
#         "-v",
#         "--verbose",
#         action="count",
#         default=0,
#         help="Verbosity (-v, -vv, etc)")
#
#     # Specify output of "--version"
#     parser.add_argument(
#         "--version",
#         action="version",
#         version="%(prog)s (version {version})".format(version=__version__))
#
#     args = parser.parse_args()
#     main(args)
