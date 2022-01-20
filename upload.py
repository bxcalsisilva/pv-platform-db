import mariadb
import sys
import datetime
import pandas as pd
from pandas.core.frame import DataFrame

import settings


class Upload:
    def __init__(self) -> None:
        self._connect_db()
        self.cursor = self.connector.cursor()
        self.report = []
        self._read_systems()

        self.settings_hourly = settings.SettingsHourly()

    def _connect_db(self):
        # Connect to MariaDB Platform
        try:
            conn = mariadb.connect(
                user="root",
                password="password",
                host="localhost",
                port=3306,
                database="pv_systems",
                autocommit=False,
            )
            self.connector = conn
            print(f"MariaDB Platform connection at {datetime.datetime.now()}")
        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)

    def _add_report(self, message) -> None:
        """Add messages of warnings"""

        self.report.append(message)

    def _read_systems(self):
        """Read the systems and locations information stored in the database"""

        self.cursor.execute(
            "SELECT l.location_id, label, city, system_id, technology, commisioned "
            + "FROM locations l JOIN systems s ON l.location_id = s.location_id"
        )

        columns = ["loc_id", "label", "city", "sys_id", "tech", "commisioned"]
        self.systems = pd.DataFrame(self.cursor.fetchall(), columns=columns)

    def read_logs(self):
        """Read system and dates already uploaded to database."""

        q = (
            "SELECT lc.location_id, lc.label, s.system_id, s.technology, date, "
            + "type, message from logs l "
            + "JOIN systems s ON l.system_id = s.system_id "
            + "JOIN locations lc ON lc.location_id = s.location_id"
        )

        self.cursor.execute(q)
        columns = ["loc_id", "loc", "sys_id", "sys", "date", "type", "message"]
        self.logs = pd.DataFrame(self.cursor.fetchall(), columns=columns)

    def check_log(self, sys_id, date, type) -> bool:
        """Check if a date has been already uploaded."""

        q = (
            "SELECT EXISTS(SELECT * FROM logs "
            + f"WHERE system_id = {sys_id} AND date = '{date}' AND type = '{type}')"
        )
        self.cursor.execute(q)
        exists = self.cursor.fetchone()[0]

        return bool(exists)

    def loc_sys_id(self, loc, tech):
        """Returns location_id and system_id."""
        [[loc_id, sys_id]] = self.systems.loc[
            (self.systems["label"] == loc) & (self.systems["tech"] == tech),
            ["loc_id", "sys_id"],
        ].values

        return loc_id, sys_id

    def upload_hourly(self, df, date, loc_id, sys_id):
        """Upload a DataFrame to database."""

        # Add missing columns
        self.df = df.reindex(columns=self.settings_hourly.names)
        self.df[["date", "loc_id", "sys_id"]] = [date, loc_id, sys_id]

        self._add_observations()
        self._add_ambients()
        self._add_tmods()
        self._add_irradiances()
        self._add_inverters()
        self.add_log(sys_id, date, type="h")

    def _to_tuples(self, df) -> tuple:
        """Transforms DataFrame to SQL INSERT format"""

        tuples = tuple(df.itertuples(index=False, name=None))
        tuples = str(tuples)[1:-1].replace("'NULL'", "NULL")

        if df.shape[1] == 1:
            tuples = tuples.replace(",)", ")")

        return tuples

    def _add_observations(self) -> DataFrame:
        """Adds the given first observation and returns the inserted id"""

        df = self.df[self.settings_hourly.datetime].astype("str")
        df.dropna(inplace=True)
        tuples = self._to_tuples(df)

        # Insert datetimes and ignores if already exists
        self.cursor.execute(
            f"INSERT IGNORE INTO observations (datetime) VALUES {tuples}"
        )

        # Gets the observation_id of used datetimes
        self.cursor.execute(
            f"SELECT observation_id, datetime FROM observations where (datetime) in ({tuples})"
        )

        # Format the fetched data to DataFrame
        obs_id = self.cursor.fetchall()
        obs_id = pd.DataFrame(obs_id, columns=["obs_id", "datetime"])

        # Adds the observation_id to each corresponding row
        self.df = self.df.merge(obs_id, how="left")

    def _is_empty(self, columns):
        """Check if DataFrame columns are empty."""
        return self.df[columns].dropna(how="all").empty

    def _clean_format(self, details, columns):
        """Clean DataFrame Nan of key columns and format Nan to SQL NULL"""
        df = self.df[details + columns].copy()
        df.dropna(subset=columns, how="all", inplace=True)
        df.fillna("NULL", inplace=True)

        return df

    def _add_ambients(self) -> None:
        """Adds ambients variables from meteorological station"""
        columns = self.settings_hourly.ambients

        if self._is_empty(columns):
            return

        df = self._clean_format(details=["obs_id", "loc_id"], columns=columns)
        tuples = self._to_tuples(df)

        q = (
            "INSERT INTO ambients "
            + "(observation_id, location_id, t_amb, humidity_relative, "
            + "humidity_absolute, wind_speed, wind_direction, air_density, "
            + "pressure_relative, pressure_absolute) "
            + f"VALUES {tuples}"
        )

        self.cursor.execute(q)

    def _add_tmods(self) -> None:
        """Adds module temperature given the observation_id and system_id"""
        columns = self.settings_hourly.t_mod + self.settings_hourly.t_noct

        if self._is_empty(columns):
            return

        df = self._clean_format(details=["obs_id", "sys_id"], columns=columns)

        tuples = self._to_tuples(df)

        self.cursor.execute(
            "INSERT IGNORE INTO t_mods (observation_id, system_id, t_mod, t_noct)"
            + f"VALUES {tuples}"
        )

    def _add_irradiances(self) -> None:
        """Adds irradiance and equipment used for the measurement"""
        columns = self.settings_hourly.irr

        if self._is_empty(columns):
            return

        df = self._clean_format(details=["obs_id", "loc_id"], columns=columns)

        tuples = self._to_tuples(df)

        self.cursor.execute(
            f"INSERT INTO irradiances (observation_id, location_id, irradiance) VALUES {tuples}"
        )

    def _add_inverters(self) -> None:
        """Adds electric variables measured with the inverter"""
        columns = self.settings_hourly.inverters

        if self._is_empty(columns):
            return

        df = self._clean_format(details=["obs_id", "sys_id"], columns=columns)

        tuples = self._to_tuples(df)

        self.cursor.execute(
            "INSERT INTO inverters "
            + "(observation_id, system_id, voltage_dc, current_dc, power_apparent, power_ac, power_dc, power_ac_t25, power_dc_t25) "
            + f"VALUES {tuples}"
        )

    def add_log(self, sys_id, date, type):
        """Add the successful uploaded date"""

        self.cursor.execute(
            f"INSERT INTO logs (system_id, date, type) VALUES ({sys_id}, '{date}', '{type}')"
        )

    def log_message(self, sys_id, date, type, message):
        """Add a message to a system_id and respective date."""
        self.cursor.execute(
            "INSERT INTO logs (system_id, date, type, message) VALUES "
            + f"({sys_id}, '{date}', '{type}', '{message}')"
        )

    def get_references(self):
        """Get reference DataFrame of each system."""
        names = settings.SettingsDaily().names_reference
        q = (
            "SELECT s.system_id, s.filename, l.label, l.city, s.technology, s.row * s.parallel, "
            + "s.area, s.nominal_power, l.latitude, l.longitude, l.altitude, "
            + "-5 as time_zone, s.inclination, s.azimuth, s.gamma "
            + "from locations l join systems s on l.location_id = s.location_id;"
        )
        self.cursor.execute(q)
        reference = self.cursor.fetchall()
        reference = pd.DataFrame(reference)
        reference.columns = names

        for col in reference.columns:
            try:
                if reference[col].dtype != int:
                    reference[col] = reference[col].astype(float)
            except:
                continue

        return reference

    def upload_daily(self, df, date, sys_id):
        # Select columns to upload
        df = df[settings.cols_performance].copy()
        df["date"] = str(date)
        df["sys_id"] = sys_id
        df.fillna("NULL", inplace=True)
        tuples = self._to_tuples(df)[:-1]

        q = (
            "INSERT INTO performances "
            + "(radiation, energy_ac, energy_dc, energy_ac_t25, energy_dc_t25, "
            + "yield_reference, yield_final, yield_absolute, yield_final_t25, "
            + "yield_absolute_t25, performance_ratio, performance_ratio_t25, "
            + "efficiency_array, efficiency_system, efficiency_inverter, "
            + "date, system_id) "
            + f"VALUES {tuples}"
        )

        self.cursor.execute(q)
        self.add_log(sys_id, date, type="d")


if __name__ == "__main__":
    from datetime import date

    upload = Upload()

    # systems = upload.systems

    # print(systems.loc[systems.sys_id == 1])

    bl = upload.check_log(1, date(2021, 11, 1), "d")
    print(bl)
