#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Main module
"""

__author__ = "Alexander Peissel"
__version__ = "0.1.0"
__license__ = "MIT"

import argparse
import logging
import logzero
from logzero import logger
from Monitor import Monitor


def clamp(n, min_n, max_n):
    return max(min(max_n, n), min_n)


def main(args):
    """ Main entry point of the app """

    # Configure logging
    log_levels = [logging.INFO, logging.DEBUG]
    clamped_verbosity = clamp(args.verbose, 0, len(log_levels) - 1)
    #logzero.loglevel(log_levels[clamped_verbosity])
    logzero.loglevel(logging.DEBUG)
    logger.info("Starting NASMon")
    logger.info(args)

    # TODO: Read config file

    # Instantiate and start the monitor
    mon = Monitor(page_directory=args.page_directory, baud_rate=args.baud_rate, serial_port=args.serial_port)
    mon.start()


if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()

    # Required positional argument
    #parser.add_argument("arg", help="Required positional argument")

    # Optional argument flag which defaults to False
    parser.add_argument("-f", "--flag", action="store_true", default=False)

    # Optional argument which requires a parameter (eg. -d test)
    parser.add_argument("-p", "--page-dir", action="store", dest="page_directory", default="pages")

    # Optional argument which requires a parameter (eg. -d test)
    parser.add_argument("-b", "--baud-rate", action="store", dest="baud_rate", default="115200")

    # Optional argument which requires a parameter (eg. -d test)
    parser.add_argument("-s", "--serial-port", action="store", dest="serial_port", default="/dev/cu.wchusbserial1420")

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
