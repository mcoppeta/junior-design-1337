import warnings
import netCDF4 as nc
import numpy
from ledger import Ledger


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

    # Should creating a new file (mode 'w') be a function on its own?
    def __init__(self, path, mode, shared=False, clobber=False, format='EX_NETCDF4', word_size=4):
        # clobber and format and word_size only apply to mode w
        if mode not in ['r', 'w', 'a']:
            raise ValueError("mode must be 'w', 'r', or 'a', got '{}'".format(mode))
        if format not in Exodus._FORMAT_MAP:
            raise ValueError("invalid file format: '{}'".format(format))
        if word_size not in [4, 8]:
            raise ValueError("word_size must be 4 or 8 bytes, {} is not supported".format(word_size))
        if path.split(".")[-1] not in ['e', 'ex2']:
            raise ValueError("file must be an exodus file with extension .e or .ex2")
        nc_format = Exodus._FORMAT_MAP[format]
        # Sets shared mode if the user asked for it. I have no idea what this does :)
        if shared:
            smode = mode + 's'
        else:
            smode = mode
        try:
            self.data = nc.Dataset(path, smode, clobber, format=nc_format)
        except FileNotFoundError:
            raise FileNotFoundError("file '{}' does not exist".format(path))
        except PermissionError:
            raise PermissionError("You do not have access to '{}'".format(path))
        except OSError:
            raise OSError("file '{}' exists, but clobber is set to False".format(path))

        self.mode = mode
        self.path = path
        self.clobber = clobber

        if mode == 'w' or mode == 'a':
            # This is important according to ex_open.c
            self.data.set_fill_off()
            self.ledger = Ledger(self)

        # save path variable for future use
        self.path = path

        # We will read a bunch of data here to make sure it exists and warn the user if they might want to fix their
        # file. We don't save anything to memory so that if our data updates we don't have to update it in memory too.
        # This is the same practice used in the C library so its probably a good idea.

        # Initialize all the important parameters
        if mode == 'w':
            self.data.setncattr('title', 'Untitled database')
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

        # TODO Uncomment these later
        #  The C library doesn't seem to care if the file is in read or modify mode when it does this
        # Add this if it doesn't exist (value of 33)
        # if 'len_name' not in self.data.dimensions:
        #     warnings.warn("'len_name' dimension is missing!")

        # Add this if it doesn't exist (value of 32)
        # if 'maximum_name_length' not in self.data.ncattrs():
        #     warnings.warn("'maximum_name_length' attribute is missing!")

        # Check version compatibility
        ver = self.version
        if ver < 2.0:
            raise RuntimeError(
                "Unsupported file version {:.2f}! Only versions >2.0 are supported.".format(ver))

        # Read word size stored in file
        ws = self.word_size
        if ws == 4:
            self._float = numpy.float32
        elif ws == 8:
            self._float = numpy.float64
        else:
            raise ValueError("file contains a word size of {} which is not supported".format(ws))

        if self.int64_status == 0:
            self._int = numpy.int32
        else:
            self._int = numpy.int64

    def to_float(self, n):
        # Convert a number to the floating point type the database is using
        return self._float(n)

    def to_int(self, n):
        # Convert a number to the integer type the database is using
        return self._int(n)

    @property
    def float(self):
        # Returns floating point type of floating point numbers stored in the database
        # You may use whatever crazy types you want while coding, but convert them before storing them in the DB
        return self._float

    @property
    def int(self):
        # Returns integer type of integers stored in the database
        return self._int

    # TODO fix function that adds missing parts of the header
    # TODO function to find the longest name in the object

    # Everything in here that says it's the same as C is pretty much adapted 1-1 from the SEACAS Github and has been
    # double checked for speed. (see /libraries/exodus/src/ex_inquire.c)
    # Anything that says NOT IN C doesn't appear in the C version (to my knowledge) probably because the user does
    # not need to worry about that information and the user should not be able to modify it

    ########################################################################
    #                                                                      #
    #                        Data File Utilities                           #
    #                                                                      #
    ########################################################################

    # GLOBAL PARAMETERS

    # TODO perhaps in-place properties like these could have property setters as well

    # Same as C
    @property
    def title(self):
        try:
            return self.data.getncattr('title')
        except AttributeError:
            AttributeError("Database title could not be found")

    # Same as C
    @property
    def max_allowed_name_length(self):
        max_name_len = Exodus._MAX_NAME_LENGTH
        if 'len_name' in self.data.dimensions:
            # Subtract 1 because in C an extra null character is added for C reasons
            max_name_len = self.data.dimensions['len_name'].size - 1
        return max_name_len

    # Same as C
    @property
    def max_used_name_length(self):
        # 32 is the default size consistent with other databases
        max_used_name_len = 32
        if 'maximum_name_length' in self.data.ncattrs():
            # The length does not include the added null character from C
            max_used_name_len = self.data.getncattr('maximum_name_length')
        return max_used_name_len

    # Same as C
    @property
    def api_version(self):
        try:
            result = self.data.getncattr('api_version')
        except AttributeError:
            # Try the old way of spelling it
            try:
                result = self.data.getncattr('api version')
            except AttributeError:
                raise AttributeError("Exodus API version could not be found")
        return result

    # Same as C
    @property
    def version(self):
        try:
            return self.data.getncattr('version')
        except AttributeError:
            raise AttributeError("Exodus database version could not be found")

    # Same as C
    @property
    def num_qa(self):
        try:
            result = self.data.dimensions['num_qa_rec'].size
        except KeyError:
            result = 0
        return result

    # Same as C
    @property
    def num_info(self):
        try:
            result = self.data.dimensions['num_info'].size
        except KeyError:
            result = 0
        return result

    ########################################################################
    #                                                                      #
    #                        Model Description                             #
    #                                                                      #
    ########################################################################

    # Same as C
    @property
    def num_dim(self):
        try:
            return self.data.dimensions['num_dim'].size
        except KeyError:
            raise KeyError("database dimensionality could not be found")

    # Same as C
    @property
    def num_nodes(self):
        try:
            result = self.data.dimensions['num_nodes'].size
        except KeyError:
            # This and following functions don't actually error in C, they return 0. I assume there's a good reason.
            result = 0
        return result

    # Same as C
    @property
    def num_elem(self):
        try:
            result = self.data.dimensions['num_elem'].size
        except KeyError:
            result = 0
        return result

    # Same as C
    @property
    def num_elem_blk(self):
        try:
            result = self.data.dimensions['num_el_blk'].size
        except KeyError:
            result = 0
        return result

    # Same as C
    @property
    def num_node_sets(self):
        try:
            result = self.data.dimensions['num_node_sets'].size
        except KeyError:
            result = 0
        return result

    # TODO /libraries/exodus/src/ex_inquire.c line 382 and 387 contain functions we don't have about concatenated
    #  node sets. exodusII-new.pdf section 4.10 contains related information. I have no clue what this is but it's
    #  probably important. (Line 44 of that file looks related?)

    # Same as C
    @property
    def num_side_sets(self):
        try:
            result = self.data.dimensions['num_side_sets'].size
        except KeyError:
            result = 0
        return result

    # TODO Same deal as todo above. See lines 459, 561, and 566

    # Same as C
    @property
    def num_time_steps(self):
        try:
            return self.data.dimensions['time_step'].size
        except KeyError:
            raise KeyError("Number of database time steps could not be found")

    # TODO Similar to above, all of the _PROP functions (ctrl+f ex_get_num_props)

    # Same as C
    @property
    def num_elem_map(self):
        try:
            result = self.data.dimensions['num_elem_maps'].size
        except KeyError:
            result = 0
        return result

    # Same as C
    @property
    def num_node_map(self):
        try:
            result = self.data.dimensions['num_node_maps'].size
        except KeyError:
            result = 0
        return result

    # TODO Below line 695 stuff gets really weird. What on earth even is an edge set, face set, and elem set?

    # Same as C (i think)
    @property
    def num_node_var(self):
        try:
            return self.data.dimensions['num_nod_var'].size
        except KeyError:
            raise KeyError("Number of nodal variables could not be found")

    # Same as C (i think)
    @property
    def num_elem_block_var(self):
        try:
            return self.data.dimensions['num_elem_var'].size
        except KeyError:
            raise KeyError("Number of element block variables could not be found")

    # Same as C (i think)
    @property
    def num_node_set_var(self):
        try:
            return self.data.dimensions['num_nset_var'].size
        except KeyError:
            raise KeyError("Number of node set variables could not be found")

    # Same as C (i think)
    @property
    def num_side_set_var(self):
        try:
            return self.data.dimensions['num_sset_var'].size
        except KeyError:
            raise KeyError("Number of side set variables could not be found")

    # Same as C (i think)
    @property
    def num_global_var(self):
        try:
            return self.data.dimensions['num_glo_var'].size
        except KeyError:
            raise KeyError("Number of global variables could not be found")

    # Below are accessors for some data records that the C library doesn't seem to have
    # Not sure where file_size is useful. int64_status and word_size are probably only useful on initialization.
    # max_string/max_line_length are probably only useful on writing qa/info records. We can keep these for now but
    # delete them later once we determine they're actually useless

    # Same as C
    @property
    def large_model(self):
        # According to a comment in ex_utils.c @ line 1614
        # "Basically, the difference is whether the coordinates and nodal variables are stored in a blob (xyz components
        # together) or as a variable per component per nodal_variable."
        # This is important for coordinate getter functions
        if 'file_size' in self.data.ncattrs():
            return self.data.getncattr('file_size')
        else:
            # return 1 if self.data.data_model == 'NETCDF3_64BIT_OFFSET' else 0
            return 0
            # No warning is raised because older files just don't have this

    # NOT IN C (only used in ex_open.c)
    @property
    def int64_status(self):
        # Determines whether or not the file uses int64s
        if 'int64_status' in self.data.ncattrs():
            return self.data.getncattr('int64_status')
        else:
            return 1 if self.data.data_model == 'NETCDF3_64BIT_DATA' else 0
            # No warning is raised because older files just don't have this

    # NOT IN C (only used in ex_open.c)
    @property
    def word_size(self):
        try:
            result = self.data.getncattr('floating_point_word_size')
        except AttributeError:
            try:
                result = self.data.getncattr('floating point word size')
            except AttributeError:
                # This should NEVER happen, but here to be safe
                raise AttributeError("Exodus database floating point word size could not be found")
        return result

    # NOT IN C
    @property
    def max_string_length(self):
        # See ex_put_qa.c @ line 119. This record is created and used when adding QA records
        max_str_len = Exodus._MAX_STR_LENGTH
        if 'len_string' in self.data.dimensions:
            # Subtract 1 because in C an extra character is added for C reasons
            max_str_len = self.data.dimensions['len_string'].size - 1
        return max_str_len

    # NOT IN C
    @property
    def max_line_length(self):
        # See ex_put_info.c @ line 121. This record is created and used when adding info records
        max_line_len = Exodus._MAX_LINE_LENGTH
        if 'len_line' in self.data.dimensions:
            # Subtract 1 because in C an extra character is added for C reasons
            max_line_len = self.data.dimensions['len_line'].size - 1
        return max_line_len

    # Getters for more advanced properties

    # Nodes and elements have IDs and internal values
    # As a programmer, when I call methods I pass in the internal value, which
    # is some contiguous number. Usually I identify stuff with their IDs though.
    # Internally, the method I call understands the internal value.
    # Say I have 1 element in my file with ID 100. The ID is 100, the internal
    # value is 1. In the connectivity array, '1' refers to this element. As a
    # backend person, I need to subtract 1 to index on this internal value.
    def get_node_id_map(self):
        num_nodes = self.num_nodes
        if num_nodes == 0:
            warnings.warn("Cannot retrieve a node id map if there are no nodes!")
            return
        if 'node_num_map' not in self.data.variables:
            # Return a default array from 1 to the number of nodes
            warnings.warn("There is no node id map in this database!")
            return numpy.arange(1, num_nodes + 1, dtype=self.int)
        return self.data.variables['node_num_map'][:]

    def get_partial_node_id_map(self, start, count):
        # Start is 1 based (>0).  start + count - 1 <= number of nodes
        num_nodes = self.num_nodes
        if num_nodes == 0:
            warnings.warn("Cannot retrieve a node id map if there are no nodes!")
            return
        if start < 1:
            raise ValueError("start index must be greater than 0")
        if start + count - 1 > num_nodes:
            raise ValueError("start index + node count is larger than the total number of nodes")
        if 'node_num_map' not in self.data.variables:
            # Return a default array from start to start + count exclusive
            warnings.warn("There is no node id map in this database!")
            return numpy.arange(start, start + count, dtype=self.int)
        return self.data.variables['node_num_map'][start - 1:start + count - 1]

    def get_elem_id_map(self):
        num_elem = self.num_elem
        if num_elem == 0:
            warnings.warn("Cannot retrieve an element id map if there are no elements!")
            return
        if 'elem_num_map' not in self.data.variables:
            # Return a default array from 1 to the number of elements
            warnings.warn("There is no element id map in this database!")
            return numpy.arange(1, num_elem + 1, dtype=self.int)
        return self.data.variables['elem_num_map'][:]

    def get_partial_elem_id_map(self, start, count):
        # Start is 1 based (>0).  start + count - 1 <= number of nodes
        num_elem = self.num_elem
        if num_elem == 0:
            warnings.warn("Cannot retrieve an element id map if there are no elements!")
            return
        if start < 1:
            raise ValueError("start index must be greater than 0")
        if start + count - 1 > num_elem:
            raise ValueError("start index + element count is larger than the total number of elements")
        if 'elem_num_map' not in self.data.variables:
            # Return a default array from start to start + count exclusive
            warnings.warn("There is no element id map in this database!")
            return numpy.arange(start, start + count, dtype=self.int)
        return self.data.variables['elem_num_map'][start - 1:start + count - 1]

    def get_elem_order_map(self):
        num_elem = self.num_elem
        if num_elem == 0:
            warnings.warn("Cannot retrieve an element order map if there are no elements!")
            return
        if 'elem_map' not in self.data.variables:
            # Return a default array from 1 to the number of elements
            warnings.warn("There is no element order map in this database!")
            return numpy.arange(1, num_elem + 1, dtype=self.int)
        return self.data.variables['elem_map'][:]

    # TODO what is ex_get_num_map.c?

    def get_all_times(self):
        try:
            result = self.data.variables['time_whole']
        except KeyError:
            raise KeyError("Could not retrieve timesteps from database!")
        return result[:]

    def _get_set_id(self, set_type, num):
        # Returns internal id for a set given it's user defined id (num)
        # valid sets are 'nodeset' and 'sideset'
        if set_type == 'nodeset':
            name = 'ns_prop1'
        elif set_type == 'sideset':
            name = 'ss_prop1'
        else:
            raise ValueError("{} is not a valid set type!".format(set_type))
        try:
            table = self.data.variables[name]
        except KeyError:
            raise KeyError("Set id map of type {} is missing from this database!".format(set_type))
        # The C library caches information about sets including whether its sequential so it can skip a lot of this
        internal_id = 1
        for table_id in table:
            if table_id == num:
                break
            internal_id += 1
        if internal_id > len(table):
            raise KeyError("Could not find set of type {} with id {}".format(set_type, num))
        return internal_id
        # The C library also does some crazy stuff with what might be the ns_status array

    # Theoretically we could have these call get partial set, but we would need to know the length of the set
    # which would require an extra call to _get_set_id(), which is slow, or crazy extra arguments or helper methods
    # that would increase the complexity enough to offset the added simplicity of this.
    # That probably explains why the C library doesn't do that either...
    # ...Alternatively we could put the maximum value for whatever integer type hdf5 uses but that's kinda hacky
    # OR WE COULD USE A CRAZY HELPER METHOD OOH
    # def get_set(self, set_type, id):
    #     # Returns a tuple containing the entry list and extra list of a set.
    #     # Node sets do not have an extra list and return None for the second tuple element.
    #     # Start is 1 based (>0) and count must be positive.
    #     # Without these requirements, this doesn't behave in a very pythonic way
    #     if set_type == 'nodeset':
    #         num_sets = self.num_node_sets
    #     elif set_type == 'sideset':
    #         num_sets = self.num_side_sets
    #     else:
    #         raise KeyError("Invalid set type {}!".format(set_type))
    #     if num_sets == 0:
    #         raise KeyError("No sets of type {} are stored in this database!".format(set_type))
    #     internal_id = self._get_set_id(set_type, id)
    #
    #     if set_type == 'nodeset':
    #         entry_list = 'node_ns%d' % internal_id
    #         extra_list = None
    #     elif set_type == 'sideset':
    #         entry_list = 'elem_ss%d' % internal_id
    #         extra_list = 'side_ss%d' % internal_id
    #     try:
    #         entry_set = self.data.variables[entry_list][:]
    #     except KeyError:
    #         raise KeyError("Failed to retrieve entry set of type {} with id {} ('{}')"
    #                        .format(set_type, id, entry_list))
    #
    #     if set_type == 'nodeset':
    #         return entry_set, None
    #     else:
    #         try:
    #             extra_set = self.data.variables[extra_list][:]
    #         except KeyError:
    #             raise KeyError("Failed to retrieve extra set of type {} with id {} ('{}')"
    #                            .format(set_type, id, extra_list))
    #         return entry_set, extra_set

    # def get_set_parameters(self, set_type, id):
    #     # Returns tuple (number of set entries, number of set distribution factors)
    #     if set_type == 'nodeset':
    #         num_sets = self.num_node_sets
    #         entry_name = 'num_nod_ns'
    #         # Node sets are special and don't have a df dimension. See ex_get_set_param
    #     elif set_type == 'sideset':
    #         num_sets = self.num_side_sets
    #         entry_name = 'num_side_ss'
    #         df_name = 'num_df_ss'
    #     else:
    #         raise KeyError("Invalid set type {}!".format(set_type))
    #     if num_sets == 0:
    #         raise KeyError("No sets of type {} are stored in this database!".format(set_type))
    #     internal_id = self._get_set_id(set_type, id)
    #     # Set entries
    #     try:
    #         num_entries = self.data.dimensions['%s%d' % (entry_name, internal_id)].size
    #     except KeyError:
    #         raise KeyError("Failed to retrieve number of entries in set of type {} with id {} ('{}')"
    #                        .format(set_type, id, '%s%d' % (entry_name, internal_id)))
    #     # Set dist facts
    #     if set_type == 'nodeset':
    #         # If the df variable exists num_df == num_entries, otherwise assume 0 df
    #         if ('dist_fact_ns%d' % internal_id) in self.data.variables:
    #             num_df = num_entries
    #         else:
    #             num_df = 0
    #     else:
    #         try:
    #             num_df = self.data.dimensions['%s%d' % (df_name, internal_id)].size
    #         except KeyError:
    #             raise KeyError("Failed to retrieve number of distribution factors in set of type {} with id {} ('{}')"
    #                            .format(set_type, id, '%s%d' % (df_name, internal_id)))
    #     return num_entries, num_df

    # def get_partial_set(self, set_type, id, start, count):
    #     # Returns a tuple containing the entry list and extra list of a set.
    #     # Node sets do not have an extra list and return None for the second tuple element.
    #     # Start is 1 based (>0) and count must be positive.
    #     # Without these requirements, this doesn't behave in a very pythonic way
    #     if set_type == 'nodeset':
    #         num_sets = self.num_node_sets
    #     elif set_type == 'sideset':
    #         num_sets = self.num_side_sets
    #     else:
    #         raise KeyError("Invalid set type {}!".format(set_type))
    #     if num_sets == 0:
    #         raise KeyError("No sets of type {} are stored in this database!".format(set_type))
    #     if start < 1:
    #         raise ValueError("Start index must be greater than 0")
    #     if count < 0:
    #         raise ValueError("Count must be a positive integer")
    #     internal_id = self._get_set_id(set_type, id)
    #
    #     if set_type == 'nodeset':
    #         entry_list = 'node_ns%d' % internal_id
    #         extra_list = None
    #     elif set_type == 'sideset':
    #         entry_list = 'elem_ss%d' % internal_id
    #         extra_list = 'side_ss%d' % internal_id
    #     try:
    #         entry_set = self.data.variables[entry_list][start - 1:start + count - 1]
    #     except KeyError:
    #         raise KeyError("Failed to retrieve entry set of type {} with id {} ('{}')"
    #                        .format(set_type, id, entry_list))
    #
    #     if set_type == 'nodeset':
    #         return entry_set, None
    #     else:
    #         try:
    #             extra_set = self.data.variables[extra_list][start - 1:start + count - 1]
    #         except KeyError:
    #             raise KeyError("Failed to retrieve extra set of type {} with id {} ('{}')"
    #                            .format(set_type, id, extra_list))
    #         return entry_set, extra_set

    def get_node_set(self, id):
        num_sets = self.num_node_sets
        if num_sets == 0:
            raise KeyError("No node sets are stored in this database!")
        internal_id = self._get_set_id('nodeset', id)
        try:
            set = self.data.variables['node_ns%d' % internal_id][:]
        except KeyError:
            raise KeyError("Failed to retrieve nodeset with id {} ('{}')".format(id, 'node_ns%d' % internal_id))
        return set

    def get_partial_node_set(self, id, start, count):
        num_sets = self.num_node_sets
        if num_sets == 0:
            raise KeyError("No node sets are stored in this database!")
        if start < 1:
            raise ValueError("Start index must be greater than 0")
        if count < 0:
            raise ValueError("Count must be a positive integer")
        internal_id = self._get_set_id('nodeset', id)
        try:
            set = self.data.variables['node_ns%d' % internal_id][start - 1:start + count - 1]
        except KeyError:
            raise KeyError("Failed to retrieve node set with id {} ('{}')".format(id, 'node_ns%d' % internal_id))
        return set

    def get_node_set_df(self, id):
        num_sets = self.num_node_sets
        if num_sets == 0:
            raise KeyError("No nodesets are stored in this database!")
        internal_id = self._get_set_id('nodeset', id)
        if ('dist_fact_ns%d' % internal_id) in self.data.variables:
            try:
                set = self.data.variables['dist_fact_ns%d' % internal_id][:]
            except KeyError:
                raise KeyError("Failed to retrieve distribution factors of nodeset with id {} ('{}')"
                               .format(id, 'dist_fact_ns%d' % internal_id))
            return set
        else:
            warnings.warn("This database does not contain dist factors for node set {}".format(id))
            return None

    def get_partial_node_set_df(self, id, start, count):
        num_sets = self.num_node_sets
        if num_sets == 0:
            raise KeyError("No nodesets are stored in this database!")
        if start < 1:
            raise ValueError("Start index must be greater than 0")
        if count < 0:
            raise ValueError("Count must be a positive integer")
        internal_id = self._get_set_id('nodeset', id)
        if ('dist_fact_ns%d' % internal_id) in self.data.variables:
            try:
                set = self.data.variables['dist_fact_ns%d' % internal_id][start - 1:start + count - 1]
            except KeyError:
                raise KeyError("Failed to retrieve distribution factors of nodeset with id {} ('{}')"
                               .format(id, 'dist_fact_ns%d' % internal_id))
            return set
        else:
            warnings.warn("This database does not contain dist factors for node set {}".format(id))
            return None

    def get_node_set_params(self, id):
        # Returns tuple (number of set entries, number of set distribution factors)
        num_sets = self.num_node_sets
        if num_sets == 0:
            raise KeyError("No nodesets are stored in this database!")
        internal_id = self._get_set_id('nodeset', id)
        try:
            num_entries = self.data.dimensions['num_nod_ns%d' % internal_id].size
        except KeyError:
            raise KeyError("Failed to retrieve number of entries in node set with id {} ('{}')"
                           .format(id, 'num_nod_ns%d' % internal_id))
        if ('dist_fact_ns%d' % internal_id) in self.data.variables:
            num_df = num_entries
        else:
            num_df = 0
        return num_entries, num_df

    def get_side_set(self, id):
        num_sets = self.num_side_sets
        if num_sets == 0:
            raise KeyError("No sidesets are stored in this database!")
        internal_id = self._get_set_id('sideset', id)
        try:
            elmset = self.data.variables['elem_ss%d' % internal_id][:]
        except KeyError:
            raise KeyError(
                "Failed to retrieve elements of sideset with id {} ('{}')".format(id, 'elem_ss%d' % internal_id))
        try:
            sset = self.data.variables['side_ss%d' % internal_id][:]
        except KeyError:
            raise KeyError(
                "Failed to retrieve sides of sideset with id {} ('{}')".format(id, 'side_ss%d' % internal_id))
        return elmset, sset

    def get_partial_side_set(self, id, start, count):
        num_sets = self.num_side_sets
        if num_sets == 0:
            raise KeyError("No side sets are stored in this database!")
        if start < 1:
            raise ValueError("Start index must be greater than 0")
        if count < 0:
            raise ValueError("Count must be a positive integer")
        internal_id = self._get_set_id('sideset', id)
        try:
            elmset = self.data.variables['elem_ss%d' % internal_id][start - 1:start + count - 1]
        except KeyError:
            raise KeyError(
                "Failed to retrieve elements of side set with id {} ('{}')".format(id, 'elem_ss%d' % internal_id))
        try:
            sset = self.data.variables['side_ss%d' % internal_id][start - 1:start + count - 1]
        except KeyError:
            raise KeyError(
                "Failed to retrieve sides of side set with id {} ('{}')".format(id, 'side_ss%d' % internal_id))
        return elmset, sset

    def get_side_set_df(self, id):
        num_sets = self.num_side_sets
        if num_sets == 0:
            raise KeyError("No sidesets are stored in this database!")
        internal_id = self._get_set_id('sideset', id)
        try:
            set = self.data.variables['dist_fact_ss%d' % internal_id][:]
        except KeyError:
            raise KeyError("Failed to retrieve distribution factors of sideset with id {} ('{}')"
                           .format(id, 'dist_fact_ss%d' % internal_id))
        return set

    def get_partial_side_set_df(self, id, start, count):
        num_sets = self.num_side_sets
        if num_sets == 0:
            raise KeyError("No sidesets are stored in this database!")
        if start < 1:
            raise ValueError("Start index must be greater than 0")
        if count < 0:
            raise ValueError("Count must be a positive integer")
        internal_id = self._get_set_id('sideset', id)
        try:
            set = self.data.variables['dist_fact_ss%d' % internal_id][start - 1:start + count - 1]
        except KeyError:
            raise KeyError("Failed to retrieve distribution factors of sideset with id {} ('{}')"
                           .format(id, 'dist_fact_ss%d' % internal_id))
        return set

    def get_side_set_params(self, id):
        # Returns tuple (number of set entries, number of set distribution factors)
        num_sets = self.num_side_sets
        if num_sets == 0:
            raise KeyError("No side sets are stored in this database!")
        internal_id = self._get_set_id('sideset', id)
        try:
            num_entries = self.data.dimensions['num_side_ss%d' % internal_id].size
        except KeyError:
            raise KeyError("Failed to retrieve number of entries in side set with id {} ('{}')"
                           .format(id, 'num_side_ss%d' % internal_id))
        try:
            num_df = self.data.dimensions['num_df_ss%d' % internal_id].size
        except KeyError:
            raise KeyError("Failed to retrieve number of distribution factors in side set with id {} ('{}')"
                           .format(id, 'num_df_ss%d' % internal_id))
        return num_entries, num_df

    def get_coords(self):
        dim_cnt = self.num_dim
        num_nodes = self.num_nodes
        if num_nodes == 0:
            return []
        large = self.large_model
        if not large:
            try:
                coord = self.data.variables['coord'][:]
            except KeyError:
                raise KeyError("Failed to retrieve nodal coordinate array!")
        else:
            try:
                coordx = self.data.variables['coordx'][:]
            except KeyError:
                raise KeyError("Failed to retrieve x axis nodal coordinate array!")
            if dim_cnt > 1:
                try:
                    coordy = self.data.variables['coordy'][:]
                except KeyError:
                    raise KeyError("Failed to retrieve y axis nodal coordinate array!")
                if dim_cnt > 2:
                    try:
                        coordz = self.data.variables['coordz'][:]
                    except KeyError:
                        raise KeyError("Failed to retrieve z axis nodal coordinate array!")
                    coord = numpy.array([coordx, coordy, coordz])
                else:
                    coord = numpy.array([coordx, coordy])
            else:
                coord = coordx
        return coord

    def get_partial_coords(self, start, count):
        if start < 1:
            raise ValueError("Start index must be greater than 0")
        if count < 0:
            raise ValueError("Count must be a positive integer")
        dim_cnt = self.num_dim
        num_nodes = self.num_nodes
        if num_nodes == 0:
            return []
        large = self.large_model
        if not large:
            try:
                coord = self.data.variables['coord'][:, start - 1:start + count - 1]
            except KeyError:
                raise KeyError("Failed to retrieve nodal coordinate array!")
        else:
            try:
                coordx = self.data.variables['coordx'][start - 1:start + count - 1]
            except KeyError:
                raise KeyError("Failed to retrieve x axis nodal coordinate array!")
            if dim_cnt > 1:
                try:
                    coordy = self.data.variables['coordy'][start - 1:start + count - 1]
                except KeyError:
                    raise KeyError("Failed to retrieve y axis nodal coordinate array!")
                if dim_cnt > 2:
                    try:
                        coordz = self.data.variables['coordz'][start - 1:start + count - 1]
                    except KeyError:
                        raise KeyError("Failed to retrieve z axis nodal coordinate array!")
                    coord = numpy.array([coordx, coordy, coordz])
                else:
                    coord = numpy.array([coordx, coordy])
            else:
                coord = coordx
        return coord

    def get_coord_x(self):
        num_nodes = self.num_nodes
        if num_nodes == 0:
            return []
        large = self.large_model
        if not large:
            try:
                coord = self.data.variables['coord'][0]
            except KeyError:
                raise KeyError("Failed to retrieve nodal coordinate array!")
        else:
            try:
                coord = self.data.variables['coordx'][:]
            except KeyError:
                raise KeyError("Failed to retrieve x axis nodal coordinate array!")
        return coord

    def get_partial_coord_x(self, start, count):
        if start < 1:
            raise ValueError("Start index must be greater than 0")
        if count < 0:
            raise ValueError("Count must be a positive integer")
        num_nodes = self.num_nodes
        if num_nodes == 0:
            return []
        large = self.large_model
        if not large:
            try:
                coord = self.data.variables['coord'][0][start - 1:start + count - 1]
            except KeyError:
                raise KeyError("Failed to retrieve nodal coordinate array!")
        else:
            try:
                coord = self.data.variables['coordx'][start - 1:start + count - 1]
            except KeyError:
                raise KeyError("Failed to retrieve x axis nodal coordinate array!")
        return coord

    def get_coord_y(self):
        dim_cnt = self.num_dim
        num_nodes = self.num_nodes
        if num_nodes == 0 or dim_cnt < 2:
            return []
        large = self.large_model
        if not large:
            try:
                coord = self.data.variables['coord'][1]
            except KeyError:
                raise KeyError("Failed to retrieve nodal coordinate array!")
        else:
            try:
                coord = self.data.variables['coordy'][:]
            except KeyError:
                raise KeyError("Failed to retrieve y axis nodal coordinate array!")
        return coord

    def get_partial_coord_y(self, start, count):
        if start < 1:
            raise ValueError("Start index must be greater than 0")
        if count < 0:
            raise ValueError("Count must be a positive integer")
        dim_cnt = self.num_dim
        num_nodes = self.num_nodes
        if num_nodes == 0 or dim_cnt < 2:
            return []
        large = self.large_model
        if not large:
            try:
                coord = self.data.variables['coord'][1][start - 1:start + count - 1]
            except KeyError:
                raise KeyError("Failed to retrieve nodal coordinate array!")
        else:
            try:
                coord = self.data.variables['coordy'][start - 1:start + count - 1]
            except KeyError:
                raise KeyError("Failed to retrieve y axis nodal coordinate array!")
        return coord

    def get_coord_z(self):
        dim_cnt = self.num_dim
        num_nodes = self.num_nodes
        if num_nodes == 0 or dim_cnt < 3:
            return []
        large = self.large_model
        if not large:
            try:
                coord = self.data.variables['coord'][2]
            except KeyError:
                raise KeyError("Failed to retrieve nodal coordinate array!")
        else:
            try:
                coord = self.data.variables['coordz'][:]
            except KeyError:
                raise KeyError("Failed to retrieve z axis nodal coordinate array!")
        return coord

    def get_partial_coord_z(self, start, count):
        if start < 1:
            raise ValueError("Start index must be greater than 0")
        if count < 0:
            raise ValueError("Count must be a positive integer")
        dim_cnt = self.num_dim
        num_nodes = self.num_nodes
        if num_nodes == 0 or dim_cnt < 3:
            return []
        large = self.large_model
        if not large:
            try:
                coord = self.data.variables['coord'][2][start - 1:start + count - 1]
            except KeyError:
                raise KeyError("Failed to retrieve nodal coordinate array!")
        else:
            try:
                coord = self.data.variables['coordz'][start - 1:start + count - 1]
            except KeyError:
                raise KeyError("Failed to retrieve z axis nodal coordinate array!")
        return coord

    def get_coord_names(self):
        try:
            names = self.data.variables['coor_names']
        except KeyError:
            raise KeyError("Failed to retrieve coordinate name array!")
        name = numpy.empty([3], str)
        for i in range(len(names)):
            name[i] = self.lineparse(names[i])
        return name

    # TODO What are coordinate frames?

    # TODO info, time, truth table, among others

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

    @property
    def time_values(self):
        """Returns a list of (float) time values for each time step"""
        values = []
        for step in self.time_steps:
            values.append(self.time_at_step(step))
        return values

    @property
    def time_steps(self):
        """Returns list of the time steps, 0-indexed"""
        return [*range(self.num_time_steps)]

    def time_at_step(self, step):
        """Given an integer time step, return the corresponding float time value"""
        return float(self.data['time_whole'][step].data)

    def step_at_time(self, time):
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

    def set_nodeset(self, node_set_id, node_ids):
        ndx = node_set_id - 1
        if "ns_prop1" in self.data.variables:
            ndx = numpy.where(self.data.variables["ns_prop1"][:] == node_set_id)[0][0]
            ndx += 1

        key = "node_ns" + str(ndx)
        nodeset = self.data[key]

        if "node_num_map" in self.data.variables:
            indices = numpy.zeros(len(node_ids))
            i = 0
            for id in node_ids:
                ndx = numpy.where(self.data["node_num_map"][:] == id)[0][0]
                indices[i] = ndx
                i += 1
            nodeset[:] = indices
            return
        nodeset[:] = node_ids

    #   def add_nodeset(self, node_ids):
    #       self.data.createDimension("num_nod_ns4", len(node_ids))
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

    def get_nodes_in_elblock(self, id):
        if "node_num_map" in self.data.variables:
            raise Exception("Using node num map")
        nodeids = self.data["connect" + str(id)]
        # flatten it into 1d
        nodeids = nodeids[:].flatten()
        return nodeids

    ################################################################
    #                                                              #
    #                        Write                                 #
    #                                                              #
    ################################################################

    def edit_coords(self, node_ids, dim, displace):
        if "node_num_map" in self.data.variables:
            raise Exception("Using node num map")
        node_ndxs = node_ids - 1
        dimnum = 0
        if dim == 'y':
            dimnum = 1
        elif dim == 'z':
            dimnum = 2
        self.data["coord"][dimnum, node_ndxs] += displace

    def add_nodeset(self, node_ids, nodeset_id):
        if self.mode != 'w' or self.mode != 'a':
            raise PermissionError("Need to be in write or append mode to add nodeset")
        self.ledger.add_nodeset(node_ids, nodeset_id)

    def remove_nodeset(self, nodeset_id):
        if self.mode != 'w' or self.mode != 'a':
            raise PermissionError("Need to be in write or append mode to add nodeset")
        self.ledger.remove_nodeset(nodeset_id)

    def merge_nodeset(self, new_id, ns1, ns2):
        if self.mode != 'w' or self.mode != 'a':
            raise PermissionError("Need to be in write or append mode to add nodeset")
        self.ledger.merge_nodesets(new_id, ns1, ns2)

    def write(self):
        if self.mode == 'w':
            self.ledger.write(self.path)
        elif self.mode == 'a':
            if self.clobber:
                self.ledger.write(self.path)
            else:
                path = self.path.split('.')[:-1]
                self.ledger.write(path + "_revision.ex2")

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
    ex = Exodus("sample-files/cube_1ts_mod.e", 'r')
