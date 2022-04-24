"""
# Introduction

Python Exodus Utilities is a Python library for interfacing with Exodus II files and assisting in performing some common
tasks. This library's only requirements are Python 3.7 or newer, [numpy](https://numpy.org/), and
[netcdf4-python](https://unidata.github.io/netcdf4-python/).

The primary purpose of this library is to allow uses to easily read and modify Exodus II files without having to go
through a more complicated interface or wrapper library. This library also includes some helpful functions for writing
out a subset of a mesh, determining the difference between two files, merging and splitting sets, and more.

Python Exodus Utilities supports most basic Exodus II features defined in
[SAND92-2137](https://www.osti.gov/servlets/purl/10102115) and the
[new documentation](https://gsjaardema.github.io/seacas-docs/exodusII-new.pdf), but lacks newer and more complicated
features from the [C library](https://gsjaardema.github.io/seacas-docs/sphinx/html/index.html#exodus-library) such as
assembly.

# Tutorial
## Opening and closing an Exodus II file
## Difference between two Exodus II files
## Output a subset of an Exodus II file
## Skinning a mesh
## Adding data to an Exodus II file
## Removing data from an Exodus II file
"""

from .exodus import Exodus
from .output_subset import output_subset
from .selector import ElementBlockSelector, SideSetSelector, NodeSetSelector, PropertySelector
from .constants import (
    # Object types
    ELEMBLOCK,
    NODESET,
    SIDESET,
    # Variable types
    GLOBAL_VAR,
    NODAL_VAR,
    ELEMENTAL_VAR,
    NODESET_VAR,
    SIDESET_VAR
)
