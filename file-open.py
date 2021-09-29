import netCDF4 as nc

path = 'sample-files/can.ex2'
ds = nc.Dataset(path)

## print dimension metadata
for dim in ds.dimensions.values():
    print(dim)

## print variable metadata
print("\n")
for var in ds.variables.values():
    print(var)