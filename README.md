# Python Exodus Utilities
A 100% Python-based library of processing tools for working with Exodus files. 
Created by GT Junior Design Team 1337 for Sandia National Labs.

**Team 1337:**  
Michael Coppeta, Christoffer Rokholm, Allen Santmier, Christopher Turko, John Washburne

## Release Notes for Version 1.0.0

### New Features
- Read data from Exodus II file
- Add and remove data from existing Exodus II file
- Split and merge sets and blocks
- List differences between files
- Mesh skinning
- Output subset of model to new Exodus II file
- Documentation and testing suite


### Bug fixes
- `output_subset` no longer creates files using HDF5 exclusive features
- Writing changes no longer defaults to netcdf3_classic format
- Read methods now use ledgers in a/w modes
- Fixed inconsistency when reading after writes in append mode

### Known bugs and defects
- Mode `‘w’` (write mode) only creates an empty Exodus file. It is currently required for running some tests, but is likely useless to end users. Write mode needs to accept input data from the user to be useful beyond internal testing.
- Cannot currently access variables by name, or write to side sets or element blocks by name. However, other features that can have names have name support.
- If the Exodus object is modified after creating a selector object, the selector object may become invalid.
- Selector objects could potentially be used in read functions, but there is currently no support.
- `output_subset` will not output data it does not recognize (things like assemblies won’t be carried over).
- The library doesn’t cache function results, so repeat identical function calls are slower than they could be if caching was used.
- `split_sideset` has known bugs (see behavior with `bake.e` sample file) and somewhat restricted functionality including a lack of support for side set variables. Coordinate-based side set splitting functions are also prone to bugs due to limited testing at time of release.
- Skinning has two main issues. First, the algorithm for eliminating duplicate faces will remove front/back faces because they share the same nodes. Second, it’s not clear whether TRI refers to triangle blocks or trishell blocks. The `skin` function currently takes a parameter so that it may be specified.  
- Elemental attributes are not handled in a/w modes. If elements are changed in append mode, then attributes may not be retained correctly. 

## Install Guide

### Prerequisites
Python 3.7 or newer installed on the system.

### Dependencies
Dependencies are detailed in the requirements.txt file. To install all dependencies, run `pip install -r requirements.txt` in the command line. To generate documentation you will additionally need to install pdoc (`pip install pdoc`).

### Download Instructions
Only source code is provided, so downloading is as simple as cloning the repository.

### Build Instructions
The source code provided is structured as a Python package. To make the package pip installable, it will need to be uploaded to pip as per standard procedure. Otherwise, no additional steps are required to use the code.

### Installation
If the package is uploaded to pip, it can be installed and imported the same as any other package. Otherwise you can use the package in any project so long as the package’s root folder is in the same directory as the project’s root folder.

### Run Instructions
Import the Exodus class from the exodus.py module into a Python script. Open an Exodus file using the Exodus constructor and interact with the files using the methods outlined in the documentation file exodus.html

### Run Tests
To run the tests using pytest, run the command `pytest` from the root directory (the one that contains the ‘tests’ folder). Pytest will automatically find all of the test files, run them, and report which tests failed.

### Troubleshooting
- If you are missing dependencies, `pip install netCDF4` and `pip install numpy`.
- If the tests will not run, make sure you are running `pytest` on the root directory and have pytest installed (`pip install pytest`).

