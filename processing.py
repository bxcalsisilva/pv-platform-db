import pandas as pd
import numpy as np


import F_PR2_V1 as Fun
import filt_values as filts


cols = [
    "Numero",
    "Fecha",
    "Tamb",
    "Tmod",
    "Irradiancia",
    "Vdc",
    "Idc",
    "Paparente",
    "Pac",
    "Pdc",
    "Pac*",
    "Pdc*",
    "TONC",
]

calc_cols = [
    "Yr",
    "Ya",
    "Yf",
    "Ya*",
    "Yf*",
    "PR (%)",
    "PR* (%)",
    "Ra (%)",
    "Rs (%)",
    "Rbos (%)",
    "Edc (kWh)",
    "Eac (kWh)",
    "Edc* (kWh)",
    "Eac* (kWh)",
    "TONCm (C)",
    "Tambm (C)",
]


def module_row(loc: str, tech: str, refs):
    module = refs[(refs["Tech"] == tech) & (refs["Location"] == loc)]
    return module


def hourly(st_date, module):
    try:
        module = Fun.Get_Reference(module)
        filt_values = filts.filts_hourly()

        loc = module["Location"].values[0]
        header_df = Fun.Get_Header(loc)

        colz = [
            "Tair (C)",
            f"TC {module.Tech.item()} (C)",
            "G (W/m2)",
            "Vdc (V)",
            "Idc (A)",
            "Sac (VA)",
            "Pac (W)",
            "Pdc (W)",
        ]
        data = pd.DataFrame(columns=["dropable"])
        # Abrir archivos directos
        data_matrix = Fun.Get_Files(st_date, module, None, header_df)

        # for dat in data_matrix:
        #     print(dat)

        # Generar datos directos
        for x in range(len(colz)):
            temp, e, r, f = Fun.Get_data(
                data_matrix, module, colz[x], header_df, filt_values
            )

            if e == 1 or r == 1:
                temp = temp.set_index("time")
                data = data.join(temp[colz[x]], how="outer")
            else:
                data[colz[x]] = np.nan

        data = data.drop("dropable", axis=1)
        # Potencia corregida
        temp, e, r, f = Fun.Get_Power_Corrected(
            data_matrix, module, "Pdc (W)", header_df, filt_values, "Pdc* (W)"
        )
        if e == 1:
            temp = temp.set_index("time")
            data = data.join(temp["Pdc* (W)"], how="outer")
        else:
            data["Pdc* (W)"] = np.nan
        # Potencia AC corregida
        temp, e, r, f = Fun.Get_Power_Corrected(
            data_matrix, module, "Pac (W)", header_df, filt_values, "Pac* (W)"
        )
        if e == 1:
            temp = temp.set_index("time")
            data = data.join(temp["Pac* (W)"], how="outer")
        else:
            data["Pac* (W)"] = np.nan
        # TONC
        temp, e, r, f = Fun.Get_TONC(
            data_matrix, module, header_df, filt_values, "TONC (C)"
        )
        if e == 1:
            temp = temp.set_index("time")
            data = data.join(temp["TONC (C)"], how="outer")
        else:
            data["TONC (C)"] = np.nan

        data = data.reset_index()
        or_cols = ["Index1", "datetime"]
        or_cols = or_cols + data.columns.tolist() + calc_cols
        data["Index1"] = data.index
        or_cols.remove("time")
        data["datetime"] = data["time"].apply(
            lambda x: x.replace(st_date.year, st_date.month, st_date.day)
        )
        data = data.drop("time", axis=1)

        ### VARIABLES CALCULADAS
        calcs = pd.DataFrame(columns=calc_cols, index=data.index)

        calcs.iloc[0, 0] = (
            Fun.Integration(data_matrix, module, "G (W/m2)", header_df, filt_values)[0]
            / 1000
        )
        calcs.iloc[0, 1] = Fun.Integration(
            data_matrix, module, "Pdc (W)", header_df, filt_values
        )[0] / (1000 * module.Pnom.item())
        calcs.iloc[0, 2] = Fun.Integration(
            data_matrix, module, "Pac (W)", header_df, filt_values
        )[0] / (1000 * module.Pnom.item())

        calcs.iloc[0, 3] = Fun.Integration_Tcorrected(
            data_matrix, module, "Pdc (W)", header_df, filt_values, "p"
        )[0] / (1000 * module.Pnom.item())
        calcs.iloc[0, 4] = Fun.Integration_Tcorrected(
            data_matrix, module, "Pac (W)", header_df, filt_values, "p"
        )[0] / (1000 * module.Pnom.item())

        calcs.iloc[0, 5] = calcs.iloc[0, 2] / calcs.iloc[0, 0]
        calcs.iloc[0, 6] = calcs.iloc[0, 4] / calcs.iloc[0, 0]

        calcs.iloc[0, 7] = (
            calcs.iloc[0, 1]
            * (module.Pnom.item())
            / (calcs.iloc[0, 0] * module.Area.item() * module.Mod_num.item())
        )
        calcs.iloc[0, 8] = (
            calcs.iloc[0, 2]
            * (module.Pnom.item())
            / (calcs.iloc[0, 0] * module.Area.item() * module.Mod_num.item())
        )

        calcs.iloc[0, 9] = calcs.iloc[0, 2] / calcs.iloc[0, 1]
        calcs.iloc[0, 10] = calcs.iloc[0, 1] * (module.Pnom.item())
        calcs.iloc[0, 11] = calcs.iloc[0, 2] * (module.Pnom.item())
        calcs.iloc[0, 12] = calcs.iloc[0, 3] * (module.Pnom.item())
        calcs.iloc[0, 13] = calcs.iloc[0, 4] * (module.Pnom.item())
        calcs.iloc[0, 14] = Fun.Prom_TONC(
            data_matrix, module, header_df, filt_values, "p"
        )[0]
        calcs.iloc[0, 15] = Fun.Prom(
            data_matrix, module, "Tair  (C)", header_df, filt_values
        )[0]
        data = data.join(calcs)
        data = data[or_cols]

        print(
            f"{module.State.item()}\\{module.Location.item()}\\{module.Tech.item()}\\{st_date.year}_{st_date.month}_{st_date.day}"
        )
        data.columns = cols + calc_cols

        data = data.iloc[:, list(range(1, 13))]
        return data

    except:
        print(
            f"Failed Hourly {module.State.item()}\\{module.Tech.item()}\\{st_date.year}_{st_date.month}_{st_date.day}"
        )


def _cols_daily(header_df):
    items = []
    for column in header_df:  # Añadimos valores de irradiancia
        items.extend(
            header_df[column][header_df[column].str.startswith("G", na=False)].values
        )

    if len(items) > 0:
        tempi = items.copy()
        for x in range(len(items)):
            s = items[x]
            if s == "G (W/m2)":
                tempi.pop(x)
        items = tempi

    cols = [
        "Fecha",
        "Radiacion",
        "Energia AC",
        "Energia DC",
        "Energia AC*",
        "Energia DC*",
        "Yr",
        "Ya",
        "Yf",
        "Ya*",
        "Yf*",
        "PR",
        "PR*",
        "Ra",
        "Rs",
        "Rbos",
        "TONCm",
        "Tpvm",
        "Tambm",
    ]

    for y in range(len(items)):
        cols.append(f'Rad_{items[y].split("(")[0]}')
    cols2 = ["Fecha"]
    for x in range(len(cols) - 1):
        cols2.append(cols[x + 1])
        cols2.append(f"{cols[x+1]}_Ok")

    return cols2, items


def daily(
    st_date,
    module,
    x=0,
):
    module = Fun.Get_Reference(module)
    loc = module["Location"].values[0]

    header_df = Fun.Get_Header(loc)

    filt_values, alt_filt_values = filts.filts_daily()

    cols2, items = _cols_daily(header_df)

    data = pd.DataFrame(columns=cols2, index=[x])
    try:

        # Abrir archivos directos
        data_matrix = Fun.Get_Files(st_date, module, None, header_df)

        data.iloc[x, 0] = st_date.strftime("%d.%m.%Y")

        ### VARIABLES CALCULADAS
        # Radiacion
        temp = Fun.Integration(data_matrix, module, "G (W/m2)", header_df, filt_values)
        if temp[1] == 1 or temp[2] == 1:
            data.iloc[x, 1] = temp[0] / 1000
            data.iloc[x, 2] = "Yes"
        else:
            data.iloc[x, 1] = (
                Fun.Integration(
                    data_matrix, module, "G (W/m2)", header_df, alt_filt_values
                )[0]
                / 1000
            )
            data.iloc[x, 2] = "No"

        # En AC
        temp = Fun.Integration(data_matrix, module, "Pac (W)", header_df, filt_values)
        if temp[1] == 1 or temp[2] == 1:
            data.iloc[x, 3] = temp[0] / (1000)
            data.iloc[x, 4] = "Yes"
        else:
            data.iloc[x, 3] = Fun.Integration(
                data_matrix, module, "Pac (W)", header_df, alt_filt_values
            )[0] / (1000)
            data.iloc[x, 4] = "No"
        # En DC
        temp = Fun.Integration(data_matrix, module, "Pdc (W)", header_df, filt_values)
        if temp[1] == 1 or temp[2] == 1:
            data.iloc[x, 5] = temp[0] / (1000)
            data.iloc[x, 6] = "Yes"
        else:
            data.iloc[x, 5] = Fun.Integration(
                data_matrix, module, "Pdc (W)", header_df, alt_filt_values
            )[0] / (1000)
            data.iloc[x, 6] = "No"
        # En AC*
        temp = Fun.Integration_Tcorrected(
            data_matrix, module, "Pac (W)", header_df, filt_values, "p"
        )
        if temp[1] == 1 or temp[2] == 1:
            data.iloc[x, 7] = temp[0] / (1000)
            data.iloc[x, 8] = "Yes"
        else:
            data.iloc[x, 7] = Fun.Integration_Tcorrected(
                data_matrix, module, "Pac (W)", header_df, alt_filt_values, "p"
            )[0] / (1000)
            data.iloc[x, 8] = "No"
        # En DC*
        temp = Fun.Integration_Tcorrected(
            data_matrix, module, "Pdc (W)", header_df, filt_values, "p"
        )
        if temp[1] == 1 or temp[2] == 1:
            data.iloc[x, 9] = temp[0] / (1000)
            data.iloc[x, 10] = "Yes"
        else:
            data.iloc[x, 9] = Fun.Integration_Tcorrected(
                data_matrix, module, "Pdc (W)", header_df, alt_filt_values, "p"
            )[0] / (1000)
            data.iloc[x, 10] = "No"
        # Yield referencial
        data.iloc[x, 11] = data.iloc[x, 1]
        data.iloc[x, 12] = data.iloc[x, 2]
        # Y AC
        data.iloc[x, 13] = data.iloc[x, 3] / (module.Pnom.item())
        data.iloc[x, 14] = data.iloc[x, 4]
        # Y DC
        data.iloc[x, 15] = data.iloc[x, 5] / (module.Pnom.item())
        data.iloc[x, 16] = data.iloc[x, 6]
        # Y AC*
        data.iloc[x, 17] = data.iloc[x, 7] / (module.Pnom.item())
        data.iloc[x, 18] = data.iloc[x, 8]
        # Y DC*
        data.iloc[x, 19] = data.iloc[x, 9] / (module.Pnom.item())
        data.iloc[x, 20] = data.iloc[x, 10]
        # PR
        data.iloc[x, 21] = data.iloc[x, 13] / data.iloc[x, 11]
        if data.iloc[x, 14] == "No" or data.iloc[x, 12] == "No":
            data.iloc[x, 22] = "No"
        else:
            data.iloc[x, 22] = "Yes"
        # PR*
        data.iloc[x, 23] = data.iloc[x, 17] / data.iloc[x, 11]
        if data.iloc[x, 18] == "No" or data.iloc[x, 12] == "No":
            data.iloc[x, 24] = "No"
        else:
            data.iloc[x, 24] = "Yes"
        # Ra
        data.iloc[x, 25] = (
            data.iloc[x, 5]
            * 100
            / (data.iloc[x, 1] * module.Area.item() * module.Mod_num.item())
        )
        if data.iloc[x, 6] == "No" or data.iloc[x, 2] == "No":
            data.iloc[x, 26] = "No"
        else:
            data.iloc[x, 26] = "Yes"
        # Rs
        data.iloc[x, 27] = (
            data.iloc[x, 3]
            * 100
            / (data.iloc[x, 1] * module.Area.item() * module.Mod_num.item())
        )
        if data.iloc[x, 4] == "No" or data.iloc[x, 2] == "No":
            data.iloc[x, 28] = "No"
        else:
            data.iloc[x, 28] = "Yes"
        # Rbos
        data.iloc[x, 29] = data.iloc[x, 3] * 100 / data.iloc[x, 5]
        if data.iloc[x, 4] == "No" or data.iloc[x, 6] == "No":
            data.iloc[x, 30] = "No"
        else:
            data.iloc[x, 30] = "Yes"
        # TONCm
        temp = Fun.Prom_TONC(data_matrix, module, header_df, filt_values, "p")
        if temp[1] == 1:
            data.iloc[x, 31] = temp[0]
            data.iloc[x, 32] = "Yes"
        else:
            data.iloc[x, 31] = Fun.Prom_TONC(
                data_matrix, module, header_df, alt_filt_values, "p"
            )[0]
            data.iloc[x, 32] = "No"
        # Tpvm
        temp = Fun.Prom(
            data_matrix,
            module,
            f"TC {module.Tech.item()} (C)",
            header_df,
            filt_values,
        )
        if temp[1] == 1:
            data.iloc[x, 33] = temp[0]
            data.iloc[x, 34] = "Yes"
        else:
            data.iloc[x, 33] = Fun.Prom(
                data_matrix,
                module,
                f"TC {module.Tech.item()} (C)",
                header_df,
                alt_filt_values,
            )[0]
            data.iloc[x, 34] = "No"
        # Tambm
        temp = Fun.Prom(data_matrix, module, "Tair (C)", header_df, filt_values)
        if temp[1] == 1:
            data.iloc[x, 35] = temp[0]
            data.iloc[x, 36] = "Yes"
        else:
            data.iloc[x, 35] = Fun.Prom(
                data_matrix, module, "Tair  (C)", header_df, alt_filt_values
            )[0]
            data.iloc[x, 36] = "No"
        for y in range(len(items)):
            temp = Fun.Integration(
                data_matrix, module, items[y], header_df, filt_values
            )
            if temp[1] == 1:
                data.iloc[x, 35 + 2 + 2 * y] = temp[0] / 1000.00
                data.iloc[x, 36 + 2 + 2 * y] = "Yes"
            else:
                data.iloc[x, 35 + 2 + 2 * y] = (
                    Fun.Prom(data_matrix, module, items[y], header_df, alt_filt_values)[
                        0
                    ]
                    / 1000.00
                )
                data.iloc[x, 36 + 2 + 2 * y] = "No"

        # print(f"{st_date.day}.{st_date.month}.{st_date.year} {module.Tech.item()}")

        data = data.iloc[[0], list(range(1, 31))]
        return data
    except:
        print(
            f"Failed Daily {st_date.day}.{st_date.month}.{st_date.year} {module.Tech.item()}"
        )
