#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Main module
"""

__author__ = "Your Name"
__version__ = "0.1.0"
__license__ = "MIT"

import argparse
from Monitor import Monitor
from logzero import logger


def main(args):
    """ Main entry point of the app """
    logger.info("Starting NASMon")
    logger.debug("hello")
    logger.info("info")
    logger.warning("warning")
    logger.error("error")
    mon = Monitor(page_directory="pages", baudrate=115200, serial_port='/dev/cu.wchusbserial1420')
    mon.start()
    mon.stop()


if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()

    # Required positional argument
    #parser.add_argument("arg", help="Required positional argument")

    # Optional argument flag which defaults to False
    parser.add_argument("-f", "--flag", action="store_true", default=False)

    # Optional argument which requires a parameter (eg. -d test)
    parser.add_argument("-n", "--name", action="store", dest="name")

    # Optional verbosity counter (eg. -v, -vv, -vvv, etc.)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Verbosity (-v, -vv, etc)")

    # Specify output of "--version"
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=__version__))

    args = parser.parse_args()
    main(args)
