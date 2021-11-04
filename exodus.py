import netCDF4 as nc
import numpy


class Exodus:

    _FORMAT_MAP = {'NETCDF4': 'NETCDF4',
                    'NETCDF4_CLASSIC': 'NETCDF4_CLASSIC',
                    'NETCDF3_LARGE_MODEL': 'NETCDF3_64BIT_OFFSET',
                    'NETCDF3_CLASSIC': 'NETCDF3_CLASSIC'}
    # In files, 1 is added to these numbers to allow for C compatibility
    # Use self._max_str_length and self._max_line_length when modifying the file in case the file has special values
    _MAX_STR_LENGTH = 32
    _MAX_LINE_LENGTH = 80

    def __init__(self, path, mode, clobber=False, format='NETCDF4', word_size=4):
        # clobber and format and word_size only apply to mode w
        if mode not in ['r', 'w', 'a']:
            raise ValueError("mode must be 'w', 'r', or 'a', got '{}'".format(mode))
        if format not in Exodus._FORMAT_MAP:
            raise ValueError("invalid file format: '{}'".format(format))
        if word_size not in [4, 8]:
            raise ValueError("word_size must be 4 or 8 bytes, {} is not supported".format(word_size))
        nc_format = Exodus._FORMAT_MAP[format]
        try:
            self.data = nc.Dataset(path, mode, clobber, format=nc_format)
        except FileNotFoundError as fnfe:
            raise FileNotFoundError("file '{}' does not exist".format(path)) from fnfe
        except PermissionError as pe:
            raise PermissionError("You do not have access to '{}'".format(path))
        except OSError as ose:
            raise OSError("file '{}' exists, but clobber is set to False".format(path))

        # init self._float
        if mode == 'w':
            # Spaces seem to be preferred over underscores
            self.data.setncattr('floating point word size', word_size)
        ws = self.word_size
        if ws == 4:
            self._float = numpy.single
        elif ws == 8:
            self._float = numpy.double
        else:
            raise ValueError("word size of {} not supported".format(ws))

        # init self._max_str/line_length
        if mode == 'w':
            # This is probably required to make this backwards compatible with C
            self.data.createDimension('len_string', Exodus._MAX_STR_LENGTH + 1)
            self.data.createDimension('len_line', Exodus._MAX_LINE_LENGTH + 1)
        if 'len_string' in self.data.dimensions and 'len_line' in self.data.dimensions:
            # This is probably pointless, but safe
            self._max_str_length = self.data.dimensions['len_string'].size - 1
            self._max_line_length = self.data.dimensions['len_line'].size - 1
        else:
            self._max_str_length = Exodus._MAX_STR_LENGTH
            self._max_line_length = Exodus._MAX_LINE_LENGTH

    def to_float(self, n):
        # Convert a number to the floating point type the file is using
        return self._float(n)

    @property
    def float(self):
        return self._float

    @property
    def max_str_length(self):
        return self._max_str_length

    @property
    def max_line_length(self):
        return self._max_line_length

    @property
    def parameters(self):
        # Returns a dictionary of global attribute/value pairs. Exodus II calls these parameters
        result = {}
        for attr in self.data.ncattrs():
            result[attr] = self.data.getncattr(attr)
        return result

    @property
    def word_size(self):
        # Both styles of spacing are used in Exodus
        params = self.parameters
        if 'floating_point_word_size' in params:
            return self.data.getncattr('floating_point_word_size')
        elif 'floating point word size' in params:
            return self.data.getncattr('floating point word size')
        else:
            raise RuntimeError("parameter 'floating point word size' cannot be found!")

    @property
    def api_version(self):
        # Both styles of spacing are used in Exodus
        params = self.parameters
        if 'api_version' in params:
            return self.data.getncattr('api_version')
        elif 'api version' in params:
            return self.data.getncattr('api version')
        else:
            raise RuntimeError("parameter 'api version' cannot be found!")

    @property
    def version(self):
        return self.data.getncattr('version')

    @property
    def title(self):
        return self.data.getncattr('title')

    num_dim = property(lambda self: self.data.dimensions['num_dim'].size)
    num_nodes = property(lambda self: self.data.dimensions['num_nodes'].size)
    num_elem = property(lambda self: self.data.dimensions['num_elem'].size)
    num_elem_blk = property(lambda self: self.data.dimensions['num_el_blk'].size)
    num_node_sets = property(lambda self: self.data.dimensions['num_node_sets'].size)
    num_side_sets = property(lambda self: self.data.dimensions['num_side_sets'].size)

    def get_dimension(self, name):
        if name in self.data.dimensions:
            return self.data.dimensions[name].size
        else:
            raise RuntimeError("dimensions '{}' cannot be found!".format(name))

    def get_parameter(self, name):
        if name in self.data.ncattrs():
            return self.data.getncattr(name)
        else:
            raise RuntimeError("parameter '{}' cannot be found!".format(name))

    def close(self):
        self.data.close()

    def print_dimensions(self):
        for dim in self.data.dimensions.values():
            print(dim)

    def get_sideset(self, i):
        elem_key = 'elem_ss' + str(i)
        side_key = 'side_ss' + str(i)
        sideset_i = {}
        sideset_i['elements'] = self.data[elem_key]
        sideset_i['sides'] = self.data[side_key]
        return sideset_i

    def get_nodeset(self, i):
        key = "node_ns" + str(i)
        return self.data[key]

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
    ex = Exodus('sample-files/can.ex2', 'r')
    print(ex.data.dimensions)
    print(ex.num_elem)

    ex.close()
