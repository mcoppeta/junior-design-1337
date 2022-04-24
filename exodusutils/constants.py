"""Constants used by the Python Exodus Utilities library."""

from typing import NewType

LIB_NAME = "Python Exodus Utilities"

# Types
ObjectType = NewType('ObjectType', str)
VariableType = NewType('VariableType', str)
ElementTopography = NewType('ElementTopography', str)

# Constants
ELEMBLOCK = ObjectType("elblock")
"""Represents an element block."""
NODESET = ObjectType("nodeset")
"""Represents a node set."""
SIDESET = ObjectType("sideset")
"""Represents a side set."""

GLOBAL_VAR = VariableType("global")
"""Represents global variables."""
NODAL_VAR = VariableType("node")
"""Represents nodal variables."""
ELEMENTAL_VAR = VariableType("elem")
"""Represents elemental variables."""
NODESET_VAR = VariableType("nodeset")
"""Represents node set variables."""
SIDESET_VAR = VariableType("sideset")
"""Represents side set variables."""

CIRCLE = ElementTopography("CIRCLE")
SPHERE = ElementTopography("SPHERE")
QUAD = ElementTopography("QUAD")
TRIANGLE = ElementTopography("TRIANGLE")
SHELL = ElementTopography("SHELL")
HEX = ElementTopography("HEX")
TETRA = ElementTopography("TETRA")
WEDGE = ElementTopography("WEDGE")
PYRAMID = ElementTopography("PYRAMID")
BEAM = ElementTopography("BEAM")
TRUSS = ElementTopography("TRUSS")
BAR = ElementTopography("BAR")
EDGE = ElementTopography("EDGE")
NULL = ElementTopography("NULL")  # This isn't officially supported by this library
UNKNOWN = ElementTopography("UNKNOWN")

# Side to node translation tables
# triangle
tri_table = [
      [1, 2, 4],  # side 1
      [2, 3, 5],  # side 2
      [3, 1, 6]   # side 3
  ]

# triangle 3d
tri3_table = [
      [1, 2, 3, 4, 5, 6, 7],  # side 1 (face)
      [3, 2, 1, 6, 5, 4, 7],  # side 2 (face)
      [1, 2, 4, 0, 0, 0, 0],  # side 3 (edge)
      [2, 3, 5, 0, 0, 0, 0],  # side 4 (edge)
      [3, 1, 6, 0, 0, 0, 0]   # side 5 (edge)
  ]

# quad
quad_table = [
      [1, 2, 5],  # side 1
      [2, 3, 6],  # side 2
      [3, 4, 7],  # side 3
      [4, 1, 8]   # side 4
  ]

# shell
shell_table = [
      [1, 2, 3, 4, 5, 6, 7, 8, 9],  # side 1 (face)
      [1, 4, 3, 2, 8, 7, 6, 5, 9],  # side 2 (face)
      [1, 2, 5, 0, 0, 0, 0, 0, 0],  # side 3 (edge)
      [2, 3, 6, 0, 0, 0, 0, 0, 0],  # side 4 (edge)
      [3, 4, 7, 0, 0, 0, 0, 0, 0],  # side 5 (edge)
      [4, 1, 8, 0, 0, 0, 0, 0, 0]   # side 6 (edge)
  ]

# tetra
tetra_table = [
      [1, 2, 4, 5, 9, 8, 14],   # Side 1 nodes
      [2, 3, 4, 6, 10, 9, 12],  # Side 2 nodes
      [1, 4, 3, 8, 10, 7, 13],  # Side 3 nodes
      [1, 3, 2, 7, 6, 5, 11]    # Side 4 nodes
  ]

# wedge
# wedge 6 or 7
wedge6_table = [
      [1, 2, 5, 4],  # Side 1 nodes -- quad
      [2, 3, 6, 5],  # Side 2 nodes -- quad
      [1, 4, 6, 3],  # Side 3 nodes -- quad
      [1, 3, 2, 0],  # Side 4 nodes -- triangle
      [4, 5, 6, 0]   # Side 5 nodes -- triangle
  ]

# wedge 12 -- localization element
wedge12_table = [
      [1, 2, 5, 4, 7, 10],   # Side 1 nodes -- quad
      [2, 3, 6, 5, 8, 11],   # Side 2 nodes -- quad
      [1, 4, 6, 3, 9, 12],   # Side 3 nodes -- quad
      [1, 3, 2, 9, 8, 7],    # Side 4 nodes -- triangle
      [4, 5, 6, 10, 11, 12]  # Side 5 nodes -- triangle
  ]

# wedge 15 or 16
wedge15_table = [
      [1, 2, 5, 4, 7, 11, 13, 10],  # Side 1 nodes -- quad
      [2, 3, 6, 5, 8, 12, 14, 11],  # Side 2 nodes -- quad
      [1, 4, 6, 3, 10, 15, 12, 9],  # Side 3 nodes -- quad
      [1, 3, 2, 9, 8, 7, 0, 0],     # Side 4 nodes -- triangle
      [4, 5, 6, 13, 14, 15, 0, 0]   # Side 5 nodes -- triangle
  ]

# wedge 20
wedge20_table = [
      [1, 2, 5, 4, 7, 11, 13, 10, 20],  # Side 1 nodes -- quad
      [2, 3, 6, 5, 8, 12, 14, 11, 18],  # Side 2 nodes -- quad
      [1, 4, 6, 3, 10, 15, 12, 9, 19],  # Side 3 nodes -- quad
      [1, 3, 2, 9, 8, 7, 16, 0, 0],     # Side 4 nodes -- triangle
      [4, 5, 6, 13, 14, 15, 17, 0, 0]   # Side 5 nodes -- triangle
  ]

# wedge 21
wedge21_table = [
      [1, 2, 5, 4, 7, 11, 13, 10, 21],  # Side 1 nodes -- quad
      [2, 3, 6, 5, 8, 12, 14, 11, 19],  # Side 2 nodes -- quad
      [1, 4, 6, 3, 10, 15, 12, 9, 20],  # Side 3 nodes -- quad
      [1, 3, 2, 9, 8, 7, 17, 0, 0],     # Side 4 nodes -- triangle
      [4, 5, 6, 13, 14, 15, 18, 0, 0]   # Side 5 nodes -- triangle
  ]

# wedge 18
wedge18_table = [
      [1, 2, 5, 4, 7, 11, 13, 10, 16],  # Side 1 nodes -- quad
      [2, 3, 6, 5, 8, 12, 14, 11, 17],  # Side 2 nodes -- quad
      [1, 4, 6, 3, 10, 15, 12, 9, 18],  # Side 3 nodes -- quad
      [1, 3, 2, 9, 8, 7, 0, 0, 0],      # Side 4 nodes -- triangle
      [4, 5, 6, 13, 14, 15, 0, 0, 0]    # Side 5 nodes -- triangle
  ]

# hex
hex_table = [
      [1, 2, 6, 5, 9, 14, 17, 13, 26],   # side 1
      [2, 3, 7, 6, 10, 15, 18, 14, 25],  # side 2
      [3, 4, 8, 7, 11, 16, 19, 15, 27],  # side 3
      [1, 5, 8, 4, 13, 20, 16, 12, 24],  # side 4
      [1, 4, 3, 2, 12, 11, 10, 9, 22],   # side 5
      [5, 6, 7, 8, 17, 18, 19, 20, 23]   # side 6
  ]

# hex 16 -- localization element
hex16_table = [
      [1, 2, 6, 5, 9, 13, 0, 0],    # side 1 -- 6 node quad
      [2, 3, 7, 6, 10, 14, 0, 0],   # side 2 -- 6 node quad
      [3, 4, 8, 7, 11, 15, 0, 0],   # side 3 -- 6 node quad
      [4, 1, 5, 8, 12, 16, 0, 0],   # side 4 -- 6 node quad
      [1, 4, 3, 2, 12, 11, 10, 9],  # side 5 -- 8 node quad
      [5, 6, 7, 8, 13, 14, 15, 16]  # side 6 -- 8 node quad
  ]

# pyramid
pyramid_table = [
      [1, 2, 5, 0, 6, 11, 10, 0, 15],  # side 1 (tri)
      [2, 3, 5, 0, 7, 12, 11, 0, 16],  # side 2 (tri)
      [3, 4, 5, 0, 8, 13, 12, 0, 17],  # side 3 (tri)
      [1, 5, 4, 0, 10, 13, 9, 0, 18],  # side 4 (tri)
      [1, 4, 3, 2, 9, 8, 7, 6, 14]     # side 5 (quad)
  ]

# NetCDF entity names
ATT_TITLE = "title"
ATT_MAX_NAME_LENGTH = "maximum_name_length"
DIM_NAME_LENGTH = "len_name"
ATT_API_VER = "api_version"
ATT_API_VER_OLD = "api version"
ATT_VERSION = "version"
DIM_STRING_LENGTH = "len_string"
DIM_LINE_LENGTH = "len_line"
ATT_FILE_SIZE = "file_size"
ATT_64BIT_INT = "int64_status"
ATT_WORD_SIZE = "floating_point_word_size"
ATT_WORD_SIZE_OLD = "floating point word size"
DIM_NUM_INFO = "num_info"
VAR_INFO = "info_records"
DIM_NUM_QA = "num_qa_rec"
DIM_FOUR = "four"
VAR_QA = "qa_records"
DIM_NUM_DIM = "num_dim"
VAR_COORD = "coord"
VAR_COORD_X = "coordx"
VAR_COORD_Y = "coordy"
VAR_COORD_Z = "coordz"
VAR_COORD_NAMES = "coor_names"
DIM_NUM_NODES = "num_nodes"
DIM_NUM_ELEM = "num_elem"
DIM_NUM_EB = "num_el_blk"
DIM_NUM_NS = "num_node_sets"
DIM_NUM_SS = "num_side_sets"
VAR_NS_NAMES = "ns_names"
VAR_SS_NAMES = "ss_names"
VAR_EB_NAMES = "eb_names"
VAR_ELEM_ORDER_MAP = "elem_map"
VAR_NODE_ID_MAP = "node_num_map"
VAR_ELEM_ID_MAP = "elem_num_map"
VAR_NS_ID_MAP = "ns_prop1"
VAR_SS_ID_MAP = "ss_prop1"
VAR_EB_ID_MAP = "eb_prop1"
DIM_NUM_TIME_STEP = "time_step"
VAR_TIME_WHOLE = "time_whole"
DIM_NUM_GLO_VAR = "num_glo_var"
DIM_NUM_NOD_VAR = "num_nod_var"
DIM_NUM_ELEM_VAR = "num_elem_var"
DIM_NUM_NS_VAR = "num_nset_var"
DIM_NUM_SS_VAR = "num_sset_var"
VAR_VALS_NOD_VAR_SMALL = "vals_nod_var"
VAR_VALS_NOD_VAR_LARGE = "vals_nod_var%d"
VAR_VALS_GLO_VAR = "vals_glo_var"
VAR_ELEM_TAB = "elem_var_tab"
VAR_NS_TAB = "nset_var_tab"
VAR_SS_TAB = "sset_var_tab"
VAR_VALS_ELEM_VAR = "vals_elem_var%deb%d"
VAR_VALS_NS_VAR = "vals_nset_var%dns%d"
VAR_VALS_SS_VAR = "vals_sset_var%dss%d"
VAR_NAME_GLO_VAR = "name_glo_var"
VAR_NAME_NOD_VAR = "name_nod_var"
VAR_NAME_ELEM_VAR = "name_elem_var"
VAR_NAME_NS_VAR = "name_nset_var"
VAR_NAME_SS_VAR = "name_sset_var"
DIM_NUM_NODE_NS = "num_nod_ns%d"
VAR_NODE_NS = "node_ns%d"
VAR_DF_NS = "dist_fact_ns%d"
VAR_ELEM_SS = "elem_ss%d"
DIM_NUM_SIDE_SS = "num_side_ss%d"
VAR_SIDE_SS = "side_ss%d"
DIM_NUM_DF_SS = "num_df_ss%d"
VAR_DF_SS = "dist_fact_ss%d"
DIM_NUM_NOD_PER_EL = "num_nod_per_el%d"
DIM_NUM_EL_IN_BLK = "num_el_in_blk%d"
DIM_NUM_ATT_IN_BLK = "num_att_in_blk%d"
VAR_CONNECT = "connect%d"
ATTR_ELEM_TYPE = "elem_type"
VAR_ELEM_ATTRIB = "attrib%d"
VAR_ELEM_ATTRIB_NAME = "attrib_name%d"
VAR_NS_PROP = "ns_prop%d"
VAR_SS_PROP = "ss_prop%d"
VAR_EB_PROP = "eb_prop%d"
ATTR_NAME = "name"
VAR_NS_STATUS = "ns_status"
VAR_SS_STATUS = "ss_status"
VAR_EB_STATUS = "eb_status"
