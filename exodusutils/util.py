"""Contains common functions used in the Python Exodus Library."""

from datetime import datetime
import numpy as np
from netCDF4 import stringtoarr
from .constants import LIB_NAME
from ._version import __version__


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


def arrparse(array, size, type):
    """Returns a Python string array from an array of C 'strings'."""
    result = np.empty([size], type)
    for i in range(size):
        result[i] = lineparse(array[i])
    return result


def convert_string(s, length):
    """
    Converts a Python string to a NetCDF4 compatible character array.

    :param s: python string
    :param length: length of the output string
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


def generate_qa_rec(length):
    """
    Returns a QA record ready to add to a file.

    :param length: length of a string (do not add 1)
    :return: qa record
    """
    rec = np.empty((4, length + 1), '|S1')
    rec[0] = stringtoarr(LIB_NAME, length+1)
    rec[1] = stringtoarr(__version__, length+1)
    t = datetime.now()
    rec[2] = stringtoarr(t.strftime("%m/%d/%y"), length+1)
    rec[3] = stringtoarr(t.strftime("%X"), length+1)
    return rec
