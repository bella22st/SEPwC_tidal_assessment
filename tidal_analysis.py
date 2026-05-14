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

def read_tidal_data(dirname):
    """Function: read_tidal_data
    Reads the txt files as pandas df

    Input: txt data
    Return: df 
    """

    log("Filename: " + dirname)
    
    df = pd.read_csv('data/whitby/2000WHI.txt', 
                  skiprows=12,
                    sep=r'\s+',)

    df.columns = ['Cycle', 'Date', 'Time', 'ASLVBG02', 'Residual']

    df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
    df = df.drop(['Date', 'Time'], axis=1)
    df.set_index('DateTime', inplace=True)
    print(df.head())
    print(df.shape)
    
    return df 

    return
    
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

    read_tidal_data(dirname)

    

if __name__ == '__main__':
    main()
