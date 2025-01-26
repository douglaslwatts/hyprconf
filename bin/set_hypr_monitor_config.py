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

HOME_DIR = os.getenv('HOME')
HYPR_CONFIG_FILE = f'{HOME_DIR}/.config/hypr/hyprland.conf'
HYPR_CONFIG_FILE_BAK = f'{HOME_DIR}/.config/hypr/hyprland.conf.bak'
HYPR_CONFIG_TMP_FILE = '/tmp/hypr_config'

WAYBAR_CONFIG_FILE = f'{HOME_DIR}/.config/waybar/config'
WAYBAR_CONFIG_FILE_BAK = f'{HOME_DIR}/.config/waybar/config.bak'
WAYBAR_CONFIG_TMP_FILE = '/tmp/waybar_config'
WAYBAR_POSITION_REGEX = re.compile('^\\s*"output":\\s*\\[\\S+\\s*],\\s*$')


def run(left_monitor_configs: list = None, center_monitor_configs: list = None,
        right_monitor_configs: list = None, builtin_monitor_configs: list = None,
        secondary_monitor: str = 'l', when_external_connected_disable_builtin: bool = False,
        dry_run: bool = False, verbose: bool = False, hypr_monitor_config: HyprMonitorConfig = None):

    shutil.copyfile(HYPR_CONFIG_FILE, HYPR_CONFIG_FILE_BAK)
    shutil.copyfile(WAYBAR_CONFIG_FILE, WAYBAR_CONFIG_FILE_BAK)

    if hypr_monitor_config:
        left_monitor_name = hypr_monitor_config.left_monitor.monitor_name \
            if hypr_monitor_config.left_monitor else None
        center_monitor_name = hypr_monitor_config.center_monitor.monitor_name \
            if hypr_monitor_config.center_monitor else None
        right_monitor_name = hypr_monitor_config.right_monitor.monitor_name \
            if hypr_monitor_config.right_monitor else None
        builtin_monitor_name = hypr_monitor_config.builtin_monitor.monitor_name \
            if hypr_monitor_config.builtin_monitor else None
    else:
        left_monitor_name = left_monitor_configs[0] if left_monitor_configs else None
        center_monitor_name = center_monitor_configs[0] if center_monitor_configs else None
        right_monitor_name = right_monitor_configs[0] if right_monitor_configs else None
        builtin_monitor_name = builtin_monitor_configs[0] if builtin_monitor_configs else None

    left_monitor_config_line_regex = re.compile(f'^(#)?monitor\\s*=\\s*{left_monitor_name}.*$') \
        if left_monitor_name else None

    center_monitor_config_line_regex = re.compile(f'^(#)?monitor\\s*=\\s*{center_monitor_name}.*$') \
        if center_monitor_name else None

    right_monitor_config_line_regex = re.compile(f'^(#)?monitor\\s*=\\s*{right_monitor_name}.*$') \
        if right_monitor_name else None

    builtin_monitor_config_line_regex = re.compile(f'^(#)?monitor\\s*=\\s*{builtin_monitor_name}.*$') \
        if builtin_monitor_name else None

    workspace_one_through_five_config_line = re.compile('^workspace\\s*=\\s*[1-5],.*$')
    workspace_six_through_seven_config_line = re.compile('^workspace\\s*=\\s*[6-7],.*$')
    workspace_eight_through_ten_config_line = re.compile('^workspace\\s*=\\s*([8-9]|10),.*$')
    workspace_eleven_config_line = re.compile('^workspace\\s*=\\s*11,.*$')

    if not hypr_monitor_config:
        hypr_monitor_config = HyprMonitorConfig(
                HyprMonitor(
                        left_monitor_configs[0],
                        left_monitor_configs[1],
                        left_monitor_configs[2],
                        left_monitor_configs[3],
                        left_monitor_configs[4]
                    ) if left_monitor_configs else None,
                HyprMonitor(
                        center_monitor_configs[0],
                        center_monitor_configs[1],
                        center_monitor_configs[2],
                        center_monitor_configs[3],
                        center_monitor_configs[4]
                    ) if center_monitor_configs else None,
                HyprMonitor(
                        right_monitor_configs[0],
                        right_monitor_configs[1],
                        right_monitor_configs[2],
                        right_monitor_configs[3],
                        right_monitor_configs[4]
                    ) if right_monitor_configs else None,
                HyprMonitor(
                        builtin_monitor_configs[0],
                        builtin_monitor_configs[1],
                        builtin_monitor_configs[2],
                        builtin_monitor_configs[3],
                        builtin_monitor_configs[4]
                    ) if builtin_monitor_configs else None,
                secondary_monitor,
                when_external_connected_disable_builtin
        )

    ## Gather and setup configs based on the status of connected and disconnected monitor(s) ##

    # Get monitor connection statuses #

    connected_monitor_names = hypr_monitor_config.set_connected_monitor_configs()

    if verbose:
        print(f'Connected monitor names => {connected_monitor_names}')

    if verbose:
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

    if dry_run:
        print(f'See generated Waybar config in:\n\t{WAYBAR_CONFIG_TMP_FILE}')
    elif verbose:
        with open(WAYBAR_CONFIG_TMP_FILE, 'r') as waybar_config_tmp_file:
            print(waybar_config_tmp_file.read())
    else:
        shutil.move(WAYBAR_CONFIG_TMP_FILE, WAYBAR_CONFIG_FILE)

    # Hyprland

    with open(HYPR_CONFIG_FILE, 'r') as hypr_config_file, \
            open(HYPR_CONFIG_TMP_FILE,'w') as hypr_config_tmp_file:

        for line in hypr_config_file:
            if left_monitor_config_line_regex and left_monitor_config_line_regex.match(line):
                hypr_config_tmp_file.write(repr(hypr_monitor_config.left_monitor))
            elif center_monitor_config_line_regex and center_monitor_config_line_regex.match(line):
                hypr_config_tmp_file.write(repr(hypr_monitor_config.center_monitor))
            elif right_monitor_config_line_regex and right_monitor_config_line_regex.match(line):
                hypr_config_tmp_file.write(repr(hypr_monitor_config.right_monitor))
            elif builtin_monitor_config_line_regex and builtin_monitor_config_line_regex.match(line):
                hypr_config_tmp_file.write(repr(hypr_monitor_config.builtin_monitor))
            elif workspace_one_through_five_config_line.match(line):
                hypr_config_tmp_file.write(hypr_monitor_config.handle_workspaces_1_through_5_config(line))
            elif workspace_six_through_seven_config_line.match(line):
                hypr_config_tmp_file.write(hypr_monitor_config.handle_workspaces_6_and_7_config(line))
            elif workspace_eight_through_ten_config_line.match(line):
                hypr_config_tmp_file.write(hypr_monitor_config.handle_workspaces_8_through_10_config(line))
            elif workspace_eleven_config_line.match(line):
                new_ws11_line = re.sub(r'default:(true|false)',
                                       'default:true'
                                               if hypr_monitor_config.any_external_monitors_connected()
                                               else 'default:false',
                                       line)
                hypr_config_tmp_file.write(new_ws11_line)
            else:
                hypr_config_tmp_file.write(line)

    if dry_run:
        print(f'See generated Hyprland config in:\n\t{HYPR_CONFIG_TMP_FILE}')
    elif verbose:
        with open(HYPR_CONFIG_TMP_FILE, 'r') as hypr_config_tmp_file:
            print(hypr_config_tmp_file.read())
    else:
        shutil.move(HYPR_CONFIG_TMP_FILE, HYPR_CONFIG_FILE)


if __name__ == "__main__":
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
    [--when-external-connected-disable-builtin]

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

    run(cli_args.left_monitor,
        cli_args.center_monitor,
        cli_args.right_monitor,
        cli_args.builtin_monitor,
        cli_args.secondary_monitor,
        cli_args.when_external_connected_disable_builtin,
        cli_args.dry_run,
        cli_args.verbose)
