#!/usr/bin/env python

# Set the monitor layout based on which monitors are connected when using hyprland as DE. call this
# prior to calling the Hyprland command. For example:
#
#                           $HOME/bin/set_hypr_monitor_config.py && Hyprland
#
# NOTE: This script is currently taking args for the monitor modes. It would be nice to find a way
#       to read them from someplace like /sys/class/drm/ instead, so it can be more dynamic and choose
#       the best available mode and refresh rate automatically. I see that the available modes can
#       be read from /sys/class/drm/card[x-monitor-name]/modes, but I have not found a way to read
#       the available refresh rates for those modes yet. This setup has a lot of room for improvements.

# TODO: * Pull functions and appropriate constants out of this script into a separate file and
#         and import that here.
#       * Create a script that also imports the above mentioned functionality, regularly checks
#         for newly connected monitors, calls this script when a new monitor is detected,
#         and restarts the Waybar if it should switch to a different monitor. The change to the
#         Hyprland config would take effect automatically, so no action needed there. To be
#         very responsive, it would be kind of like the bin/hypr_low_batt script but with a much
#         shorter interval in the forever loop. It just needs to read some files to see what
#         monitor ports have a connected status, so I wonder if it is okay to just set the interval
#         at one second.

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
[-h]
[--left-monitor <name> <resolution> <refresh-rate> <starting-coordinate> <scale>]
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
    '--when-external-connected-disable-builtin',
    '-w',
    help='Disable the builtin monitor when external monitors are connected',
    action='store_true'
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


def get_new_config_line(first_workspace: int, first_workspace_is_on_new_monitor: bool,
                        monitor_name: str, workspace_config_line: str)-> str:
    first_workspace_regex = re.compile(f'^workspace\\s*=\\s*{first_workspace}.*$')

    new_config_line = re.sub(
        rf'({LEFT_MONITOR_NAME}|{CENTER_MONITOR_NAME}|{RIGHT_MONITOR_NAME}|{BUILTIN_MONITOR_NAME})',
        monitor_name,
        workspace_config_line)

    new_config_line = re.sub(
        r'default:(true|false)',
        'default:true'
            if first_workspace_regex.match(workspace_config_line) and first_workspace_is_on_new_monitor
            else 'default:false',
        new_config_line)

    return new_config_line


def handle_workspaces_1_through_5_config(workspace_config_line: str) -> str:

    if THREE_EXTERNAL_MONITORS_CONNECTED \
            or (ONLY_LEFT_AND_CENTER_MONITORS_CONNECTED and SECONDARY_MONITOR_LEFT) \
            or (ONLY_CENTER_AND_RIGHT_MONITORS_CONNECTED and SECONDARY_MONITOR_RIGHT) \
            or ONLY_CENTER_MONITOR_CONNECTED:
        monitor = CENTER_MONITOR_NAME
    elif ((ONLY_LEFT_AND_CENTER_MONITORS_CONNECTED or ONLY_LEFT_AND_RIGHT_MONITORS_CONNECTED)
          and SECONDARY_MONITOR_RIGHT) \
            or ONLY_LEFT_MONITOR_CONNECTED:
        monitor = LEFT_MONITOR_NAME
    elif ((ONLY_CENTER_AND_RIGHT_MONITORS_CONNECTED or ONLY_LEFT_AND_RIGHT_MONITORS_CONNECTED)
          and SECONDARY_MONITOR_LEFT) \
            or ONLY_RIGHT_MONITOR_CONNECTED:
        monitor = RIGHT_MONITOR_NAME
    else:
        monitor = BUILTIN_MONITOR_NAME

    return get_new_config_line(1, True, monitor, workspace_config_line)


def handle_workspaces_6_and_7_config(workspace_config_line: str) -> str:

    if THREE_EXTERNAL_MONITORS_CONNECTED or ONLY_LEFT_MONITOR_CONNECTED:
        monitor = LEFT_MONITOR_NAME
    elif (ONLY_LEFT_AND_CENTER_MONITORS_CONNECTED and SECONDARY_MONITOR_LEFT) \
            or (ONLY_CENTER_AND_RIGHT_MONITORS_CONNECTED and SECONDARY_MONITOR_RIGHT) \
            or ONLY_CENTER_MONITOR_CONNECTED:
        monitor = CENTER_MONITOR_NAME
    elif ((ONLY_LEFT_AND_RIGHT_MONITORS_CONNECTED or ONLY_CENTER_AND_RIGHT_MONITORS_CONNECTED)
          and SECONDARY_MONITOR_LEFT) \
            or ONLY_RIGHT_MONITOR_CONNECTED:
        monitor = RIGHT_MONITOR_NAME
    elif (ONLY_LEFT_AND_RIGHT_MONITORS_CONNECTED or ONLY_LEFT_AND_CENTER_MONITORS_CONNECTED) \
            and SECONDARY_MONITOR_RIGHT:
        monitor = LEFT_MONITOR_NAME
    else:
        monitor = BUILTIN_MONITOR_NAME

    return get_new_config_line(6, THREE_EXTERNAL_MONITORS_CONNECTED, monitor, workspace_config_line)


def handle_workspaces_8_through_10_config(workspace_config_line: str) -> str:

    if THREE_EXTERNAL_MONITORS_CONNECTED \
            or ((ONLY_LEFT_AND_RIGHT_MONITORS_CONNECTED or ONLY_CENTER_AND_RIGHT_MONITORS_CONNECTED)
                and SECONDARY_MONITOR_RIGHT) \
            or ONLY_RIGHT_MONITOR_CONNECTED:
        monitor = RIGHT_MONITOR_NAME
    elif ((ONLY_LEFT_AND_RIGHT_MONITORS_CONNECTED or ONLY_LEFT_AND_CENTER_MONITORS_CONNECTED)
          and SECONDARY_MONITOR_LEFT) \
            or ONLY_LEFT_MONITOR_CONNECTED:
        monitor = LEFT_MONITOR_NAME
    elif (ONLY_LEFT_AND_CENTER_MONITORS_CONNECTED and SECONDARY_MONITOR_RIGHT) \
            or (ONLY_CENTER_AND_RIGHT_MONITORS_CONNECTED and SECONDARY_MONITOR_LEFT) \
            or ONLY_CENTER_MONITOR_CONNECTED:
        monitor = CENTER_MONITOR_NAME
    else:
        monitor = BUILTIN_MONITOR_NAME

    at_least_two_monitors_connected = ONLY_LEFT_AND_CENTER_MONITORS_CONNECTED \
                                      or ONLY_LEFT_AND_RIGHT_MONITORS_CONNECTED \
                                      or ONLY_CENTER_AND_RIGHT_MONITORS_CONNECTED \
                                      or THREE_EXTERNAL_MONITORS_CONNECTED

    return get_new_config_line(8, at_least_two_monitors_connected, monitor, workspace_config_line)


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

LEFT_MONITOR_CONFIGS = cli_args.left_monitor
CENTER_MONITOR_CONFIGS = cli_args.center_monitor
RIGHT_MONITOR_CONFIGS = cli_args.right_monitor
BUILTIN_MONITOR_CONFIGS = cli_args.builtin_monitor
SECONDARY_MONITOR_LEFT = cli_args.secondary_monitor == 'l'
SECONDARY_MONITOR_RIGHT = cli_args.secondary_monitor == 'r'
WHEN_EXTERNAL_CONNECTED_DISABLE_BUILTIN = cli_args.when_external_connected_disable_builtin
VERBOSE = cli_args.verbose
DRY_RUN = cli_args.dry_run

LEFT_MONITOR_NAME = LEFT_MONITOR_CONFIGS[0] if LEFT_MONITOR_CONFIGS else None
CENTER_MONITOR_NAME = CENTER_MONITOR_CONFIGS[0] if CENTER_MONITOR_CONFIGS else None
RIGHT_MONITOR_NAME = RIGHT_MONITOR_CONFIGS[0] if RIGHT_MONITOR_CONFIGS else None
BUILTIN_MONITOR_NAME = BUILTIN_MONITOR_CONFIGS[0] if BUILTIN_MONITOR_CONFIGS else None

LEFT_MONITOR_CONFIG_LINE_REGEX = re.compile(f'^(#)?monitor\\s*=\\s*{LEFT_MONITOR_NAME}.*$') \
    if LEFT_MONITOR_CONFIGS else None

CENTER_MONITOR_CONFIG_LINE_REGEX = re.compile(f'^(#)?monitor\\s*=\\s*{CENTER_MONITOR_NAME}.*$') \
    if CENTER_MONITOR_CONFIGS else None

RIGHT_MONITOR_CONFIG_LINE_REGEX = re.compile(f'^(#)?monitor\\s*=\\s*{RIGHT_MONITOR_NAME}.*$') \
    if RIGHT_MONITOR_CONFIGS else None

BUILTIN_MONITOR_CONFIG_LINE_REGEX = re.compile(f'^(#)?monitor\\s*=\\s*{BUILTIN_MONITOR_NAME}.*$') \
    if BUILTIN_MONITOR_CONFIGS else None

WORKSPACE_ONE_THROUGH_FIVE_CONFIG_LINE = re.compile('^workspace\\s*=\\s*[1-5],.*$')
WORKSPACE_SIX_THROUGH_SEVEN_CONFIG_LINE = re.compile('^workspace\\s*=\\s*[6-7],.*$')
WORKSPACE_EIGHT_THROUGH_TEN_CONFIG_LINE = re.compile('^workspace\\s*=\\s*([8-9]|10),.*$')
WORKSPACE_ELEVEN_CONFIG_LINE = re.compile('^workspace\\s*=\\s*11,.*$')

###### Gather and setup configs based on the status of connected and disconnected monitor(s) #######

# Get monitor connection statuses

BUILTIN_MONITOR_DIR_REGEX = re.compile(f'^\\S+{BUILTIN_MONITOR_NAME}$') \
    if BUILTIN_MONITOR_CONFIGS else None

LEFT_MONITOR_DIR_REGEX = re.compile(f'^\\S+{LEFT_MONITOR_NAME}$') \
    if LEFT_MONITOR_CONFIGS else None

CENTER_MONITOR_DIR_REGEX = re.compile(f'^\\S+{CENTER_MONITOR_NAME}$') \
    if CENTER_MONITOR_CONFIGS else None

RIGHT_MONITOR_DIR_REGEX = re.compile(f'^\\S+{RIGHT_MONITOR_NAME}$') \
    if RIGHT_MONITOR_CONFIGS else None

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
                connected_monitor_names.append(BUILTIN_MONITOR_NAME)
        elif LEFT_MONITOR_DIR_REGEX and LEFT_MONITOR_DIR_REGEX.match(monitor_dir):
            left_monitor_connected = monitor_status == CONNECTED_STATUS

            if left_monitor_connected:
                connected_monitor_names.append(LEFT_MONITOR_NAME)
        elif CENTER_MONITOR_DIR_REGEX and CENTER_MONITOR_DIR_REGEX.match(monitor_dir):
            center_monitor_connected = monitor_status == CONNECTED_STATUS

            if center_monitor_connected:
                connected_monitor_names.append(CENTER_MONITOR_NAME)
        elif RIGHT_MONITOR_DIR_REGEX and RIGHT_MONITOR_DIR_REGEX.match(monitor_dir):
            right_monitor_connected = monitor_status == CONNECTED_STATUS

            if right_monitor_connected:
                connected_monitor_names.append(RIGHT_MONITOR_NAME)

if VERBOSE:
    print(f'Connected monitor names => {connected_monitor_names}')

# Alter monitors' start position coordinates with respect to which monitors are actually
# connected, and set up config file line for specifying which monitor the Waybar should display on.

waybar_position = ''

ONLY_LEFT_AND_CENTER_MONITORS_CONNECTED = \
    left_monitor_connected and center_monitor_connected and not right_monitor_connected

ONLY_LEFT_AND_RIGHT_MONITORS_CONNECTED = \
        left_monitor_connected and not center_monitor_connected and right_monitor_connected

ONLY_CENTER_AND_RIGHT_MONITORS_CONNECTED = \
        not left_monitor_connected and center_monitor_connected and right_monitor_connected

ONLY_LEFT_MONITOR_CONNECTED = \
        left_monitor_connected and not center_monitor_connected and not right_monitor_connected

ONLY_CENTER_MONITOR_CONNECTED = \
        not left_monitor_connected and center_monitor_connected and not right_monitor_connected

ONLY_RIGHT_MONITOR_CONNECTED = \
        not left_monitor_connected and not center_monitor_connected and right_monitor_connected

THREE_EXTERNAL_MONITORS_CONNECTED = \
        left_monitor_connected and center_monitor_connected and right_monitor_connected

NO_EXTERNAL_MONITORS_CONNECTED = \
        not left_monitor_connected and not center_monitor_connected and not right_monitor_connected

ANY_EXTERNAL_MONITORS_CONNECTED = \
    left_monitor_connected or center_monitor_connected or right_monitor_connected

if THREE_EXTERNAL_MONITORS_CONNECTED:

    if VERBOSE:
        print('... all monitors connected')

    waybar_position = f'{WAYBAR_OUTPUT_START}{CENTER_MONITOR_NAME}{WAYBAR_OUTPUT_END}'
elif ONLY_CENTER_AND_RIGHT_MONITORS_CONNECTED:

    if VERBOSE:
        print('... left monitor not connected')

    BUILTIN_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX] = RIGHT_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX]
    RIGHT_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX] = CENTER_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX]
    CENTER_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX] = LEFT_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX]

    if SECONDARY_MONITOR_LEFT:
        waybar_position = f'{WAYBAR_OUTPUT_START}{RIGHT_MONITOR_NAME}{WAYBAR_OUTPUT_END}'
    else:
        waybar_position = f'{WAYBAR_OUTPUT_START}{CENTER_MONITOR_NAME}{WAYBAR_OUTPUT_END}'
elif ONLY_LEFT_AND_RIGHT_MONITORS_CONNECTED:

    if VERBOSE:
        print('... center monitor not connected')

    BUILTIN_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX] = RIGHT_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX]
    RIGHT_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX] = CENTER_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX]

    if SECONDARY_MONITOR_LEFT:
        waybar_position = f'{WAYBAR_OUTPUT_START}{RIGHT_MONITOR_NAME}{WAYBAR_OUTPUT_END}'
    else:
        waybar_position = f'{WAYBAR_OUTPUT_START}{LEFT_MONITOR_NAME}{WAYBAR_OUTPUT_END}'
elif ONLY_LEFT_AND_CENTER_MONITORS_CONNECTED:

    if VERBOSE:
        print('... right monitor not connected')

    BUILTIN_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX] = RIGHT_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX]

    if SECONDARY_MONITOR_LEFT:
        waybar_position = f'{WAYBAR_OUTPUT_START}{CENTER_MONITOR_NAME}{WAYBAR_OUTPUT_END}'
    else:
        waybar_position = f'{WAYBAR_OUTPUT_START}{LEFT_MONITOR_NAME}{WAYBAR_OUTPUT_END}'
elif ONLY_LEFT_MONITOR_CONNECTED:

    if VERBOSE:
        print('... center and right monitors not connected')

    BUILTIN_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX] = CENTER_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX]
    waybar_position = f'{WAYBAR_OUTPUT_START}{LEFT_MONITOR_NAME}{WAYBAR_OUTPUT_END}'
elif ONLY_CENTER_MONITOR_CONNECTED:

    if VERBOSE:
        print('... left and right monitors not connected')

    BUILTIN_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX] = CENTER_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX]
    CENTER_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX] = LEFT_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX]
    waybar_position = f'{WAYBAR_OUTPUT_START}{CENTER_MONITOR_NAME}{WAYBAR_OUTPUT_END}'
elif ONLY_RIGHT_MONITOR_CONNECTED:

    if VERBOSE:
        print('... left and center monitors not connected')

    BUILTIN_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX] = CENTER_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX]
    RIGHT_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX] = LEFT_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX]
    waybar_position = f'{WAYBAR_OUTPUT_START}{RIGHT_MONITOR_NAME}{WAYBAR_OUTPUT_END}'
elif NO_EXTERNAL_MONITORS_CONNECTED:

    if VERBOSE:
        print('... No external monitors are connected')

    BUILTIN_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX] = LEFT_MONITOR_CONFIGS[POSITION_COORDINATE_INDEX]
    waybar_position = f'{WAYBAR_OUTPUT_START}{BUILTIN_MONITOR_NAME}{WAYBAR_OUTPUT_END}'

# Validate args for, and set monitor configuration file lines

monitor_configs = [
    LEFT_MONITOR_CONFIGS,
    CENTER_MONITOR_CONFIGS,
    RIGHT_MONITOR_CONFIGS,
    BUILTIN_MONITOR_CONFIGS
]

monitor_config_lines = {}

for config in monitor_configs:
    if config:
        if not validate_monitor_config_args(config):
            exit(1)

        if config[0] in connected_monitor_names:
            if WHEN_EXTERNAL_CONNECTED_DISABLE_BUILTIN \
                    and ANY_EXTERNAL_MONITORS_CONNECTED \
                    and config[0] == BUILTIN_MONITOR_NAME:
                monitor_config_lines[config[0]] = f'monitor = {config[0]}, disable\n'
            else:
                monitor_config_lines[config[0]] = \
                    f'monitor = {config[0]}, {config[1]}@{config[2]}, {config[3]}, {config[4]}\n'
        else:
            monitor_config_lines[config[0]] = \
                f'#monitor = {config[0]}, {config[1]}@{config[2]}, {config[3]}, {config[4]}\n'

if VERBOSE:
    print('-----------------------------------\nMonitor Configurations:\n')

    for monitor_config in monitor_config_lines:
        print(monitor_config)

    print('-----------------------------------\nWaybar Position:\n')
    print(waybar_position)
    print('-----------------------------------')

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

if DRY_RUN:
    print(f'See generated Waybar config in:\n\t{WAYBAR_CONFIG_TMP_FILE}')
elif VERBOSE:
    with open(WAYBAR_CONFIG_TMP_FILE, 'r') as waybar_config_tmp_file:
        print(waybar_config_tmp_file.read())
else:
    shutil.move(WAYBAR_CONFIG_TMP_FILE, WAYBAR_CONFIG_FILE)

# Hyprland

with open(HYPR_CONFIG_FILE, 'r') as hypr_config_file,\
        open(HYPR_CONFIG_TMP_FILE,'w') as hypr_config_tmp_file:

    for line in hypr_config_file:
        if LEFT_MONITOR_CONFIG_LINE_REGEX and LEFT_MONITOR_CONFIG_LINE_REGEX.match(line):
            hypr_config_tmp_file.write(monitor_config_lines[LEFT_MONITOR_NAME])
        elif CENTER_MONITOR_CONFIG_LINE_REGEX and CENTER_MONITOR_CONFIG_LINE_REGEX.match(line):
            hypr_config_tmp_file.write(monitor_config_lines[CENTER_MONITOR_NAME])
        elif RIGHT_MONITOR_CONFIG_LINE_REGEX and RIGHT_MONITOR_CONFIG_LINE_REGEX.match(line):
            hypr_config_tmp_file.write(monitor_config_lines[RIGHT_MONITOR_NAME])
        elif BUILTIN_MONITOR_CONFIG_LINE_REGEX and BUILTIN_MONITOR_CONFIG_LINE_REGEX.match(line):
            hypr_config_tmp_file.write(monitor_config_lines[BUILTIN_MONITOR_NAME])
        elif WORKSPACE_ONE_THROUGH_FIVE_CONFIG_LINE.match(line):
            hypr_config_tmp_file.write(handle_workspaces_1_through_5_config(line))
        elif WORKSPACE_SIX_THROUGH_SEVEN_CONFIG_LINE.match(line):
            hypr_config_tmp_file.write(handle_workspaces_6_and_7_config(line))
        elif WORKSPACE_EIGHT_THROUGH_TEN_CONFIG_LINE.match(line):
            hypr_config_tmp_file.write(handle_workspaces_8_through_10_config(line))
        elif WORKSPACE_ELEVEN_CONFIG_LINE.match(line):
            print('TODO')
            new_ws11_line = re.sub(r'default:(true|false)',
                                     'default:true' if ANY_EXTERNAL_MONITORS_CONNECTED else 'default:false',
                                   line)
            hypr_config_tmp_file.write(new_ws11_line)
        else:
            hypr_config_tmp_file.write(line)

if DRY_RUN:
    print(f'See generated Hyprland config in:\n\t{HYPR_CONFIG_TMP_FILE}')
elif VERBOSE:
    with open(HYPR_CONFIG_TMP_FILE, 'r') as hypr_config_tmp_file:
        print(hypr_config_tmp_file.read())
else:
    shutil.move(HYPR_CONFIG_TMP_FILE, HYPR_CONFIG_FILE)
