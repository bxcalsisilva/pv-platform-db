cols_performance = [
    "radiation",
    "e_ac",
    "e_dc",
    "e_ac_t25",
    "e_dc_t25",
    "yield_reference",
    "yield_absolute",
    "yield_final",
    "yield_absolute_t25",
    "yield_final_t25",
    "performance_ratio",
    "performance_ratio_t25",
    "efficiency_array",
    "efficiency_system",
    "efficiency_inverter",
]

cols_reference = [
    "Id",
    "Name",
    "Location",
    "State",
    "Tech",
    "Mod_num",
    "Area",
    "Pnom",
    "Lat",
    "Long",
    "Height",
    "Timezone",
    "Tilt",
    "Azimuth",
    "PowerFactor",
]


def performance_columns():
    columns = []
    for col in cols_performance:
        columns.append(col)
        columns.append(col + "_ok")

    return columns


class SettingsHourly:
    def __init__(self):
        self.initial_names = [
            "datetime",
            "t_amb",
            "t_mod",
            "irr",
            "v_dc",
            "i_dc",
            "p_app",
            "p_ac",
            "p_dc",
            "p_ac_t25",
            "p_dc_t25",
            "t_noct",
        ]
        self.datetime = ["datetime"]
        self.ambients = [
            "t_amb",
            "h_rel",
            "h_abs",
            "w_spd",
            "w_dir",
            "d_air",
            "p_rel",
            "p_abs",
        ]
        self.t_mod = ["t_mod"]
        self.irr = ["irr"]
        self.t_noct = ["t_noct"]
        self.inverters = [
            "v_dc",
            "i_dc",
            "p_app",
            "p_ac",
            "p_dc",
            "p_ac_t25",
            "p_dc_t25",
        ]

        self.names = (
            self.datetime
            + self.ambients
            + self.t_mod
            + self.irr
            + self.t_noct
            + self.inverters
        )


class SettingsDaily:
    def __init__(self):
        self.names_reference = [
            "sys_id",
            "filename",
            "label",
            "city",
            "tech",
            "n_mods",
            "area",
            "p_m",
            "lat",
            "long",
            "alt",
            "tz",
            "tilt",
            "azimuth",
            "gamma",
        ]
