from datetime import date
from numpy import nan

from upload import Upload
import processing
import settings


class PhotovoltaicPlatform:
    """Manage calls for download, process and upload of PV Systems"""

    def __init__(self):
        self.settings_hourly = settings.SettingsHourly()
        self.settings_daily = settings.SettingsDaily()
        self.upload = Upload()

        self.systems = self.upload.systems.set_index("sys_id")
        self.references = self.upload.get_references()

    def process_upload_date(self, date):
        """Iterative upload on a particular date."""
        for sys_id in self.references["sys_id"]:
            if not self.in_log(sys_id, date, "h"):
                df_hourly = self.process_hourly(sys_id, date)
                self.upload_hourly(sys_id, date, df_hourly)
            else:
                print(date, sys_id, "already uploaded hourly")
            if not self.in_log(sys_id, date, "d"):
                df_daily = self.process_daily(sys_id, date)
                self.upload_daily(sys_id, date, df_daily)
            else:
                print(date, sys_id, "already uploaded daily")

    def module_references(self, sys_id: int):
        """Get single row DataFrame of module information for processing."""
        return self.references[self.references["sys_id"] == sys_id]

    def process_hourly(self, sys_id: int, date: date):
        """Calls process hourly and returns DataFrame."""
        module = self.module_references(sys_id)
        return processing.hourly(date, module)

    def process_daily(self, sys_id: int, date: date):
        """Calls process hourly and returns DataFrame."""
        module = self.module_references(sys_id)
        return processing.daily(date, module)

    def upload_hourly(self, sys_id, date, df):
        """Renames DataFrame and upload hourly based process."""
        if df is None:
            self.upload.log_message(sys_id, date, "h", "failed")
        else:
            df.columns = self.settings_hourly.initial_names
            loc_id = self.systems.loc[sys_id, "loc_id"]
            self.upload.upload_hourly(df, date, loc_id, sys_id)

        self._commit_queries()

    def upload_daily(self, sys_id, date, df):
        """Renames DataFrame and upload daily based process."""
        if df is None:
            self.upload.log_message(sys_id, date, "d", "failed")
        else:
            df = self._clean_performance(df)
            self.upload.upload_daily(df, date, sys_id)

        self._commit_queries()

    def _commit_queries(self):
        """Commit queries previously run."""
        self.upload.connector.commit()

    def _clean_performance(self, df):
        """
        Change performance DataFrame column names and prepares it for upload.
        Checks and remove invalid calculations.
        """

        # Change column names
        df.columns = settings.performance_columns()

        # Get column with incorrect calculations ('No' invalid, 'Yes' correct)
        no_cols = df[df == "No"].dropna(axis=1).columns.tolist()
        # Remove '_Ok' from column names
        no_cols = [col[:-3] for col in no_cols]
        # Change incorrect calculations to nan
        for col in no_cols:
            df[col] = nan

        return df

    def in_log(self, sys_id: str, date: date, type: str):
        """Checks if date already been uploaded of a system and process type."""
        return self.upload.check_log(sys_id, date, type)


if __name__ == "__main__":
    from pathlib import Path
    import pandas as pd

    platform = PhotovoltaicPlatform()

    # Read already processed dates and upload to database
    path = Path.cwd().parent / "processed"
    print(path)

    systems = platform.systems
    systems.commisioned = pd.to_datetime(systems.commisioned)
    print(systems)
