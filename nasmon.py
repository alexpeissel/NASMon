import click
import click_config_file
import yaml

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
@click.option('--page_dir', help='Diretory containing the page definition files.')
@click_config_file.configuration_option(provider=yaml_provider, config_file_name="config.yaml")
def handle_args(port, baudrate, timeout, page_dir):
    """Load config and arguments, (arguments have precidence)"""
    mon = Monitor(port, baudrate, timeout, page_dir)
    mon.start()

#######################################
# Main
#######################################
if __name__ == '__main__':
    handle_args()
