import numpy as np
import pandas as pd
from pandas.core.frame import DataFrame
from scipy import stats
import datetime
from pvlib import location
from pvlib import irradiance
import re
import os.path
import matplotlib.pyplot as plt
from pathlib import Path

from download import DriveDownload
from upload import Upload

## FUNCIONES DE SOPORTE ----------------------------------------------------------------------------------------------------------------------------------------------------------

#
# def save(dir_arch_out, data, name):  # Grabación de una tabla del tipo List
#     dir_arch_out_ar = dir_arch_out.split('\\')
#     dir = ''
#     for x in range(len(dir_arch_out_ar)):
#         dir = dir + dir_arch_out_ar[x] + '/'
#     dir = dir + name
#     data.to_csv(path_or_buf=f'{dir}.csv', index=False)


def m_s(num):
    if num < 10:
        return f"0{num}"
    else:
        return f"{num}"


## FUNCIONES DE FILTRADO Y CORRECCION --------------------------------------------------------------------------------------------------------------------------------------------


def shadow_correction(data, Header, data_matrix, module, header_df, filt_values):
    # Jalar valores de irradiancia
    idata, iexist, ireplaced, ifiltered_points = Get_data(
        data_matrix, module, "G (W/m2)", header_df, filt_values
    )
    if iexist == 1 or ireplaced == 1:
        data2 = data.copy()
        data2["datetime"] = pd.to_datetime(data2["time"], format="%H:%M:%S")
        idata["datetime"] = pd.to_datetime(idata["time"], format="%H:%M:%S")
        data2 = data2.set_index("datetime")
        idata = idata.set_index("datetime")
        t1 = pd.merge(
            data2[Header],
            idata["G (W/m2)"],
            how="outer",
            left_index=True,
            right_index=True,
        )
        t2 = t1.drop(columns=[Header])
        t2 = t2.interpolate()
        t1 = pd.merge(
            data2[Header],
            t2["G (W/m2)"],
            how="inner",
            left_index=True,
            right_index=True,
        )
        t1 = t1.dropna()
        t1 = t1.reset_index()
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            t1["G (W/m2)"], t1[Header]
        )
        t1[f"{Header}_lin"] = t1["G (W/m2)"] * slope + intercept
        t1["dif"] = t1[Header] - t1[f"{Header}_lin"]
        t1[f"{Header}_cor"] = t1[Header]
        t1.loc[t1["dif"] * 100 / t1[f"{Header}_lin"] < -25, f"{Header}_cor"] = t1[
            f"{Header}_lin"
        ]
        t1.loc[t1[f"{Header}_cor"] <= 0, f"{Header}_cor"] = t1[Header]
        return t1[f"{Header}_cor"]
    else:
        return data[Header]


def Filter_and_Reject(data, Header, filt_values, module):
    exist = 1
    in_length = len(data.index)
    # Filtrado de valores mayores a umbral mínimo
    unit = re.search(" (.*)", Header)
    if unit.group(1) == "(W/m2)":  # Para valores de irradiancia
        if filt_values[0][0].get() == 1:
            data = data[data[Header] >= float(filt_values[1][0].get()) * 1000 / 100]
    if unit.group(1) == "(W)":  # Para valores de potencia
        if filt_values[0][0].get() == 1:
            data = data[
                data[Header]
                >= float(filt_values[1][0].get()) * module.Pnom.item() * 1000 / 100
            ]
    # Filtro de horas mayor a umbral
    if filt_values[0][1].get() == 1:
        data = data[data["hours"] >= float(filt_values[1][1].get())]
    # Filtro de horas menor a umbral
    if filt_values[0][2].get() == 1:
        data = data[data["hours"] <= float(filt_values[1][2].get())]
    # Rechazo de día por falta de datos
    if filt_values[0][3].get() == 1:
        data["diff"] = data["hours"].diff()
        if (
            data["diff"].max()
            > (data["hours"].max() - data["hours"].min())
            * float(filt_values[1][3].get())
            / 100
        ):
            exist = 0
        data = data.drop(["diff"], axis=1)
    # Rechazo de día por inicio o fin tardio o temprano
    if filt_values[0][4].get() == 1 and data["hours"].min() > float(
        filt_values[1][4].get()
    ):
        exist = 0
    if filt_values[0][5].get() == 1 and data["hours"].max() < float(
        filt_values[1][5].get()
    ):
        exist = 0
    filtered_points = in_length - len(data.index)
    if filtered_points > 0:
        data = data.reset_index()
    # Agrupación de data
    if filt_values[2][3].get() == 1:
        temp = data[["time"]].copy().diff().min().item()
        temp = int(temp.total_seconds() / 60)
        if temp != int(filt_values[3][1].get()):
            data = data.set_index("time")
            data = data.resample(
                f"{int(filt_values[3][1].get())}T", label="right"
            ).mean()
            data = data.reset_index()
            data["hours"] = pd.to_datetime(data["time"])
            data["hours"] = data["hours"].apply(
                lambda x: x.hour + x.minute / 60 + x.second / 3600
            )
    return data, exist, filtered_points


def STD_Filtering(data, Header, filt_values, module):
    data = data.copy()
    exist = 1
    in_length = len(data.index)
    ## Filtros de la norma IEC-61724-2
    if filt_values[1][6] == "IEC-61724-2":
        unit = re.search(" (.*)", Header)
        if unit.group(1) == "(W/m2)":  # Para valores de irradiancia
            # FALTA DEFINIR TRC
            # data = data[(data[Header] > -6) & (data[Header] < 1500)]
            data["diff"] = data[Header].diff().abs()
            data = data[data["diff"] > 0.0001]
            df2 = data.set_index("datetime")
            df3 = df2.resample("15T", label="right").agg(["mean"])
            df2 = df2.resample("15T").agg(["min", "max", "mean", "std"])
            df2 = df2.reset_index()
            df3 = df3.reset_index()
            df2["datetime_end"] = df3["datetime"]
            # df2['consid'] = df2[Header]['std']*100/df2[Header]['mean']
            dfpo = pd.DataFrame(columns=["datetime", Header])
            for index, row in df2.iterrows():
                temp = data[
                    (data["datetime"] > row["datetime"].item())
                    & (data["datetime"] < row["datetime_end"].item())
                ]
                temp = temp[
                    (temp[Header] > 95 * row[Header]["mean"] / 100)
                    & (temp[Header] < 105 * row[Header]["mean"] / 100)
                ]
                dfpo = dfpo.append(temp)
            dfpo["hours"] = dfpo["datetime"].apply(
                lambda x: x.hour + x.minute / 60 + x.second / 3600
            )
            data = dfpo
        if unit.group(1) == "(C)":  # Para valores de temperatura
            data = data[(data[Header] > -10) & (data[Header] < 50)]
            data["diff"] = data[Header].diff().abs()
            data = data[(data["diff"] > 0.0001) & (data["diff"] < 4)]
        if unit.group(1) == "(m/s)":  # Para valores de velocidad de viento
            data = data[(data[Header] > 0) & (data[Header] < 32)]
            data["diff"] = data[Header].diff().abs()
            data = data[data["diff"] < 10]
        if unit.group(1) == "(W)":  # Para valores de Potencia
            data = data[
                (data[Header] > -0.01 * module.Pnom.item() * 1000)
                & (data[Header] < 1.02 * module.Pnom.item() * 1000)
            ]
            df2 = data.set_index("datetime")
            df3 = df2.resample("15T", label="right").agg(["mean"])
            df2 = df2.resample("15T").agg(["min", "max", "mean", "std"])
            df2 = df2.reset_index()
            df3 = df3.reset_index()
            df2["datetime_end"] = df3["datetime"]
            # df2['consid'] = df2[Header]['std']*100/df2[Header]['mean']
            dfpo = pd.DataFrame(columns=["datetime", Header])
            for index, row in df2.iterrows():
                temp = data[
                    (data["datetime"] > row["datetime"].item())
                    & (data["datetime"] < row["datetime_end"].item())
                ]
                temp = temp[
                    (temp[Header] > 95 * row[Header]["mean"] / 100)
                    & (temp[Header] < 105 * row[Header]["mean"] / 100)
                ]
                dfpo = dfpo.append(temp)
            dfpo["hours"] = dfpo["datetime"].apply(
                lambda x: x.hour + x.minute / 60 + x.second / 3600
            )
            data = dfpo
    ## Filtros de la norma IEC-61724-3
    if filt_values[1][6] == "IEC-61724-3":
        unit = re.search(" (.*)", Header)
        if unit.group(1) == "(W/m2)":  # Para valores de irradiancia
            data = data[(data[Header] > -6) & (data[Header] < 1500)]
            data["diff"] = data[Header].diff().abs()
            data = data[(data["diff"] > 0.0001) & (data["diff"] < 800)]
        if unit.group(1) == "(C)":  # Para valores de temperatura
            data = data[(data[Header] > -30) & (data[Header] < 50)]
            data["diff"] = data[Header].diff().abs()
            data = data[(data["diff"] > 0.0001) & (data["diff"] < 4)]
        if unit.group(1) == "(m/s)":  # Para valores de velocidad de viento
            data = data[(data[Header] > 0) & (data[Header] < 32)]
            data["diff"] = data[Header].diff().abs()
            data = data[data["diff"] < 10]
        if unit.group(1) == "(W)":  # Para valores de Potencia
            data = data[
                (data[Header] > -0.01 * module.Pnom.item() * 1000)
                & (data[Header] < 1.02 * module.Pnom.item() * 1000)
            ]
            data["diff"] = data[Header].diff().abs()
            data = data[data["diff"] < 0.8 * module.Pnom.item() * 1000]
    filtered_points = in_length - len(data.index)
    if filtered_points > 0:
        data = data.reset_index(drop=True)
    return data, exist, filtered_points


def GetObsDF(dataE, obsE, obsH):
    obs = pd.DataFrame(columns=["date", "day", "exist", "replaced", "filtered_points"])
    obs["date"] = dataE["date"]
    obs["day"] = dataE["day"]
    TempE = obsE["exist"].apply(lambda x: True if x == 1 else False)
    TempH = obsH["exist"].apply(lambda x: True if x == 1 else False)
    Temp = TempE & TempH
    obs["exist"] = Temp.apply(lambda x: 1 if True else 0)
    TempE = obsE["replaced"].apply(lambda x: True if x == 1 else False)
    TempH = obsH["replaced"].apply(lambda x: True if x == 1 else False)
    Temp = TempE | TempH
    obs["replaced"] = Temp.apply(lambda x: 1 if True else 0)
    obs["filtered_points"] = obsE["filtered_points"] + obsH["filtered_points"]
    return obs[["date", "day", "exist", "replaced", "filtered_points"]]


## OBTENER O GENERAR DATA ---------------------------------------------------------------------------------------------------------------------------------------------------------


def Get_Reference(references: DataFrame):
    columns = [
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
    references.columns = columns
    return references


def Get_Header(loc):
    f = Path.cwd() / f"config/header_{loc.lower()}.csv"
    df_header = pd.read_csv(f)
    # base_dir = Path("/home/bcalsi/Downloads/PV2/PV")
    # df_header = pd.read_csv(base_dir / f"{loc}/Headers.csv")
    return df_header


def Set_hours(data):
    data = data.copy()
    data["datetime"] = data["date"] + " " + data["time"]
    data["datetime"] = pd.to_datetime(data["datetime"])
    data["hours"] = pd.to_datetime(data["time"])
    data["time"] = data["hours"]

    data["hours"] = data["hours"].apply(
        lambda x: x.hour + x.minute / 60 + x.second / 3600
    )
    data = data.dropna().reset_index()
    return data


def Get_Files(date, module, base_dir, header_df):
    download = DriveDownload()
    name = module.Name.values[0]
    tech = module.Tech.values[0]
    loc = module.Location.values[0]

    # Condiciones ambientales (CA)
    try:
        data_CA = download.read_ca(date, loc)
        columns = header_df["CA"].dropna().values
        data_CA.columns = columns
        data_CA = Set_hours(data_CA)
    except:
        data_CA = pd.DataFrame()
        print("error ca")

    # Variables eléctricas (SFCR)
    try:
        data_E = download.read_inverters(name, tech, loc, date)
        columns = header_df["SFCR"].dropna().values
        data_E.columns = columns
        data_E = Set_hours(data_E)
    except:
        data_E = pd.DataFrame()
        print("error e")

    # Variables eléctricas alternativas (SunnyPortal)
    adata_E = pd.DataFrame()

    # Variables Temperatura e Irradiancias (DAQ)
    try:
        data_DAQ = download.read_daq(loc, date)
        print("daq empty?", data_DAQ.empty)
        columns = header_df["DAQ"].dropna().values
        data_DAQ.columns = columns
        data_DAQ = Set_hours(data_DAQ)
    except:
        data_DAQ = pd.DataFrame()
        print("error daq")

    # Variables Temperatura e Irradiancia alternativa
    adata_DAQ = pd.DataFrame()

    return [data_CA, data_E, adata_E, data_DAQ, adata_DAQ]


def Get_data(data_matrix, module, Header, header_df, filt_values):
    """
    input:
    data_matrix: Get_Files output
    module: row of referencias.xlsx
    header: nombre de la columna a utilizar
    header_df: header.slsx
    filt_values
    """
    exist = 1
    replaced = 0
    filtered_points = 0
    data = pd.DataFrame()
    # Asignar desde los datos importados
    if Header in header_df["DAQ"].values:
        data = data_matrix[3][["time", "hours", Header]]
    if Header in header_df["SFCR"].values:
        data = data_matrix[1][["time", "hours", Header]]
    if Header in header_df["CA"].values:
        data = data_matrix[0][["time", "hours", Header]]

    # Revisar existencia de archivo y filtrar
    if data.empty:
        exist = 0
    else:
        # Filtros estandarizados
        data, exist, filtered_points = STD_Filtering(data, Header, filt_values, module)
        # Filtros adicionales
        data, exist, filtered_points2 = Filter_and_Reject(
            data, Header, filt_values, module
        )
        filtered_points = filtered_points + filtered_points2
        if data.empty:
            exist = 0
        else:
            data = data[["time", "hours", Header]].dropna()

    # Uso de reemplazo
    if (exist == 0 and filt_values[2][0].get() == 1) or filt_values[2][2].get() == 1:
        # exist = 0
        if Header in header_df["DAQ"].values:
            try:
                data = data_matrix[4][["time", "hours", Header]]
            except:
                data = pd.DataFrame()
        if Header in header_df["SFCR"].values:
            try:
                data = data_matrix[2][["time", "hours", Header]]
                data[Header] = data[Header] * 1000
            except:
                data = pd.DataFrame()
        else:
            data = pd.DataFrame()

        if data.empty:
            replaced = 0
        else:
            # Filtros estandarizados
            data, replaced, filtered_points = STD_Filtering(
                data, Header, filt_values, module
            )
            # Filtros adicionales
            data, replaced, filtered_points2 = Filter_and_Reject(
                data, Header, filt_values, module
            )
            filtered_points = filtered_points + filtered_points2
            if data.empty:
                replaced = 0
            else:
                data = data[["time", "hours", Header]].dropna()

    # Reemplazo de valores afectados por sombra (Solo aplicado en potencia)
    if (
        (filt_values[2][1].get() == 1)
        and Header[0] == "P"
        and (exist == 1 or replaced == 1)
    ):
        for x in range(int(filt_values[3][0].get())):
            data[Header] = shadow_correction(
                data, Header, data_matrix, module, header_df, filt_values
            )

    return data, exist, replaced, filtered_points


def Get_Power_Corrected(data_matrix, module, Header, header_df, filt_values, out_h):
    exist = 1
    replaced = 0
    filtered_points = 0
    dataP, existP, replacedP, filtered_pointsP = Get_data(
        data_matrix, module, Header, header_df, filt_values
    )
    dataT, existT, replacedT, filtered_pointsT = Get_data(
        data_matrix, module, f"TC {module.Tech.item()} (C)", header_df, filt_values
    )
    if existP + existT < 2:
        exist = 0
    else:
        dataP = dataP.set_index("time")
        dataT = dataT.set_index("time")  # ; dataG = dataG.set_index('time')
        dataP = dataP.join(dataT[f"TC {module.Tech.item()} (C)"], how="outer")
        dataP[f"TC {module.Tech.item()} (C)"] = dataP[
            f"TC {module.Tech.item()} (C)"
        ].interpolate()
        dataP = dataP.dropna(subset=[Header])
        # dataP = dataP.join(dataG['G (W/m2)'], how='left'); dataP['G (W/m2)'] = dataP['G (W/m2)'].interpolate()
        dataP = dataP.reset_index()
        pf = float(module.PowerFactor.item())
        dataP["T"] = dataP[f"TC {module.Tech.item()} (C)"] - 25.0
        dataP["corr"] = 1.0 + ((pf / 100) * dataP["T"])
        dataP[out_h] = dataP[Header] / dataP["corr"]
        dataP = dataP[["time", "hours", out_h]].dropna()
    return dataP, exist, replacedP, filtered_pointsP


def Get_TONC(data_matrix, module, header_df, filt_values, out_h):
    exist = 1
    replaced = 0
    filtered_points = 0
    dataT, existT, replacedT, filtered_pointsT = Get_data(
        data_matrix, module, f"TC {module.Tech.item()} (C)", header_df, filt_values
    )
    dataG, existG, replacedG, filtered_pointsG = Get_data(
        data_matrix, module, "G (W/m2)", header_df, filt_values
    )
    dataA, existA, replacedA, filtered_pointsA = Get_data(
        data_matrix, module, "Tair (C)", header_df, filt_values
    )
    if existG + existT + existA < 3:
        exist = 0
    else:
        dataA = dataA.set_index("time")
        dataT = dataT.set_index("time")
        dataG = dataG.set_index("time")
        dataT = dataT.join(dataA["Tair (C)"], how="left")
        dataT["Tair (C)"] = dataT["Tair (C)"].interpolate()
        dataT = dataT.join(dataG["G (W/m2)"], how="left")
        dataT["G (W/m2)"] = dataT["G (W/m2)"].interpolate()
        dataT = dataT.reset_index()
        dataT[out_h] = (
            (dataT[f"TC {module.Tech.item()} (C)"] - dataT["Tair (C)"])
            * 800.0
            / dataT["G (W/m2)"]
        ) + 20.0
        dataT = dataT[["time", "hours", out_h]].dropna()
    return dataT, exist, replacedT, filtered_pointsT


def Get_CS_POA(date, module, Header):
    lat, long = module.Lat.item(), module.Long.item()
    tzonedt = int(module.Timezone.item())
    if tzonedt < 0:
        tzone_site = f"Etc/GMT{tzonedt}"
        tzone_drange = f"Etc/GMT+{-tzonedt}"
    if tzonedt > 0:
        tzone_site = f"Etc/GMT+{tzonedt}"
        tzone_drange = f"Etc/GMT{-tzonedt}"
    if tzonedt == 0:
        tzone_site = f"Etc/GMT{tzonedt}"
        tzone_drange = f"Etc/GMT{tzonedt}"
    site = location.Location(lat, long, tz=tzone_site)
    times = pd.date_range(
        start=date, end=date + datetime.timedelta(days=1), freq="1T", tz=tzone_drange
    )
    cs = site.get_clearsky(times)
    solar_position = site.get_solarposition(times=times)
    POA = irradiance.get_total_irradiance(
        surface_tilt=int(module.Tilt.item()),
        surface_azimuth=int(module.Azimuth.item()),
        dni=cs["dni"],
        ghi=cs["ghi"],
        dhi=cs["dhi"],
        solar_zenith=solar_position["apparent_zenith"],
        solar_azimuth=solar_position["azimuth"],
    )
    POA.drop(POA.tail(1).index, inplace=True)
    POA["datetime"] = POA.index.to_pydatetime()
    POA = POA.reset_index()
    data = pd.DataFrame(columns=["date", "time", Header], index=POA.index)
    data["time"] = POA["datetime"]
    data["hours"] = data["time"].apply(
        lambda x: x.hour + x.minute / 60 + x.second / 3600
    )
    data[Header] = POA["poa_global"]
    data = data[data[Header] > 20].reset_index()
    exist = 1
    replaced = 0
    filtered_points = 0
    return data[["time", "hours", Header]], exist, replaced, filtered_points


def PDC_nom_Jose(data_matrix, module, header_df, filt_values):
    data_P, exist_P, replaced_P, filtered_P = Get_data(
        data_matrix, module, "Pdc (W)", header_df, filt_values
    )
    data_G, exist_G, replaced_G, filtered_G = Get_data(
        data_matrix, module, "G (W/m2)", header_df, filt_values
    )
    data_TS, exist_TS, replaced_TS, filtered_TS = Get_data(
        data_matrix, module, f"TS {module.Tech.item()} (C)", header_df, filt_values
    )
    data_TC, exist_TC, replaced_TC, filtered_TC = Get_data(
        data_matrix, module, f"TC {module.Tech.item()} (C)", header_df, filt_values
    )
    ex_tab = [
        exist_P,
        exist_G,
        exist_TS,
        exist_TC,
        f"TS_{module.Tech.item()} (C)",
        f"TC {module.Tech.item()} (C)",
    ]
    if exist_P == 1 and exist_G == 1 and exist_TS == 1 and exist_TC == 1:
        data_P = data_P.set_index("time")
        data_G = data_G.set_index("time")
        data_TS = data_TS.set_index("time")
        data_TC = data_TC.set_index("time")
        data = pd.merge(data_P, data_G, how="inner", left_index=True, right_index=True)
        data = pd.merge(data, data_TS, how="inner", left_index=True, right_index=True)
        data = pd.merge(data, data_TC, how="inner", left_index=True, right_index=True)
        data[f"TProm {module.Tech.item()} (C)"] = (
            data[f"TC {module.Tech.item()} (C)"] + data[f"TS {module.Tech.item()} (C)"]
        ) / 2
        data = data.reset_index()
        messages = []
        messages.append(f"Puntos filtrados en Potencia: {filtered_P}")
        messages.append(f"Puntos filtrados en Irradiancia: {filtered_G}")
        messages.append(f"Puntos filtrados en Temperatura lado: {filtered_TS}")
        messages.append(f"Puntos filtrados en Temperatura central: {filtered_TC}")
        for x in range(len(data.index) - len(messages)):
            messages.append(np.nan)
        data["Messages"] = messages

        return data
    else:
        return pd.DataFrame({"A": []})


## CALCULOS DE UN DIA ---------------------------------------------------------------------------------------------------------------------------------------------------------


def Integration(data_matrix, module, Header, header_df, filt_values):
    data, exist, replaced, filtered_points = Get_data(
        data_matrix, module, Header, header_df, filt_values
    )
    integration = np.nan
    if exist == 1 or replaced == 1:
        integrations_val = (
            (data[Header].diff().dropna() / 2).reset_index()[Header] + data[Header]
        ).dropna()

        integrations_time = (
            data["time"].diff().dropna().dt.total_seconds() / 3600
        ).reset_index()["time"]

        integrations = integrations_val * integrations_time
        integration = integrations.sum()
    return integration, exist, replaced, filtered_points


def Integration_Tcorrected(data_matrix, module, Header, header_df, filt_values, out_h):
    data, exist, replaced, filtered_points = Get_Power_Corrected(
        data_matrix, module, Header, header_df, filt_values, out_h
    )
    integration = np.nan
    if exist == 1:
        integrations_val = (
            (data[out_h].diff().dropna() / 2).reset_index()[out_h] + data[out_h]
        ).dropna()
        integrations_time = (
            data["time"].diff().dropna().dt.total_seconds() / 3600
        ).reset_index()["time"]
        integrations = integrations_val * integrations_time
        integration = integrations.sum()
    return integration, exist, replaced, filtered_points


def Prom(data_matrix, module, Header, header_df, filt_values):
    data, exist, replaced, filtered_points = Get_data(
        data_matrix, module, Header, header_df, filt_values
    )
    prom = np.nan
    if exist == 1 or replaced == 1:
        prom = data[Header].mean()
    return prom, exist, replaced, filtered_points


def Data_Avb(data_matrix, module, Header, header_df, filt_values):
    data, exist, replaced, filtered_points = Get_data(
        data_matrix, module, Header, header_df, filt_values
    )
    Percentage = 0
    if exist == 1 or replaced == 1:
        data["diff"] = data["hours"].diff()
        step = data["diff"].min()
        points = (data["hours"].max() - data["hours"].min()) / step
        Percentage = (data["hours"].count() - 1) * 100 / points
        # if Percentage > 100:
        #    Percentage = 100
    return Percentage, exist, replaced, filtered_points


def Prom_TONC(data_matrix, module, header_df, filt_values, out_h):
    data, exist, replaced, filtered_points = Get_TONC(
        data_matrix, module, header_df, filt_values, out_h
    )
    prom = np.nan
    if exist == 1 or replaced == 1:
        prom = data[out_h].mean()
    return prom, exist, replaced, filtered_points


def Hi_CS(date, module, Header):
    data, exist, replaced, filtered_points = Get_CS_POA(date, module, Header)
    integration = None
    if exist == 1 or replaced == 1:
        integrations_val = (
            (data[Header].diff().dropna() / 2).reset_index()[Header] + data[Header]
        ).dropna()
        integrations_time = (
            data["time"].diff().dropna().dt.total_seconds() / 3600
        ).reset_index()["time"]
        integrations = integrations_val * integrations_time
        integration = integrations.sum() / 1000
    return integration, exist, replaced, filtered_points


def VI(data_matrix, date, module, Header, header_df, filt_values):
    data, exist, replaced, filtered_points = Get_data(
        data_matrix, module, Header, header_df, filt_values
    )
    VAR = None
    if exist == 1 or replaced == 1:
        temp = data.copy()
        temp["Idiff"] = temp[Header].diff()
        temp["Tdiff"] = temp["hours"].diff()
        temp["preSQRT"] = (temp["Idiff"] ** 2) + (temp["Tdiff"] ** 2)
        temp["SQRT"] = np.sqrt(temp[["preSQRT"]])
        VAR1 = temp["SQRT"].sum()
        data, exist1, replaced1, filtered_points1 = Get_CS_POA(date, module, Header)
        temp = data.copy()
        temp["Idiff"] = temp[Header].diff()
        temp["Tdiff"] = temp["hours"].diff()
        temp["preSQRT"] = (temp["Idiff"] ** 2) + (temp["Tdiff"] ** 2)
        temp["SQRT"] = np.sqrt(temp[["preSQRT"]])
        VAR2 = temp["SQRT"].sum()
        VAR = VAR1 / VAR2
    return VAR, exist, replaced, filtered_points


def TemporalDistribution(data_matrix, module, Header, header_df, filt_values):
    data, exist, replaced, filtered_points = Get_data(
        data_matrix, module, Header, header_df, filt_values
    )
    Fm = None
    if exist == 1 or replaced == 1:
        data2 = data[data["hours"] < 12].copy().reset_index()
        integrations_val = (
            (data[Header].diff().dropna() / 2).reset_index()[Header] + data[Header]
        ).dropna()
        integrations_time = (
            data["time"].diff().dropna().dt.total_seconds() / 3600
        ).reset_index()["time"]
        integrations = integrations_val * integrations_time
        Den = integrations.sum()
        integrations_val = (
            (data2[Header].diff().dropna() / 2).reset_index()[Header] + data2[Header]
        ).dropna()
        integrations_time = (
            data2["time"].diff().dropna().dt.total_seconds() / 3600
        ).reset_index()["time"]
        integrations = integrations_val * integrations_time
        Num = integrations.sum()
        Fm = Num / Den
    return Fm, exist, replaced, filtered_points


# ## CALCULOS DE VARIOS DIAS ---------------------------------------------------------------------------------------------------------------------------------------------------------
#
#
# def Daily_Calculation(date, edate, module, base_dir, Header, header_df, filt_values, out_h, type):
#     st_date = f'{date.month}/{date.day}/{date.year}'
#     end_date = f'{edate.month}/{edate.day}/{edate.year}'
#     # if date.month == 12:
#     #     end_date = f'01/01/{date.year + 1}'
#     # else:
#     #     end_date = f'{date.month + 1}/01/{date.year}'
#     dates = pd.date_range(start=st_date, end=end_date)
#     dates = dates.to_pydatetime()
#     dates = dates[:-1]
#     data = pd.DataFrame(columns=['date', 'day', out_h, 'exist', 'replaced', 'filtered_points'])
#     data['date'] = dates
#     #data['date'] = data['date'].dt.date
#     data['day'] = data['date'].apply(lambda x: x.day)
#     data['day'] = data['date']
#     if type == 1:  ## Se solicita una integración
#         data['touples'] = data['date'].apply(lambda x: Integration(x, module, base_dir, Header, header_df, filt_values))
#     if type == 2:  ## Se solicita el promedio
#         data['touples'] = data['date'].apply(lambda x: Prom(x, module, base_dir, Header, header_df, filt_values))
#     if type == 3: ## Irradiancia de condiciones de cielo claro
#         data['touples'] = data['date'].apply(lambda x: Hi_CS(x, module, Header))
#     if type == 4:  ## Indice de variabilidad
#         data['touples'] = data['date'].apply(lambda x: VI(x, module, base_dir, Header, header_df, filt_values))
#     if type == 5:  ## Distribución Temporal
#         data['touples'] = data['date'].apply(lambda x: TemporalDistribution(x, module, base_dir, Header, header_df, filt_values))
#     if type == 6: ## Energía corregida por temperatura
#         data['touples'] = data['date'].apply(lambda x: Integration_Tcorrected(x, module, base_dir, Header, header_df, filt_values, out_h))
#     if type == 7: ## TONC promedio
#         data['touples'] = data['date'].apply(lambda x: Prom_TONC(date, module, base_dir, header_df, filt_values, out_h))
#     if type == 8:  ## Data Availabilty
#         data['touples'] = data['date'].apply(lambda x: Data_Avb(x, module, base_dir, Header, header_df, filt_values))
#
#     data[out_h] = data['touples'].apply(lambda x: x[0])
#     data['exist'] = data['touples'].apply(lambda x: x[1])
#     data['replaced'] = data['touples'].apply(lambda x: x[2])
#     data['filtered_points'] = data['touples'].apply(lambda x: x[3])
#     return data[['date', 'day', out_h]], data[['date', 'day', 'exist', 'replaced', 'filtered_points']]
#
# def DailyE(date, edate, module, base_dir, Header, header_df, filt_values, out_h):
#     data, obs = Daily_Calculation(date, edate, module, base_dir, Header, header_df, filt_values, out_h, 1)
#     data[out_h] = data[out_h]/1000
#     return data[['date', 'day', out_h]], obs[['date', 'day', 'exist', 'replaced', 'filtered_points']]
#
# def DailyYield(date, edate, module, base_dir, Header, header_df, filt_values, out_h):
#     data, obs = DailyE(date, edate, module, base_dir, Header, header_df, filt_values, out_h)
#     data[out_h] = data[out_h]/module.Pnom.item()
#     return data[['date', 'day', out_h]], obs[['date', 'day', 'exist', 'replaced', 'filtered_points']]
#
# def DailyYield_TCor(date, edate, module, base_dir, Header, header_df, filt_values, out_h):
#     data, obs = Daily_Calculation(date, edate, module, base_dir, Header, header_df, filt_values, out_h, 4)
#     data[out_h] = data[out_h] / 1000
#     data[out_h] = data[out_h]/module.Pnom.item()
#     return data[['date', 'day', out_h]], obs[['date', 'day', 'exist', 'replaced', 'filtered_points']]
#
# def DailyPR(date, edate, module, base_dir, header_df, filt_values, out_h):
#     dataE, obsE = DailyYield(date, edate, module, base_dir, 'Pac (W)', header_df, filt_values, out_h)
#     dataH, obsH = DailyE(date, edate, module, base_dir, 'G (W/m2)', header_df, filt_values, out_h)
#     dataE = dataE.rename(columns={out_h: 'Yf day (kW-h/kW)'})
#     dataH = dataH.rename(columns={out_h: 'Yr day (kW-h/kW)'})
#     data = pd.DataFrame(columns=['date', 'day', 'Yf day (kW-h/kW)', 'Yr day (kW-h/kW)', out_h], index=dataE.index)
#     data['date'] = dataE['date']; data['day'] = dataE['day']; data['Yf day (kW-h/kW)'] = dataE['Yf day (kW-h/kW)']
#     data['Yr day (kW-h/kW)'] = dataH['Yr day (kW-h/kW)']
#     data[out_h] = data['Yf day (kW-h/kW)']/data['Yr day (kW-h/kW)']
#     obs = GetObsDF(dataE, obsE, obsH)
#     return data[['date', 'day', 'Yf day (kW-h/kW)', 'Yr day (kW-h/kW)', out_h]], obs[['date', 'day', 'exist', 'replaced', 'filtered_points']]
#
# def DailyPR_TCor(date, edate, module, base_dir, header_df, filt_values, out_h):
#     dataE, obsE = DailyYield_TCor(date, edate, module, base_dir, 'Pac (W)', header_df, filt_values, out_h)
#     dataH, obsH = DailyE(date, edate, module, base_dir, 'G (W/m2)', header_df, filt_values, out_h)
#     dataE = dataE.rename(columns={out_h: 'Yf day (kW-h/kW)'})
#     dataH = dataH.rename(columns={out_h: 'Yr day (kW-h/kW)'})
#     data = pd.DataFrame(columns=['date', 'day', 'Yf day (kW-h/kW)', 'Yr day (kW-h/kW)', out_h], index=dataE.index)
#     data['date'] = dataE['date']; data['day'] = dataE['day']; data['Yf day (kW-h/kW)'] = dataE['Yf day (kW-h/kW)']
#     data['Yr day (kW-h/kW)'] = dataH['Yr day (kW-h/kW)']
#     data[out_h] = data['Yf day (kW-h/kW)']/data['Yr day (kW-h/kW)']
#     obs = GetObsDF(dataE, obsE, obsH)
#     return data[['date', 'day', 'Yf day (kW-h/kW)', 'Yr day (kW-h/kW)', out_h]], obs[['date', 'day', 'exist', 'replaced', 'filtered_points']]
#
# def DailyEfficiencies(date, edate, module, base_dir, header_df, filt_values, out_h, type):
#     if type == 1:  #Array Efficiency
#         dataNum, obsNum = DailyE(date, edate, module, base_dir, 'Pdc (W)', header_df, filt_values, out_h)
#         dataDen, obsDen = DailyE(date, edate, module, base_dir, 'G (W/m2)', header_df, filt_values, out_h)
#         dataDen[out_h] = dataDen[out_h]*module.Area.item()*module.Mod_num.item()
#     if type == 2: #System Efficiency
#         dataNum, obsNum = DailyE(date, edate, module, base_dir, 'Pac (W)', header_df, filt_values, out_h)
#         dataDen, obsDen = DailyE(date, edate, module, base_dir, 'G (W/m2)', header_df, filt_values, out_h)
#         dataDen[out_h] = dataDen[out_h] * module.Area.item() * module.Mod_num.item()
#     if type == 3: #BOS Efficiency
#         dataNum, obsNum = DailyE(date, edate, module, base_dir, 'Pac (W)', header_df, filt_values, out_h)
#         dataDen, obsDen = DailyE(date, edate, module, base_dir, 'Pdc (W)', header_df, filt_values, out_h)
#     dataNum = dataNum.rename(columns={out_h: 'Num'})
#     dataDen = dataDen.rename(columns={out_h: 'Den'})
#     data = pd.DataFrame(columns=['date', 'day', 'Num', 'Den', out_h], index=dataNum.index)
#     data['date'] = dataNum['date']; data['day'] = dataNum['day']; data['Num'] = dataNum['Num']
#     data['Den'] = dataDen['Den']
#     data[out_h] = data['Num'] / data['Den']
#     obs = GetObsDF(dataNum, obsNum, obsDen)
#     return data[['date', 'day', out_h]], obs[['date', 'day', 'exist', 'replaced', 'filtered_points']]
#
#
# def DailyLosses(date, edate, module, base_dir, header_df, filt_values, out_h, type):
#     if type == 1: # Capture Losses
#         dataE, obsE = DailyYield(date, edate, module, base_dir, 'Pdc (W)', header_df, filt_values, out_h)
#         dataH, obsH = DailyE(date, edate, module, base_dir, 'G (W/m2)', header_df, filt_values, out_h)
#     if type == 2: # Balance of Systems Losses
#         dataE, obsE = DailyYield(date, edate, module, base_dir, 'Pac (W)', header_df, filt_values, out_h)
#         dataH, obsH = DailyYield(date, edate, module, base_dir, 'Pdc (W)', header_df, filt_values, out_h)
#     dataE = dataE.rename(columns={out_h: 'OUT'})
#     dataH = dataH.rename(columns={out_h: 'IN'})
#     data = pd.DataFrame(columns=['date', 'day', 'OUT', 'IN', out_h], index=dataE.index)
#     data['date'] = dataE['date']; data['day'] = dataE['day']; data['OUT'] = dataE['OUT']
#     data['IN'] = dataH['IN']
#     data[out_h] = data['IN'] - data['OUT']
#     obs = GetObsDF(dataE, obsE, obsH)
#     return data[['date', 'day', out_h]], obs[['date', 'day', 'exist', 'replaced', 'filtered_points']]
#
# def DailyKb(date, edate, module, base_dir, header_df, filt_values, out_h):
#     dataH, obsH = DailyE(date, edate, module, base_dir, 'G (W/m2)', header_df, filt_values, out_h)
#     dataCS, obsCS = Daily_Calculation(date, edate, module, base_dir, 'header', header_df, filt_values, out_h, 3)
#     dataH = dataH.rename(columns={out_h: 'POA'})
#     dataCS = dataCS.rename(columns={out_h: 'CS'})
#     data = pd.DataFrame(columns=['date', 'day', 'POA', 'CS', out_h], index=dataH.index)
#     data['date'] = dataH['date'];data['day'] = dataH['day']; data['POA'] = dataH['POA']
#     data['CS'] = dataCS['CS']
#     data[out_h] = data['POA'] / data['CS']
#     obs = GetObsDF(dataH, obsH, obsCS)
#     return data[['date', 'day', out_h]], obs[['date', 'day', 'exist', 'replaced', 'filtered_points']]
#
#
# def Month_Calculation(date, edate, module, base_dir, Header, header_df, filt_values, out_h, type):
#     if type == 1:  #Yr
#         data, obs = DailyE(date, edate, module, base_dir, Header, header_df, filt_values, out_h)
#         data = data[out_h].sum()
#     if type == 2:  #Otros Yield
#         data, obs = DailyYield(date, edate, module, base_dir, Header, header_df, filt_values, out_h)
#         data = data[out_h].sum()
#     if type == 3:  #Valores promedio
#         data, obs = Daily_Calculation(date, edate, module, base_dir, Header, header_df, filt_values, out_h, 2)
#         data = data[out_h].mean()
#     if type == 4:  #Energía corregida
#         data, obs = Daily_Calculation(date, edate, module, base_dir, Header, header_df, filt_values, out_h, 6)
#         data = data[out_h].sum()/1000.0
#     if type == 5:  #TONC Mensual
#         data, obs = Daily_Calculation(date, edate, module, base_dir, Header, header_df, filt_values, out_h, 7)
#         data = data[out_h].mean()
#     Temp1 = obs['exist'].apply(lambda x: True if x == 1 else False)
#     Temp2 = obs['replaced'].apply(lambda x: True if x == 1 else False)
#     Temp = Temp1 | Temp2
#     Tempnum = Temp.apply(lambda x: 1 if x==True else 0)
#     errors = np.size(Tempnum) - np.count_nonzero(Tempnum)
#     return data, errors
#
# def Month_PR(date, edate, module, base_dir, header_df, filt_values, out_h):
#     data, obs = DailyPR(date, edate, module, base_dir, header_df, filt_values, out_h)
#     data = data.dropna()
#     PR = data['Yf day (kW-h/kW)'].sum()/data['Yr day (kW-h/kW)'].sum()
#     Temp1 = obs['exist'].apply(lambda x: True if x == 1 else False)
#     Temp2 = obs['replaced'].apply(lambda x: True if x == 1 else False)
#     Temp = Temp1 | Temp2
#     Tempnum = Temp.apply(lambda x: 1 if x == True else 0)
#     errors = np.size(Tempnum) - np.count_nonzero(Tempnum)
#     return PR, errors
#
# def Month_PR_TCor(date, edate, module, base_dir, header_df, filt_values, out_h):
#     data, obs = DailyPR_TCor(date, edate, module, base_dir, header_df, filt_values, out_h)
#     data = data.dropna()
#     PR = data['Yf day (kW-h/kW)'].sum()/data['Yr day (kW-h/kW)'].sum()
#     Temp1 = obs['exist'].apply(lambda x: True if x == 1 else False)
#     Temp2 = obs['replaced'].apply(lambda x: True if x == 1 else False)
#     Temp = Temp1 | Temp2
#     Tempnum = Temp.apply(lambda x: 1 if x == True else 0)
#     errors = np.size(Tempnum) - np.count_nonzero(Tempnum)
#     return PR, errors
#
# def MonthEfficiencies(date, edate, module, base_dir, header_df, filt_values, out_h, type):
#     if type == 1:  #Array Efficiency
#         dataNum, obsNum = DailyE(date, edate, module, base_dir, 'Pdc (W)', header_df, filt_values, out_h)
#         dataDen, obsDen = DailyE(date, edate, module, base_dir, 'G (W/m2)', header_df, filt_values, out_h)
#         dataDen[out_h] = dataDen[out_h]*module.Area.item()*module.Mod_num.item()
#     if type == 2: #System Efficiency
#         dataNum, obsNum = DailyE(date, edate, module, base_dir, 'Pac (W)', header_df, filt_values, out_h)
#         dataDen, obsDen = DailyE(date, edate, module, base_dir, 'G (W/m2)', header_df, filt_values, out_h)
#         dataDen[out_h] = dataDen[out_h] * module.Area.item() * module.Mod_num.item()
#     if type == 3: #BOS Efficiency
#         dataNum, obsNum = DailyE(date, edate, module, base_dir, 'Pac (W)', header_df, filt_values, out_h)
#         dataDen, obsDen = DailyE(date, edate, module, base_dir, 'Pdc (W)', header_df, filt_values, out_h)
#     dataNum = dataNum.rename(columns={out_h: 'Num'})
#     dataDen = dataDen.rename(columns={out_h: 'Den'})
#     data = pd.DataFrame(columns=['date', 'day', 'Num', 'Den', out_h], index=dataNum.index)
#     data['date'] = dataNum['date']; data['day'] = dataNum['day']; data['Num'] = dataNum['Num']
#     data['Den'] = dataDen['Den']
#     data[out_h] = data['Num']/data['Den']
#     data = data.dropna()
#     Eff = data['Num'].sum()/data['Den'].sum()
#     Temp1 = obsNum['exist'].apply(lambda x: True if x == 1 else False)
#     Temp2 = obsDen['replaced'].apply(lambda x: True if x == 1 else False)
#     Temp = Temp1 | Temp2
#     Tempnum = Temp.apply(lambda x: 1 if x == True else 0)
#     errors = np.size(Tempnum) - np.count_nonzero(Tempnum)
#     return Eff, errors
#
#
# def MonthlyYield(st_date, end_date, module, base_dir, Header, header_df, filt_values, out_h, type):
#     months = pd.date_range(st_date, end_date, freq='M')
#     months = months.to_pydatetime()
#     months = np.append(months, end_date)
#     index = list(range(len(months)))
#     data = pd.DataFrame(columns=['Month', 'Number', out_h], index=index)
#     data['Month'] = months
#     data['Number'] = data['Month'].apply(lambda x: x.month)
#     data['touples'] = data['Month'].apply(lambda x: Month_Calculation(x, module, base_dir, Header, header_df, filt_values, 'Y', type))
#     data[out_h] = data['touples'].apply(lambda x: x[0])
#     errors = pd.DataFrame(columns=['Month', 'Number', 'error_days'], index=index)
#     errors['Month'] = months
#     errors['Number'] = data['Month'].apply(lambda x: x.month)
#     errors['error_days'] = data['touples'].apply(lambda x: x[1])
#     return data[['Month', 'Number', out_h]], errors
#
# #def MonthlyPR(st_date, end_date, module, base_dir, Header, header_df, filt_values, out_h):
#     #YieldE =
#     #return None

if __name__ == "__main__":
    references = Get_Reference()

    df_header = Get_Header("PUCP")

    dt = datetime.datetime(2021, 1, 6)

    idx = references.loc[
        (references["Tech"] == "CIGS") & (references["Location"] == "PUCP")
    ].index[0]

    module = references.iloc[[idx], :]

    base_dir = r"/home/bcalsi/Downloads/PV2/PV/"

    matrix = Get_Files(dt, module, base_dir, df_header)

    for n in range(5):
        print(matrix[n].empty)
