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

# Exodus variable names
ATTR_TITLE = "title"
ATTR_MAX_NAME_LENGTH = "maximum_name_length"
DIM_NAME_LENGTH = "len_name"
ATTR_API_VER = "api_version"
ATTR_API_VER_OLD = "api version"
ATTR_VERSION = "version"
DIM_NUM_QA = "num_qa_rec"
VAR_QA = "qa_records"
DIM_FOUR = "four"
DIM_STRING_LENGTH = "len_string"
DIM_LINE_LENGTH = "len_line"
ATTR_FILE_SIZE = "file_size"
ATTR_64BIT_INT = "int64_status"
ATTR_WORD_SIZE = "floating_point_word_size"
ATTR_WORD_SIZE_OLD = "floating point word size"

# TODO put all the variable strings in here instead of hard coding them
