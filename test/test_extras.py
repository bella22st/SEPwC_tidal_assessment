import sys
import os
sys.path.insert(0, os.pardir)
sys.path.insert(0, ".")
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from tidal_analysis import get_longest_contiguous_data, tide_table


class TestUncoveredFunctions():
    """Tests for functions not covered in test_tides.py"""

    def test_get_longest_contiguous_data_simple(self):
        """Test get_longest_contiguous_data with a simple contiguous sequence"""
        data = pd.DataFrame({
            'year': [2000, 2001, 2002, 2003],
            'value': [1, 2, 3, 4]
        })
        result = get_longest_contiguous_data(data)
        assert len(result) == 4
        assert result['year'].tolist() == [2000, 2001, 2002, 2003]

    def test_get_longest_contiguous_data_with_gaps(self):
        """Test get_longest_contiguous_data with gaps in years"""
        data = pd.DataFrame({
            'year': [2000, 2001, 2002, 2005, 2006, 2007, 2008],
            'value': [1, 2, 3, 6, 7, 8, 9]
        })
        result = get_longest_contiguous_data(data)
        # Should return the longest sequence: 2005-2008
        assert len(result) == 4
        assert result['year'].tolist() == [2005, 2006, 2007, 2008]

    def test_get_longest_contiguous_data_equal_length_sequences(self):
        """Test get_longest_contiguous_data when there are multiple sequences of equal length"""
        data = pd.DataFrame({
            'year': [2000, 2001, 2005, 2006],
            'value': [1, 2, 3, 4]
        })
        result = get_longest_contiguous_data(data)
        # When there are ties, it should return the last one found
        assert len(result) == 2

    def test_tide_table_basic(self):
        """Test tide_table formatting with basic inputs"""
        result = tide_table("Dover", 1.5, 0.8)
        assert "Dover" in result
        assert "1.5" in result
        assert "0.8" in result
        assert "M2 Amplitude" in result
        assert "S2 Amplitude" in result

    def test_tide_table_float_values(self):
        """Test tide_table with float amplitude values"""
        result = tide_table("Aberdeen", 1.307, 0.441)
        assert "Aberdeen" in result
        assert "1.307" in result
        assert "0.441" in result

    def test_tide_table_contains_headers(self):
        """Test that tide_table includes proper headers"""
        result = tide_table("Whitby", 1.0, 0.5)
        assert "Station Name" in result
        assert "M2 Amplitude" in result
        assert "S2 Amplitude" in result
