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
        """
        # This stuff will currently cause errors if you create a new file because there's nothing to access
        self.nodal_coord_arr = self.data['coord']

        # build sideset array
        num_sidesets = self.data.dimensions['num_side_sets'].size
        sidesets = []
        for i in range(1,  num_sidesets + 1): # +1 since side sets index from 1
            elem_key = 'elem_ss' + str(i)
            side_key = 'side_ss' + str(i)
            sideset_i = {}
            sideset_i['elements'] = self.data[elem_key]
            sideset_i['sides'] = self.data[side_key]
            sidesets.append(sideset_i)"""


    def close(self):
        self.data.close()


    def print_dimensions(self):
        for dim in self.data.dimensions.values():
            print(dim)

    
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
    ex.close()
