from distutils.core import setup

setup(
    name="PythonExodusUtilities",
    version="1.0dev",
    packages=["exodusutils"],
    install_requires=['netCDF4', 'numpy']
)
