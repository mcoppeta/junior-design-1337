import netCDF4 as nc
import numpy as np

class Exodus:

    def __init__(self, path):
        self.data = nc.Dataset("./bingobongo")
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
            sidesets.append(sideset_i)
        

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
    ex = Exodus('sample-files/disk_out_ref.ex2')
    print(ex.data['name_nod_var'])
    for var in ex.data['name_nod_var']:
        Exodus.print(var)