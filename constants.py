"""Constants used by the Python Exodus Utilities library."""

from typing import NewType

LIB_VERSION_MAJOR = 0
LIB_VERSION_MINOR = 1337
LIB_NAME = "Python Exodus Utilities"

# Types
ObjectType = NewType('ObjectType', str)
VariableType = NewType('VariableType', str)

# Constants
ELEMBLOCK = ObjectType("elblock")
NODESET = ObjectType("nodeset")
SIDESET = ObjectType("sideset")

GLOBAL_VAR = VariableType("global")
NODAL_VAR = VariableType("node")
ELEMENTAL_VAR = VariableType("elem")
NODESET_VAR = VariableType("nodeset")
SIDESET_VAR = VariableType("sideset")

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
