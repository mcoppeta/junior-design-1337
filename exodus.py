import netCDF4 as nc

class Exodus:

    def __init__(self, path):
        self.data = nc.Dataset(path)

    def print_dimensions(self):
        for dim in self.data.dimensions.values():
            print(dim)

    # prints legacy character array as string
    def print_line(self, line):
        s = ""
        for c in line:
            if str(c) != '--':
                s += str(c)[2]
        
        print(s)
        return s

if __name__ == "__main__":
    ex = Exodus('sample-files/disk_out_ref.ex2')
    print(ex.data.variables.keys())
    print(ex.data['eb_status'])