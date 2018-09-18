# -*- coding: utf-8 -*-
"""
Microcontroller
Interface between application and Arduino.
"""

__author__ = "Alexander Peissel"
__version__ = "0.1.0"
__license__ = "MIT"

from cobs import cobs
import serial
import struct
import time
from logzero import logger

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

    def _send_command(self, data=None):
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

        logger.debug("Sending (chars): %s", encoded + '\x00')
        logger.debug("Sending (hex): %s", (encoded + '\x00').encode("hex"))
        self._serial.write(encoded + '\x00')

        self.commands_sent += 1

    def _reset_read_buffer(self):
        self._read_buf[0:self._read_buf_pos] = [None] * self._read_buf_pos
        self._read_buf_pos = 0

    def _recv_command(self):
        """Reads a full line from the microcontroller
        We expect to complete a read when this is invoked, so don't invoke unless
        you expect to get data from the microcontroller. We raise a timeout if we
        cannot read a command in the alloted timeout interval."""

        while True:
            c = self._serial.read(1)
            if not c:
                break
                raise serial.SerialTimeoutException(
                    "Couldn't recv command in %d seconds" % self.IO_TIMEOUT_SEC)

            # finished reading an entire COBS structure
            if c == '\x00':
                # grab the data and reset the buffer
                logger.debug("")
                data = self._read_buf[0:self._read_buf_pos]
                self._reset_read_buffer()

                # return decoded data
                decoded = cobs.decode(str(bytearray(data)))
                logger.debug("Decoded (%i bytes): %s", len(data), str(data))
                return decoded

            # still got reading to do
            else:
                self._read_buf[self._read_buf_pos] = c
                self._read_buf_pos += 1
                #print self._read_buf[0:self._read_buf_pos]

                # ugh. buffer overflow. wat do?
                if self._read_buf_pos == len(self._read_buf):
                    #print(cobs.decode(str(bytearray(self._read_buf))).encode("hex"))
                    # resetting the buffer likely means the next recv will fail, too (we lost the start bits)
                    self._reset_read_buffer()
                    raise RuntimeError("IO read buffer overflow :(")

    def send_formatted_data(self, data_format, mode, *args):
        if args:
            data = struct.pack(data_format, mode, *args)
        else:
            data = struct.pack(data_format, mode)

        self._send_command(data)
        received_data = self._recv_command()
        return received_data

    def clear_displays(self):
        return self.send_formatted_data('>B', self.SEND_CLEAR_MODE)

    def ping(self):
        return self.send_formatted_data('>B', self.SEND_PING_MODE)

    def get_wave_status(self):
        return self.send_formatted_data('>B', self.GET_WAVE_MODE)

    def display_text(self, text, x, y, size):
         print text, x, y, size
         return self.send_formatted_data('>BBBB128s', self.SEND_TEXT_MODE, int(size), int(x), int(y), str(text))

    def display_bmp(self, bmp, x, y, width, height):
        print bmp, x, y, width, height
        return self.send_formatted_data('>BBBBB128s', self.SEND_BMP_MODE, width, height, x, y, bmp)

    def display_bargraph(self, sequence):
        print sequence
        return self.send_formatted_data('>B24s', self.SEND_BARGRAPH_MODE, sequence)

    def is_requesting_data(self):
        requesting_data = False

        response = self.get_wave_status()
        if response != "nack_wav":
            requesting_data = True

        return requesting_data

    def is_up(self, max_attempts=5):
        logger.debug("Attempting to ping microcontroller")
        status = False
        attempts = max_attempts
        time.sleep(2)
        while attempts >= 0:
            logger.debug("%i of %i attempts left", attempts, max_attempts)
            if self.ping:
                status = True
                logger.info("Microcontroller is up")
                break

            attempts -= 1

        return status
