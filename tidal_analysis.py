"""UK Tidal analysis - Calculate tidal constituents and RSL from tide gauge data."""
# import the modules we need
import glob
import pandas as pd
import datetime
import os
import numpy as np
import uptide
import pytz
import math
from scipy import stats
import matplotlib.dates as mdates
import argparse


# ============ DONT CHANGE FNs ============

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
        errors="coerce",
    )

    # Convert numeric fields to NaN if they contain invalid characters
    df["Sea Level"] = pd.to_numeric(df["Sea Level"], errors="coerce")
    df["Residual"] = pd.to_numeric(df["Residual"], errors="coerce")

    df = df[["DateTime", "Time", "Sea Level", "Residual"]]
    df = df[df["DateTime"].notna()]
    
    # Set DateTime as the index
    df.set_index("DateTime", inplace=True)

    return df
    
def extract_single_year_remove_mean(year, data):
    """ Extract a single year of tidal data and remove the mean sea level """

    year_data = data[data.index.year == int(year)].copy()

    mean_sea_level = year_data["Sea Level"].mean()
    year_data["Sea Level"] = year_data["Sea Level"] - mean_sea_level

    return year_data


def extract_section_remove_mean(start, end, data):
    """Extract a section of data between two dates and remove mean sea level"""

    start_date = pd.to_datetime(start, format="%Y%m%d")

    # We add a day since we want the start and end date to be inclusive
    end_date = pd.to_datetime(end, format="%Y%m%d") + pd.Timedelta(days=1)

    year_data = data[(data.index >= start_date) & (data.index < end_date)].copy()

    mean_sea_level = year_data["Sea Level"].mean()
    year_data["Sea Level"] = year_data["Sea Level"] - mean_sea_level

    return year_data


def join_data(data1, data2):
    """Join two tidal datasets into one DataFrame"""

    data = pd.concat([data1, data2])
    data = data.sort_index()

    return data

def sea_level_rise(data):
    """Run linear regression to calculate sea level rise (metres per day)"""
    df = data.copy()

    # Clean numeric sea level
    df["Sea Level"] = pd.to_numeric(df["Sea Level"], errors="coerce")

    # Use the actual datetime information; the index is the correct full datetime field.
    if isinstance(df.index, pd.DatetimeIndex):
        times = df.index
    elif "DateTime" in df.columns:
        times = pd.to_datetime(df["DateTime"], errors="coerce")
    else:
        times = pd.to_datetime(df["Time"], errors="coerce")

    df = df.assign(_Time=times)

    # Drop invalid rows
    clean = df.dropna(subset=["_Time", "Sea Level"])

    # Convert time using REQUIRED method (date2num converts to days since 1970)
    x = mdates.date2num(clean["_Time"])
    y = clean["Sea Level"].to_numpy()

    result = stats.linregress(x, y)

    # Return slope (metres per day) and p-value
    return result.slope, result.pvalue



def tidal_analysis(data, constituents, start_datetime):
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


def get_longest_contiguous_data(data):

    return 

# ==============================================


def tide_table(station_name, m2, s2):
    """
    Returns a formatted table string for tidal amplitudes.

    Parameters:
    station_name (str): Name of the station
    m2 (float or str): M2 amplitude in meters
    s2 (float or str): S2 amplitude in meters
    """

    # Ensure values are strings with units
    m2_str = f"{m2} m" if isinstance(m2, (int, float)) else str(m2)
    s2_str = f"{s2} m" if isinstance(s2, (int, float)) else str(s2)

    table = (
        f"Station Name\tM2 Amplitude\tS2 Amplitude\n"
        f"{station_name}\t{m2_str}\t{s2_str}"
    )

    return table



def main(args_list=None):

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

    args = parser.parse_args(args_list)
    dirname = args.directory
    verbose = args.verbose

    running_data = None

    for filename in sorted(glob.glob(os.path.join(dirname, "*.txt"))):
        data = read_tidal_data(filename)
        running_data = join_data(running_data, data)
    
    constituents  = ['M2', 'S2']
    tz = pytz.timezone("utc")
    start_datetime = datetime.datetime(1946,6,1,0,0,0, tzinfo=tz)
    amp, pha = tidal_analysis(running_data, constituents, start_datetime)

    if verbose:
        print(tide_table("Whitby", amp[0], amp[1]))

if __name__ == '__main__':
    main()
