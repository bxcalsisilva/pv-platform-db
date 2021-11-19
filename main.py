import pandas as pd
import numpy as np
from datetime import date, timedelta

import processing
from pv_platform import PhotovoltaicPlatform

platform = PhotovoltaicPlatform()

systems = platform.systems
systems.commisioned = pd.to_datetime(systems.commisioned)

start_dt = date(2021, 11, 11)
yesterday = date.today() - timedelta(days=1)

for dt in pd.date_range(start_dt, date(2021, 11, 11)):
    dt = dt.to_pydatetime().date()
    platform.process_upload_date(dt)


# dt = date(2021, 11, 1)
# module = platform.module_references(1)

# df = processing.hourly(dt, module)
# print("Original size", df.shape)
# aux = df.replace("No", np.nan).dropna(axis=1)
# # print(aux)
# print("Only correct calculations", aux.shape)
