from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import pandas as pd
from datetime import datetime
from io import StringIO
import time
from pathlib import Path
import numpy as np


class DriveDownload:
    """
    Google Drive connection and data extraction for inverter and tracer.
    """

    def __init__(self):
        gauth = GoogleAuth()
        gauth.CommandLineAuth()
        self.drive = GoogleDrive(gauth)

    def file_inverter(self, filename: str, tech: str, loc: str, dt: datetime):
        """
        Returns file title and id DataFrame of a date.

        tech: technology
        loc: university/institution where systems are installed
        dt: date as datetime type
        """
        dt = dt.strftime("%Y_%m_%d")
        q = f"title contains '{filename}-{tech}-{loc}_{dt}'"
        files = self.drive.ListFile({"q": q}).GetList()

        try:
            file = files[0]
            return file
        except:
            return

    def read_inverters(self, filename: str, tech: str, loc: str, dt: datetime):
        """
        Read and concat inverters data.
        """
        file = self.file_inverter(filename, tech, loc, dt)
        try:
            content = self._get_content(file)
            df = self._to_frame(content)

            return df
        except:
            return

    def _get_content(self, file, encoding="utf-8"):
        """
        Download content of file and returns a string.
        """
        f = self.drive.CreateFile({"id": file["id"]})
        content = f.GetContentString(file["title"], encoding=encoding)

        return content

    def _to_frame(self, content, skiprows=None, sep=";", header=None):
        """
        Transforms string to a intermediate text buffer.
        Returns a Pandas DataFrame.
        """
        buffer = StringIO(content)
        df = pd.read_csv(buffer, sep=sep, header=header, skiprows=skiprows)

        return df

    def read_ca(self, dt: datetime, loc: str):
        """Read tracer ambients preprocessed on a minute basis."""

        try:
            q = dt.strftime(f"title contains 'CA-{loc}-%Y-%m-%d' and trashed=false")
            file = self.drive.ListFile({"q": q}).GetList()[0]
            content = self._get_content(file)
            df = self._to_frame(content, sep=",", header=0)

            df["datetime"] = pd.to_datetime(df["datetime"])
            df = df.groupby(pd.Grouper(key="datetime", freq="min")).mean().reset_index()

            df.insert(0, "date", df["datetime"].dt.strftime("%Y-%m-%d"))
            df.insert(1, "time", df["datetime"].dt.strftime("%H:%M:%S"))

            idxs_no_nan = df.dropna().index
            df.insert(2, "empty", np.nan)
            df.loc[idxs_no_nan, "empty"] = 0

            [df.pop(col) for col in ["datetime", "g_o_2", "g_i_2"]]

            return df
        except:
            return

    def read_daq(self, loc: str, dt: datetime):
        """Returns DataFrame of DAQ GoogleDriveFile."""
        file = self.file_daq(loc=loc, dt=dt)
        content = self._get_content(file)
        df = self._to_frame(content)

        return df

    def file_daq(self, loc: str, dt: datetime):
        """Returns pydrive GoogleDriveFile."""
        dt = dt.strftime("%Y_%m_%d")
        title = f"DAQ-{loc}_{dt}"
        q = f"title contains '{title}' and trashed=false"
        files = self.drive.ListFile({"q": q}).GetList()

        if not files:
            title = f"DAQ-MS80M-{loc}_{dt}.csv"
            q = f"title contains '{title}' and trashed=false"
            files = self.drive.ListFile({"q": q}).GetList()

        file = files[0]

        return file


if __name__ == "__main__":
    download = DriveDownload()
    dt = datetime(2021, 11, 11)
    loc = "PUCP"
    tech = "HIT"
    name = "SFCR1"

    # read conditional ambients
    df = download.read_ca(dt, loc)

    # read_inverters
    # df = download.read_inverters(name, tech, loc, dt)
    # read_daq
    # df = download.read_daq(loc, dt)

    print(df.dropna().head())
