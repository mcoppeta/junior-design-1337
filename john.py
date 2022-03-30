from exodus import Exodus
from iterate import SampleFiles
import netCDF4 as nc

data = nc.Dataset('sample-files/w/test.ex2', 'w', format='NETCDF3_CLASSIC')

data.createDimension('dim1', 0)
data.createDimension('dim2', 0)
data.createDimension('dim3', 0)