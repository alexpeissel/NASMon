# -*- coding: utf-8 -*-
"""
Module Docstring
"""

__author__ = "Your Name"
__version__ = "0.1.0"
__license__ = "MIT"

from cobs import cobs
import serial
import struct
from logzero import logger

class Microcontroler(object):
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
        received = self._recv_command()
        return recieved_data

    def display_text(self, text, x, y, size):
        data = struct.pack('>BBBB128s', self.SEND_TEXT_MODE, size, x, y, text)
        self._send_command(data)
        received = self._recv_command()
        return recieved_data

    def display_bmp(self, bmp, x, y, width, height):
        data = struct.pack('>BBBBB128s', self.SEND_BMP_MODE, x, y, width, height, bmp)
        self._send_command(data)
        received = self._recv_command()
        return recieved_data

    def display_bargraph(self, sequence):
        data = struct.pack('>B24s', self.SEND_BARGRAPH_MODE, sequence)
        self._send_command(data)
        received = self._recv_command()
        return recieved_data

    def is_requesting_data(self):
        requesting_data = False
        data = struct.pack('>B', self.GET_WAVE_MODE)
        self._send_command(data)
        received = self._recv_command()
        print recieved_data
        if "wav_y" in recieved_data:
            requesting_data = True

        return requesting_data

    def ping(self, attempts=5):
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
