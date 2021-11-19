from pathlib import Path
import pandas as pd
from datetime import date

from pv_platform import PhotovoltaicPlatform

platform = PhotovoltaicPlatform()

# Read already processed dates and upload to database
path = Path.cwd() / "processed"
print(path)

systems = platform.systems
systems.commisioned = pd.to_datetime(systems.commisioned)
print(systems)

# Upload hourly based calculations
print("Uploading hourly calculations")
for sys_id, sys in systems.iterrows():
    print("Processing hourly", sys.city, sys.label, sys.tech)
    dir = path / sys.city / sys.label / sys.tech
    if not dir.is_dir():
        print("directory not found:", dir)
        continue
    for dt in pd.date_range(sys.commisioned, end="2021-11-1"):
        dt = dt.to_pydatetime().date()

        in_log = platform.upload.check_log(sys_id, dt, type="h")
        if in_log:
            continue

        # find particular day
        dir = path / sys.city / sys.label / sys.tech / dt.strftime("%Y_%m_%d.csv")

        # check if exists and if is file
        if not dir.is_file():
            print(f"file not found: ", dir)
            platform.upload.log_message(sys_id, dt, "h", "empty")
            platform.upload.connector.commit()
            continue

        # read particular day
        df = pd.read_csv(dir, usecols=list(range(1, 13)), na_values="Nan")
        df.columns = platform.settings_hourly.initial_names
        df["datetime"] = pd.to_datetime(df["datetime"])

        platform.upload.upload_hourly(df, dt, sys.loc_id, sys_id)
        platform.upload.connector.commit()

        print(f"{sys.city}, {sys.label}, {sys.tech}, and {dt} uploaded.")

# Upload daily based calculations
print("Uploading daily calculations")
for sys_id, sys in systems.iterrows():
    print("Processing daily", sys.city, sys.label, sys.tech)
    dir = path / sys.city / sys.label / sys.tech / "Overall_Daily.csv"
    # check if exists and if is file
    if not dir.is_file():
        print("directory not found:", dir)
        continue

    dailys = pd.read_csv(dir, usecols=list(range(0, 31)), na_values="Nan")
    dailys["Fecha"] = pd.to_datetime(dailys["Fecha"], format="%d.%m.%Y")

    for dt in pd.date_range(sys.commisioned, end="2021-11-1"):
        dt = dt.to_pydatetime()

        in_log = platform.upload.check_log(sys_id, dt, type="d")
        if in_log:
            continue

        df = dailys[dailys["Fecha"] == dt].iloc[:, 1:].reset_index(drop=True)

        if df.empty:
            print(f"date {dt} not found in daily processed")
            platform.upload.log_message(sys_id, dt, "d", "empty")
            platform.upload.connector.commit()
            continue

        df = platform._clean_performance(df)

        platform.upload.upload_daily(df, dt, sys_id)
        platform.upload.connector.commit()

        print(f"{sys.city}, {sys.label}, {sys.tech}, and {dt.day} uploaded.")
