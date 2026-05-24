"""UK Tidal analysis

This program calculates statistics based on tidal data.

Copyright 2025 by Bella Stoyanova. CC-BY-SA.

"""

# import the modules we need
import datetime
import glob
import os
import argparse
import pandas as pd
import numpy as np
import uptide
import pytz
from scipy import stats
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

def read_tidal_data(filename: str) -> pd.DataFrame:
    """Load all txt tidal data files from dirname into one sanitized DataFrame."""

    df = pd.read_csv(
        filename,
        skiprows=11,
        sep=r"\s+",
        names=["Cycle", "Date", "Time", "Sea Level", "Residual"],
        engine="python",
    )

    # Remove dodgy values (ending in M, N, T) by replacing with NaN
    df["Sea Level"] = df["Sea Level"].replace(to_replace=r".*[MNT]$", value=np.nan, regex=True)
    df["Residual"] = df["Residual"].replace(to_replace=r".*[MNT]$", value=np.nan, regex=True)

    # Parse combined datetime field
    df["DateTime"] = pd.to_datetime(
        df["Date"].astype(str) + " " + df["Time"].astype(str),
        format="%Y/%m/%d %H:%M:%S",
        errors="coerce",)

    # Convert numeric fields to NaN if they contain invalid characters
    df["Sea Level"] = pd.to_numeric(df["Sea Level"], errors="coerce")
    df["Residual"] = pd.to_numeric(df["Residual"], errors="coerce")

    df = df[["DateTime", "Time", "Sea Level", "Residual"]]
    df = df[df["DateTime"].notna()]

    # Set DateTime as the index
    df.set_index("DateTime", inplace=True)

    return df

def extract_single_year_remove_mean(year:str, data: pd.DataFrame) -> pd.DataFrame:
    """ Extract a single year of tidal data and remove the mean sea level """

    year_data = data[data.index.year == int(year)].copy()

    mean_sea_level = year_data["Sea Level"].mean()
    year_data["Sea Level"] = year_data["Sea Level"] - mean_sea_level

    return year_data


def extract_section_remove_mean(start: str, end: str, data: pd.DataFrame) -> pd.DataFrame:
    """Extract a section of data between two dates and remove mean sea level"""

    start_date = pd.to_datetime(start, format="%Y%m%d")

    # We add a day since we want the start and end date to be inclusive
    end_date = pd.to_datetime(end, format="%Y%m%d") + pd.Timedelta(days=1)

    year_data = data[(data.index >= start_date) & (data.index < end_date)].copy()

    mean_sea_level = year_data["Sea Level"].mean()
    year_data["Sea Level"] = year_data["Sea Level"] - mean_sea_level

    return year_data


def join_data(data1: pd.DataFrame, data2: pd.DataFrame) -> pd.DataFrame:
    """Join two tidal datasets into one DataFrame"""

    data = pd.concat([data1, data2])
    data = data.sort_index()

    return data

def sea_level_rise(data: pd.DataFrame) -> tuple[float, float]:
    """Run linear regression to calculate sea level rise (metres per day)"""

    df = data.copy()

    df["Sea Level"] = pd.to_numeric(df["Sea Level"], errors="coerce")

    if isinstance(df.index, pd.DatetimeIndex):
        times = df.index
    elif "DateTime" in df.columns:
        times = pd.to_datetime(df["DateTime"], errors="coerce")
    else:
        times = pd.to_datetime(df["Time"], errors="coerce")

    df = df.assign(_Time=times)

    clean = df.dropna(subset=["_Time", "Sea Level"])


    x = mdates.date2num(clean["_Time"])
    y = clean["Sea Level"].to_numpy()

    result = stats.linregress(x, y)


    return result.slope, result.pvalue



def tidal_analysis(data: pd.DataFrame,
                   constituents: list[str],
                   start_datetime: str) -> tuple[float, float]:
    """Calculate tidal amplitudes and phases from sea level data."""

    start_datetime = pd.Timestamp(start_datetime).tz_localize(None)

    # Remove NaN values
    data_clean = data.dropna(subset=["Sea Level"])

    # Convert times into seconds since the start date
    t = (data_clean.index - pd.Timestamp(start_datetime)).total_seconds().to_numpy()

    # Get sea level values
    eta = data_clean["Sea Level"].to_numpy()

    # Set up tidal constituents
    tide = uptide.Tides(constituents)

    tide.set_initial_time(start_datetime)

    # Run tidal analysis
    amp, pha = uptide.harmonic_analysis(tide, eta, t)

    return amp, pha


def get_longest_contiguous_data(data: pd.DataFrame) -> pd.DataFrame:
    """Returns the longest stretch of contiguous yearly data."""

    data = data.sort_values("year")

    longest = []
    current = []

    years = data["year"].tolist()

    for i, year in enumerate(years):
        if i == 0 or year == years[i - 1] + 1:
            current.append(year)
        else:
            if len(current) > len(longest):
                longest = current
            current = [year]

    if len(current) > len(longest):
        longest = current

    return data[data["year"].isin(longest)]


# ==============================================


def tide_table(station_name: str, m2: float, s2: float) -> pd.DataFrame:
    """
    Returns a formatted table string for tidal amplitudes.

    Parameters:
    station_name (str): Name of the station
    m2 (float or str): M2 amplitude in meters
    s2 (float or str): S2 amplitude in meters
    """

    table = (
        f"Station Name\tM2 Amplitude\tS2 Amplitude\n"
        f"{station_name}\t\t{m2}\t\t{s2}")

    return table

def graph_data(data: list[pd.DataFrame]) -> None:
    """
    Plots a boxplot of Sea Level by year.

    Each DataFrame in the list is combined and grouped by year, with
    outliers removed using the IQR rule before plotting.

    Parameters:
    data (list[pd.DataFrame]): List of DataFrames to be plotted
    """

    if not data:
        return

    yearly_values = {}

    for df in data:
        if df is None or df.empty:
            continue
        if "Sea Level" not in df.columns:
            continue

        df_copy = df.copy()
        if not isinstance(df_copy.index, pd.DatetimeIndex):
            df_copy.index = pd.to_datetime(df_copy.index, errors="coerce")

        df_copy = df_copy.dropna(subset=["Sea Level"])
        df_copy = df_copy[df_copy.index.notna()]
        if df_copy.empty:
            continue

        df_copy["year"] = df_copy.index.year
        for year, group in df_copy.groupby("year"):
            sea_level = group["Sea Level"].dropna()
            if sea_level.empty:
                continue

            q1 = sea_level.quantile(0.25)
            q3 = sea_level.quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            cleaned = sea_level[(sea_level >= lower) & (sea_level <= upper)]
            if cleaned.empty:
                continue

            yearly_values.setdefault(year, []).extend(cleaned.to_list())

    if not yearly_values:
        return

    years = sorted(yearly_values)
    box_data = [yearly_values[year] for year in years]

    plt.figure()
    plt.boxplot(box_data, labels=[str(year) for year in years], patch_artist=True)
    plt.xlabel("Year")
    plt.ylabel("Sea Level")
    plt.title("Sea Level Distribution by Year")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def main(args_list=None):
    """Program entry point."""

    parser = argparse.ArgumentParser(
                     prog="UK Tidal analysis",
                     description="Calculate tidal constiuents and RSL from tide gauge data",
                     )

    parser.add_argument("directory",
                    help="the directory containing txt files with data")

    parser.add_argument('-v', '--verbose',
                    action='store_true',
                    default=False,
                    help="Print progress")

    parser.add_argument('-g', '--graph_values',
                        action="store_true",
                        default=False,
                        help="Graph tidal data")

    args = parser.parse_args(args_list)
    dirname = os.path.normpath(args.directory.strip())
    verbose = args.verbose
    graph_values = args.graph_values

    running_data = None
    data_arr = []

    for filename in sorted(glob.glob(os.path.join(dirname, "*.txt"))):
        data = read_tidal_data(filename)
        data_arr.append(data)
        running_data = join_data(running_data, data)

    if graph_values:
        graph_data(data_arr)

    amp, _ = tidal_analysis(
        running_data, ['M2', 'S2'],
        datetime.datetime(1946,6,1,0,0,0,
                          tzinfo=pytz.timezone("utc")))

    station_map = {
        "whitby": "Whitby",
        "dover": "Dover",
        "aberdeen": "Aberdeen",
    }

    station_key = os.path.basename(dirname).lower()
    station_name = station_map.get(station_key, station_key.title())

    output_text = tide_table(station_name, f"{amp[0]:.3f}", f"{amp[1]:.3f}")

    if verbose:
        print(output_text)
    else:
        with open("output.txt", "w", encoding="utf-8") as f:
            f.write(output_text + "\n")


if __name__ == '__main__':
    main()
