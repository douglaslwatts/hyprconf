#!/usr/bin/env python

# A work in progress to eventually replace set_hypr_monitor_config and set_hypr_monitor_config.awk

import argparse
import os
import sys
from pathlib import Path
import shutil
import re

arg_parser = argparse.ArgumentParser(
    description='''
Edits the Hyprland configuration file to set up a monitor configuration based on what monitors are
connected.

Note: This script is intended for use with up to 3 monitors placed side-by-side, or up to 3 
side-by-side external monitors and a builtin laptop monitor. 
''',
    epilog='Hyprland monitor configuration',
    argument_default=None,
    usage='''
[-h] [--left-monitor <name> <resolution> <refresh-rate> <starting-coordinate> <scale>]
[--center-monitor <name> <resolution> <refresh-rate> <starting-coordinate> <scale>]
[--right-monitor <name> <resolution> <refresh-rate> <starting-coordinate> <scale>]
[--builtin-monitor <name> <resolution> <refresh-rate> <starting-coordinate> <scale>]
[--dry-run]
[--verbose]
--secondary-monitor <l|r>

For help with these values, see https://wiki.hyprland.org/configuring/monitors/
'''
)

arg_parser.add_argument(
    '--left-monitor',
    '-l',
    help='Left monitor hypr configuration',
    nargs=5
)

arg_parser.add_argument(
    '--center-monitor',
    '-c',
    help='Center monitor hypr configuration',
    nargs=5
)

arg_parser.add_argument(
    '--right-monitor',
    '-r',
    help='Right monitor hypr configuration',
    nargs=5
)

arg_parser.add_argument(
    '--builtin-monitor',
    '-b',
    help='Builtin monitor hypr configuration',
    nargs=5
)

arg_parser.add_argument(
    '--secondary-monitor',
    '-s',
    help='Place secondary monitor to the left (l) or right (r) when only 2 monitors are connected?',
    required=True,
    choices=['l', 'r']
)

arg_parser.add_argument(
    '--verbose',
    '-v',
    help='Print output to the CLI verbosely',
    action='store_true'
)

arg_parser.add_argument(
    '--dry-run',
    '-d',
    help='Output new config file, but do not overwrite existing config',
    action='store_true'
)

def validate_monitor_config_args(monitor_config_args: list) -> bool:
    valid = True

    if not RESOLUTION_REGEX.match(monitor_config_args[1]):
        valid = False

        print(
            f'Error, invalid resolution for {monitor_config_args[0]} -> {monitor_config_args[1]}',
            file=sys.stderr
        )

    if not REFRESH_RATE_REGEX.match(monitor_config_args[2]):
        valid = False

        print(
            f'Error, invalid refresh rate for {monitor_config_args[0]} -> {monitor_config_args[2]}',
            file=sys.stderr
        )

    if not POSITION_COORDINATE_REGEX.match(monitor_config_args[3]):
        valid = False

        print(
            f'Error, starting coordinate for {monitor_config_args[0]} -> {monitor_config_args[3]}',
            file=sys.stderr
        )

    if not SCALING_REGEX.match(monitor_config_args[4]):
        valid = False

        print(
            f'Error, scale for {monitor_config_args[0]} -> {monitor_config_args[4]}',
            file=sys.stderr
        )

    return valid

HOME_DIR = os.getenv('HOME')
HYPR_CONFIG_FILE = f'{HOME_DIR}/.config/hypr/hyprland.conf'
HYPR_CONFIG_FILE_BAK = f'{HOME_DIR}/.config/hypr/hyprland.conf.bak'
HYPR_CONFIG_TMP_FILE = '/tmp/hypr_config'

WAYBAR_CONFIG_FILE = f'{HOME_DIR}/.config/waybar/config'
WAYBAR_CONFIG_FILE_BAK = f'{HOME_DIR}/.config/waybar/config.bak'
WAYBAR_CONFIG_TMP_FILE = '/tmp/waybar_config'
WAYBAR_OUTPUT_START = '    "output": ["'
WAYBAR_OUTPUT_END = '", ],\n'
WAYBAR_POSITION_REGEX = re.compile('^\\s*"output":\\s*\\[\\S+\\s*],\\s*$')

RESOLUTION_REGEX = re.compile('^[0-9]{4}x[0-9]{3,4}$')
REFRESH_RATE_REGEX = re.compile('^[0-9]{2,3}$')
POSITION_COORDINATE_REGEX = re.compile('^[0-9]{1,4}x0$')
SCALING_REGEX = re.compile('^[0-9]$')

DRM_DIR = '/sys/class/drm'
STATUS_FILE = 'status'
MONITOR_DIR_REGEX = re.compile(f'^{DRM_DIR}/card[0-9]-\\S+$')
CONNECTED_STATUS = 'connected'

POSITION_COORDINATE_INDEX = 3

cli_args = arg_parser.parse_args()

# If no Hyprland and/or Waybar config backup exists, make them

if not os.path.isfile(HYPR_CONFIG_FILE_BAK):
    if cli_args.verbose:
        print('No hyprland.conf.bak found, creating one...')

    shutil.copyfile(HYPR_CONFIG_FILE, HYPR_CONFIG_FILE_BAK)

if not os.path.isfile(WAYBAR_CONFIG_FILE_BAK):
    if cli_args.verbose:
        print('No Waybar config.bak found, creating one...')

    shutil.copyfile(WAYBAR_CONFIG_FILE, WAYBAR_CONFIG_FILE_BAK)

left_monitor_configs = cli_args.left_monitor
center_monitor_configs = cli_args.center_monitor
right_monitor_configs = cli_args.right_monitor
builtin_monitor_configs = cli_args.builtin_monitor
secondary_monitor_left = cli_args.secondary_monitor == 'l'
verbose = cli_args.verbose
dry_run = cli_args.dry_run

###### Gather and setup configs based on the status of connected and disconnected monitor(s) #######

# Get monitor connection statuses

BUILTIN_MONITOR_DIR_REGEX = re.compile(f'^\\S+{builtin_monitor_configs[0]}$') \
    if builtin_monitor_configs else None

LEFT_MONITOR_DIR_REGEX = re.compile(f'^\\S+{left_monitor_configs[0]}$')\
    if left_monitor_configs else None

CENTER_MONITOR_DIR_REGEX = re.compile(f'^\\S+{center_monitor_configs[0]}$')\
    if center_monitor_configs else None

RIGHT_MONITOR_DIR_REGEX = re.compile(f'^\\S+{right_monitor_configs[0]}$')\
    if right_monitor_configs else None

drm_path = Path(DRM_DIR)

monitor_dirs = [
    str(dir_name) for dir_name in drm_path.iterdir()
    if dir_name.is_dir() and MONITOR_DIR_REGEX.match(str(dir_name))
]

left_monitor_connected = False
center_monitor_connected = False
right_monitor_connected = False
builtin_monitor_connected = False

connected_monitor_names = []

for monitor_dir in monitor_dirs:

    with open(f'{monitor_dir}/{STATUS_FILE}', 'r') as file:
        monitor_status = file.read().strip()

        # NOTE: Often, the name assigned to the laptop's builtin monitor will be a superset of one
        #       or more of the names assigned to external monitors, so checking it first here to
        #       avoid a false match.

        if BUILTIN_MONITOR_DIR_REGEX and BUILTIN_MONITOR_DIR_REGEX.match(monitor_dir):
            builtin_monitor_connected = monitor_status == CONNECTED_STATUS

            if builtin_monitor_connected:
                connected_monitor_names.append(builtin_monitor_configs[0])
        elif LEFT_MONITOR_DIR_REGEX and LEFT_MONITOR_DIR_REGEX.match(monitor_dir):
            left_monitor_connected = monitor_status == CONNECTED_STATUS

            if left_monitor_connected:
                connected_monitor_names.append(left_monitor_configs[0])
        elif CENTER_MONITOR_DIR_REGEX and CENTER_MONITOR_DIR_REGEX.match(monitor_dir):
            center_monitor_connected = monitor_status == CONNECTED_STATUS

            if center_monitor_connected:
                connected_monitor_names.append(center_monitor_configs[0])
        elif RIGHT_MONITOR_DIR_REGEX and RIGHT_MONITOR_DIR_REGEX.match(monitor_dir):
            right_monitor_connected = monitor_status == CONNECTED_STATUS

            if right_monitor_connected:
                connected_monitor_names.append(right_monitor_configs[0])

if verbose:
    print(f'Connected monitor names => {connected_monitor_names}')

# Alter monitors' start position coordinates with respect to which monitors are actually
# connected, and set up config file line for specifying which monitor the Waybar should display on.

waybar_position = ''

if left_monitor_connected and center_monitor_connected and right_monitor_connected:

    if verbose:
        print('... all monitors connected')

    waybar_position = f'{WAYBAR_OUTPUT_START}{center_monitor_configs[0]}{WAYBAR_OUTPUT_END}'
elif not left_monitor_connected and center_monitor_connected and right_monitor_connected:

    if verbose:
        print('... left monitor not connected')

    builtin_monitor_configs[POSITION_COORDINATE_INDEX] = right_monitor_configs[POSITION_COORDINATE_INDEX]
    right_monitor_configs[POSITION_COORDINATE_INDEX] = center_monitor_configs[POSITION_COORDINATE_INDEX]
    center_monitor_configs[POSITION_COORDINATE_INDEX] = left_monitor_configs[POSITION_COORDINATE_INDEX]

    if secondary_monitor_left:
        waybar_position = f'{WAYBAR_OUTPUT_START}{right_monitor_configs[0]}{WAYBAR_OUTPUT_END}'
    else:
        waybar_position = f'{WAYBAR_OUTPUT_START}{center_monitor_configs[0]}{WAYBAR_OUTPUT_END}'
elif left_monitor_connected and not center_monitor_connected and right_monitor_connected:

    if verbose:
        print('... center monitor not connected')

    builtin_monitor_configs[POSITION_COORDINATE_INDEX] = right_monitor_configs[POSITION_COORDINATE_INDEX]
    right_monitor_configs[POSITION_COORDINATE_INDEX] = center_monitor_configs[POSITION_COORDINATE_INDEX]

    if secondary_monitor_left:
        waybar_position = f'{WAYBAR_OUTPUT_START}{right_monitor_configs[0]}{WAYBAR_OUTPUT_END}'
    else:
        waybar_position = f'{WAYBAR_OUTPUT_START}{left_monitor_configs[0]}{WAYBAR_OUTPUT_END}'
elif left_monitor_connected and center_monitor_connected and not right_monitor_connected:

    if verbose:
        print('... right monitor not connected')

    builtin_monitor_configs[POSITION_COORDINATE_INDEX] = right_monitor_configs[POSITION_COORDINATE_INDEX]

    if secondary_monitor_left:
        waybar_position = f'{WAYBAR_OUTPUT_START}{center_monitor_configs[0]}{WAYBAR_OUTPUT_END}'
    else:
        waybar_position = f'{WAYBAR_OUTPUT_START}{left_monitor_configs[0]}{WAYBAR_OUTPUT_END}'
elif left_monitor_connected and not center_monitor_connected and not right_monitor_connected:

    if verbose:
        print('... center and right monitors not connected')

    builtin_monitor_configs[POSITION_COORDINATE_INDEX] = center_monitor_configs[POSITION_COORDINATE_INDEX]
    waybar_position = f'{WAYBAR_OUTPUT_START}{left_monitor_configs[0]}{WAYBAR_OUTPUT_END}'
elif not left_monitor_connected and center_monitor_connected and not right_monitor_connected:

    if verbose:
        print('... left and right monitors not connected')

    builtin_monitor_configs[POSITION_COORDINATE_INDEX] = center_monitor_configs[POSITION_COORDINATE_INDEX]
    center_monitor_configs[POSITION_COORDINATE_INDEX] = left_monitor_configs[POSITION_COORDINATE_INDEX]
    waybar_position = f'{WAYBAR_OUTPUT_START}{center_monitor_configs[0]}{WAYBAR_OUTPUT_END}'
elif not left_monitor_connected and not center_monitor_connected and right_monitor_connected:

    if verbose:
        print('... left and center monitors not connected')

    builtin_monitor_configs[POSITION_COORDINATE_INDEX] = center_monitor_configs[POSITION_COORDINATE_INDEX]
    right_monitor_configs[POSITION_COORDINATE_INDEX] = left_monitor_configs[POSITION_COORDINATE_INDEX]
    waybar_position = f'{WAYBAR_OUTPUT_START}{right_monitor_configs[0]}{WAYBAR_OUTPUT_END}'
elif not left_monitor_connected and not center_monitor_connected and not right_monitor_connected:

    if verbose:
        print('... No external monitors are connected')

    builtin_monitor_configs[POSITION_COORDINATE_INDEX] = left_monitor_configs[POSITION_COORDINATE_INDEX]
    waybar_position = f'{WAYBAR_OUTPUT_START}{builtin_monitor_configs[0]}{WAYBAR_OUTPUT_END}'

# Validate args for, and set monitor configuration file lines

left_monitor = ''
center_monitor = ''
right_monitor = ''
builtin_monitor = ''

monitor_configs = [
    left_monitor_configs,
    center_monitor_configs,
    right_monitor_configs,
    builtin_monitor_configs
]

monitor_config_lines = []

for config in monitor_configs:
    if config:
        if not validate_monitor_config_args(config):
            exit(1)

    if config[0] in connected_monitor_names:
        monitor_config_lines.append(
            f'monitor = {config[0]}, {config[1]}@{config[2]}, {config[3]}, {config[4]}\n'
        )
    else:
        monitor_config_lines.append(
            f'#monitor = {config[0]}, {config[1]}@{config[2]}, {config[3]}, {config[4]}\n'
        )

if verbose:

    for monitor_config in monitor_config_lines:
        print(monitor_config)

    print(waybar_position)

############################### End gather and setup configs #######################################

#################### Write configs to file, or if dry_run, send them to stdout #####################

# Waybar

with open(WAYBAR_CONFIG_FILE, 'r') as waybar_config_file,\
        open(WAYBAR_CONFIG_TMP_FILE, 'w') as waybar_config_tmp_file:
    for line in waybar_config_file:
        if WAYBAR_POSITION_REGEX.match(line):
            waybar_config_tmp_file.write(re.sub(WAYBAR_POSITION_REGEX, waybar_position, line))
        else:
            waybar_config_tmp_file.write(line)

if dry_run:
    with open(WAYBAR_CONFIG_TMP_FILE, 'r') as waybar_config_tmp_file:
        print(waybar_config_tmp_file.read())
else:
    shutil.move(WAYBAR_CONFIG_TMP_FILE, WAYBAR_CONFIG_FILE)

# TODO: Write configs for Hyprland based on the currently connected monitors to file

# Hyprland

with open(HYPR_CONFIG_FILE, 'r') as hypr_config_file,\
        open(HYPR_CONFIG_TMP_FILE,'w') as hypr_config_tmp_file:
    print('TODO: Write configs for Hyprland based on the currently connected monitors to file')
