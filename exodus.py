import warnings
import netCDF4 as nc
import numpy
from iterate import SampleFiles


class Exodus:
    _FORMAT_MAP = {'EX_NETCDF4': 'NETCDF4',
                   'EX_LARGE_MODEL': 'NETCDF3_64BIT_OFFSET',
                   'EX_NORMAL_MODEL': 'NETCDF3_CLASSIC',
                   'EX_64BIT_DATA': 'NETCDF3_64BIT_DATA'}
    # Default values
    _MAX_STR_LENGTH = 32
    _MAX_NAME_LENGTH = 32
    _MAX_LINE_LENGTH = 80
    _EXODUS_VERSION = 7.22

    def __init__(self, path, mode, clobber=False, format='EX_NETCDF4', word_size=4):
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
        except FileNotFoundError:
            raise FileNotFoundError("file '{}' does not exist".format(path))
        except PermissionError:
            raise PermissionError("You do not have access to '{}'".format(path))
        except OSError:
            raise OSError("file '{}' exists, but clobber is set to False".format(path))

        if mode == 'w' or mode == 'a':
            # This is important according to ex_open.c
            self.data.set_fill_off()

        # We will read a bunch of data here to make sure it exists and warn the user if they might want to fix their
        # file. We don't save anything to memory so that if our data updates we don't have to update it in memory too.
        # This is the same practice used in the C library so its probably a good idea.

        # Initialize all the important parameters
        if mode == 'w':
            self.data.createDimension('title', 'Untitled database')
            self.data.createDimension('len_string', Exodus._MAX_STR_LENGTH + 1)
            self.data.createDimension('len_name', Exodus._MAX_NAME_LENGTH + 1)
            self.data.createDimension('len_line', Exodus._MAX_LINE_LENGTH + 1)
            self.data.setncattr('maximum_name_length', Exodus._MAX_NAME_LENGTH)
            self.data.setncattr('version', Exodus._EXODUS_VERSION)
            self.data.setncattr('api_version', Exodus._EXODUS_VERSION)
            self.data.setncattr('floating_point_word_size', word_size)
            file_size = 0
            if nc_format == 'NETCDF3_64BIT_OFFSET':
                file_size = 1
            self.data.setncattr('file_size', file_size)
            int64bit_status = 0
            if nc_format == 'NETCDF3_64BIT_DATA':
                int64bit_status = 1
            self.data.setncattr('int64_status', int64bit_status)

        # Warn the user if some non-critical parameters are missing
        if 'len_string' not in self.data.dimensions:
            warnings.warn("'len_string' dimension is missing!")
        if 'len_name' not in self.data.dimensions:
            warnings.warn("'len_name' dimension is missing!")
        if 'len_line' in self.data.dimensions:
            warnings.warn("'len_line' dimension is missing!")
        if 'maximum_name_length' in self.data.ncattrs():
            warnings.warn("'maximum_name_length' attribute is missing!")

        # Check version compatibility
        ver = self.version
        if ver < 2.0:
            raise RuntimeError(
                "Unsupported file version {:.2f}! Only versions >2.0 are supported.".format(ver))

        # Read word size stored in file
        ws = self.word_size
        if ws == 4:
            # This needs to be double checked because our examples use float32 and float64 which may be different
            self._float = numpy.single
        elif ws == 8:
            self._float = numpy.double
        else:
            raise ValueError("file contains a word size of {} which is not supported".format(ws))

    def to_float(self, n):
        # Convert a number to the floating point type the file is using
        return self._float(n)

    @property
    def float(self):
        return self._float

    # TODO fix function that adds missing parts of the header
    # TODO function to find the longest name in the object
    # TODO maximum_name_length should be the actual length, not with the 1 C character added. confirm this

    ########################################################################
    #                                                                      #
    #                        Data File Utilities                           #
    #                                                                      #
    ########################################################################

    @property
    def parameters(self):
        # Returns a dictionary of global attribute/value pairs. Exodus II calls these parameters
        result = {}
        for attr in self.data.ncattrs():
            result[attr] = self.data.getncattr(attr)
        return result

    @property
    def title(self):
        # Guaranteed to exist
        return self.data.getncattr('title')

    @property
    def max_string_length(self):
        max_str_len = Exodus._MAX_STR_LENGTH
        if 'len_string' in self.data.dimensions:
            # Subtract 1 because in C an extra character is added for C reasons
            max_str_len = self.data.dimensions['len_string'].size - 1
        return max_str_len

    @property
    def max_line_length(self):
        max_line_len = Exodus._MAX_LINE_LENGTH
        if 'len_line' in self.data.dimensions:
            # Subtract 1 because in C an extra character is added for C reasons
            max_line_len = self.data.dimensions['len_line'].size - 1
        return max_line_len

    @property
    def max_allowed_name_length(self):
        max_name_len = Exodus._MAX_NAME_LENGTH
        if 'len_name' in self.data.dimensions:
            # Subtract 1 because in C an extra character is added for C reasons
            max_name_len = self.data.dimensions['len_name'].size - 1
        return max_name_len

    @property
    def max_used_name_length(self):
        max_used_name_len = 0
        if 'maximum_name_length' in self.data.ncattrs():
            max_used_name_len = self.data.getncattr('maximum_name_length')
        return max_used_name_len

    @property
    def api_version(self):
        # Guaranteed to exist
        params = self.parameters
        if 'api_version' in params:
            return self.data.getncattr('api_version')
        elif 'api version' in params:
            return self.data.getncattr('api version')

    @property
    def version(self):
        # Guaranteed to exist
        return self.data.getncattr('version')

    @property
    def file_size(self):
        if 'file_size' in self.data.ncattrs():
            return self.data.getncattr('file_size')
        else:
            return 1 if self.data.data_model == 'NETCDF3_64BIT_OFFSET' else 0
            # No warning is raised because older files just don't have this

    @property
    def int64_status(self):
        # This might actually be for NETCDF5 files but I'm not certain
        if 'int64_status' in self.data.ncattrs():
            return self.data.getncattr('int64_status')
        else:
            return 1 if self.data.data_model == 'NETCDF3_64BIT_DATA' else 0
            # No warning is raised because older files just don't have this

    @property
    def word_size(self):
        # Guaranteed to exist
        params = self.parameters
        if 'floating_point_word_size' in params:
            return self.data.getncattr('floating_point_word_size')
        elif 'floating point word size' in params:
            return self.data.getncattr('floating point word size')

    @property
    def qa_records(self):
        lst = []
        for line in self.data.variables['qa_records'][0]:
            lst.append(Exodus.lineparse(line))
        return lst

    @property
    def info_records(self):
        lst = []
        for line in self.data.variables['info_records']:
            lst.append(Exodus.lineparse(line))
        return lst

    ########################################################################
    #                                                                      #
    #                        Model Description                             #
    #                                                                      #
    ########################################################################

    @property
    def num_dim(self):
        return self.data.dimensions['num_dim'].size

    @property
    def num_nodes(self):
        return self.data.dimensions['num_nodes'].size

    @property
    def num_elem(self):
        return self.data.dimensions['num_elem'].size

    @property
    def num_elem_blk(self):
        return self.data.dimensions['num_el_blk'].size

    @property
    def num_node_sets(self):
        return self.data.dimensions['num_node_sets'].size

    @property
    def num_side_sets(self):
        return self.data.dimensions['num_side_sets'].size

    @property
    def num_time_steps(self):
        return self.data['time_whole'].size

    @property
    def time_values(self):
        """Returns a list of (float) time values for each time step"""
        values = []
        for step in self.time_steps:
            values.append(self.timeAtStep(step))
        return values

    @property
    def time_steps(self):
        """Returns list of the time steps, 0-indexed"""
        return [*range(self.num_time_steps)]

    def timeAtStep(self, step):
        """Given an integer time step, return the corresponding float time value"""
        return float(self.data['time_whole'][step].data)

    def stepAtTime(self, time):
        """Given a float time value, return the corresponding time step"""
        for index, value in enumerate(self.time_values):
            if value == time:
                return index
        return None

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

    def print_dimension_names(self):
        for dim in self.data.dimensions:
            print(dim)

    def print_variables(self):
        for v in self.data.variables.values():
            print(v, "\n")

    def print_variable_names(self):
        for v in self.data.variables:
            print(v)

    def get_sideset(self, id):
        ndx = id - 1

        if ("ss_prop1" in self.data.variables):
            ndx = numpy.where(self.data.variables["ss_prop1"][:] == id)[0][0]
            ndx += 1

        elem_key = 'elem_ss' + str(ndx)
        side_key = 'side_ss' + str(ndx)
        sideset_i = {}

        if elem_key in self.data.variables and side_key in self.data.variables:
            if ("elem_num_map" in self.data.variables):
                sideset_i['elements'] = self.data["elem_num_map"][self.data[elem_key][:]]
            else:
                sideset_i['elements'] = self.data[elem_key][:]
            sideset_i['sides'] = self.data[side_key][:]
        else:
            raise RuntimeError("sideset '{}' cannot be found!".format(id))

        return sideset_i

    def get_nodeset(self, id):
        ndx = id - 1
        if ("ns_prop1" in self.data.variables):
            ndx = numpy.where(self.data.variables["ns_prop1"][:] == id)[0][0]
            ndx += 1

        key = "node_ns" + str(ndx)
        if ("node_num_map" in self.data.variables):
            return self.data["node_num_map"][self.data[key][:]]
        return self.data[key][:]


    def set_nodeset(self, node_set_id, node_ids):
        ndx = node_set_id - 1
        if ("ns_prop1" in self.data.variables):
            ndx = numpy.where(self.data.variables["ns_prop1"][:] == node_set_id)[0][0]
            ndx += 1
        
        key = "node_ns" + str(ndx)
        nodeset = self.data[key]

        if ("node_num_map" in self.data.variables):
            indices = numpy.zeros(len(node_ids))
            i = 0
            for id in node_ids:
                ndx = numpy.where(self.data["node_num_map"][:] == id)[0][0]
                indices[i] = ndx
                i += 1
            nodeset[:] = indices
            return
        nodeset[:] = node_ids

    # def add_nodeset(self, node_ids):
    #     # self.data.createDimension("num_nod_ns4", len(node_ids))
    #     # self.data.createVariable("node_ns4", numpy.dtype('i4'), ("num_nod_ns4"))

    #     self.data.dimensions["num_node_sets"].size += 1
    #     # if ("node_num_map" not in self.data.variables):
    #     #     self.data["node_ns4"][:] = node_ids
    #     #     return

    #     # i = 0
    #     # for id in node_ids:
    #     #     ndx = numpy.where(self.data["node_num_map"][:] == id)[0][0]
    #     #     self.data["node_ns4"][i] = ndx
    #     #     i += 1
            


    # prints legacy character array as string
    @staticmethod
    def print(line):
        print(Exodus.lineparse(line))

    @staticmethod
    def lineparse(line):
        s = ""
        for c in line:
            if str(c) != '--':
                s += str(c)[2]

        return s


if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        for file in SampleFiles():
            ex = Exodus(file, 'r')
            try:
                print(ex.data)
            except KeyError:
                print("no QA record found")
        ex.close()
