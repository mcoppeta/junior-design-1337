"""Contains common functions used in the Python Exodus Library."""

import numpy as np


def c_print(line):
    """Prints a C character array to the console."""
    print(lineparse(line))


def lineparse(line):
    """Returns the Python string form of a C character array."""
    s = ""
    for c in line:
        if str(c) != '--':
            s += str(c)[2]

    return s


def convert_string(s, length):
    """
    Converts a Python string to a NetCDF4 compatible character array.

    :param s: python string
    :param length: length of the output string (not including null terminator)
    :return: character array
    """
    length += 1  # we've got to add the null character
    arr = np.empty(length, '|S1')
    for i in range(len(s)):
        arr[i] = s[i]

    mask = np.empty(length, bool)
    for i in range(length):
        if i < len(s):
            mask[i] = False
        else:
            mask[i] = True

    out = np.ma.core.MaskedArray(arr, mask)
    return out
