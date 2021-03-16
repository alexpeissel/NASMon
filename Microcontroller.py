import logging
import serial
import struct

from loguru import logger
class Microcontroller():
    def __init__(self, port, baudrate, timeout):
        logger.debug(f"Opening port: {port} @ {baudrate} baud...")
        self._serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout)

        if not self._serial.isOpen():
            raise ValueError(f"Couldn't open {port}")

        logger.debug("Port opened successfully!")

        #self.reset()

    def _send_command(self, command_byte, data_format, *args):
        command = bytes(command_byte, "utf-8")

        if args:
            data = struct.pack(data_format, command, *args)
        else:
            data = struct.pack(data_format, command)
        
        logger.debug(f"Sending {len(data)} bytes, (command byte: {command_byte}) to uC")
        logger.trace(f"Sending data: {data.hex()}")
        self._serial.write(data)

        return self._serial.readline()

    def is_requesting_data(self):
        requesting = False

        if self._serial.inWaiting() > 0:
            response = self._serial.readline().decode("utf-8") 
            if "req" in response:
                requesting = True
            else:
                logger.error(f"Got non-request type message from uC: {response}")

        return requesting

    def stop(self):
        self._serial.close()

    def reset(self):
        return self._send_command('r', 'c')

    def display_image(self, bmp_bytes, x, y, width, height):
        return self._send_command('b', 'cBBBB512s', x, y, width, height, bmp_bytes)

    def display_text(self, x, y, size, text_bytes):
        return self._send_command('t', 'cBBB128s', x, y, size, text_bytes)

    def display_bargraph(self, graph_bytes):
        return self._send_command('g', 'c24s', graph_bytes)

    def clear_displays(self):
        return self._send_command('c', 'c')

    def set_settings(self, bargraph_brightness, max_display_on_time):
        return self._send_command('s', 'cBI', bargraph_brightness, max_display_on_time)

    def ping(self):
        return self._send_command('p', 'c')
