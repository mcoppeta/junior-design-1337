from distutils.core import setup
from distutils.util import convert_path

v = {}
ver_path = convert_path('exodusutils/_version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), v)

setup(
    name="PythonExodusUtilities",
    version=v['__version__'],
    packages=["exodusutils"],
    install_requires=['netCDF4', 'numpy']
)
