# import the modules we need
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
import glob

VERBOSE = True


# ============ DONT CHANGE FNs ============

def read_tidal_data(dirname: str) -> pd.DataFrame:
    """Load all txt tidal data files from dirname into one sanitized DataFrame."""

    log(f"Directory: {dirname}")

    all_dfs = []

    for filename in sorted(glob.glob(os.path.join(dirname, "*.txt"))):
        log(f"Reading file: {filename}")

        df = pd.read_csv(
            filename,
            skiprows=12,
            sep=r"\s+",
            names=["Cycle", "Date", "Time", "SeaLevel", "Residual"],
            engine="python",
        )

        # Parse combined datetime field
        df["DateTime"] = pd.to_datetime(
            df["Date"].astype(str) + " " + df["Time"].astype(str),
            format="%Y/%m/%d %H:%M:%S",
            errors="coerce",
        )

        # Convert DateTime to matplotlib numeric date values
        df["DateTime"] = mdates.date2num(df["DateTime"])

        # Sanitize numeric fields and remove stray letters
        df["SeaLevel"] = pd.to_numeric(
            df["SeaLevel"].astype(str).str.replace(r"[^0-9eE\.-]", "", regex=True),
            errors="coerce",
        )
        df["Residual"] = pd.to_numeric(
            df["Residual"].astype(str).str.replace(r"[^0-9eE\.-]", "", regex=True),
            errors="coerce",
        )

        df = df[["DateTime", "SeaLevel", "Residual"]]
        df = df[df["DateTime"].notna()]

        all_dfs.append(df)

    combined_df = pd.concat(all_dfs, ignore_index=True)
    combined_df.sort_values("DateTime", inplace=True)
    combined_df.reset_index(drop=True, inplace=True)

    if VERBOSE:
        print(combined_df.head())
        print(combined_df.shape)

    return combined_df 
    
def extract_single_year_remove_mean(year, data):

    return 


def extract_section_remove_mean(start, end, data):
    year_data = 0

    return year_data


def join_data(data1, data2):

    return 

def sea_level_rise(data):

    return

def tidal_analysis(data, constituents, start_datetime):

    return

def get_longest_contiguous_data(data):

    return 

# ==============================================

def log(str: str):
    if VERBOSE:
        print(str)
    else:
        pass

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
    VERBOSE = args.verbose

    print("Add your code here to do things!")

    data = read_tidal_data(dirname)
    log(data)
    

if __name__ == '__main__':
    main()
