import os
import re
import sys

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


class HyprMonitor(object):

    connected_status: str
    disabled: bool
    monitor_name: str
    resolution: str
    refresh_rate: int
    position_coordinate: str
    scaling: int


    def __init__(self, monitor_name: str, resolution: str, refresh_rate: int,
                 position_coordinate: str, scaling: int):
        self.connected_status = 'disconnected'
        self.disabled = False
        self.monitor_name = monitor_name
        self.resolution = resolution
        self.refresh_rate = refresh_rate
        self.position_coordinate = position_coordinate
        self.scaling = scaling


    def __repr__(self):
        if self.disabled:
            hypr_monitor_config = f'monitor = {self.monitor_name}, disable\n'
        else:
            hypr_monitor_config = (f'monitor = {self.monitor_name}, '
                                       + f'{self.resolution}@{self.refresh_rate}, '
                                       + f'{self.position_coordinate}, {self.scaling}\n')

        return hypr_monitor_config


    @property
    def connected_status(self):
        return self.connected_status


    @connected_status.setter
    def connected_status(self, connected_status: str):
        self.connected_status = connected_status


    def is_connected(self):
        return self.connected_status == 'connected'


    @property
    def disabled(self):
        return self.disabled


    @disabled.setter
    def disabled(self, disabled: bool):
        self.disabled = disabled


    @property
    def monitor_name(self):
        return self.monitor_name


    @monitor_name.setter
    def monitor_name(self, monitor_name: str):
        self.monitor_name = monitor_name


    @property
    def resolution(self):
        return self.resolution


    @resolution.setter
    def resolution(self, resolution: str):
        self.resolution = resolution


    @property
    def refresh_rate(self):
        return self.refresh_rate


    @refresh_rate.setter
    def refresh_rate(self, refresh_rate: int):
        self.refresh_rate = refresh_rate


    @property
    def position_coordinate(self):
        return self.position_coordinate


    @position_coordinate.setter
    def position_coordinate(self, position_coordinate: str):
        self.position_coordinate = position_coordinate


    @property
    def scaling(self):
        return self.scaling


    @scaling.setter
    def scaling(self, scaling: int):
        self.scaling = scaling


class HyprMonitorConfig(object):

    left_monitor: HyprMonitor
    center_monitor: HyprMonitor
    right_monitor: HyprMonitor
    builtin_monitor: HyprMonitor
    secondary_monitor_left: bool
    secondary_monitor_right: bool
    monitor_names: list[str]


    def __init__(self, left_monitor: HyprMonitor = None, center_monitor: HyprMonitor = None,
                 right_monitor: HyprMonitor = None, builtin_monitor: HyprMonitor = None,
                 secondary_monitor: str = 'l'):
        self.left_monitor = left_monitor
        self.center_monitor = center_monitor
        self.right_monitor = right_monitor
        self.builtin_monitor = builtin_monitor
        self.secondary_monitor_left = secondary_monitor == 'l'
        self.secondary_monitor_right = secondary_monitor == 'r'

        monitors = [
            left_monitor,
            center_monitor,
            right_monitor,
            builtin_monitor
        ]

        self.monitor_names = [monitor.monitor_name for monitor in monitors if monitor]


    def three_monitors_connected(self):
        return self.left_monitor.is_connected() \
            and self.center_monitor.is_connected() \
            and self.right_monitor.is_connected()


    def no_external_monitors_connected(self):
        return not self.left_monitor.is_connected() \
            and not self.center_monitor.is_connected() \
            and not self.right_monitor.is_connected()


    def any_external_monitors_connected(self):
        return self.left_monitor.is_connected() \
            or self.center_monitor.is_connected() \
            or self.right_monitor.is_connected()


    def only_left_and_center_monitors_connected(self):
        return self.left_monitor.is_connected() \
            and self.center_monitor.is_connected() \
            and not self.right_monitor.is_connected()


    def only_left_and_right_monitors_connected(self):
        return self.left_monitor.is_connected() \
            and not self.center_monitor.is_connected() \
            and self.right_monitor.is_connected()


    def only_center_and_right_monitors_connected(self):
        return not self.left_monitor.is_connected() \
            and self.center_monitor.is_connected() \
            and self.right_monitor.is_connected()


    def only_left_monitor_connected(self):
        return self.left_monitor.is_connected() \
            and not self.center_monitor.is_connected() \
            and not self.right_monitor.is_connected()


    def only_center_monitor_connected(self):
        return not self.left_monitor.is_connected() \
            and self.center_monitor.is_connected() \
            and not self.right_monitor.is_connected()


    def only_right_monitor_connected(self):
        return not self.left_monitor.is_connected() \
            and not self.center_monitor.is_connected() \
            and self.right_monitor.is_connected()


    @staticmethod
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


    def get_new_config_line(self, first_workspace: int, first_workspace_is_on_new_monitor: bool,
                            monitor_name: str, workspace_config_line: str) -> (
            str):
        first_workspace_regex = re.compile(f'^workspace\\s*=\\s*{first_workspace}.*$')

        new_config_line = re.sub(
            rf'({'|'.join(self.monitor_names)})',
            monitor_name,
            workspace_config_line)

        new_config_line = re.sub(
            r'default:(true|false)',
            'default:true'
            if first_workspace_regex.match(
                workspace_config_line) and first_workspace_is_on_new_monitor
            else 'default:false',
            new_config_line)

        return new_config_line


    def handle_workspaces_1_through_5_config(self, workspace_config_line: str) -> str:

        if self.three_monitors_connected() \
                or (self.only_left_and_center_monitors_connected() and self.secondary_monitor_left) \
                or (self.only_center_and_right_monitors_connected() and self.secondary_monitor_right) \
                or self.only_center_monitor_connected():
            monitor = self.center_monitor.monitor_name
        elif ((self.only_left_and_center_monitors_connected() or self.only_left_and_right_monitors_connected())
              and self.secondary_monitor_right) \
                or self.only_left_monitor_connected():
            monitor = self.left_monitor.monitor_name
        elif ((self.only_center_and_right_monitors_connected() or self.only_left_and_right_monitors_connected())
              and self.secondary_monitor_left) \
                or self.only_right_monitor_connected():
            monitor = self.right_monitor.monitor_name
        else:
            monitor = self.builtin_monitor.monitor_name

        return self.get_new_config_line(1, True, monitor, workspace_config_line)


    def handle_workspaces_6_and_7_config(self, workspace_config_line: str) -> str:

        if self.three_monitors_connected() or self.only_left_monitor_connected():
            monitor = self.left_monitor.monitor_name
        elif (self.only_left_and_center_monitors_connected() and self.secondary_monitor_left) \
                or (self.only_center_and_right_monitors_connected() and self.secondary_monitor_right) \
                or self.only_center_monitor_connected():
            monitor = self.center_monitor.monitor_name
        elif ((self.only_left_and_right_monitors_connected() or self.only_center_and_right_monitors_connected())
              and self.secondary_monitor_left) \
                or self.only_right_monitor_connected:
            monitor = self.right_monitor.monitor_name
        elif (self.only_left_and_right_monitors_connected() or self.only_left_and_center_monitors_connected()) \
                and self.secondary_monitor_right:
            monitor = self.left_monitor.monitor_name
        else:
            monitor = self.builtin_monitor.monitor_name

        return self.get_new_config_line(6, self.three_monitors_connected(), monitor,
                                        workspace_config_line)


    def handle_workspaces_8_through_10_config(self, workspace_config_line: str) -> str:

        if self.three_monitors_connected() \
                or ((self.only_left_and_right_monitors_connected() or self.only_center_and_right_monitors_connected())
                    and self.secondary_monitor_right) \
                or self.only_right_monitor_connected():
            monitor = self.right_monitor.monitor_name
        elif ((self.only_left_and_right_monitors_connected() or self.only_left_and_center_monitors_connected())
              and self.secondary_monitor_left) \
                or self.only_left_monitor_connected():
            monitor = self.left_monitor.monitor_name
        elif (self.only_left_and_center_monitors_connected() and self.secondary_monitor_right) \
                or (self.only_center_and_right_monitors_connected() and self.secondary_monitor_left) \
                or self.only_center_monitor_connected():
            monitor = self.center_monitor.monitor_name
        else:
            monitor = self.builtin_monitor.monitor_name

        at_least_two_monitors_connected = self.only_left_and_center_monitors_connected() \
                                          or self.only_left_and_right_monitors_connected() \
                                          or self.only_center_and_right_monitors_connected() \
                                          or self.three_monitors_connected()

        return self.get_new_config_line(8, at_least_two_monitors_connected, monitor,
                                        workspace_config_line)
