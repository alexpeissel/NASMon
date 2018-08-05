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
import yaml

from Monitor import Monitor


def main(args):
    """ Main entry point of the app """
    # Configure logging
    if args.verbose == 1:
        logzero.loglevel(logging.INFO)
    elif args.verbose == 2:
        logzero.loglevel(logging.INFO)
    elif args.verbose == 3:
        logzero.loglevel(logging.DEBUG)
    elif args.verbose == 4:
        logzero.loglevel(logging.DEBUG)
    else:
        logzero.loglevel(logging.INFO)

    # Instantiate and start the monitor
    logger.info("Starting NASMon")
    mon = Monitor(page_directory=args.page_directory, baud_rate=args.baud_rate, serial_port=args.serial_port)
    mon.start()


def _parse_config_file(config_file):
    config_file_data = None

    with open(config_file) as stream:
        try:
            config_file_data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            logger.error(exc)

    return config_file_data


if __name__ == "__main__":
    """ This is executed when run from the command line """

    parser = argparse.ArgumentParser()

    # Optional argument which requires a parameter (eg. -d test)
    parser.add_argument("-c", "--config", action="store", dest="config_file", default="conf/conf.yml")
    config_set = _parse_config_file("conf/conf.yml")

    parser.add_argument("-p", "--page-dir", action="store", dest="page_directory",
                        default=config_set.get("pages", "pages").get("page_directory"))
    parser.add_argument("-b", "--baud-rate", action="store", dest="baud_rate",
                        default=config_set.get("serial", "115200").get("baud_rate"))
    parser.add_argument("-s", "--serial-port", action="store", dest="serial_port",
                        default=config_set.get("serial", "/dev/cu.wchusbserial1410").get("port"))

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
