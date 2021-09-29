import netCDF4 as nc

path = 'sample-files/can.ex2'
ds = nc.Dataset(path)

for dim in ds.dimensions.values():
    print(dim)