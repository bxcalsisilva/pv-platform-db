import pandas as pd
from pathlib import Path
import os
import csv


def check_ncols(file, ncols=20):
    f = open(file, "r")

    try:
        reader = csv.reader(f, delimiter=";")
        ncol = len(next(reader))
        f.seek(0)
        return ncol == ncols
    except:
        return False


def extract_ambients(file, sep=";"):
    df = pd.read_csv(file, sep=sep, header=None)
    df["datetime"] = df[18] + " " + df[19]
    df["datetime"] = pd.to_datetime(df["datetime"], format="%d-%m-%Y %H:%M:%S")

    columns = [
        "g_o_1",
        "g_o_2",
        "g_i_1",
        "g_i_2",
        "t_amb",
        "h_r",
        "p_r",
        "d_air",
        "wind_spd",
        "wind_dir",
        "name",
        "filename",
        "datetime",
    ]
    ambients = pd.DataFrame(columns=columns)

    dt = df.iloc[0, 20]
    f = file.name
    filename = f[: f.find("_")]

    ambients.loc[0] = [
        df.iloc[0, 9],
        df.iloc[1, 9],
        df.iloc[0, 10],
        df.iloc[1, 10],
        df.iloc[0, 11],
        df.iloc[0, 12],
        df.iloc[0, 13],
        df.iloc[0, 14],
        df.iloc[0, 15],
        df.iloc[0, 16],
        df.iloc[0, 17],
        filename,
        dt,
    ]

    return ambients


# root folder for data of each year
year = 2021
root = Path(f"/media/bcalsi/Disc-HDD/data/")

modules = [
    "VBHN330",
    "CS6K270P",
    "NAF128GK",
    "DUSTCS6K270P",
    "LG345N1C",
    "LG370Q1C",
    "CDF1150A1",
    "GSA060",
    "CS1H335",
]

# Iterate each subdirectory
ambients = pd.DataFrame()
months = [
    0,
    "Ene",
    "Feb",
    "Mar",
    "Abr",
    "May",
    "Jun",
    "Jul",
    "Ago",
    "Sep",
    "Oct",
    "Nov",
    "Dic",
]

for dt in pd.date_range("2021-01-01", "2022-01-01"):
    dir = root / dt.strftime(f"%Y/{months[dt.month]}_%Y/%d_{months[dt.month]}_%Y")
    if not dir.exists():
        continue

    pattern = dt.strftime("*_%d_%m_%Y_*_*_*.csv")
    files = dir.glob(pattern)

    if not files:
        continue

    for f in files:

        if not check_ncols(f, ncols=20):
            continue

        try:
            # extract only ambient measurements and append to dataframe
            df = extract_ambients(f)
            ambients = pd.concat([ambients, df], ignore_index=True)
        except:
            continue

ambients.sort_values("datetime")
ambients.to_csv(root / f"{year}_ambients.csv", index=False)
