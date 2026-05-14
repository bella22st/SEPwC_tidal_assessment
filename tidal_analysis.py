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

VERBOSE = True


# ============ DONT CHANGE FNs ============

def read_tidal_data(filename: str) -> pd.DataFrame:
    """Load all txt tidal data files from dirname into one sanitized DataFrame."""

    log(f"Reading file: {filename}")

    df = pd.read_csv(
        filename,
        skiprows=11,
        sep=r"\s+",
        names=["Cycle", "Date", "Time", "Sea Level", "Residual"],
        engine="python",
    )

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

    return

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

def log(str: str):
    if VERBOSE == True:
        print(str)

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

    global VERBOSE
    args = parser.parse_args(args_list)
    dirname = args.directory
    VERBOSE = args.verbose
    log(f"verbose={VERBOSE}")

    log("Add your code here to do things!")

    all_dfs = []

    for filename in sorted(glob.glob(os.path.join(dirname, "*.txt"))):
        data = read_tidal_data(filename)
        all_dfs.append(data)

    log(all_dfs)

if __name__ == '__main__':
    main()
