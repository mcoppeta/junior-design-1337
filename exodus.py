import builtins
import warnings
import netCDF4 as nc
import numpy
from typing import Tuple
from ledger import Ledger
import util
from constants import *
from dataclasses import dataclass


@dataclass
class ElemBlockParam:
    """Stores data used to create a side set node count list."""
    # Adapted from exodusII_int.h on SEACAS
    elem_type_str: str
    elem_blk_id: numpy.int64
    num_elem_in_blk: numpy.int64
    num_nodes_per_elem: int
    num_sides: int
    num_nodes_per_side: numpy.ndarray
    num_attr: int
    elem_ctr: numpy.int64
    elem_type_val: ElementTopography


class Exodus:
    _FORMAT_MAP = {'EX_NETCDF4': 'NETCDF4',
                   'EX_LARGE_MODEL': 'NETCDF3_64BIT_OFFSET',
                   'EX_NORMAL_MODEL': 'NETCDF3_CLASSIC',
                   'EX_64BIT_DATA': 'NETCDF3_64BIT_DATA'}
    # Default values
    _MAX_STR_LENGTH = 32
    _MAX_STR_LENGTH_T = 'U32'
    _MAX_NAME_LENGTH = 32
    _MAX_LINE_LENGTH = 80
    _MAX_LINE_LENGTH_T = 'U80'
    _EXODUS_VERSION = 7.22

    # Should creating a new file (mode 'w') be a function on its own?
    def __init__(self, path, mode, shared=False, format='EX_NETCDF4', word_size=4):
        # clobber and format and word_size only apply to mode w
        if mode not in ['r', 'w', 'a']:
            raise ValueError("mode must be 'w', 'r', or 'a', got '{}'".format(mode))
        if format not in Exodus._FORMAT_MAP.keys():
            raise ValueError("invalid file format: '{}'".format(format))
        if word_size not in [4, 8]:
            raise ValueError("word_size must be 4 or 8 bytes, {} is not supported".format(word_size))
        nc_format = Exodus._FORMAT_MAP[format]

        self.mode = mode
        self.path = path

        # file should never actually be opened in append mode
        # if append mode is specified, open file in read mode and write out changes to separate file
        if mode == 'a':
            mode = 'r'

        # Sets shared mode if the user asked for it. I have no idea what this does :)
        if shared:
            smode = mode + 's'
        else:
            smode = mode
        try:
            self.data = nc.Dataset(path, smode, clobber=False, format=nc_format)
        except FileNotFoundError:
            raise FileNotFoundError("file '{}' does not exist".format(path)) from None
        except PermissionError:
            raise PermissionError("You do not have access to '{}'".format(path)) from None
        # TODO this can actually hide some errors which is bad. This check should be done explicitly
        except OSError:
            raise OSError("file '{}' already exists".format(path)) from None



        if self.mode == 'w':
            # This is important according to ex_open.c
            self.data.set_fill_off()

        if self.mode == 'a' or self.mode == 'w':
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

        # important for storing names in numpy arrays
        self._MAX_NAME_LENGTH_T = 'U%s' % self.max_allowed_name_length

    def to_float(self, n):
        """Returns ``n`` converted to the floating-point type stored in the database."""
        # Convert a number to the floating point type the database is using
        return self._float(n)

    def to_int(self, n):
        """Returns ``n`` converted to the integer type stored in the database."""
        # Convert a number to the integer type the database is using
        return self._int(n)

    @property
    def float(self):
        """The floating-point type stored in the database."""
        # Returns floating point type of floating point numbers stored in the database
        # You may use whatever crazy types you want while coding, but convert them before storing them in the DB
        return self._float

    @property
    def int(self):
        """The integer type stored in the database."""
        # Returns integer type of integers stored in the database
        return self._int

    ########################################################################
    #                                                                      #
    #                        Data File Utilities                           #
    #                                                                      #
    ########################################################################

    # GLOBAL PARAMETERS AND MODEL DEFINITION

    # region Properties

    # TODO perhaps in-place properties like these could have property setters as well

    # TODO it would be nice to have the return values cached for these so they execute faster and act more like
    #  properties and less like small functions. This will require some write integration.

    @property
    def title(self):
        """The database title."""
        try:
            return self.data.getncattr(ATT_TITLE)
        except AttributeError:
            AttributeError("Database title could not be found")

    @property
    def max_allowed_name_length(self):
        """The maximum allowed length for variable/dimension/attribute names in this database."""
        max_name_len = Exodus._MAX_NAME_LENGTH
        if DIM_NAME_LENGTH in self.data.dimensions:
            # Subtract 1 because in C an extra null character is added for C reasons
            max_name_len = self.data.dimensions[DIM_NAME_LENGTH].size - 1
        return max_name_len

    @property
    def max_used_name_length(self):
        """The maximum used length for variable/dimension/attribute names in this database."""
        # 32 is the default size consistent with other databases
        max_used_name_len = 32
        if ATT_MAX_NAME_LENGTH in self.data.ncattrs():
            # The length does not include the added null character from C
            max_used_name_len = self.data.getncattr(ATT_MAX_NAME_LENGTH)
        return max_used_name_len

    @property
    def max_string_length(self):
        """Maximum QA record string length."""
        # See ex_put_qa.c @ line 119. This record is created and used when adding QA records
        max_str_len = Exodus._MAX_STR_LENGTH
        if DIM_STRING_LENGTH in self.data.dimensions:
            # Subtract 1 because in C an extra character is added for C reasons
            max_str_len = self.data.dimensions[DIM_STRING_LENGTH].size - 1
        return max_str_len

    @property
    def max_line_length(self):
        """Maximum info record line length."""
        # See ex_put_info.c @ line 121. This record is created and used when adding info records
        max_line_len = Exodus._MAX_LINE_LENGTH
        if DIM_LINE_LENGTH in self.data.dimensions:
            # Subtract 1 because in C an extra character is added for C reasons
            max_line_len = self.data.dimensions[DIM_LINE_LENGTH].size - 1
        return max_line_len

    @property
    def api_version(self):
        """The Exodus API version this database was built with."""
        try:
            result = self.data.getncattr(ATT_API_VER)
        except AttributeError:
            # Try the old way of spelling it
            try:
                result = self.data.getncattr(ATT_API_VER_OLD)
            except AttributeError:
                raise AttributeError("Exodus API version could not be found")
        return result

    @property
    def version(self):
        """The Exodus version this database uses."""
        try:
            return self.data.getncattr(ATT_VERSION)
        except AttributeError:
            raise AttributeError("Exodus database version could not be found")

    @property
    def large_model(self):
        """
        Describes how coordinates are stored in this database.

        If true: nodal coordinates and variables are stored in separate x, y, z variables.
        If false: nodal coordinates and variables are stored in a single variable.

        :return: 1 if stored separately (large), 0 if stored in a blob
        """
        # According to a comment in ex_utils.c @ line 1614
        # "Basically, the difference is whether the coordinates and nodal variables are stored in a blob (xyz components
        # together) or as a variable per component per nodal_variable."
        # This is important for coordinate getter functions
        if ATT_FILE_SIZE in self.data.ncattrs():
            return self.data.getncattr(ATT_FILE_SIZE)
        else:
            return 0
            # No warning is raised because older files just don't have this

    @property
    def int64_status(self):
        """
        64-bit integer support for this database.

        Use ``int()`` to get the integer type used by this database.

        :return: 1 if 64-bit integers are supported, 0 otherwise
        """
        # Determines whether the file uses int64s
        if ATT_64BIT_INT in self.data.ncattrs():
            return self.data.getncattr(ATT_64BIT_INT)
        else:
            return 1 if self.data.data_model == 'NETCDF3_64BIT_DATA' else 0
            # No warning is raised because older files just don't have this

    @property
    def word_size(self):
        """
        Word size of floating point variables in this database.

        Use ``float()`` to get the float type used by this database.

        :return: floating point word size
        """
        try:
            result = self.data.getncattr(ATT_WORD_SIZE)
        except AttributeError:
            try:
                result = self.data.getncattr(ATT_WORD_SIZE_OLD)
            except AttributeError:
                # This should NEVER happen, but here to be safe
                raise AttributeError("Exodus database floating point word size could not be found")
        return result

    @property
    def num_qa(self):
        """Number of QA records."""
        try:
            result = self.data.dimensions[DIM_NUM_QA].size
        except KeyError:
            result = 0
        return result

    @property
    def num_info(self):
        """Number of info records."""
        try:
            result = self.data.dimensions[DIM_NUM_INFO].size
        except KeyError:
            result = 0
        return result

    @property
    def num_dim(self):
        """Number of dimensions (coordinate axes) used in the model."""
        try:
            return self.data.dimensions[DIM_NUM_DIM].size
        except KeyError:
            raise KeyError("Database dimensionality could not be found")

    @property
    def num_nodes(self):
        """Number of nodes stored in this database."""
        try:
            result = self.data.dimensions[DIM_NUM_NODES].size
        except KeyError:
            # This and following functions don't actually error in C, they return 0. I assume there's a good reason.
            result = 0
        return result

    @property
    def num_elem(self):
        """Number of elements stored in this database."""
        if self.mode == 'w' or self.mode == 'a':
            return self.ledger.num_elem()

        try:
            result = self.data.dimensions[DIM_NUM_ELEM].size
        except KeyError:
            result = 0
        return result

    @property
    def num_elem_blk(self):
        """Number of element blocks stored in this database."""
        if self.mode == 'w' or self.mode == 'a':
            return self.ledger.num_elem_blocks()

        try:
            result = self.data.dimensions[DIM_NUM_EB].size
        except KeyError:
            result = 0
        return result

    @property
    def num_node_sets(self):
        """Number of node sets stored in this database."""
        if self.mode == 'w' or self.mode == 'a':
            return self.ledger.num_node_sets()

        try:
            result = self.data.dimensions[DIM_NUM_NS].size
        except KeyError:
            result = 0
        return result

    @property
    def num_side_sets(self):
        """Number of side sets stored in this database."""
        try:
            result = self.data.dimensions[DIM_NUM_SS].size
        except KeyError:
            result = 0
        return result

    @property
    def num_time_steps(self):
        """Number of time steps stored in this database."""
        try:
            return self.data.dimensions[DIM_NUM_TIME_STEP].size
        except KeyError:
            raise KeyError("Number of database time steps could not be found")

    @property
    def num_elem_block_prop(self):
        """Number of element block properties in this database."""
        return self._get_num_object_properties(VAR_EB_PROP)

    @property
    def num_node_set_prop(self):
        """Number of node set properties in this database."""
        return self._get_num_object_properties(VAR_NS_PROP)

    @property
    def num_side_set_prop(self):
        """Number of side set properties in this database."""
        return self._get_num_object_properties(VAR_SS_PROP)

    @property
    def num_global_var(self):
        """Number of global variables."""
        try:
            return self.data.dimensions[DIM_NUM_GLO_VAR].size
        except KeyError:
            return 0

    @property
    def num_node_var(self):
        """Number of nodal variables."""
        try:
            return self.data.dimensions[DIM_NUM_NOD_VAR].size
        except KeyError:
            return 0

    @property
    def num_elem_block_var(self):
        """Number of elemental variables."""
        if self.mode == 'w' or self.mode == 'a':
            return self.ledger.num_elem_variable()

        try:
            return self.data.dimensions[DIM_NUM_ELEM_VAR].size
        except KeyError:
            return 0

    @property
    def num_node_set_var(self):
        """Number of node set variables."""
        try:
            return self.data.dimensions[DIM_NUM_NS_VAR].size
        except KeyError:
            return 0

    @property
    def num_side_set_var(self):
        """Number of side set variables."""
        try:
            return self.data.dimensions[DIM_NUM_SS_VAR].size
        except KeyError:
            return 0

    # endregion

    # MODEL VARIABLE ACCESSORS

    # region Get methods

    ##############
    # Order maps #
    ##############

    def get_elem_order_map(self):
        """Returns the optional element order map for this database."""
        num_elem = self.num_elem
        if num_elem == 0:
            warnings.warn("Cannot retrieve an element order map if there are no elements!")
            return
        if VAR_ELEM_ORDER_MAP not in self.data.variables:
            # Return a default array from 1 to the number of elements
            warnings.warn("There is no element order map in this database!")
            return numpy.arange(1, num_elem + 1, dtype=self.int)
        return self.data.variables[VAR_ELEM_ORDER_MAP][:]

    # OK so we have two types of maps on the database: ID maps & ORDER maps (also called NUMBER maps).
    # ID maps used to be called number maps and number maps used to be called order maps, which is super confusing.
    # This library supports the classic element order map (as defined in Exodus II API documentation), but does not
    # support the new 'number maps' that the SEACAS C library has support for.

    ###########
    # ID maps #
    ###########

    # Below is an explanation of entity IDs in lieu of a proper one in any official documentation.
    # Nodes and elements have two IDs: an internal ID used by Exodus and all Exodus libraries, and a user-defined ID
    # used by analysts interacting with the database. To translate user-defined IDs to internal IDs, Exodus files store
    # an optional node ID map and element ID map. If they are not defined, user-defined IDs = internal IDs. This map
    # stores the user-defined ID for an entity at the index internal ID-1. We subtract 1 from the internal ID because
    # internal IDs are 1-based, meaning they start counting up from 1, not 0!
    # When working with element connectivity lists, we have to manually calculate the internal ID of each element since
    # connectivity lists do not store element IDs, only their constituent nodes.
    # The general formula to get the internal ID of the element at index i of element block n is as follows:
    # offset = sum(num_elem_in_block(1), num_elem_in_block(2), ..., num_elem_in_block(n - 1);
    # internal_id = offset + i + 1;
    # Example: EB1 has 7 elements, EB2 has 10 elements. The internal ID of the 4th element in EB2 is 7 + 3 + 1

    def get_node_id_map(self):
        """Return the node ID map for this database."""
        num_nodes = self.num_nodes
        return self.get_partial_node_id_map(1, num_nodes)

    def get_reverse_node_id_dict(self):
        """Returns a dictionary with user-defined IDs as the keys and internal IDs as the values."""
        nim = self.get_node_id_map()
        u2i_map = {}
        for i in range(self.num_nodes):
            u2i_map[nim[i]] = i + 1
        return u2i_map

    def get_partial_node_id_map(self, start, count):
        """
        Return a subset of the node ID map for this database.

        Subset starts at node number ``start`` (1-based) and contains ``count`` elements.
        """
        # Start is 1 based (>0).  start + count - 1 <= number of nodes
        num_nodes = self.num_nodes
        if num_nodes == 0:
            raise KeyError("Cannot retrieve a node id map if there are no nodes!")
        if start < 1:
            raise ValueError("start index must be greater than 0")
        if start + count - 1 > num_nodes:
            raise ValueError("start index + node count is larger than the total number of nodes")
        if VAR_NODE_ID_MAP not in self.data.variables:
            # Return a default array from start to start + count exclusive
            warnings.warn("There is no node id map in this database!")
            return numpy.arange(start, start + count, dtype=self.int)
        return self.data.variables[VAR_NODE_ID_MAP][start - 1:start + count - 1]

    def get_elem_id_map(self):
        """Return the element ID map for this database."""
        num_elem = self.num_elem
        return self.get_partial_elem_id_map(1, num_elem)

    def get_reverse_elem_id_dict(self):
        """Returns a dictionary with user-defined IDs as the keys and internal IDs as the values."""
        eim = self.get_elem_id_map()
        u2i_map = {}
        for i in range(self.num_elem):
            u2i_map[eim[i]] = i + 1
        return u2i_map

    def get_partial_elem_id_map(self, start, count):
        """
        Return a subset of the element ID map for this database.

        Subset starts at element number ``start`` (1-based) and contains ``count`` elements.
        """
        # Start is 1 based (>0).  start + count - 1 <= number of nodes
        if self.mode == 'w' or self.mode == 'a':
            return self.ledger.get_elem_num_map()[start - 1:start + count - 1]

        num_elem = self.num_elem
        if num_elem == 0:
            raise KeyError("Cannot retrieve a element id map if there are no elements!")
        if start < 1:
            raise ValueError("start index must be greater than 0")
        if start + count - 1 > num_elem:
            raise ValueError("start index + element count is larger than the total number of elements")
        if VAR_ELEM_ID_MAP not in self.data.variables:
            # Return a default array from start to start + count exclusive
            warnings.warn("There is no element id map in this database!")
            return numpy.arange(start, start + count, dtype=self.int)
        return self.data.variables[VAR_ELEM_ID_MAP][start - 1:start + count - 1]

    def get_elem_id_map_for_block(self, obj_id):
        """Reads the element ID map for the element block with specified ID."""
        if self.num_elem_blk == 0:
            raise KeyError("There are no element blocks in this database!")
        internal_id = self._lookup_id(ELEMBLOCK, obj_id)
        num_elem, _, _, _ = self._int_get_elem_block_params(obj_id, internal_id)
        offset = 0
        emap = self.get_elem_id_map()
        for i in range(1, internal_id):
            n, _, _, _ = self._int_get_elem_block_params(emap[i - 1], i)
            offset += n
        return self.get_partial_elem_id_map(offset + 1, num_elem)

    def get_node_set_id_map(self):
        """Returns the id map for node sets (ns_prop1)."""
        if self.mode == 'w' or self.mode == 'a':
            return self.ledger.get_node_set_id_map()

        try:
            table = self.data.variables[VAR_NS_ID_MAP][:]
        except KeyError:
            raise KeyError("Node set id map is missing from this database!".format(type))
        return table

    def get_side_set_id_map(self):
        """Returns the id map for side sets (ss_prop1)."""
        try:
            table = self.data.variables[VAR_SS_ID_MAP][:]
        except KeyError:
            raise KeyError("Side set id map is missing from this database!".format(type))
        return table

    def get_elem_block_id_map(self):
        """Returns the id map for element blocks (eb_prop1)."""
        if self.mode == 'w' or self.mode == 'a':
            return self.ledger.get_eb_prop1()[:]

        try:
            table = self.data.variables[VAR_EB_ID_MAP][:]
        except KeyError:
            raise KeyError("Element block id map is missing from this database!".format(type))
        return table

    def _lookup_id(self, obj_type: ObjectType, num):
        """
        Returns the internal ID of a set or block of the given type and user-defined ID.

        FOR INTERNAL USE ONLY!

        :param obj_type: type of object this id refers to
        :param num: user-defined ID (aka number) of the set/block
        :return: internal ID
        """
        if obj_type == NODESET:
            table = self.get_node_set_id_map()
        elif obj_type == SIDESET:
            table = self.get_side_set_id_map()
        elif obj_type == ELEMBLOCK:
            table = self.get_elem_block_id_map()
        else:
            raise ValueError("{} is not a valid set/block type!".format(obj_type))
        # The C library caches information about sets including whether its sequential, so it can skip a lot of this
        internal_id = 1
        for table_id in table:
            if table_id == num:
                break
            internal_id += 1
        if internal_id > len(table):
            raise KeyError("Could not find set/block of type {} with id {}".format(obj_type, num))
        return internal_id
        # The C library also does some crazy stuff with what might be the ns_status array

    def get_node_set_number(self, obj_id):
        """
        Returns the internal ID (1-based) of the node set with the user-defined ID.

        Note that this function is O(n) complexity for n number of node sets. While useful for quick tests, you should
        create an ID lookup table yourself if you plan to convert IDs often.
        """
        return self._lookup_id(NODESET, obj_id)

    def get_side_set_number(self, obj_id):
        """
        Returns the internal ID (1-based) of the side set with the user-defined ID.

        Note that this function is O(n) complexity for n number of node sets. While useful for quick tests, you should
        create an ID lookup table yourself if you plan to convert IDs often.
        """
        return self._lookup_id(SIDESET, obj_id)

    def get_elem_block_number(self, obj_id):
        """
        Returns the internal ID (1-based) of the elem block with the user-defined ID.

        Note that this function is O(n) complexity for n number of node sets. While useful for quick tests, you should
        create an ID lookup table yourself if you plan to convert IDs often.
        """
        return self._lookup_id(ELEMBLOCK, obj_id)

    ############################
    # Variables and time steps #
    ############################

    def get_all_times(self):
        """Returns an array of all time values from all time steps from this database."""
        try:
            result = self.data.variables[VAR_TIME_WHOLE][:]
        except KeyError:
            raise KeyError("Could not retrieve time steps from database!")
        return result

    def get_time(self, time_step):
        """
        Returns the time value for specified time step.

        Time steps are 1-indexed. The first time step is at 1, and the last at num_time_steps.
        """
        num_steps = self.num_time_steps
        if num_steps <= 0:
            raise ValueError("There are no time steps in this database!")
        if time_step <= 0 or time_step > num_steps:
            raise ValueError("Time step out of range. Got {}".format(time_step))
        return self.get_all_times()[time_step - 1]

    def get_nodal_var_at_time(self, time_step, var_index):
        """
        Returns the values of the nodal variable with given index at specified time step.

        Time step and variable index are both 1-based. First time step is at 1, last at num_time_steps.
        """
        return self.get_nodal_var_across_times(time_step, time_step, var_index)[0]

    def get_nodal_var_across_times(self, start_time_step, end_time_step, var_index):
        """
        Returns the values of the nodal variable with given index between specified time steps (inclusive).

        Time steps and variable index are both 1-based. First time step is at 1, last at num_time_steps.
        """
        return self.get_partial_nodal_var_across_times(start_time_step, end_time_step, var_index, 1, self.num_nodes)

    def get_partial_nodal_var_across_times(self, start_time_step, end_time_step, var_index, start_index, count):
        """
        Returns partial values of a nodal variable between specified time steps (inclusive).

        Time steps, variable index, ID and start index are all 1-based. First time step is at 1, last at num_time_steps.
        Array starts at element number ``start`` (1-based) and contains ``count`` elements.
        """
        if self.num_nodes == 0:
            return [[]]
        num_steps = self.num_time_steps
        if num_steps <= 0:
            raise ValueError("There are no time steps in this database!")
        if start_time_step <= 0 or start_time_step > num_steps:
            raise ValueError("Start time step out of range. Got {}".format(start_time_step))
        if end_time_step <= 0 or end_time_step < start_time_step or end_time_step > num_steps:
            raise ValueError("End time step out of range. Got {}".format(end_time_step))
        if var_index <= 0 or var_index > self.num_node_var:
            raise ValueError("Variable index out of range. Got {}".format(var_index))
        if start_index <= 0:
            raise ValueError("Start index must be greater than 0")
        if count < 0:
            raise ValueError("Count must be a positive integer")
        if not self.large_model:
            # All vars stored in one variable
            try:
                # Do not subtract 1 from end (inclusive)
                result = self.data.variables[VAR_VALS_NOD_VAR_SMALL][
                         start_time_step - 1:end_time_step, var_index - 1, start_index - 1:start_index + count - 1]
            except KeyError:
                raise KeyError("Could not find the nodal variables in this database!")
        else:
            # Each var to its own variable
            try:
                result = self.data.variables[VAR_VALS_NOD_VAR_LARGE % var_index][start_time_step - 1:end_time_step, :]
            except KeyError:
                raise KeyError("Could not find nodal variable {} in this database!".format(var_index))
        return result

    def get_global_vars_at_time(self, time_step):
        """
        Returns the values of the all global variables at specified time step.

        Time steps are 1-based. First time step is at 1, last at num_time_steps.
        """
        return self.get_global_vars_across_times(time_step, time_step)[0]

    def get_global_vars_across_times(self, start_time_step, end_time_step):
        """
        Returns the values of the all global variables between specified time steps (inclusive).

        Time steps are 1-based. First time step is at 1, last at num_time_steps.
        """
        num_steps = self.num_time_steps
        if num_steps <= 0:
            raise ValueError("There are no time steps in this database!")
        if start_time_step <= 0 or start_time_step > num_steps:
            raise ValueError("Time step out of range. Got {}".format(start_time_step))
        if end_time_step <= 0 or end_time_step < start_time_step or end_time_step > num_steps:
            raise ValueError("End time step out of range. Got {}".format(end_time_step))
        try:
            # Do not subtract 1 from end (inclusive)
            result = self.data.variables[VAR_VALS_GLO_VAR][start_time_step - 1:end_time_step, :]
        except KeyError:
            raise KeyError("Could not find global variables in this database!")
        return result

    def get_global_var_at_time(self, time_step, var_index):
        """
        Returns the values of the global variable with given index at specified time step.

        Time step and variable index are both 1-based. First time step is at 1, last at num_time_steps.
        """
        return self.get_global_var_across_times(time_step, time_step, var_index)[0]

    def get_global_var_across_times(self, start_time_step, end_time_step, var_index):
        """
        Returns the values of the global variable with given index between specified time steps (inclusive).

        Time steps and variable index are both 1-based. First time step is at 1, last at num_time_steps.
        """
        num_steps = self.num_time_steps
        if num_steps <= 0:
            raise ValueError("There are no time steps in this database!")
        if start_time_step <= 0 or start_time_step > num_steps:
            raise ValueError("Time step out of range. Got {}".format(start_time_step))
        if end_time_step <= 0 or end_time_step < start_time_step or end_time_step > num_steps:
            raise ValueError("End time step out of range. Got {}".format(end_time_step))
        if var_index <= 0 or var_index > self.num_global_var:
            raise ValueError("Variable index out of range. Got {}".format(var_index))
        try:
            result = self.data.variables[VAR_VALS_GLO_VAR][start_time_step - 1:end_time_step, var_index - 1]
        except KeyError:
            raise KeyError("Could not find global variables in this database!")
        return result

    def _int_get_partial_object_var_across_times(self, obj_type: ObjectType, internal_id, start_time_step,
                                                 end_time_step, var_index,
                                                 start_index, count):
        """
        Returns partial values of an element block variable between specified time steps (inclusive).

        FOR INTERNAL USE ONLY!

        :param obj_type: type of object this id refers to
        :param internal_id: INTERNAL (1-based) id
        :param start_time_step: start time (inclusive)
        :param end_time_step:  end time (inclusive)
        :param var_index: variable index (1-based)
        :param start_index: element start index (1-based)
        :param count: number of elements
        :return: 2d array storing the partial variable array at each time step
        """

        num_steps = self.num_time_steps
        if num_steps <= 0:
            raise ValueError("There are no time steps in this database!")
        if start_time_step <= 0 or start_time_step > num_steps:
            raise ValueError("Time step out of range. Got {}".format(start_time_step))
        if end_time_step <= 0 or end_time_step < start_time_step or end_time_step > num_steps:
            raise ValueError("End time step out of range. Got {}".format(end_time_step))

        if obj_type == ELEMBLOCK:
            varname = VAR_VALS_ELEM_VAR
            numvar = self.num_elem_block_var
        elif obj_type == NODESET:
            varname = VAR_VALS_NS_VAR
            numvar = self.num_node_set_var
        elif obj_type == SIDESET:
            varname = VAR_VALS_SS_VAR
            numvar = self.num_side_set_var
        else:
            raise ValueError("Invalid variable type {}!".format(obj_type))

        if var_index <= 0 or var_index > numvar:
            raise ValueError("Variable index out of range. Got {}".format(var_index))
        if start_index <= 0:
            raise ValueError("Start index must be greater than 0")
        if count < 0:
            raise ValueError("Count must be a positive integer")
        try:
            result = self.data.variables[varname % (var_index, internal_id)][
                     start_time_step - 1:end_time_step, start_index - 1:start_index + count - 1]
        except KeyError:
            raise KeyError("Could not find variables of type {} in this database!".format(obj_type))
        return result

    def get_elem_block_var_at_time(self, obj_id, time_step, var_index):
        """
        Returns the values of variable with index stored in the element block with id at time step.

        Time step, variable index, and ID are all 1-based. First time step is at 1, last at num_time_steps.
        """
        return self.get_elem_block_var_across_times(obj_id, time_step, time_step, var_index)[0]

    def get_elem_block_var_across_times(self, obj_id, start_time_step, end_time_step, var_index):
        """
        Returns the values of variable with index stored in the element block with id between time steps (inclusive).

        Time steps, variable index, and ID are all 1-based. First time step is at 1, last at num_time_steps.
        """
        # This method cannot simply call its partial version because we cannot know the number of elements to read
        #  without looking up the id first. This extra id lookup call is slow, so we get around it with a helper method.
        internal_id = self._lookup_id(ELEMBLOCK, obj_id)
        size = self._int_get_elem_block_params(obj_id, internal_id)[0]
        return self._int_get_partial_object_var_across_times(ELEMBLOCK, internal_id, start_time_step, end_time_step,
                                                             var_index, 1, size)

    def get_partial_elem_block_var_across_times(self, obj_id, start_time_step, end_time_step, var_index, start_index,
                                                count):
        """
        Returns partial values of an element block variable between specified time steps (inclusive).

        Time steps, variable index, ID and start index are all 1-based. First time step is at 1, last at num_time_steps.
        Array starts at element number ``start`` (1-based) and contains ``count`` elements.
        """
        internal_id = self._lookup_id(ELEMBLOCK, obj_id)
        return self._int_get_partial_object_var_across_times(ELEMBLOCK, internal_id, start_time_step, end_time_step,
                                                             var_index, start_index, count)

    def get_node_set_var_at_time(self, obj_id, time_step, var_index):
        """
        Returns the values of variable with index stored in the node set with id at time step.

        Time step, variable index, and ID are all 1-based. First time step is at 1, last at num_time_steps.
        """
        return self.get_node_set_var_across_times(obj_id, time_step, time_step, var_index)[0]

    def get_node_set_var_across_times(self, obj_id, start_time_step, end_time_step, var_index):
        """
        Returns the values of variable with index stored in the node set with id between time steps (inclusive).

        Time steps, variable index, and ID are all 1-based. First time step is at 1, last at num_time_steps.
        """
        internal_id = self._lookup_id(NODESET, obj_id)
        size = self._int_get_node_set_params(obj_id, internal_id)[0]
        return self._int_get_partial_object_var_across_times(NODESET, internal_id, start_time_step, end_time_step,
                                                             var_index, 1, size)

    def get_partial_node_set_var_across_times(self, obj_id, start_time_step, end_time_step, var_index, start_index,
                                              count):
        """
        Returns partial values of a node set variable between specified time steps (inclusive).

        Time steps, variable index, ID and start index are all 1-based. First time step is at 1, last at num_time_steps.
        Array starts at element number ``start`` (1-based) and contains ``count`` elements.
        """
        internal_id = self._lookup_id(NODESET, obj_id)
        return self._int_get_partial_object_var_across_times(NODESET, internal_id, start_time_step, end_time_step,
                                                             var_index, start_index, count)

    def get_side_set_var_at_time(self, obj_id, time_step, var_index):
        """
        Returns the values of variable with index stored in the side set with id at time step.

        Time step, variable index, and ID are all 1-based. First time step is at 1, last at num_time_steps.
        """
        return self.get_side_set_var_across_times(obj_id, time_step, time_step, var_index)[0]

    def get_side_set_var_across_times(self, obj_id, start_time_step, end_time_step, var_index):
        """
        Returns the values of variable with index stored in the side set with id between time steps (inclusive).

        Time steps, variable index, and ID are all 1-based. First time step is at 1, last at num_time_steps.
        """
        internal_id = self._lookup_id(SIDESET, obj_id)
        size = self._int_get_side_set_params(obj_id, internal_id)[0]
        return self._int_get_partial_object_var_across_times(SIDESET, internal_id, start_time_step, end_time_step,
                                                             var_index, 1, size)

    def get_partial_side_set_var_across_times(self, obj_id, start_time_step, end_time_step, var_index, start_index,
                                              count):
        """
        Returns partial values of a side set variable between specified time steps (inclusive).

        Time steps, variable index, ID and start index are all 1-based. First time step is at 1, last at num_time_steps.
        Array starts at element number ``start`` (1-based) and contains ``count`` elements.
        """
        internal_id = self._lookup_id(SIDESET, obj_id)
        return self._int_get_partial_object_var_across_times(SIDESET, internal_id, start_time_step, end_time_step,
                                                             var_index, start_index, count)

    def _get_truth_table(self, obj_type: ObjectType):
        """
        Returns the truth table for variables of a given object type.

        FOR INTERNAL USE ONLY!

        :param obj_type: type of object
        :return: truth table
        """
        if obj_type == ELEMBLOCK:
            tabname = VAR_ELEM_TAB
            valname = VAR_VALS_ELEM_VAR
            num_entity = self.num_elem_blk
            num_var = self.num_elem_block_var
        elif obj_type == NODESET:
            tabname = VAR_NS_TAB
            valname = VAR_VALS_NS_VAR
            num_entity = self.num_node_sets
            num_var = self.num_node_set_var
        elif obj_type == SIDESET:
            tabname = VAR_SS_TAB
            valname = VAR_VALS_SS_VAR
            num_entity = self.num_side_sets
            num_var = self.num_side_set_var
        else:
            raise ValueError("Invalid object type {}!".format(obj_type))
        if tabname in self.data.variables:
            result = self.data.variables[tabname][:]
        else:
            # we have to figure it out for ourselves
            result = numpy.zeros((num_entity, num_var), dtype=self.int)
            for e in range(num_entity):
                for v in range(num_var):
                    if valname % (v + 1, e + 1) in self.data.variables:
                        result[e, v] = 1
        return result

    def get_elem_block_truth_table(self):
        """Returns the variable truth table for element blocks."""
        return self._get_truth_table(ELEMBLOCK)

    def get_node_set_truth_table(self):
        """Returns the variable truth table for node sets."""
        return self._get_truth_table(NODESET)

    def get_side_set_truth_table(self):
        """Returns the variable truth table for side sets."""
        return self._get_truth_table(SIDESET)

    def _get_var_names(self, var_type: VariableType):
        """
        Returns a list of variable names for objects of a given type.

        :param var_type: the type of variable
        :return: a list of variable names
        """
        if var_type == GLOBAL_VAR:
            varname = VAR_NAME_GLO_VAR
        elif var_type == NODAL_VAR:
            varname = VAR_NAME_NOD_VAR
        elif var_type == ELEMENTAL_VAR:
            varname = VAR_NAME_ELEM_VAR
        elif var_type == NODESET_VAR:
            varname = VAR_NAME_NS_VAR
        elif var_type == SIDESET_VAR:
            varname = VAR_NAME_SS_VAR
        else:
            raise ValueError("Invalid variable type {}!".format(var_type))
        try:
            names = self.data.variables[varname][:]
        except KeyError:
            raise KeyError("No {} variable names stored in database!".format(var_type))
        result = numpy.empty([len(names)], self._MAX_NAME_LENGTH_T)
        for i in range(len(names)):
            result[i] = util.lineparse(names[i])
        return result

    def has_var_names(self, var_type: VariableType):
        """
        .Test if this Exodus file has variable names for a variable type.

        :param var_type: GLOBAL_VAR, NODAL_VAR, ELEMENTAL_VAR, NODESET_VAR, or SIDESET_VAR from `constants`
        :return: True if this variable type has names defined, false otherwise
        """
        if var_type == GLOBAL_VAR:
            varname = VAR_NAME_GLO_VAR
        elif var_type == NODAL_VAR:
            varname = VAR_NAME_NOD_VAR
        elif var_type == ELEMENTAL_VAR:
            varname = VAR_NAME_ELEM_VAR
        elif var_type == NODESET_VAR:
            varname = VAR_NAME_NS_VAR
        elif var_type == SIDESET_VAR:
            varname = VAR_NAME_SS_VAR
        else:
            raise ValueError("Invalid variable type {}!".format(var_type))
        return varname in self.data.variables

    def get_global_var_names(self):
        """Returns a list of all global variable names. Index of the variable is the index of the name + 1."""
        return self._get_var_names(GLOBAL_VAR)

    def get_nodal_var_names(self):
        """Returns a list of all nodal variable names. Index of the variable is the index of the name + 1."""
        return self._get_var_names(NODAL_VAR)

    def get_elem_var_names(self):
        """Returns a list of all element variable names. Index of the variable is the index of the name + 1."""
        return self._get_var_names(ELEMENTAL_VAR)

    def get_node_set_var_names(self):
        """Returns a list of all node set variable names. Index of the variable is the index of the name + 1."""
        return self._get_var_names(NODESET_VAR)

    def get_side_set_var_names(self):
        """Returns a list of all node set variable names. Index of the variable is the index of the name + 1."""
        return self._get_var_names(SIDESET_VAR)

    def _get_var_name(self, var_type, index):
        """Returns variable name of variable with given index of given object type."""
        names = self._get_var_names(var_type)
        try:
            name = names[index - 1]
        except IndexError:
            raise IndexError("Variable index out of range. Got {}".format(index))
        return name

    def get_global_var_name(self, index):
        """Returns the name of the global variable with the given index."""
        return self._get_var_name(GLOBAL_VAR, index)

    def get_nodal_var_name(self, index):
        """Returns the name of the nodal variable with the given index."""
        return self._get_var_name(NODAL_VAR, index)

    def get_elem_var_name(self, index):
        """Returns the name of the element variable with the given index."""
        return self._get_var_name(ELEMENTAL_VAR, index)

    def get_node_set_var_name(self, index):
        """Returns the name of the node set variable with the given index."""
        return self._get_var_name(NODESET_VAR, index)

    def get_side_set_var_name(self, index):
        """Returns the name of the side set variable with the given index."""
        return self._get_var_name(SIDESET_VAR, index)

    ######################
    # Node and side sets #
    ######################

    def _int_get_partial_node_set(self, obj_id, internal_id, start, count):
        """
        Returns a partial array of the nodes contained in the node set with given ID.

        FOR INTERNAL USE ONLY!

        :param obj_id: EXTERNAL (user-defined) id
        :param internal_id: INTERNAL (1-based) id
        :param start: node start index (1-based)
        :param count: number of nodes
        :return: array containing the selected part of the node set
        """
        num_sets = self.num_node_sets
        if num_sets == 0:
            raise KeyError("No node sets are stored in this database!")
        if start < 1:
            raise ValueError("Start index must be greater than 0")
        if count < 0:
            raise ValueError("Count must be a positive integer")
        try:
            set = self.data.variables[VAR_NODE_NS % internal_id][start - 1:start + count - 1]
        except KeyError:
            raise KeyError("Failed to retrieve node set with id {} ('{}')".format(obj_id, VAR_NODE_NS % internal_id))
        return set

    def _int_get_partial_node_set_df(self, obj_id, internal_id, start, count):
        """
        Returns a partial array of the distribution factors contained in the node set with given ID.

        FOR INTERNAL USE ONLY!

        :param obj_id: EXTERNAL (user-defined) id
        :param internal_id: INTERNAL (1-based) id
        :param start: node start index (1-based)
        :param count: number of nodes
        :return: array containing the selected part of the node set distribution factors list
        """
        num_sets = self.num_node_sets
        if num_sets == 0:
            raise KeyError("No node sets are stored in this database!")
        if start < 1:
            raise ValueError("Start index must be greater than 0")
        if count < 0:
            raise ValueError("Count must be a positive integer")
        if ('dist_fact_ns%d' % internal_id) in self.data.variables:
            set = self.data.variables[VAR_DF_NS % internal_id][start - 1:start + count - 1]
        else:
            warnings.warn("This database does not contain dist factors for node set {}".format(obj_id))
            set = []
        return set

    def _int_get_node_set_params(self, obj_id, internal_id):
        """
        Returns a tuple containing the parameters for the node set with given ID.

        FOR INTERNAL USE ONLY!

        :param obj_id: EXTERNAL (user-defined) id
        :param internal_id: INTERNAL (1-based) id
        :return: (number of nodes, number of distribution factors)
        """
        num_sets = self.num_node_sets
        if num_sets == 0:
            raise KeyError("No node sets are stored in this database!")
        try:
            num_entries = self.data.dimensions[DIM_NUM_NODE_NS % internal_id].size
        except KeyError:
            raise KeyError("Failed to retrieve number of entries in node set with id {} ('{}')"
                           .format(obj_id, DIM_NUM_NODE_NS % internal_id))
        if (VAR_DF_NS % internal_id) in self.data.variables:
            num_df = num_entries
        else:
            num_df = 0
        return num_entries, num_df

    def get_node_set(self, identifier):
        """Returns an array of the nodes contained in the node set with given ID."""
        if self.mode == 'w' or self.mode == 'a':
            return self.ledger.get_node_set(identifier)

        internal_id = self._lookup_id(NODESET, identifier)
        size = self._int_get_node_set_params(identifier, internal_id)[0]
        return self._int_get_partial_node_set(identifier, internal_id, 1, size)

    def get_partial_node_set(self, identifier, start, count):
        """
        Returns a partial array of the nodes contained in the node set with given ID.

        Array starts at node number ``start`` (1-based) and contains ``count`` elements.
        """
        if self.mode == 'w' or self.mode == 'a':
            return self.ledger.get_partial_node_set(identifier, start, count)

        internal_id = self._lookup_id(NODESET, identifier)
        return self._int_get_partial_node_set(identifier, internal_id, start, count)

    def get_node_set_df(self, obj_id):
        """Returns an array containing the distribution factors in the node set with given ID."""
        internal_id = self._lookup_id(NODESET, obj_id)
        size = self._int_get_node_set_params(obj_id, internal_id)[1]
        return self._int_get_partial_node_set_df(obj_id, internal_id, 1, size)

    def get_partial_node_set_df(self, obj_id, start, count):
        """
        Returns a partial array of the distribution factors contained in the node set with given ID.

        Array starts at node number ``start`` (1-based) and contains ``count`` elements.
        """
        internal_id = self._lookup_id(NODESET, obj_id)
        return self._int_get_partial_node_set_df(obj_id, internal_id, start, count)

    def get_node_set_params(self, obj_id):
        """
        Returns a tuple containing the parameters for the node set with given ID.

        Returned tuple is of format (number of nodes, number of distribution factors).
        """
        internal_id = self._lookup_id(NODESET, obj_id)
        return self._int_get_node_set_params(obj_id, internal_id)

    def _int_get_partial_side_set(self, obj_id, internal_id, start, count):
        """
        Returns tuple containing a subset of the elements and side contained in the side set with given ID.

        FOR INTERNAL USE ONLY!

        :param obj_id: EXTERNAL (user-defined) id
        :param internal_id: INTERNAL (1-based) id
        :param start: element start index (1-based)
        :param count: number of elements
        :return: tuple containing the selected part of the side set of format: (elements, corresponding sides)
        """
        num_sets = self.num_side_sets
        if num_sets == 0:
            raise KeyError("No side sets are stored in this database!")
        if start < 1:
            raise ValueError("Start index must be greater than 0")
        if count < 0:
            raise ValueError("Count must be a positive integer")
        try:
            elmset = self.data.variables[VAR_ELEM_SS % internal_id][start - 1:start + count - 1]
        except KeyError:
            raise KeyError(
                "Failed to retrieve elements of side set with id {} ('{}')".format(obj_id, VAR_ELEM_SS % internal_id))
        try:
            sset = self.data.variables[VAR_SIDE_SS % internal_id][start - 1:start + count - 1]
        except KeyError:
            raise KeyError(
                "Failed to retrieve sides of side set with id {} ('{}')".format(obj_id, VAR_SIDE_SS % internal_id))
        return elmset, sset

    def _int_get_partial_side_set_df(self, obj_id, internal_id, start, count):
        """
        Returns a partial array of the distribution factors contained in the side set with given ID.

        FOR INTERNAL USE ONLY!

        :param obj_id: EXTERNAL (user-defined) id
        :param internal_id: INTERNAL (1-based) id
        :param start: element start index (1-based)
        :param count: number of elements
        :return: array containing the selected part of the side set distribution factors list
        """
        num_sets = self.num_side_sets
        if num_sets == 0:
            raise KeyError("No side sets are stored in this database!")
        if start < 1:
            raise ValueError("Start index must be greater than 0")
        if count < 0:
            raise ValueError("Count must be a positive integer")
        if (VAR_DF_SS % internal_id) in self.data.variables:
            set = self.data.variables[VAR_DF_SS % internal_id][start - 1:start + count - 1]
        else:
            warnings.warn("This database does not contain dist factors for side set {}".format(obj_id))
            set = []
        return set

    def _int_get_side_set_params(self, obj_id, internal_id):
        """
        Returns a tuple containing the parameters for the side set with given ID.

        FOR INTERNAL USE ONLY

        :param obj_id: EXTERNAL (user-defined) id
        :param internal_id: INTERNAL (1-based) id
        :return: (number of elements, number of distribution factors)
        """
        num_sets = self.num_side_sets
        if num_sets == 0:
            raise KeyError("No side sets are stored in this database!")
        try:
            num_entries = self.data.dimensions[DIM_NUM_SIDE_SS % internal_id].size
        except KeyError:
            raise KeyError("Failed to retrieve number of entries in side set with id {} ('{}')"
                           .format(obj_id, DIM_NUM_SIDE_SS % internal_id))
        if DIM_NUM_DF_SS % internal_id in self.data.dimensions:
            num_df = self.data.dimensions[DIM_NUM_DF_SS % internal_id].size
        else:
            num_df = 0
        return num_entries, num_df

    def get_side_set(self, obj_id):
        """
        Returns tuple containing the elements and sides contained in the side set with given ID.

        Returned tuple is of format (elements in side set, sides in side set).
        """
        internal_id = self._lookup_id(SIDESET, obj_id)
        size = self._int_get_side_set_params(obj_id, internal_id)[0]
        return self._int_get_partial_side_set(obj_id, internal_id, 1, size)

    def get_side_set_node_count_list(self, obj_id):
        """Returns array of number of nodes per side/face."""
        # Adapted from ex_get_side_set_node_count.c
        internal_id = self._lookup_id(SIDESET, obj_id)
        num_eb = self.num_elem_blk
        ndim = self.num_dim
        num_ss_elem, _ = self._int_get_side_set_params(obj_id, internal_id)
        elem_list, side_list = self.get_side_set(obj_id)
        ss_elem_idx = numpy.argsort(elem_list)
        eb_id_map = self.get_elem_block_id_map()
        eb_params = []
        elem_ctr = 0
        for i in range(num_eb):
            id = eb_id_map[i]
            eb_params.append(self._int_get_elem_block_param_object(id, ndim))
            elem_ctr += eb_params[i].num_elem_in_blk
            eb_params[i].elem_ctr = elem_ctr
        node_count_list = numpy.empty(num_ss_elem, self.int)
        j = 0  # current elem block
        for ii in range(num_ss_elem):
            i = ss_elem_idx[ii]
            elem = elem_list[i]
            side = side_list[i] - 1  # 0 based side
            while j < num_eb:
                if elem <= eb_params[j].elem_ctr:
                    break
                else:
                    j += 1
            if j >= num_eb:
                raise ValueError("Invalid element number %d in side set %d!" % (elem, obj_id))
            if side >= eb_params[j].num_sides:
                raise ValueError("Invalid side number %d for element type %s in side set %d!" %
                                 (side, eb_params[j].elem_type_str, obj_id))
            node_count_list[i] = eb_params[j].num_nodes_per_side[side]
        return node_count_list

    def get_side_set_node_list(self, obj_id):
        """
        Returns array of nodes for this side set and the node count list.

        :return: (node list, node count list)
        """
        # Adapted from ex_get_side_set_node_list.c.
        # I really really really hope this doesn't have errors in it
        internal_id = self._lookup_id(SIDESET, obj_id)
        num_eb = self.num_elem_blk
        num_elem = self.num_elem
        ndim = self.num_dim
        num_ss_elem, num_ss_df = self._int_get_side_set_params(obj_id, internal_id)
        elem_list, side_list = self.get_side_set(obj_id)
        ss_elem_idx = numpy.argsort(elem_list)
        eb_id_map = self.get_elem_block_id_map()
        eb_params = []
        elem_ctr = 0
        for i in range(num_eb):
            id = eb_id_map[i]
            eb_params.append(self._int_get_elem_block_param_object(id, ndim))
            elem_ctr += eb_params[i].num_elem_in_blk
            eb_params[i].elem_ctr = elem_ctr
        ss_param_idx = numpy.empty(num_ss_elem, int)  # ss element to eb param index
        ss_elem_node_idx = numpy.empty(num_ss_elem, int)  # ss element to node list index
        node_count_list = numpy.empty(num_ss_elem, self.int)
        node_ctr = 0
        j = 0  # current elem block
        for ii in range(num_ss_elem):
            i = ss_elem_idx[ii]
            elem = elem_list[i]
            side = side_list[i]
            while j < num_eb:
                if eb_params[j].elem_type_val != NULL:
                    if elem <= eb_params[j].elem_ctr:
                        break
                    else:
                        j += 1
            if j >= num_eb:
                raise ValueError("Invalid element number %d in side set %d!" % (elem, obj_id))
            if side >= eb_params[j].num_sides:
                raise ValueError("Invalid side number %d for element type %s in side set %d!" %
                                 (side, eb_params[j].elem_type_str, obj_id))
            ss_param_idx[i] = j
            ss_elem_node_idx[i] = eb_params[j].num_nodes_per_side[side - 1]
            node_ctr += eb_params[j].num_nodes_per_side[side - 1]

        if num_ss_df > 0 and num_ss_df != num_ss_elem:
            if node_ctr != num_ss_df:
                warnings.warn("Side set %d dist fact count (%d) does not match node list length (%d)! This may indicate"
                              " a corrupt database." % (obj_id, num_ss_df, node_ctr))

        for i in range(num_ss_elem):
            node_count_list[i] = ss_elem_node_idx[i]

        sum = 0
        for i in range(num_ss_elem):
            cnt = ss_elem_node_idx[i]
            ss_elem_node_idx[i] = sum
            sum += cnt

        node_list = numpy.empty(node_ctr, self.int)

        elem_ctr = 0
        connect = None
        for j in range(num_ss_elem):
            elem_idx = ss_elem_idx[j]
            elem = elem_list[elem_idx]
            side = side_list[elem_idx]
            param_idx = ss_param_idx[elem_idx]

            if elem > elem_ctr:
                # We're doing this the C way because copying code from SEACAS saves development time
                connect = numpy.ndarray.flatten(self.get_elem_block_connectivity(eb_params[param_idx].elem_blk_id))
                elem_ctr = eb_params[param_idx].elem_ctr

            if connect is None:
                raise ValueError("connect is None in get_side_set_node_list. This is likely the result of an abnormal"
                                 " Exodus file.")

            elem_num = elem - 1
            elem_num_pos = elem_num - (eb_params[param_idx].elem_ctr - eb_params[param_idx].num_elem_in_blk)

            num_nodes_per_elem = eb_params[param_idx].num_nodes_per_elem
            connect_offset = num_nodes_per_elem * elem_num_pos
            side_num = side - 1
            node_pos = ss_elem_node_idx[elem_idx]

            if eb_params[param_idx].elem_type_val == CIRCLE or eb_params[param_idx].elem_type_val == SPHERE:
                node_list[node_pos] = connect[connect_offset]
            elif eb_params[param_idx].elem_type_val == TRUSS:
                node_list[node_pos] = connect[connect_offset + side_num]
            elif eb_params[param_idx].elem_type_val == BEAM:
                for i in range(num_nodes_per_elem):
                    node_list[node_pos + i] = connect[connect_offset + i]
            elif eb_params[param_idx].elem_type_val == TRIANGLE:
                if ndim == 2:
                    if side_num + 1 < 1 or side_num + 1 > 3:
                        raise ValueError("Invalid triangle side number %d!" % (side_num + 1))
                    node_list[node_pos] = connect[connect_offset + tri_table[side_num][0] - 1]
                    node_list[node_pos + 1] = connect[connect_offset + tri_table[side_num][1] - 1]
                    if num_nodes_per_elem > 3:
                        node_list[node_pos + 2] = connect[connect_offset + tri_table[side_num][2] - 1]
                elif ndim == 3:
                    if side_num + 1 < 1 or side_num + 1 > 5:
                        raise ValueError("Invalid triangle side number %d!" % (side_num + 1))
                    node_list[node_pos] = connect[connect_offset + tri3_table[side_num][0] - 1]
                    node_list[node_pos + 1] = connect[connect_offset + tri3_table[side_num][1] - 1]
                    if side_num + 1 <= 2:
                        if num_nodes_per_elem == 3:
                            node_list[node_pos + 2] = connect[connect_offset + tri3_table[side_num][2] - 1]
                        elif num_nodes_per_elem == 4:
                            node_list[node_pos + 2] = connect[connect_offset + tri3_table[side_num][2] - 1]
                            # This looks wrong, but it's what the C library does...
                            node_list[node_pos + 2] = connect[connect_offset + 4 - 1]
                        elif num_nodes_per_elem == 6:
                            node_list[node_pos + 2] = connect[connect_offset + tri3_table[side_num][2] - 1]
                            node_list[node_pos + 3] = connect[connect_offset + tri3_table[side_num][3] - 1]
                            node_list[node_pos + 4] = connect[connect_offset + tri3_table[side_num][4] - 1]
                            node_list[node_pos + 5] = connect[connect_offset + tri3_table[side_num][5] - 1]
                        elif num_nodes_per_elem == 7:
                            node_list[node_pos + 2] = connect[connect_offset + tri3_table[side_num][2] - 1]
                            node_list[node_pos + 3] = connect[connect_offset + tri3_table[side_num][3] - 1]
                            node_list[node_pos + 4] = connect[connect_offset + tri3_table[side_num][4] - 1]
                            node_list[node_pos + 5] = connect[connect_offset + tri3_table[side_num][5] - 1]
                            node_list[node_pos + 6] = connect[connect_offset + tri3_table[side_num][6] - 1]
                        else:
                            raise ValueError("%d is an unsupported number of nodes for triangle elements!" %
                                             num_nodes_per_elem)
                    else:
                        if num_nodes_per_elem > 3:
                            node_list[node_pos + 2] = connect[connect_offset + tri3_table[side_num][2] - 1]
            elif eb_params[param_idx].elem_type_val == QUAD:
                if side_num + 1 < 1 or side_num + 1 > 4:
                    raise ValueError("Invalid quad side number %d!" % (side_num + 1))
                node_list[node_pos + 0] = connect[connect_offset + quad_table[side_num][0] - 1]
                node_list[node_pos + 1] = connect[connect_offset + quad_table[side_num][1] - 1]
                if num_nodes_per_elem > 5:
                    node_list[node_pos + 2] = connect[connect_offset + quad_table[side_num][2] - 1]
            elif eb_params[param_idx].elem_type_val == SHELL:
                if side_num + 1 < 1 or side_num + 1 > 6:
                    raise ValueError("Invalid shell side number %d!" % (side_num + 1))
                node_list[node_pos + 0] = connect[connect_offset + shell_table[side_num][0] - 1]
                node_list[node_pos + 1] = connect[connect_offset + shell_table[side_num][1] - 1]
                if num_nodes_per_elem > 2:
                    if side_num + 1 <= 2:
                        node_list[node_pos + 2] = connect[connect_offset + shell_table[side_num][2] - 1]
                        node_list[node_pos + 3] = connect[connect_offset + shell_table[side_num][3] - 1]
                if num_nodes_per_elem == 8:
                    if side_num + 1 <= 2:
                        node_list[node_pos + 4] = connect[connect_offset + shell_table[side_num][4] - 1]
                        node_list[node_pos + 5] = connect[connect_offset + shell_table[side_num][5] - 1]
                        node_list[node_pos + 6] = connect[connect_offset + shell_table[side_num][6] - 1]
                        node_list[node_pos + 7] = connect[connect_offset + shell_table[side_num][7] - 1]
                    else:
                        node_list[node_pos + 2] = connect[connect_offset + shell_table[side_num][2] - 1]
                if num_nodes_per_elem == 9:
                    if side_num + 1 <= 2:
                        node_list[node_pos + 4] = connect[connect_offset + shell_table[side_num][4] - 1]
                        node_list[node_pos + 5] = connect[connect_offset + shell_table[side_num][5] - 1]
                        node_list[node_pos + 6] = connect[connect_offset + shell_table[side_num][6] - 1]
                        node_list[node_pos + 7] = connect[connect_offset + shell_table[side_num][7] - 1]
                        node_list[node_pos + 8] = connect[connect_offset + shell_table[side_num][8] - 1]
                    else:
                        node_list[node_pos + 2] = connect[connect_offset + shell_table[side_num][2] - 1]
            elif eb_params[param_idx].elem_type_val == TETRA:
                if side_num + 1 < 1 or side_num + 1 > 4:
                    raise ValueError("Invalid tetra side number %d!" % (side_num + 1))
                node_list[node_pos + 0] = connect[connect_offset + tetra_table[side_num][0] - 1]
                node_list[node_pos + 1] = connect[connect_offset + tetra_table[side_num][1] - 1]
                node_list[node_pos + 2] = connect[connect_offset + tetra_table[side_num][2] - 1]
                if num_nodes_per_elem == 8:
                    node_list[node_pos + 3] = connect[connect_offset + tetra_table[side_num][3] - 1]
                elif num_nodes_per_elem > 8:
                    node_list[node_pos + 3] = connect[connect_offset + tetra_table[side_num][3] - 1]
                    node_list[node_pos + 4] = connect[connect_offset + tetra_table[side_num][4] - 1]
                    node_list[node_pos + 5] = connect[connect_offset + tetra_table[side_num][5] - 1]
            elif eb_params[param_idx].elem_type_val == WEDGE:
                if side_num + 1 < 1 or side_num + 1 > 5:
                    raise ValueError("Invalid wedge side number %d!" % (side_num + 1))
                if num_nodes_per_elem == 6 or num_nodes_per_elem == 7:
                    node_list[node_pos + 0] = connect[connect_offset + wedge6_table[side_num][0] - 1]
                    node_list[node_pos + 1] = connect[connect_offset + wedge6_table[side_num][1] - 1]
                    node_list[node_pos + 2] = connect[connect_offset + wedge6_table[side_num][2] - 1]
                    if side_num == 3 or side_num == 4:
                        pass
                    else:
                        node_list[node_pos + 3] = connect[connect_offset + wedge6_table[side_num][3] - 1]
                elif num_nodes_per_elem == 15 or num_nodes_per_elem == 16:
                    node_list[node_pos + 0] = connect[connect_offset + wedge15_table[side_num][0] - 1]
                    node_list[node_pos + 1] = connect[connect_offset + wedge15_table[side_num][1] - 1]
                    node_list[node_pos + 2] = connect[connect_offset + wedge15_table[side_num][2] - 1]
                    node_list[node_pos + 3] = connect[connect_offset + wedge15_table[side_num][3] - 1]
                    node_list[node_pos + 4] = connect[connect_offset + wedge15_table[side_num][4] - 1]
                    node_list[node_pos + 5] = connect[connect_offset + wedge15_table[side_num][5] - 1]
                    if side_num == 3 or side_num == 4:
                        pass
                    else:
                        node_list[node_pos + 6] = connect[connect_offset + wedge15_table[side_num][6] - 1]
                        node_list[node_pos + 7] = connect[connect_offset + wedge15_table[side_num][7] - 1]
                elif num_nodes_per_elem == 12:
                    node_list[node_pos + 0] = connect[connect_offset + wedge12_table[side_num][0] - 1]
                    node_list[node_pos + 1] = connect[connect_offset + wedge12_table[side_num][1] - 1]
                    node_list[node_pos + 2] = connect[connect_offset + wedge12_table[side_num][2] - 1]
                    node_list[node_pos + 3] = connect[connect_offset + wedge12_table[side_num][3] - 1]
                    node_list[node_pos + 4] = connect[connect_offset + wedge12_table[side_num][4] - 1]
                    node_list[node_pos + 5] = connect[connect_offset + wedge12_table[side_num][5] - 1]
                elif num_nodes_per_elem == 20:
                    node_list[node_pos + 0] = connect[connect_offset + wedge20_table[side_num][0] - 1]
                    node_list[node_pos + 1] = connect[connect_offset + wedge20_table[side_num][1] - 1]
                    node_list[node_pos + 2] = connect[connect_offset + wedge20_table[side_num][2] - 1]
                    node_list[node_pos + 3] = connect[connect_offset + wedge20_table[side_num][3] - 1]
                    node_list[node_pos + 4] = connect[connect_offset + wedge20_table[side_num][4] - 1]
                    node_list[node_pos + 5] = connect[connect_offset + wedge20_table[side_num][5] - 1]
                    node_list[node_pos + 6] = connect[connect_offset + wedge20_table[side_num][6] - 1]
                    if side_num == 3 or side_num == 4:
                        pass
                    else:
                        node_list[node_pos + 7] = connect[connect_offset + wedge20_table[side_num][7] - 1]
                        node_list[node_pos + 8] = connect[connect_offset + wedge20_table[side_num][8] - 1]
                elif num_nodes_per_elem == 21:
                    node_list[node_pos + 0] = connect[connect_offset + wedge21_table[side_num][0] - 1]
                    node_list[node_pos + 1] = connect[connect_offset + wedge21_table[side_num][1] - 1]
                    node_list[node_pos + 2] = connect[connect_offset + wedge21_table[side_num][2] - 1]
                    node_list[node_pos + 3] = connect[connect_offset + wedge21_table[side_num][3] - 1]
                    node_list[node_pos + 4] = connect[connect_offset + wedge21_table[side_num][4] - 1]
                    node_list[node_pos + 5] = connect[connect_offset + wedge21_table[side_num][5] - 1]
                    node_list[node_pos + 6] = connect[connect_offset + wedge21_table[side_num][6] - 1]
                    if side_num == 3 or side_num == 4:
                        pass
                    else:
                        node_list[node_pos + 7] = connect[connect_offset + wedge21_table[side_num][7] - 1]
                        node_list[node_pos + 8] = connect[connect_offset + wedge21_table[side_num][8] - 1]
                elif num_nodes_per_elem == 18:
                    node_list[node_pos + 0] = connect[connect_offset + wedge18_table[side_num][0] - 1]
                    node_list[node_pos + 1] = connect[connect_offset + wedge18_table[side_num][1] - 1]
                    node_list[node_pos + 2] = connect[connect_offset + wedge18_table[side_num][2] - 1]
                    node_list[node_pos + 3] = connect[connect_offset + wedge18_table[side_num][3] - 1]
                    node_list[node_pos + 4] = connect[connect_offset + wedge18_table[side_num][4] - 1]
                    node_list[node_pos + 5] = connect[connect_offset + wedge18_table[side_num][5] - 1]
                    if side_num == 3 or side_num == 4:
                        pass
                    else:
                        node_list[node_pos + 6] = connect[connect_offset + wedge18_table[side_num][6] - 1]
                        node_list[node_pos + 7] = connect[connect_offset + wedge18_table[side_num][7] - 1]
                        node_list[node_pos + 8] = connect[connect_offset + wedge18_table[side_num][8] - 1]
            elif eb_params[param_idx].elem_type_val == PYRAMID:
                if side_num + 1 < 1 or side_num + 1 > 5:
                    raise ValueError("Invalid pyramid side number %d!" % (side_num + 1))
                node_list[node_pos] = connect[connect_offset + pyramid_table[side_num][0] - 1]
                node_pos += 1
                node_list[node_pos] = connect[connect_offset + pyramid_table[side_num][1] - 1]
                node_pos += 1
                node_list[node_pos] = connect[connect_offset + pyramid_table[side_num][2] - 1]
                node_pos += 1
                if pyramid_table[side_num][3] == 0:
                    pass  # this one even confuses the C library
                else:
                    node_list[node_pos] = connect[connect_offset + pyramid_table[side_num][3] - 1]
                    node_pos += 1
                if num_nodes_per_elem > 5:
                    node_list[node_pos] = connect[connect_offset + pyramid_table[side_num][4] - 1]
                    node_pos += 1
                    node_list[node_pos] = connect[connect_offset + pyramid_table[side_num][5] - 1]
                    node_pos += 1
                    node_list[node_pos] = connect[connect_offset + pyramid_table[side_num][6] - 1]
                    node_pos += 1
                    if side_num == 4:
                        node_list[node_pos] = connect[connect_offset + pyramid_table[side_num][7] - 1]
                        node_pos += 1
                        if num_nodes_per_elem >= 14:
                            node_list[node_pos] = connect[connect_offset + pyramid_table[side_num][8] - 1]
                            node_pos += 1
                    else:
                        if num_nodes_per_elem >= 18:
                            node_list[node_pos] = connect[connect_offset + pyramid_table[side_num][8] - 1]
                            node_pos += 1
            elif eb_params[param_idx].elem_type_val == HEX:
                if side_num + 1 < 1 or side_num + 1 > 6:
                    raise ValueError("Invalid hex side number %d!" % (side_num + 1))
                if num_nodes_per_elem == 16:
                    node_list[node_pos + 0] = connect[connect_offset + hex16_table[side_num][0] - 1]
                    node_list[node_pos + 1] = connect[connect_offset + hex16_table[side_num][1] - 1]
                    node_list[node_pos + 2] = connect[connect_offset + hex16_table[side_num][2] - 1]
                    node_list[node_pos + 3] = connect[connect_offset + hex16_table[side_num][3] - 1]
                    # I have no idea whats going on with these next two statements
                    node_list[node_pos + 3] = connect[connect_offset + hex16_table[side_num][4] - 1]
                    node_list[node_pos + 3] = connect[connect_offset + hex16_table[side_num][5] - 1]
                    if side_num + 1 == 5 or side_num + 1 == 6:
                        # Also no idea about these ones
                        node_list[node_pos] = connect[connect_offset + hex16_table[side_num][6] - 1]
                        node_pos += 1
                        node_list[node_pos] = connect[connect_offset + hex16_table[side_num][7] - 1]
                        node_pos += 1
                else:
                    node_list[node_pos + 0] = connect[connect_offset + hex_table[side_num][0] - 1]
                    node_list[node_pos + 1] = connect[connect_offset + hex_table[side_num][1] - 1]
                    node_list[node_pos + 2] = connect[connect_offset + hex_table[side_num][2] - 1]
                    node_list[node_pos + 3] = connect[connect_offset + hex_table[side_num][3] - 1]
                    if num_nodes_per_elem > 12:
                        node_list[node_pos + 4] = connect[connect_offset + hex_table[side_num][4] - 1]
                        node_list[node_pos + 5] = connect[connect_offset + hex_table[side_num][5] - 1]
                        node_list[node_pos + 6] = connect[connect_offset + hex_table[side_num][6] - 1]
                        node_list[node_pos + 7] = connect[connect_offset + hex_table[side_num][7] - 1]
                    if num_nodes_per_elem == 27:
                        node_list[node_pos + 8] = connect[connect_offset + hex_table[side_num][8] - 1]
            else:
                raise ValueError("%s is an unsupported element type." % eb_params[param_idx].elem_type_str)
        return node_list, node_count_list

    def get_partial_side_set(self, obj_id, start, count):
        """
        Returns tuple containing a subset of the elements and sides contained in the side set with given ID.

        Arrays start at element number ``start`` (1-based) and contains ``count`` elements.
        Returned tuple is of format (elements in side set, sides in side set).
        """
        internal_id = self._lookup_id(SIDESET, obj_id)
        return self._int_get_partial_side_set(obj_id, internal_id, start, count)

    def get_side_set_df(self, obj_id):
        """Returns an array containing the distribution factors in the side set with given ID."""
        internal_id = self._lookup_id(SIDESET, obj_id)
        size = self._int_get_side_set_params(obj_id, internal_id)[1]
        return self._int_get_partial_side_set_df(obj_id, internal_id, 1, size)

    def get_partial_side_set_df(self, obj_id, start, count):
        """
        Returns a partial array of the distribution factors contained in the side set with given ID.

        Array starts at element number ``start`` (1-based) and contains ``count`` elements.
        """
        internal_id = self._lookup_id(SIDESET, obj_id)
        return self._int_get_partial_side_set_df(obj_id, internal_id, start, count)

    def get_side_set_params(self, obj_id):
        """
        Returns a tuple containing the parameters for the side set with given ID.

        Returned tuple is of format (number of elements, number of distribution factors).
        """
        internal_id = self._lookup_id(SIDESET, obj_id)
        return self._int_get_side_set_params(obj_id, internal_id)

    ##################
    # Element blocks #
    ##################

    def _int_get_partial_elem_block_connectivity(self, obj_id, internal_id, start, count):
        """
        Returns a partial connectivity list for the element block with given ID.

        FOR INTERNAL USE ONLY!

        :param obj_id: EXTERNAL (user-defined) id
        :param internal_id: INTERNAL (1-based) id
        :param start: element start index (1-based)
        :param count: number of elements
        :return: array containing the selected part of the connectivity list
        """
        if start < 1:
            raise ValueError("Start index must be greater than 0")
        if count < 0:
            raise ValueError("Count must be a positive integer")

        if self.mode == 'w' or self.mode == 'a':
            num_node_entry = self.ledger.get_num_nodes_per_el_block(internal_id)
	elif (DIM_NUM_NOD_PER_EL % internal_id) in self.data.dimensions:
            num_node_entry = self.data.dimensions[DIM_NUM_NOD_PER_EL % internal_id].size
        else:
            num_node_entry = 0

        if num_node_entry > 0:
            try:
                if self.mode == 'w' or self.mode == 'a':
                    result = self.ledger.get_connectX(internal_id)[start - 1:start + count - 1]
		else:
		    result = self.data.variables[VAR_CONNECT % internal_id][start - 1:start + count - 1]

            except KeyError:
                raise KeyError("Failed to retrieve connectivity list of element block with id {} ('{}')"
                               .format(obj_id, VAR_CONNECT % internal_id))
        else:
            result = []
        return result

    def _int_get_elem_block_params(self, obj_id, internal_id):
        """
        Returns a tuple containing the parameters for the element block with given ID.

        FOR INTERNAL USE ONLY

        :param obj_id: EXTERNAL (user-defined) id
        :param internal_id: INTERNAL (1-based) id
        :return: (number of elements, nodes per element, topology, number of attributes)
        """
        # TODO this will be way faster with caching
        try:
	    if self.mode == 'w' or self.mode == 'a':
                num_entries = self.ledger.get_num_elem_in_block(internal_id)
            else:
                num_entries = self.data.dimensions[DIM_NUM_EL_IN_BLK % internal_id].size
        except KeyError:
            raise KeyError("Failed to retrieve number of elements in element block with id {} ('{}')"
                           .format(obj_id, DIM_NUM_EL_IN_BLK % internal_id))
        
	if self.mode == 'w' or self.mode == 'a':
            num_node_entry = self.ledger.get_num_nodes_per_el_block(internal_id)
        elif (DIM_NUM_NOD_PER_EL % internal_id) in self.data.dimensions:
            num_node_entry = self.data.dimensions[DIM_NUM_NOD_PER_EL % internal_id].size
        else:
            num_node_entry = 0

        try:
            if self.mode == 'w' or self.mode == 'a':
                topology = self.ledger.get_elem_block_type(internal_id)
            if num_node_entry > 0:
                connect = self.data.variables[VAR_CONNECT % internal_id]
                topology = connect.getncattr(ATTR_ELEM_TYPE)
            else:
                topology = None
        except KeyError:
            raise KeyError("Failed to retrieve connectivity list of element block with id {} ('{}')"
                           .format(obj_id, VAR_CONNECT % internal_id))
        
	# TODO: Add case for append mode if attributes added
        if (DIM_NUM_ATT_IN_BLK % internal_id) in self.data.dimensions:
            num_att_blk = self.data.dimensions[DIM_NUM_ATT_IN_BLK % internal_id].size
        else:
            num_att_blk = 0
        return num_entries, num_node_entry, topology, num_att_blk

    def get_elem_block_connectivity(self, obj_id):
        """Returns the connectivity list for the element block with given ID."""
        internal_id = self._lookup_id(ELEMBLOCK, obj_id)
        size = self._int_get_elem_block_params(obj_id, internal_id)[0]
        return self._int_get_partial_elem_block_connectivity(obj_id, internal_id, 1, size)

    def get_partial_elem_block_connectivity(self, obj_id, start, count):
        """
        Returns a partial connectivity list for the element block with given ID.

        Array starts at element number ``start`` (1-based) and contains ``count`` elements.
        """
        internal_id = self._lookup_id(ELEMBLOCK, obj_id)
        return self._int_get_partial_elem_block_connectivity(obj_id, internal_id, start, count)

    def get_elem_block_params(self, obj_id) -> Tuple[builtins.int, builtins.int, str, builtins.int]:
        """
        Returns a tuple containing the parameters for the element block with given ID.

        Returned tuple is of format (number of elements, nodes per element, topology, number of attributes).
        """
        internal_id = self._lookup_id(ELEMBLOCK, obj_id)
        return self._int_get_elem_block_params(obj_id, internal_id)

    def _int_get_elem_block_param_object(self, obj_id, ndim) -> ElemBlockParam:
        """Returns parameters used to describe an elem block."""
        # Adapted from ex_int_get_block_param.c
        # Used to get side set node count list
        num_el, nod_el, topo, num_att = self.get_elem_block_params(obj_id)
        topo = topo.upper()
        num_nod_side = numpy.zeros(6, builtins.int)
        if topo[:3] == CIRCLE[:3]:
            el_type = CIRCLE
            num_sides = 1
            num_nod_side[0] = 1
        elif topo[:3] == SPHERE[:3]:
            el_type = SPHERE
            num_sides = 1
            num_nod_side[0] = 1
        elif topo[:3] == QUAD[:3]:
            el_type = QUAD
            num_sides = 4
            if nod_el == 4 or nod_el == 5:
                num_nod_side[0] = 2
                num_nod_side[1] = 2
                num_nod_side[2] = 2
                num_nod_side[3] = 2
            elif nod_el == 9 or nod_el == 8:
                num_nod_side[0] = 3
                num_nod_side[1] = 3
                num_nod_side[2] = 3
                num_nod_side[3] = 3
            elif nod_el == 12 or nod_el == 16:
                num_nod_side[0] = 4
                num_nod_side[1] = 4
                num_nod_side[2] = 4
                num_nod_side[3] = 4
            else:
                raise ValueError("Element of type %s with %d nodes is invalid!" % (topo, nod_el))
        elif topo[:3] == TRIANGLE[:3]:
            el_type = TRIANGLE
            if ndim == 2:
                num_sides = 3
                if nod_el == 3 or nod_el == 4:
                    num_nod_side[0] = 2
                    num_nod_side[1] = 2
                    num_nod_side[2] = 2
                elif nod_el == 6 or nod_el == 7:
                    num_nod_side[0] = 3
                    num_nod_side[1] = 3
                    num_nod_side[2] = 3
                elif nod_el == 9 or nod_el == 13:
                    num_nod_side[0] = 4
                    num_nod_side[1] = 4
                    num_nod_side[2] = 4
                else:
                    raise ValueError("Element of type %s with %d nodes is invalid!" % (topo, nod_el))
            elif ndim == 3:
                num_sides = 5
                if nod_el == 3 or nod_el == 4:
                    num_nod_side[0] = nod_el
                    num_nod_side[1] = nod_el
                    num_nod_side[2] = 2
                    num_nod_side[3] = 2
                    num_nod_side[4] = 2
                elif nod_el == 6 or nod_el == 7:
                    num_nod_side[0] = nod_el
                    num_nod_side[1] = nod_el
                    num_nod_side[2] = 3
                    num_nod_side[3] = 3
                    num_nod_side[4] = 3
                elif nod_el == 9 or nod_el == 13:
                    num_nod_side[0] = nod_el
                    num_nod_side[1] = nod_el
                    num_nod_side[2] = 4
                    num_nod_side[3] = 4
                    num_nod_side[4] = 4
                else:
                    raise ValueError("Element of type %s with %d nodes is invalid!" % (topo, nod_el))
        elif topo[:3] == SHELL[:3]:
            el_type = SHELL
            if nod_el == 2:
                num_sides = 2
                num_nod_side[0] = 2
                num_nod_side[1] = 2
            elif nod_el == 4:
                num_sides = 6
                num_nod_side[0] = 4
                num_nod_side[1] = 4
                num_nod_side[2] = 2
                num_nod_side[3] = 2
                num_nod_side[4] = 2
                num_nod_side[5] = 2
            elif nod_el == 8 or nod_el == 9:
                num_sides = 6
                num_nod_side[0] = nod_el
                num_nod_side[1] = nod_el
                num_nod_side[2] = 3
                num_nod_side[3] = 3
                num_nod_side[4] = 3
                num_nod_side[5] = 3
            else:
                raise ValueError("Element of type %s with %d nodes is invalid!" % (topo, nod_el))
        elif topo[:3] == HEX[:3]:
            el_type = HEX
            num_sides = 6
            if nod_el == 8 or nod_el == 9:
                num_nod_side[0] = 4
                num_nod_side[1] = 4
                num_nod_side[2] = 4
                num_nod_side[3] = 4
                num_nod_side[4] = 4
                num_nod_side[5] = 4
            elif nod_el == 12:
                num_nod_side[0] = 6
                num_nod_side[1] = 6
                num_nod_side[2] = 6
                num_nod_side[3] = 6
                num_nod_side[4] = 4
                num_nod_side[5] = 4
            elif nod_el == 16:
                num_nod_side[0] = 6
                num_nod_side[1] = 6
                num_nod_side[2] = 6
                num_nod_side[3] = 6
                num_nod_side[4] = 8
                num_nod_side[5] = 8
            elif nod_el == 20:
                num_nod_side[0] = 8
                num_nod_side[1] = 8
                num_nod_side[2] = 8
                num_nod_side[3] = 8
                num_nod_side[4] = 8
                num_nod_side[5] = 8
            elif nod_el == 27:
                num_nod_side[0] = 9
                num_nod_side[1] = 9
                num_nod_side[2] = 9
                num_nod_side[3] = 9
                num_nod_side[4] = 9
                num_nod_side[5] = 9
            elif nod_el == 32:
                num_nod_side[0] = 12
                num_nod_side[1] = 12
                num_nod_side[2] = 12
                num_nod_side[3] = 12
                num_nod_side[4] = 12
                num_nod_side[5] = 12
            elif nod_el == 64:
                num_nod_side[0] = 16
                num_nod_side[1] = 16
                num_nod_side[2] = 16
                num_nod_side[3] = 16
                num_nod_side[4] = 16
                num_nod_side[5] = 16
            else:
                raise ValueError("Element of type %s with %d nodes is invalid!" % (topo, nod_el))
        elif topo[:3] == TETRA[:3]:
            el_type = TETRA
            num_sides = 4
            if nod_el == 4 or nod_el == 5:
                num_nod_side[0] = 3
                num_nod_side[1] = 3
                num_nod_side[2] = 3
                num_nod_side[3] = 3
            elif nod_el == 8:
                num_nod_side[0] = 4
                num_nod_side[1] = 4
                num_nod_side[2] = 4
                num_nod_side[3] = 4
            elif nod_el == 10 or nod_el == 11:
                num_nod_side[0] = 6
                num_nod_side[1] = 6
                num_nod_side[2] = 6
                num_nod_side[3] = 6
            elif nod_el == 14 or nod_el == 15:
                num_nod_side[0] = 7
                num_nod_side[1] = 7
                num_nod_side[2] = 7
                num_nod_side[3] = 7
            elif nod_el == 16:
                num_nod_side[0] = 9
                num_nod_side[1] = 9
                num_nod_side[2] = 9
                num_nod_side[3] = 9
            elif nod_el == 40:
                num_nod_side[0] = 13
                num_nod_side[1] = 13
                num_nod_side[2] = 13
                num_nod_side[3] = 13
            else:
                raise ValueError("Element of type %s with %d nodes is invalid!" % (topo, nod_el))
        elif topo[:3] == WEDGE[:3]:
            el_type = WEDGE
            num_sides = 5
            if nod_el == 6:
                num_nod_side[0] = 4
                num_nod_side[1] = 4
                num_nod_side[2] = 4
                num_nod_side[3] = 3
                num_nod_side[4] = 3
            elif nod_el == 12:
                num_nod_side[0] = 6
                num_nod_side[1] = 6
                num_nod_side[2] = 6
                num_nod_side[3] = 6
                num_nod_side[4] = 6
            elif nod_el == 15 or nod_el == 16:
                num_nod_side[0] = 8
                num_nod_side[1] = 8
                num_nod_side[2] = 8
                num_nod_side[3] = 6
                num_nod_side[4] = 6
            elif nod_el == 18:
                num_nod_side[0] = 9
                num_nod_side[1] = 9
                num_nod_side[2] = 9
                num_nod_side[3] = 6
                num_nod_side[4] = 6
            elif nod_el == 20 or nod_el == 21:
                num_nod_side[0] = 9
                num_nod_side[1] = 9
                num_nod_side[2] = 9
                num_nod_side[3] = 7
                num_nod_side[4] = 7
            elif nod_el == 24:
                num_nod_side[0] = 12
                num_nod_side[1] = 12
                num_nod_side[2] = 12
                num_nod_side[3] = 9
                num_nod_side[4] = 9
            elif nod_el == 52:
                num_nod_side[0] = 16
                num_nod_side[1] = 16
                num_nod_side[2] = 16
                num_nod_side[3] = 13
                num_nod_side[4] = 13
            else:
                raise ValueError("Element of type %s with %d nodes is invalid!" % (topo, nod_el))
        elif topo[:3] == PYRAMID[:3]:
            el_type = PYRAMID
            num_sides = 5
            if nod_el == 5:
                num_nod_side[0] = 3
                num_nod_side[1] = 3
                num_nod_side[2] = 3
                num_nod_side[3] = 3
                num_nod_side[4] = 4
            elif nod_el == 13:
                num_nod_side[0] = 6
                num_nod_side[1] = 6
                num_nod_side[2] = 6
                num_nod_side[3] = 6
                num_nod_side[4] = 8
            elif nod_el == 14:
                num_nod_side[0] = 6
                num_nod_side[1] = 6
                num_nod_side[2] = 6
                num_nod_side[3] = 6
                num_nod_side[4] = 9
            elif nod_el == 18 or nod_el == 19:
                num_nod_side[0] = 7
                num_nod_side[1] = 7
                num_nod_side[2] = 7
                num_nod_side[3] = 7
                num_nod_side[4] = 9
            else:
                raise ValueError("Element of type %s with %d nodes is invalid!" % (topo, nod_el))
        elif topo[:3] == BEAM[:3]:
            el_type = BEAM
            num_sides = 2
            if nod_el == 2:
                num_nod_side[0] = 2
                num_nod_side[1] = 2
            elif nod_el == 3:
                num_nod_side[0] = 3
                num_nod_side[1] = 3
            elif nod_el == 4:
                num_nod_side[0] = 4
                num_nod_side[1] = 4
            else:
                raise ValueError("Element of type %s with %d nodes is invalid!" % (topo, nod_el))
        elif topo[:3] == TRUSS[:3] or topo[:3] == BAR[:3] or topo[:3] == EDGE[:3]:
            el_type = TRUSS
            num_sides = 2
            if nod_el == 2 or nod_el == 3:
                num_nod_side[0] = 1
                num_nod_side[1] = 1
            else:
                raise ValueError("Element of type %s with %d nodes is invalid!" % (topo, nod_el))
        # Special case for null elements
        elif topo[:3] == NULL[:3]:
            el_type = NULL
            num_sides = 0
            num_nod_side[0] = 0
            num_el = 0
        else:
            el_type = UNKNOWN
            num_sides = 0
            num_nod_side[0] = 0
        return ElemBlockParam(topo, obj_id, num_el, nod_el, num_sides, num_nod_side, num_att, 0, el_type)

    #########
    # Names #
    #########

    def _get_set_block_names(self, obj_type: ObjectType):
        """
        Returns a list of names for objects of a given type.
        :param obj_type: type of object
        :return: a list of names
        """
        names = []
        if obj_type == NODESET:
            try:
                names = self.data.variables[VAR_NS_NAMES]
            except KeyError:
                warnings.warn("This database does not contain node set names.")
        elif obj_type == SIDESET:
            try:
                names = self.data.variables[VAR_SS_NAMES]
            except KeyError:
                warnings.warn("This database does not contain side set names.")
        elif obj_type == ELEMBLOCK:
            try:
                names = self.data.variables[VAR_EB_NAMES]
            except KeyError:
                warnings.warn("This database does not contain element block names.")
        else:
            raise ValueError("{} is not a valid set/block type!".format(obj_type))
        result = numpy.empty([len(names)], self._MAX_NAME_LENGTH_T)
        for i in range(len(names)):
            result[i] = util.lineparse(names[i])
        return result

    def get_elem_block_names(self):
        """Returns an array containing the names of element blocks in this database."""
        if self.mode == 'w' or self.mode == 'a':
            return self.ledger.get_elem_block_names()
	return self._get_set_block_names(ELEMBLOCK)

    def get_elem_block_name(self, obj_id):
        """Returns the name of the given element block."""
        if self.mode == 'w' or self.mode == 'a':
            return self.ledger.get_elem_block_name(obj_id)

	internal_id = self._lookup_id(ELEMBLOCK, obj_id)
        names = self._get_set_block_names(ELEMBLOCK)

        if len(names) > 0:
            return names[internal_id - 1]
        else:
            return None

    def get_node_set_names(self):
        """Returns an array containing the names of node sets in this database."""
        if self.mode == 'a' or self.mode == 'w':
            return self.ledger.get_node_set_names()
        return self._get_set_block_names(NODESET)

    def get_node_set_name(self, identifier):
        """Returns the name of the given node set."""
        if self.mode == 'a' or self.mode == 'w':
            return self.ledger.get_node_set_name(identifier)

        internal_id = self._lookup_id(NODESET, identifier)
        names = self._get_set_block_names(NODESET)
        if len(names) > 0:
            return names[internal_id - 1]
        else:
            return None

    def get_side_set_names(self):
        """Returns an array containing the names of side sets in this database."""
        return self._get_set_block_names(SIDESET)

    def get_side_set_name(self, obj_id):
        """Returns the name of the given side set."""
        internal_id = self._lookup_id(SIDESET, obj_id)
        names = self._get_set_block_names(SIDESET)
        if len(names) > 0:
            return names[internal_id - 1]
        else:
            return None

    ######################
    # Element Attributes #
    ######################

    def _int_get_num_elem_attrib(self, internal_id):
        """
        Returns the number of attributes in the element block with given internal ID.

        FOR INTERNAL USE ONLY!
        """
        # Some databases don't have attributes
        if (DIM_NUM_ATT_IN_BLK % internal_id) in self.data.dimensions:
            num = self.data.dimensions[DIM_NUM_ATT_IN_BLK % internal_id].size
        else:
            # No need to warn. If there are no attributes, the number is 0...
            num = 0
        return num

    def _int_get_partial_elem_attrib(self, obj_id, internal_id, start, count):
        """
        Returns a partial list of all attributes for the element block with given ID.

        Returns an empty array if the element block doesn't have attributes.

        FOR INTERNAL USE ONLY

        :param obj_id: EXTERNAL (user-defined) id
        :param internal_id: INTERNAL (1-based) id
        :param start: element start index (1-based)
        :param count: number of elements
        :return: array containing the selected part of the attribute list
        """
        if start < 1:
            raise ValueError("Start index must be greater than 0")
        if count < 0:
            raise ValueError("Count must be a positive integer")
        varname = VAR_ELEM_ATTRIB % internal_id
        if varname in self.data.variables:
            result = self.data.variables[varname][start - 1:start + count - 1, :]
        else:
            result = []
            warnings.warn("Element block {} has no attributes.".format(obj_id))
        return result

    def _int_get_partial_one_elem_attrib(self, obj_id, internal_id, attrib_index, start, count):
        """
        Returns a partial list of one attribute for the element block with given ID.

        Returns an empty array if the element block doesn't have attributes.

        FOR INTERNAL USE ONLY

        :param obj_id: EXTERNAL (user-defined) id
        :param internal_id: INTERNAL (1-based) id
        :param attrib_index: attribute index (1-based)
        :param start: element start index (1-based)
        :param count: number of elements
        :return: array containing the selected part of the attribute list
        """
        if start < 1:
            raise ValueError("Start index must be greater than 0")
        if count < 0:
            raise ValueError("Count must be a positive integer")
        num_attrib = self._int_get_num_elem_attrib(internal_id)
        if num_attrib > 0:  # faster to check this than if the variable exists like in the function above this one
            if attrib_index < 1 or attrib_index > num_attrib:
                raise ValueError("Attribute index out of range. Got {}".format(attrib_index))
            result = self.data.variables[VAR_ELEM_ATTRIB % internal_id][start - 1:start + count - 1, attrib_index - 1]
        else:
            result = []
            warnings.warn("Element block {} has no attributes.".format(obj_id))
        return result

    def get_partial_one_elem_attrib(self, obj_id, attrib_index, start, count):
        """
        Returns a partial list of one attribute for the specified elements in the element block with given ID.

        Array starts at element number ``start`` (1-based) and contains ``count`` elements.
        Returns an empty array if the element block doesn't have attributes.
        """
        internal_id = self._lookup_id(ELEMBLOCK, obj_id)
        return self._int_get_partial_one_elem_attrib(obj_id, internal_id, attrib_index, start, count)

    def get_one_elem_attrib(self, obj_id, attrib_index):
        """
        Returns a list of one attribute for each element in the element block with given ID.

        Returns an empty array if the element block doesn't have attributes.
        """
        internal_id = self._lookup_id(ELEMBLOCK, obj_id)
        size = self._int_get_elem_block_params(obj_id, internal_id)[0]
        return self._int_get_partial_one_elem_attrib(obj_id, internal_id, attrib_index, 1, size)

    def get_elem_attrib(self, obj_id):
        """
        Returns a list of all attributes for each element in the element block with given ID.

        Returns an empty array if the element block doesn't have attributes.
        """
        internal_id = self._lookup_id(ELEMBLOCK, obj_id)
        size = self._int_get_elem_block_params(obj_id, internal_id)[0]
        return self._int_get_partial_elem_attrib(obj_id, internal_id, 1, size)

    def get_partial_elem_attrib(self, obj_id, start, count):
        """
        Returns a partial list of all attributes for the specified elements in the element block with given ID.

        Array starts at element number ``start`` (1-based) and contains ``count`` elements.
        Returns an empty array if the element block doesn't have attributes.
        """
        internal_id = self._lookup_id(ELEMBLOCK, obj_id)
        return self._int_get_partial_elem_attrib(obj_id, internal_id, start, count)

    def get_elem_attrib_names(self, obj_id):
        """
        Returns a list of the names of attributes in the element block with given ID.

        Returns an empty array if the element block doesn't have attributes or attribute names.
        """
        internal_id = self._lookup_id(ELEMBLOCK, obj_id)
        num_attrib = self._int_get_num_elem_attrib(internal_id)
        result = []
        if num_attrib == 0:
            warnings.warn("Element block {} has no attributes.".format(obj_id))
        else:
            varname = VAR_ELEM_ATTRIB_NAME % internal_id
            # Older datasets don't have attribute names
            if varname in self.data.variables:
                names = self.data.variables[varname][:]
                result = util.arrparse(names, len(names), self._MAX_NAME_LENGTH_T)
            else:
                warnings.warn("Attributes of element block {} have no names.".format(obj_id))
        return result

    def get_num_elem_attrib(self, obj_id):
        """Returns the number of attributes in the element block with given ID."""
        internal_id = self._lookup_id(ELEMBLOCK, obj_id)
        return self._int_get_num_elem_attrib(internal_id)

    #####################
    # Object properties #
    #####################

    # This method contains a general algorithm for counting the number of properties an object has.
    # This is used by the num_*_prop properties which are in turn used by _get_object_property_names
    def _get_num_object_properties(self, varname):
        """
        Returns the number of properties an object has.

        :param varname: the netCDF variable name of the property. ("xx_prop_%d") where xx is ns, ss, or eb
        :return: number of properties
        """
        # loop over the prop variables and count how many there are
        n = 0
        while True:
            if varname % (n + 1) in self.data.variables:
                n += 1
            else:
                break
        return n

    def _get_object_property(self, obj_type: ObjectType, obj_id, name):
        """
        Returns the value of a specific object's property.

        :param obj_type: type of object this id refers to
        :param obj_id: EXTERNAL (user-defined) id
        :param name: name of the property
        :return: value of the property for the specified object
        """
        internal_id = self._lookup_id(obj_type, obj_id)
        prop = self._get_object_property_array(obj_type, name)
        # We don't want to index into prop if it's empty
        if len(prop) > 0:
            return prop[internal_id - 1]
        else:
            return None

    def get_node_set_property(self, obj_id, name):
        """Returns the value of the specified property for the node set with the given ID."""
        return self._get_object_property(NODESET, obj_id, name)

    def get_side_set_property(self, obj_id, name):
        """Returns the value of the specified property for the side set with the given ID."""
        return self._get_object_property(SIDESET, obj_id, name)

    def get_elem_block_property(self, obj_id, name):
        """Returns the value of the specified property for the element block with the given ID."""
        return self._get_object_property(ELEMBLOCK, obj_id, name)

    def _get_object_property_array(self, obj_type: ObjectType, name):
        """
        Returns a list containing all the values of a particular property for objects of a given type.

        :param obj_type: type of object this id refers to
        :param name: name of the property
        :return: array containing values of the property for objects of the given type
        """
        if obj_type == NODESET:
            varname = VAR_NS_PROP
        elif obj_type == SIDESET:
            varname = VAR_SS_PROP
        elif obj_type == ELEMBLOCK:
            varname = VAR_EB_PROP
        else:
            raise ValueError("Invalid variable type {}!".format(obj_type))
        prop = []
        # Search for the property for the right name
        # We don't use a for loop over the number of props because that would cost a second loop over the props
        n = 1
        while True:
            if varname % n in self.data.variables:
                propname = self.data.variables[varname % n].getncattr(ATTR_NAME)
                if propname == name:
                    # we've found our property
                    prop = self.data.variables[varname % n][:]
                    break
                else:
                    # check next property
                    n += 1
                    continue
            else:
                # "xx_prop_n" doesn't exist. name doesn't exist in file
                warnings.warn("Property {} does not exist!".format(name))
                break
        return prop

    def get_node_set_property_array(self, name):
        """Returns a list containing the values of the specified property for all node sets."""
        return self._get_object_property_array(NODESET, name)

    def get_side_set_property_array(self, name):
        """Returns a list containing the values of the specified property for all side sets."""
        return self._get_object_property_array(SIDESET, name)

    def get_elem_block_property_array(self, name):
        """Returns a list containing the values of the specified property for all element blocks."""
        return self._get_object_property_array(ELEMBLOCK, name)

    def _get_object_property_names(self, obj_type: ObjectType):
        """
        Returns a list containing the names of properties defined for objects of a given type.

        :param obj_type: type of object
        :return: array of property names
        """
        if obj_type == NODESET:
            varname = VAR_NS_PROP
            num_props = self.num_node_set_prop
        elif obj_type == SIDESET:
            varname = VAR_SS_PROP
            num_props = self.num_side_set_prop
        elif obj_type == ELEMBLOCK:
            varname = VAR_EB_PROP
            num_props = self.num_elem_block_prop
        else:
            raise ValueError("Invalid variable type {}!".format(obj_type))
        # num_props = self._get_num_object_properties(varname)
        result = numpy.empty([num_props], self._MAX_NAME_LENGTH_T)
        for n in range(num_props):
            result[n] = self.data.variables[varname % (n + 1)].getncattr(ATTR_NAME)
        return result

    def get_node_set_property_names(self):
        """Returns a list of node set property names."""
        return self._get_object_property_names(NODESET)

    def get_side_set_property_names(self):
        """Returns a list of side set property names."""
        return self._get_object_property_names(SIDESET)

    def get_elem_block_property_names(self):
        """Returns a list of element block property names."""
        return self._get_object_property_names(ELEMBLOCK)

    ###############
    # Coordinates #
    ###############

    def get_coords(self):
        """Returns a multidimensional array containing the coordinates of all nodes."""
        # Technically this incurs an extra call to num_nodes, but the reduced complexity is worth it
        return self.get_partial_coords(1, self.num_nodes)

    def get_partial_coords(self, start, count):
        """
        Returns a multidimensional array containing the coordinates of the specified set of nodes.

        Array starts at node number ``start`` (1-based) and contains ``count`` elements.
        """
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
                coord = self.data.variables[VAR_COORD][:, start - 1:start + count - 1]
            except KeyError:
                raise KeyError("Failed to retrieve nodal coordinate array!")
        else:
            try:
                coordx = self.data.variables[VAR_COORD_X][start - 1:start + count - 1]
            except KeyError:
                raise KeyError("Failed to retrieve x axis nodal coordinate array!")
            if dim_cnt > 1:
                try:
                    coordy = self.data.variables[VAR_COORD_Y][start - 1:start + count - 1]
                except KeyError:
                    raise KeyError("Failed to retrieve y axis nodal coordinate array!")
                if dim_cnt > 2:
                    try:
                        coordz = self.data.variables[VAR_COORD_Z][start - 1:start + count - 1]
                    except KeyError:
                        raise KeyError("Failed to retrieve z axis nodal coordinate array!")
                    coord = numpy.array([coordx, coordy, coordz])
                else:
                    coord = numpy.array([coordx, coordy])
            else:
                coord = coordx
        return coord

    def get_coord_x(self):
        """Returns an array containing the x coordinate of all nodes."""
        return self.get_partial_coord_x(1, self.num_nodes)

    def get_partial_coord_x(self, start, count):
        """
        Returns an array containing the x coordinate of the specified set of nodes.

        Array starts at node number ``start`` (1-based) and contains ``count`` elements.
        """
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
                coord = self.data.variables[VAR_COORD][0][start - 1:start + count - 1]
            except KeyError:
                raise KeyError("Failed to retrieve nodal coordinate array!")
        else:
            try:
                coord = self.data.variables[VAR_COORD_X][start - 1:start + count - 1]
            except KeyError:
                raise KeyError("Failed to retrieve x axis nodal coordinate array!")
        return coord

    def get_coord_y(self):
        """Returns an array containing the y coordinate of all nodes."""
        return self.get_partial_coord_y(1, self.num_nodes)

    def get_partial_coord_y(self, start, count):
        """
        Returns an array containing the y coordinate of the specified set of nodes.

        Array starts at node number ``start`` (1-based) and contains ``count`` elements.
        """
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
                coord = self.data.variables[VAR_COORD][1][start - 1:start + count - 1]
            except KeyError:
                raise KeyError("Failed to retrieve nodal coordinate array!")
        else:
            try:
                coord = self.data.variables[VAR_COORD_Y][start - 1:start + count - 1]
            except KeyError:
                raise KeyError("Failed to retrieve y axis nodal coordinate array!")
        return coord

    def get_coord_z(self):
        """Returns an array containing the z coordinate of all nodes."""
        return self.get_partial_coord_z(1, self.num_nodes)

    def get_partial_coord_z(self, start, count):
        """
        Returns an array containing the z coordinate of the specified set of nodes.

        Array starts at node number ``start`` (1-based) and contains ``count`` elements.
        """
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
                coord = self.data.variables[VAR_COORD][2][start - 1:start + count - 1]
            except KeyError:
                raise KeyError("Failed to retrieve nodal coordinate array!")
        else:
            try:
                coord = self.data.variables[VAR_COORD_Z][start - 1:start + count - 1]
            except KeyError:
                raise KeyError("Failed to retrieve z axis nodal coordinate array!")
        return coord

    def get_coord_names(self):
        """Returns an array containing the names of the coordinate axes in this database."""
        dim_cnt = self.num_dim
        try:
            names = self.data.variables[VAR_COORD_NAMES]
        except KeyError:
            raise KeyError("Failed to retrieve coordinate name array!")
        result = util.arrparse(names, dim_cnt, self._MAX_NAME_LENGTH_T)
        return result

    ################
    # File records #
    ################

    def get_info(self):
        """Returns an array containing the info records stored in this database."""
        num = self.num_info
        result = numpy.empty([num], Exodus._MAX_LINE_LENGTH_T)
        if num > 0:
            try:
                infos = self.data.variables[VAR_INFO]
            except KeyError:
                raise KeyError("Failed to retrieve info records from database!")
            for i in range(num):
                result[i] = util.lineparse(infos[i])
        return result

    def get_qa(self):
        """Returns an n x 4 array containing the QA records stored in this database."""
        num = self.num_qa
        result = numpy.empty([num, 4], Exodus._MAX_STR_LENGTH_T)
        if num > 0:
            try:
                qas = self.data.variables[VAR_QA]
            except KeyError:
                raise KeyError("Failed to retrieve qa records from database!")
            for i in range(num):
                for j in range(4):
                    result[i, j] = util.lineparse(qas[i, j])
        return result

    # endregion

    @property
    def time_steps(self):
        """Returns list of the time steps, 0-indexed"""
        return [*range(self.num_time_steps)]

    def step_at_time(self, time):
        """Given a float time value, return the corresponding time step"""
        for index, value in enumerate(self.get_all_times()):
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

    def get_nodes_in_elblock(self, id):
        if self.mode == 'w' or self.mode == 'a':
            return self.ledger.get_connectX(id)

        if "node_num_map" in self.data.variables:
            raise Exception("Using node num map")
        nodeids = self.data["connect" + str(id)]
        # flatten it into 1d
        nodeids = nodeids[:].flatten()
        return nodeids

    def diff(self, other):
        # # Nodesets
        selfNS = self.num_node_sets
        otherNS = other.num_node_sets
        print("Self # Nodesets:\t{}".format(selfNS))
        print("Other # Nodesets:\t{}".format(otherNS))

        # # Sidesets
        selfSS = self.num_side_sets
        otherSS = other.num_side_sets
        print("\nSelf # Sidesets:\t{}".format(selfSS))
        print("Other # Sidesets:\t{}".format(otherSS))

        # # Nodes
        selfN = self.num_nodes
        otherN = other.num_nodes
        print("\nSelf # Nodes:\t\t{}".format(selfN))
        print("Other # Nodes:\t\t{}".format(otherN))

        # # Elements
        selfE = self.num_elem
        otherE = other.num_elem
        print("\nSelf # Elements:\t{}".format(selfE))
        print("Other # Elements:\t{}\n".format(otherE))

        # Length of output variables (nodal/elemental)

    def diff_nodeset(self, id, other, id2=None):
        """
        Prints the overlap and difference between two nodesets
        :param id: the nodeset ID of the self Exodus object
        :param other: the other Exodus object to compare to
        :param id2: optional parameter specifying the nodeset ID of other Exodus object. Default to the first id.
        """

        if other is None:
            raise ValueError("Other Exodus file is None")

        if id2 is None:
            id2 = id
        try:
            ns1 = self.get_node_set(id)
        except KeyError:
            raise KeyError("Self Exodus file does not contain nodeset with ID {}".format(id))

        try:
            ns2 = other.get_node_set(id2)
        except KeyError:
            raise KeyError("Other Exodus file does not contain nodeset with ID {}".format(id2))

        equivalent = numpy.array_equal(numpy.array(sorted(ns1.tolist())), numpy.array(sorted(ns2.tolist())))
        if equivalent:
            print("Self NS {} contains the same Node IDs as Other NS ID {}".format(id, id2))
        else:
            print("Self NS ID {} does NOT contain the same nodes as Other NS ID {}".format(id, id2))
            intersection = set(ns1) & set(ns2)
            print("\tBoth nodesets share the following nodes:\n\t{}".format(sorted(list(intersection))))
            ns1_diff = sorted(list(set(ns1) - intersection))
            print("\tSelf NS ID {} also contains nodes:\n\t{}".format(id, ns1_diff))
            ns2_diff = sorted(list(set(ns2) - intersection))
            print("\tOther NS ID {} also contains nodes:\n\t{}\n".format(id2, ns2_diff))

    ################################################################
    #                                                              #
    #                        Write                                 #
    #                                                              #
    ################################################################

    def add_nodeset(self, node_ids, nodeset_id, nodeset_name=""):
        if self.mode != 'w' and self.mode != 'a':
            raise PermissionError("Need to be in write or append mode to add nodeset")
        self.ledger.add_nodeset(node_ids, nodeset_id, nodeset_name)

    def remove_nodeset(self, identifier):
        if self.mode != 'w' and self.mode != 'a':
            raise PermissionError("Need to be in write or append mode to add nodeset")
        self.ledger.remove_nodeset(identifier)

    def merge_nodeset(self, new_id, ns1, ns2, delete=True):
        if self.mode != 'w' and self.mode != 'a':
            raise PermissionError("Need to be in write or append mode to add nodeset")
        self.ledger.merge_nodesets(new_id, ns1, ns2, delete)

    def add_node_to_nodeset(self, node_id, identifier):
        if self.mode != 'w' and self.mode != 'a':
            raise PermissionError("Need to be in write or append mode to add nodeset")
        self.ledger.add_node_to_nodeset(node_id, identifier)

    def add_nodes_to_nodeset(self, node_ids, identifier):
        if self.mode != 'w' and self.mode != 'a':
            raise PermissionError("Need to be in write or append mode to add nodeset")
        self.ledger.add_nodes_to_nodeset(node_ids, identifier)

    def remove_node_from_nodeset(self, node_id, identifier):
        if self.mode != 'w' and self.mode != 'a':
            raise PermissionError("Need to be in write or append mode to add nodeset")
        self.ledger.remove_node_from_nodeset(node_id, identifier)

    def remove_nodes_from_nodeset(self, node_ids, identifier):
        if self.mode != 'w' and self.mode != 'a':
            raise PermissionError("Need to be in write or append mode to add nodeset")
        self.ledger.remove_nodes_from_nodeset(node_ids, identifier)

    def add_sideset(self, elem_ids, side_ids, ss_id, ss_name, dist_fact=None, variables=None):
        if self.mode != 'w' and self.mode != 'a':
            raise PermissionError("Need to be in write or append mode to add nodeset")
        self.ledger.add_sideset(elem_ids, side_ids, ss_id, ss_name, dist_fact, variables)

    def remove_sideset(self, ss_id):
        if self.mode != 'w' and self.mode != 'a':
            raise PermissionError("Need to be in write or append mode to add nodeset")
        self.ledger.remove_sideset(ss_id)


    def add_sides_to_sideset(self, elem_ids, side_ids, ss_id, dist_facts=None, variables=None):
        if self.mode != 'w' and self.mode != 'a':
            raise PermissionError("Need to be in write or append mode to add nodeset")
        self.ledger.add_sides_to_sideset(elem_ids, side_ids, ss_id, dist_facts, variables)

    def remove_sides_from_sideset(self, elem_ids, side_ids, ss_id):
        if self.mode != 'w' and self.mode != 'a':
            raise PermissionError("Need to be in write or append mode to add nodeset")
        self.ledger.remove_sides_from_sideset(elem_ids, side_ids, ss_id)

    def split_sideset(self, old_ss, function, ss_id1, ss_id2, delete, ss_name1="", ss_name2=""):
        if self.mode != 'w' and self.mode != 'a':
            raise PermissionError("Need to be in write or append mode to split sideset")
        self.ledger.split_sideset(old_ss, function, ss_id1, ss_id2, delete, ss_name1, ss_name2)
    

    def add_element(self, block_id, nodelist):
        if self.mode != 'w' and self.mode != 'a':
            raise PermissionError("Need to be in write or append mode to add nodeset")
        return self.ledger.add_element(block_id, nodelist)


    def remove_element(self, elem_id):
        if self.mode != 'w' and self.mode != 'a':
            raise PermissionError("Need to be in write or append mode to add nodeset")
        return self.ledger.remove_element(elem_id)

    def skin_element_block(self, block_id, skin_id, skin_name):
        if self.mode != 'w' and self.mode != 'a':
            raise PermissionError("Need to be in write or append mode to skin element into new sideset")
        self.ledger.skin_element_block(block_id, skin_id, skin_name)

    def skin(self, skin_id, skin_name):
        if self.mode != 'w' and self.mode != 'a':
            raise PermissionError("Need to be in write or append mode to skin element into new sideset")
        self.ledger.skin(skin_id, skin_name)
        
    def write(self, path=None):
        if self.mode != 'w' and self.mode != 'a':
            raise PermissionError("Need to be in write or append mode to write")
        elif self.mode == 'a' and path is None:
            raise AttributeError("Must specify a new path when in append mode")
        elif self.mode == 'w' and path is not None:
            raise AttributeError("Do not specify a new path in write mode. Initialization path will be used")
        self.ledger.write(path)


# TODO some functions return numpy arrays, some return Python lists. Should be consistently one or the other.
# TODO you should be able to select variables by name as well as id!
#  that's what Sandia told us to do originally!
#  Same goes for other data types!


if __name__ == "__main__":
    ...
