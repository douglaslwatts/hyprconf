BEGIN {
    left_monitor_config = "monitor = "left_monitor", "left_monitor_res_rate", "left_monitor_placement", "left_monitor_scaling;

    center_monitor_config = "monitor = "center_monitor", "center_monitor_res_rate", "center_monitor_placement", "center_monitor_scaling;

    right_monitor_config = "monitor = "right_monitor", "right_monitor_res_rate", "right_monitor_placement", "right_monitor_scaling;

    builtin_monitor_config = "monitor = "builtin_monitor", "builtin_monitor_res_rate", "builtin_monitor_placement", "builtin_monitor_scaling;

    builtin_monitor_off = "monitor = "builtin_monitor", disable";

    left_monitor_connected = match(left_monitor_status, "^connected$");
    center_monitor_connected = match(center_monitor_status, "^connected$");
    right_monitor_connected = match(right_monitor_status, "^connected$");

    three_monitors_connected = left_monitor_connected && center_monitor_connected &&
            right_monitor_connected;

    workspace_defaults = "rounding:true, decorate:false, border:true,"
}

{
    if (match($0, "^(#)?monitor = "left_monitor".*$")) {
        if (match(left_monitor_status, "^connected$")) {
            printf "%s\n", left_monitor_config;
        } else {
            printf "#%s\n", left_monitor_config;
        }
    } else if (match($0, "^(#)?monitor = "center_monitor".*$")) {
        if (match(center_monitor_status, "^connected$")) {
            printf "%s\n", center_monitor_config;
        } else {
            printf "#%s\n", center_monitor_config;
        }
    } else if (match($0, "^(#)?monitor = "right_monitor".*$")) {
        if (match(right_monitor_status, "^connected$")) {
            printf "%s\n", right_monitor_config;
        } else {
            printf "#%s\n", right_monitor_config;
        }
    } else if (match($0, "^(#)?monitor = "builtin_monitor".*$")) {
        if (left_monitor_connected || center_monitor_connected || right_monitor_connected) {
            printf "%s\n", builtin_monitor_off;
        } else {
            printf "%s\n", builtin_monitor_config;
        }
    } else if (match($0, "^workspace = [1-5],.*$")) {

        if (three_monitors_connected ||
            (left_monitor_connected && center_monitor_connected && secondary_left) ||
            (center_monitor_connected && right_monitor_connected && secondary_right) ||
            (center_monitor_connected && !left_monitor_connected && !right_monitor_connected)) {
            if (match($3, "1,")) {
                printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"center_monitor", default:true";
            } else {
                printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"center_monitor", default:false";
            }
        } else if ((left_monitor_connected && center_monitor_connected && secondary_right) ||
                   (left_monitor_connected && right_monitor_connected && secondary_right) ||
                    left_monitor_connected && !center_monitor_connected && !right_monitor_connected) {

            if (match($3, "1,")) {
                printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"left_monitor", default:true";
            } else {
                printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"left_monitor", default:false";
            }
        } else if ((center_monitor_connected && right_monitor_connected && secondary_left) ||
                   (left_monitor_connected && right_monitor_connected && secondary_left) ||
                    right_monitor_connected && !left_monitor_connected && !center_monitor_connected) {

            if (match($3, "1,")) {
                printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"right_monitor", default:true";
            } else {
                printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"right_monitor", default:false";
            }
        } else {

            if (match($3, "1,")) {
                printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"builtin_monitor", default:true";
            } else {
                printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"builtin_monitor", default:false";
            }
        }
    } else if (match($0, "^workspace = [6-7],.*$")) {

        if (three_monitors_connected) {
            if (match($3, "6,")) {
                printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"left_monitor", default:true";
            } else {
                printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"left_monitor", default:false";
            }
        } else if ((left_monitor_connected && center_monitor_connected && secondary_left) ||
                   (center_monitor_connected && right_monitor_connected && secondary_right)) {
            printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"center_monitor", default:false";
        } else if ((left_monitor_connected && right_monitor_connected && secondary_left) ||
                   (center_monitor_connected && right_monitor_connected && secondary_left)) {
            printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"right_monitor", default:false";
        } else if (((left_monitor_connected && right_monitor_connected) ||
                   (left_monitor_connected && center_monitor_connected)) &&
                   secondary_right) {
            printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"left_monitor", default:false";
        } else if (left_monitor_connected) {
            printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"left_monitor", default:false";
        } else if (center_monitor_connected) {
            printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"center_monitor", default:false";
        } else if (right_monitor_connected) {
            printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"right_monitor", default:false";
        } else {
            printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"builtin_monitor", default:false";
        }
    } else if (match($0, "^workspace = [8-9],.*$") || match($0, "^workspace = 10,.*$")) {

        if (three_monitors_connected ||
            (left_monitor_connected && right_monitor_connected && secondary_right) ||
            (center_monitor_connected && right_monitor_connected && secondary_right)) {
            if (match($3, "8,")) {
                printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"right_monitor", default:true";
            } else {
                printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"right_monitor", default:false";
            }
        } else if ((left_monitor_connected && right_monitor_connected && secondary_left) ||
                   (left_monitor_connected && center_monitor_connected && secondary_left)) {
            if (match($3, "8,")) {
                printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"left_monitor", default:true";
            } else {
                printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"left_monitor", default:false";
            }
        } else if ((left_monitor_connected && center_monitor_connected && secondary_right) ||
                   (center_monitor_connected && right_monitor_connected && secondary_left)) {
            if (match($3, "8,")) {
                printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"center_monitor", default:true";
            } else {
                printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"center_monitor", default:false";
            }
        } else if (left_monitor_connected) {
            printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"left_monitor", default:false";
        } else if (center_monitor_connected) {
            printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"center_monitor", default:false";
        } else if (right_monitor_connected) {
            printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"right_monitor", default:false";
        } else {
            printf "%s %s %s %s %s\n", $1, $2, $3, workspace_defaults, "monitor:"builtin_monitor", default:false";
        }
    } else if (match($0, "^workspace = 11,.*$")) {
        if (!left_monitor_connected && !center_monitor_connected && !right_monitor_connected) {
            printf "%s %s %s %s %s %s\n", $1, $2, $3, workspace_defaults, $7, "default:false";
        } else {
            printf "%s %s %s %s %s %s\n", $1, $2, $3, workspace_defaults, $7, "default:true";
        }
    } else {
        printf "%s\n", $0;
    }
}

END {
}
