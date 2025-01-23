import re
import sys
from pathlib import Path

WAYBAR_OUTPUT_START = '    "output": ["'
WAYBAR_OUTPUT_END = '", ],\n'

RESOLUTION_REGEX = re.compile('^[0-9]{4}x[0-9]{3,4}$')
REFRESH_RATE_REGEX = re.compile('^[0-9]{2,3}$')
POSITION_COORDINATE_REGEX = re.compile('^[0-9]{1,4}x0$')
SCALING_REGEX = re.compile('^[0-9]$')

DRM_DIR = '/sys/class/drm'
STATUS_FILE = 'status'
MONITOR_DIR_REGEX = re.compile(f'^{DRM_DIR}/card[0-9]-\\S+$')
CONNECTED_STATUS = 'connected'


class HyprMonitor(object):

    _connected: bool
    _disabled: bool
    _monitor_name: str
    _resolution: str
    _refresh_rate: int
    _position_coordinate: str
    _scaling: int


    def __init__(self, monitor_name: str, resolution: str, refresh_rate: int,
                 position_coordinate: str, scaling: int):
        self._connected = False
        self._disabled = False
        self._monitor_name = monitor_name
        self._resolution = resolution
        self._refresh_rate = refresh_rate
        self._position_coordinate = position_coordinate
        self._scaling = scaling


    def __repr__(self):
        if self._disabled:
            hypr_monitor_config = f'monitor = {self._monitor_name}, disable\n'
        else:
            if self._connected:
                hypr_monitor_config = (f'monitor = {self._monitor_name}, '
                                           + f'{self._resolution}@{self._refresh_rate}, '
                                           + f'{self._position_coordinate}, {self._scaling}\n')
            else:
                hypr_monitor_config = (f'#monitor = {self._monitor_name}, '
                                       + f'{self._resolution}@{self._refresh_rate}, '
                                       + f'{self._position_coordinate}, {self._scaling}\n')

        return hypr_monitor_config


    @property
    def connected(self):
        return self._connected


    @connected.setter
    def connected(self, connected: bool):
        self._connected = connected


    @property
    def disabled(self):
        return self._disabled


    @disabled.setter
    def disabled(self, disabled: bool):
        self._disabled = disabled


    @property
    def monitor_name(self):
        return self._monitor_name


    @monitor_name.setter
    def monitor_name(self, monitor_name: str):
        self._monitor_name = monitor_name


    @property
    def resolution(self):
        return self._resolution


    @resolution.setter
    def resolution(self, resolution: str):
        self._resolution = resolution


    @property
    def refresh_rate(self):
        return self._refresh_rate


    @refresh_rate.setter
    def refresh_rate(self, refresh_rate: int):
        self._refresh_rate = refresh_rate


    @property
    def position_coordinate(self):
        return self._position_coordinate


    @position_coordinate.setter
    def position_coordinate(self, position_coordinate: str):
        self._position_coordinate = position_coordinate


    @property
    def scaling(self):
        return self._scaling


    @scaling.setter
    def scaling(self, scaling: int):
        self._scaling = scaling


class HyprMonitorConfig(object):

    _left_monitor: HyprMonitor
    _center_monitor: HyprMonitor
    _right_monitor: HyprMonitor
    _builtin_monitor: HyprMonitor
    _when_external_connected_disable_builtin: bool
    _secondary_monitor_left: bool
    _secondary_monitor_right: bool
    _monitor_names: list[str]
    _monitors: list[HyprMonitor]
    _waybar_position: str


    def __init__(self, left_monitor: HyprMonitor = None, center_monitor: HyprMonitor = None,
                 right_monitor: HyprMonitor = None, builtin_monitor: HyprMonitor = None,
                 secondary_monitor: str = 'l', when_external_connected_disable_builtin: bool = False):
        self._left_monitor = left_monitor
        self._center_monitor = center_monitor
        self._right_monitor = right_monitor
        self._builtin_monitor = builtin_monitor
        self._secondary_monitor_left = secondary_monitor == 'l'
        self._secondary_monitor_right = secondary_monitor == 'r'
        self._when_external_connected_disable_builtin = when_external_connected_disable_builtin

        monitors = [
            left_monitor,
            center_monitor,
            right_monitor,
            builtin_monitor
        ]

        self._monitor_names = [monitor.monitor_name for monitor in monitors if monitor]
        self._monitors = [monitor for monitor in monitors if monitor]


    @property
    def left_monitor(self):
        return self._left_monitor


    @property
    def center_monitor(self):
        return self._center_monitor


    @property
    def right_monitor(self):
        return self._right_monitor


    @property
    def builtin_monitor(self):
        return self._builtin_monitor


    @property
    def when_external_connected_disable_builtin(self):
        return self._when_external_connected_disable_builtin


    @property
    def secondary_monitor_left(self):
        return self._secondary_monitor_left


    @property
    def secondary_monitor_right(self):
        return self._secondary_monitor_right


    @property
    def monitor_names(self):
        return self._monitor_names


    @property
    def monitors(self):
        return self._monitors


    @property
    def waybar_position(self):
        return self._waybar_position


    def three_monitors_connected(self):
        return self._left_monitor.connected \
            and self._center_monitor.connected \
            and self._right_monitor.connected


    def no_external_monitors_connected(self):
        return not self._left_monitor.connected \
            and not self._center_monitor.connected \
            and not self._right_monitor.connected


    def any_external_monitors_connected(self):
        return self._left_monitor.connected \
            or self._center_monitor.connected \
            or self._right_monitor.connected


    def only_left_and_center_monitors_connected(self):
        return self._left_monitor.connected \
            and self._center_monitor.connected \
            and not self._right_monitor.connected


    def only_left_and_right_monitors_connected(self):
        return self._left_monitor.connected \
            and not self._center_monitor.connected \
            and self._right_monitor.connected


    def only_center_and_right_monitors_connected(self):
        return not self._left_monitor.connected \
            and self._center_monitor.connected \
            and self._right_monitor.connected


    def only_left_monitor_connected(self):
        return self._left_monitor.connected \
            and not self._center_monitor.connected \
            and not self._right_monitor.connected


    def only_center_monitor_connected(self):
        return not self._left_monitor.connected \
            and self._center_monitor.connected \
            and not self._right_monitor.connected


    def only_right_monitor_connected(self):
        return not self._left_monitor.connected \
            and not self._center_monitor.connected \
            and self._right_monitor.connected


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
                            monitor_name: str, workspace_config_line: str) -> str:
        first_workspace_regex = re.compile(f'^workspace\\s*=\\s*{first_workspace}.*$')

        new_config_line = re.sub(
            rf'({'|'.join(self._monitor_names)})',
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
                or (self.only_left_and_center_monitors_connected() and self._secondary_monitor_left) \
                or (self.only_center_and_right_monitors_connected() and self._secondary_monitor_right) \
                or self.only_center_monitor_connected():
            monitor = self._center_monitor.monitor_name
        elif ((self.only_left_and_center_monitors_connected() or self.only_left_and_right_monitors_connected())
              and self._secondary_monitor_right) \
                or self.only_left_monitor_connected():
            monitor = self._left_monitor.monitor_name
        elif ((self.only_center_and_right_monitors_connected() or self.only_left_and_right_monitors_connected())
              and self._secondary_monitor_left) \
                or self.only_right_monitor_connected():
            monitor = self._right_monitor.monitor_name
        else:
            monitor = self._builtin_monitor.monitor_name

        return self.get_new_config_line(1, True, monitor, workspace_config_line)


    def handle_workspaces_6_and_7_config(self, workspace_config_line: str) -> str:

        if self.three_monitors_connected() or self.only_left_monitor_connected():
            monitor = self._left_monitor.monitor_name
        elif (self.only_left_and_center_monitors_connected() and self._secondary_monitor_left) \
                or (self.only_center_and_right_monitors_connected() and self._secondary_monitor_right) \
                or self.only_center_monitor_connected():
            monitor = self._center_monitor.monitor_name
        elif ((self.only_left_and_right_monitors_connected() or self.only_center_and_right_monitors_connected())
              and self._secondary_monitor_left) \
                or self.only_right_monitor_connected:
            monitor = self._right_monitor.monitor_name
        elif (self.only_left_and_right_monitors_connected() or self.only_left_and_center_monitors_connected()) \
                and self._secondary_monitor_right:
            monitor = self._left_monitor.monitor_name
        else:
            monitor = self._builtin_monitor.monitor_name

        return self.get_new_config_line(6, self.three_monitors_connected(), monitor,
                                        workspace_config_line)


    def handle_workspaces_8_through_10_config(self, workspace_config_line: str) -> str:

        if self.three_monitors_connected() \
                or ((self.only_left_and_right_monitors_connected() or self.only_center_and_right_monitors_connected())
                    and self._secondary_monitor_right) \
                or self.only_right_monitor_connected():
            monitor = self._right_monitor.monitor_name
        elif ((self.only_left_and_right_monitors_connected() or self.only_left_and_center_monitors_connected())
              and self._secondary_monitor_left) \
                or self.only_left_monitor_connected():
            monitor = self._left_monitor.monitor_name
        elif (self.only_left_and_center_monitors_connected() and self._secondary_monitor_right) \
                or (self.only_center_and_right_monitors_connected() and self._secondary_monitor_left) \
                or self.only_center_monitor_connected():
            monitor = self._center_monitor.monitor_name
        else:
            monitor = self._builtin_monitor.monitor_name

        at_least_two_monitors_connected = self.only_left_and_center_monitors_connected() \
                                          or self.only_left_and_right_monitors_connected() \
                                          or self.only_center_and_right_monitors_connected() \
                                          or self.three_monitors_connected()

        return self.get_new_config_line(8, at_least_two_monitors_connected, monitor,
                                        workspace_config_line)


    def set_connected_monitor_configs(self) -> list[str]:
        builtin_monitor_dir_regex = re.compile(f'^\\S+{self._builtin_monitor.monitor_name}$') \
            if self._builtin_monitor else None

        left_monitor_dir_regex = re.compile(f'^\\S+{self._left_monitor.monitor_name}$') \
            if self._left_monitor else None

        center_monitor_dir_regex = re.compile(f'^\\S+{self._center_monitor.monitor_name}$') \
            if self._center_monitor else None

        right_monitor_dir_regex = re.compile(f'^\\S+{self._right_monitor.monitor_name}$') \
            if self._right_monitor else None

        drm_path = Path(DRM_DIR)

        monitor_dirs = [
            str(dir_name) for dir_name in drm_path.iterdir()
            if dir_name.is_dir() and MONITOR_DIR_REGEX.match(str(dir_name))
        ]

        for monitor_dir in monitor_dirs:

            with open(f'{monitor_dir}/{STATUS_FILE}', 'r') as file:
                monitor_status = file.read().strip()

                # NOTE: Often, the name assigned to the laptop's builtin monitor will be a superset of one
                #       or more of the names assigned to external monitors, so checking it first here to
                #       avoid a false match.

                if builtin_monitor_dir_regex and builtin_monitor_dir_regex.match(monitor_dir):
                    self._builtin_monitor.connected = monitor_status == CONNECTED_STATUS
                elif left_monitor_dir_regex and left_monitor_dir_regex.match(monitor_dir):
                    self._left_monitor.connected = monitor_status == CONNECTED_STATUS
                elif center_monitor_dir_regex and center_monitor_dir_regex.match(monitor_dir):
                    self._center_monitor.connected = monitor_status == CONNECTED_STATUS
                elif right_monitor_dir_regex and right_monitor_dir_regex.match(monitor_dir):
                    self._right_monitor.connected = monitor_status == CONNECTED_STATUS

        if self._when_external_connected_disable_builtin and self.any_external_monitors_connected():
            self._builtin_monitor.disabled = True

        self.set_monitor_position_coordinates()

        return [monitor.monitor_name for monitor in self.monitors if monitor.connected]


    def set_monitor_position_coordinates(self):

        # Alter monitors' start position coordinates with respect to which monitors are actually
        # connected, and set up config file line for specifying which monitor the Waybar should display on.

        if self.three_monitors_connected():
            self._waybar_position = f'{WAYBAR_OUTPUT_START}{self._center_monitor.monitor_name}{WAYBAR_OUTPUT_END}'
        elif self.only_center_and_right_monitors_connected():
            self._builtin_monitor.position_coordinate = self._right_monitor.position_coordinate
            self._right_monitor.position_coordinate = self._center_monitor.position_coordinate
            self._center_monitor.position_coordinate = self._left_monitor.position_coordinate

            if self._secondary_monitor_left:
                self._waybar_position = f'{WAYBAR_OUTPUT_START}{self._right_monitor.monitor_name}{WAYBAR_OUTPUT_END}'
            else:
                self._waybar_position = f'{WAYBAR_OUTPUT_START}{self._center_monitor.monitor_name}{WAYBAR_OUTPUT_END}'
        elif self.only_left_and_right_monitors_connected():
            self._builtin_monitor.position_coordinate = self._right_monitor.position_coordinate
            self._right_monitor.position_coordinate = self._center_monitor.position_coordinate

            if self._secondary_monitor_left:
                self._waybar_position = f'{WAYBAR_OUTPUT_START}{self._right_monitor.monitor_name}{WAYBAR_OUTPUT_END}'
            else:
                self._waybar_position = f'{WAYBAR_OUTPUT_START}{self._left_monitor.monitor_name}{WAYBAR_OUTPUT_END}'
        elif self.only_left_and_center_monitors_connected():
            self._builtin_monitor.position_coordinate = self._right_monitor.position_coordinate

            if self._secondary_monitor_left:
                self._waybar_position = f'{WAYBAR_OUTPUT_START}{self._center_monitor.monitor_name}{WAYBAR_OUTPUT_END}'
            else:
                self._waybar_position = f'{WAYBAR_OUTPUT_START}{self._left_monitor.monitor_name}{WAYBAR_OUTPUT_END}'
        elif self.only_left_monitor_connected():
            self._builtin_monitor.position_coordinate = self._center_monitor.position_coordinate
            self._waybar_position = f'{WAYBAR_OUTPUT_START}{self._left_monitor.monitor_name}{WAYBAR_OUTPUT_END}'
        elif self.only_center_monitor_connected():
            self._builtin_monitor.position_coordinate = self._center_monitor.position_coordinate
            self._center_monitor.position_coordinate = self._left_monitor.position_coordinate
            self._waybar_position = f'{WAYBAR_OUTPUT_START}{self._center_monitor.monitor_name}{WAYBAR_OUTPUT_END}'
        elif self.only_right_monitor_connected():
            self._builtin_monitor.position_coordinate = self._center_monitor.position_coordinate
            self._right_monitor.position_coordinate = self._left_monitor.position_coordinate
            self._waybar_position = f'{WAYBAR_OUTPUT_START}{self._right_monitor.monitor_name}{WAYBAR_OUTPUT_END}'
        elif self.no_external_monitors_connected():
            self._builtin_monitor.position_coordinate = self._left_monitor.position_coordinate
            self._waybar_position = f'{WAYBAR_OUTPUT_START}{self._builtin_monitor.monitor_name}{WAYBAR_OUTPUT_END}'
