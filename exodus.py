import netCDF4 as nc
import numpy as np

class Exodus:

    __FORMAT_MAP = {'NETCDF4': 'NETCDF4',
                    'NETCDF4_CLASSIC': 'NETCDF4_CLASSIC',
                    'NETCDF3_LARGE_MODEL': 'NETCDF3_64BIT_OFFSET',
                    'NETCDF3_CLASSIC': 'NETCDF3_CLASSIC'}

    def __init__(self, path, mode, clobber=False, format='NETCDF4'):
        if mode not in ['r', 'w', 'a']:
            raise ValueError("mode must be 'w', 'r', or 'a', got '{}'".format(mode))
        if format not in Exodus.__FORMAT_MAP:
            raise ValueError("invalid file format: '{}'".format(format))
        nc_format = Exodus.__FORMAT_MAP[format]
        try:
            self.data = nc.Dataset(path, mode, clobber, format=nc_format)
        except FileNotFoundError as fnfe:
            raise FileNotFoundError("file '{}' does not exist".format(path)) from fnfe
        except PermissionError as pe:
            raise PermissionError("You do not have access to '{}'".format(path))
        except OSError as ose:
            raise OSError("file '{}' exists, but clobber is set to False".format(path))


    def close(self):
        self.data.close()


    def print_dimensions(self):
        for dim in self.data.dimensions.values():
            print(dim)

    def get_sideset(self, i):
        elem_key = 'elem_ss' + str(i)
        side_key = 'side_ss' + str(i)
        sideset_i = {}
        sideset_i['elements'] = self.data[elem_key][:]
        sideset_i['sides'] = self.data[side_key][:]
        return sideset_i

    def get_nodeset(self, i):
        key = "node_ns" + str(i)
        return self.data[key][:]


    
    # prints legacy character array as string
    @staticmethod
    def print(line):
        s = ""
        for c in line:
            if str(c) != '--':
                s += str(c)[2]
        
        print(s)
        return s


if __name__ == "__main__":
    ex = Exodus('sample-files/disk_out_ref.ex2', 'r')
    print(ex.data)
    print(ex.get_nodeset(1))
    sideset2 = ex.get_sideset(3)
    print(sideset2['elements'])
    print(sideset2['sides'])
    ex.close()
