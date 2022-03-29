from typing import NewType

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

# TODO put all the variable strings in here instead of hard coding them
