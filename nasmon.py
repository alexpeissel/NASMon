#!/usr/bin/env python

import click
import click_config_file
import sys
import yaml

from loguru import logger

from Monitor import Monitor

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
@click.option('--port', help='NASMon connected serial port.')
@click.option('--baudrate', default=115200, help='Connection speed of the serial port.')
@click.option('--timeout', default=2, help='Number of seconds before connection to device times out.')
@click.option('--page_dir', default="./pages", help='Directory containing the page definition files.')
@click.option('--debug', default=False, is_flag=True, help='Show debug logs.')
@click_config_file.configuration_option(provider=yaml_provider, config_file_name="config.yaml")
def handle_args(port, baudrate, timeout, page_dir, debug):
    """Load config and arguments, (arguments have precidence)"""

    # Remove the default logger and add one with a log level we set
    logger.remove(0)
    logger.start(sys.stderr, level=("DEBUG" if debug else "INFO"))
    logger.info("Starting NASMon...")
    
    mon = Monitor(port, baudrate, timeout, page_dir)
    mon.start()

#######################################
# Main
#######################################
if __name__ == '__main__':
    handle_args()
