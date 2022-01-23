import netCDF4 as nc


def deep_copy(new_path, old_path):
    new = nc.Dataset(new_path, "w", True, format="NETCDF3_CLASSIC")
    old = nc.Dataset(old_path, 'r', False)

    new.setncatts(old.__dict__)

    # copy dimensions
    for dimension in old.dimensions.keys():
        new.createDimension(dimension, old.dimensions[dimension].size)

    # copy variables
    for var in old.variables:
        var_data = old[var]

        # variable creation data
        varname = var_data.name
        datatype = var_data.dtype
        dimensions = var_data.dimensions
        new.createVariable(varname, datatype, dimensions)

        new[varname][:] = old[var][:]
        new[varname].setncatts(old[varname].__dict__)

    print(new)
    print('\n\n\n')
    print(old)
    new.close()
    old.close()


if __name__ == "__main__":
    deep_copy('sample-files/write.ex2', 'sample-files/can.ex2')