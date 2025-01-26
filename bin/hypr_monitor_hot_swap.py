#!/usr/bin/env python

# TODO: Continue live use of this for extended testing. When a monitor is plugged/unplugged, and the config is
#       updated based on that, Hyprland gets temporarily confused about which workspace is on wich monitor.
#       From initial testing, Hyprland does sort it out and get the workspaces right based on the new config,
#       but only after switching through the workspaces. I think I can live with it, and there is not likely
#       anything I can do about it anyway. The config is set up correctly by these scripts, it just takes
#       Hyprland a bit to sort out the new workspace locations based on the newly connected/disconnected
#       monitor(s).
#       UPDATE: Switching to the first workspace that should be on each monitor causes Hyprland to correct
#               the workspace to monitor mapping based on the changes to the config file after a hot swap
#               is triggered by connecting or disconnecting an external monitor.

import argparse
import os
import subprocess

from time import sleep
from signal import SIGKILL

import set_hypr_monitor_config

from hypr_monitor_config import (
    HyprMonitor,
    HyprMonitorConfig
)

PIDOF_COMMAND = 'pidof'
WAYBAR_PROCESS_NAME = 'waybar'
WAYBAR_COMMAND = 'waybar'
MONITOR_CHECK_INTERVAL_SECONDS = 2

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

    LEFT_MONITOR_CONFIGS = cli_args.left_monitor
    CENTER_MONITOR_CONFIGS = cli_args.center_monitor
    RIGHT_MONITOR_CONFIGS = cli_args.right_monitor
    BUILTIN_MONITOR_CONFIGS = cli_args.builtin_monitor

    for config in [cli_args.left_monitor, cli_args.center_monitor, cli_args.right_monitor,
                   cli_args.builtin_monitor]:
        if config and not HyprMonitorConfig.validate_monitor_config_args(config):
            exit(1)

    hypr_monitor_config = HyprMonitorConfig(
            HyprMonitor(
                    LEFT_MONITOR_CONFIGS[0],
                    LEFT_MONITOR_CONFIGS[1],
                    LEFT_MONITOR_CONFIGS[2],
                    LEFT_MONITOR_CONFIGS[3],
                    LEFT_MONITOR_CONFIGS[4]
                ) if LEFT_MONITOR_CONFIGS else None,
            HyprMonitor(
                    CENTER_MONITOR_CONFIGS[0],
                    CENTER_MONITOR_CONFIGS[1],
                    CENTER_MONITOR_CONFIGS[2],
                    CENTER_MONITOR_CONFIGS[3],
                    CENTER_MONITOR_CONFIGS[4]
                ) if CENTER_MONITOR_CONFIGS else None,
            HyprMonitor(
                    RIGHT_MONITOR_CONFIGS[0],
                    RIGHT_MONITOR_CONFIGS[1],
                    RIGHT_MONITOR_CONFIGS[2],
                    RIGHT_MONITOR_CONFIGS[3],
                    RIGHT_MONITOR_CONFIGS[4]
                ) if RIGHT_MONITOR_CONFIGS else None,
            HyprMonitor(
                    BUILTIN_MONITOR_CONFIGS[0],
                    BUILTIN_MONITOR_CONFIGS[1],
                    BUILTIN_MONITOR_CONFIGS[2],
                    BUILTIN_MONITOR_CONFIGS[3],
                    BUILTIN_MONITOR_CONFIGS[4]
                ) if BUILTIN_MONITOR_CONFIGS else None,
            cli_args.secondary_monitor,
            cli_args.when_external_connected_disable_builtin
        )

    set_hypr_monitor_config.run(secondary_monitor=cli_args.secondary_monitor,
                                dry_run=cli_args.dry_run,
                                verbose=cli_args.verbose,
                                hypr_monitor_config=hypr_monitor_config)

    while True:
        sleep(MONITOR_CHECK_INTERVAL_SECONDS)

        if hypr_monitor_config.any_monitor_connection_changes():

            if LEFT_MONITOR_CONFIGS:
                hypr_monitor_config.left_monitor.position_coordinate = LEFT_MONITOR_CONFIGS[3]

            if CENTER_MONITOR_CONFIGS:
                hypr_monitor_config.center_monitor.position_coordinate = CENTER_MONITOR_CONFIGS[3]

            if RIGHT_MONITOR_CONFIGS:
                hypr_monitor_config.right_monitor.position_coordinate = RIGHT_MONITOR_CONFIGS[3]

            if BUILTIN_MONITOR_CONFIGS:
                hypr_monitor_config.builtin_monitor.position_coordinate = BUILTIN_MONITOR_CONFIGS[3]

            set_hypr_monitor_config.run(secondary_monitor=cli_args.secondary_monitor,
                                        dry_run=cli_args.dry_run,
                                        verbose=cli_args.verbose,
                                        hypr_monitor_config=hypr_monitor_config)
