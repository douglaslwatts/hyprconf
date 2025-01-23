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

import argparse
import os
import sys
import shutil
import re

from hypr_monitor_config import (
    HyprMonitor,
    HyprMonitorConfig
    )

if __name__ == "__main__":
    HOME_DIR = os.getenv('HOME')
    HYPR_CONFIG_FILE = f'{HOME_DIR}/.config/hypr/hyprland.conf'
    HYPR_CONFIG_FILE_BAK = f'{HOME_DIR}/.config/hypr/hyprland.conf.bak'
    HYPR_CONFIG_TMP_FILE = '/tmp/hypr_config'

    WAYBAR_CONFIG_FILE = f'{HOME_DIR}/.config/waybar/config'
    WAYBAR_CONFIG_FILE_BAK = f'{HOME_DIR}/.config/waybar/config.bak'
    WAYBAR_CONFIG_TMP_FILE = '/tmp/waybar_config'
    WAYBAR_POSITION_REGEX = re.compile('^\\s*"output":\\s*\\[\\S+\\s*],\\s*$')

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

    cli_args = arg_parser.parse_args()

    # If no Hyprland and/or Waybar config backup exists, make them

    if not os.path.isfile(HYPR_CONFIG_FILE):
        if cli_args.verbose:
            print('Error! No hyprland.conf found!', file=sys.stderr)
            exit(1)

    if not os.path.isfile(WAYBAR_CONFIG_FILE):
        if cli_args.verbose:
            print('Error! No Waybar config found!', file=sys.stderr)
            exit(1)

    for config in [cli_args.left_monitor, cli_args.center_monitor, cli_args.right_monitor,
                   cli_args.builtin_monitor]:
        if config and not HyprMonitorConfig.validate_monitor_config_args(config):
                exit(1)

    shutil.copyfile(HYPR_CONFIG_FILE, HYPR_CONFIG_FILE_BAK)
    shutil.copyfile(WAYBAR_CONFIG_FILE, WAYBAR_CONFIG_FILE_BAK)

    LEFT_MONITOR_CONFIGS = cli_args.left_monitor
    CENTER_MONITOR_CONFIGS = cli_args.center_monitor
    RIGHT_MONITOR_CONFIGS = cli_args.right_monitor
    BUILTIN_MONITOR_CONFIGS = cli_args.builtin_monitor
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

    hypr_monitor_config = HyprMonitorConfig(
        HyprMonitor(
            LEFT_MONITOR_CONFIGS[0],
            LEFT_MONITOR_CONFIGS[1],
            LEFT_MONITOR_CONFIGS[2],
            LEFT_MONITOR_CONFIGS[3],
            LEFT_MONITOR_CONFIGS[4]
        ),
        HyprMonitor(
            CENTER_MONITOR_CONFIGS[0],
            CENTER_MONITOR_CONFIGS[1],
            CENTER_MONITOR_CONFIGS[2],
            CENTER_MONITOR_CONFIGS[3],
            CENTER_MONITOR_CONFIGS[4]
        ),
        HyprMonitor(
            RIGHT_MONITOR_CONFIGS[0],
            RIGHT_MONITOR_CONFIGS[1],
            RIGHT_MONITOR_CONFIGS[2],
            RIGHT_MONITOR_CONFIGS[3],
            RIGHT_MONITOR_CONFIGS[4]
        ),
        HyprMonitor(
            BUILTIN_MONITOR_CONFIGS[0],
            BUILTIN_MONITOR_CONFIGS[1],
            BUILTIN_MONITOR_CONFIGS[2],
            BUILTIN_MONITOR_CONFIGS[3],
            BUILTIN_MONITOR_CONFIGS[4]
        ),
        cli_args.secondary_monitor,
        cli_args.when_external_connected_disable_builtin
    )

    ## Gather and setup configs based on the status of connected and disconnected monitor(s) ##

    # Get monitor connection statuses #

    connected_monitor_names = hypr_monitor_config.set_connected_monitor_configs()

    if VERBOSE:
        print(f'Connected monitor names => {connected_monitor_names}')

    if VERBOSE:
        print('-----------------------------------\nMonitor Configurations:\n')

        for monitor in hypr_monitor_config.monitors:
            print(monitor)

        print('-----------------------------------\nWaybar Position:\n')
        print(hypr_monitor_config.waybar_position)
        print('-----------------------------------')

    ############################### End gather and setup configs #######################################

    #################### Write configs to file, or if dry_run, send them to stdout #####################

    # Waybar

    with open(WAYBAR_CONFIG_FILE, 'r') as waybar_config_file, \
            open(WAYBAR_CONFIG_TMP_FILE, 'w') as waybar_config_tmp_file:
        for line in waybar_config_file:
            if WAYBAR_POSITION_REGEX.match(line):
                waybar_config_tmp_file.write(re.sub(WAYBAR_POSITION_REGEX, hypr_monitor_config.waybar_position, line))
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

    with open(HYPR_CONFIG_FILE, 'r') as hypr_config_file, \
            open(HYPR_CONFIG_TMP_FILE,'w') as hypr_config_tmp_file:

        for line in hypr_config_file:
            if LEFT_MONITOR_CONFIG_LINE_REGEX and LEFT_MONITOR_CONFIG_LINE_REGEX.match(line):
                hypr_config_tmp_file.write(repr(hypr_monitor_config.left_monitor))
            elif CENTER_MONITOR_CONFIG_LINE_REGEX and CENTER_MONITOR_CONFIG_LINE_REGEX.match(line):
                hypr_config_tmp_file.write(repr(hypr_monitor_config.center_monitor))
            elif RIGHT_MONITOR_CONFIG_LINE_REGEX and RIGHT_MONITOR_CONFIG_LINE_REGEX.match(line):
                hypr_config_tmp_file.write(repr(hypr_monitor_config.right_monitor))
            elif BUILTIN_MONITOR_CONFIG_LINE_REGEX and BUILTIN_MONITOR_CONFIG_LINE_REGEX.match(line):
                hypr_config_tmp_file.write(repr(hypr_monitor_config.builtin_monitor))
            elif WORKSPACE_ONE_THROUGH_FIVE_CONFIG_LINE.match(line):
                hypr_config_tmp_file.write(hypr_monitor_config.handle_workspaces_1_through_5_config(line))
            elif WORKSPACE_SIX_THROUGH_SEVEN_CONFIG_LINE.match(line):
                hypr_config_tmp_file.write(hypr_monitor_config.handle_workspaces_6_and_7_config(line))
            elif WORKSPACE_EIGHT_THROUGH_TEN_CONFIG_LINE.match(line):
                hypr_config_tmp_file.write(hypr_monitor_config.handle_workspaces_8_through_10_config(line))
            elif WORKSPACE_ELEVEN_CONFIG_LINE.match(line):
                new_ws11_line = re.sub(r'default:(true|false)',
                                       'default:true'
                                               if hypr_monitor_config.any_external_monitors_connected()
                                               else 'default:false',
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
