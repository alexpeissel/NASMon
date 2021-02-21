#!/usr/bin/env python

import click
import click_config_file
import click_logging
import logging
import yaml

from Monitor import Monitor

#######################################
# Logging
#######################################
logger = logging.getLogger(__name__)
click_logging.basic_config(logger)

#######################################
# Utilities
#######################################
def yaml_provider(file_path, cmd_name):
    with open(file_path) as f:
        return yaml.load(f, Loader=yaml.FullLoader).get("nasmon")

#######################################
# Commands
#######################################
@click.command()
@click_logging.simple_verbosity_option(logger)
@click.option('--port', help='NASMon connected serial port.')
@click.option('--baudrate', default=115200, help='Connection speed of the serial port.')
@click.option('--timeout', default=2, help='Number of seconds before connection to device times out.')
@click.option('--page_dir', default="./pages", help='Directory containing the page definition files.')
@click_config_file.configuration_option(provider=yaml_provider, config_file_name="config.yaml")
def handle_args(port, baudrate, timeout, page_dir):
    """Load config and arguments, (arguments have precidence)"""
    logger.info("Starting NASMon...")
    mon = Monitor(port, baudrate, timeout, page_dir, logger)
    mon.start()

#######################################
# Main
#######################################
if __name__ == '__main__':
    handle_args()
