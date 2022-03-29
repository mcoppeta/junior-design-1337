from __future__ import annotations  # use the magic of python 3.7 to let use write Exodus instead of "Exodus"

from abc import ABC, abstractmethod
from constants import *

# Give us some handy type checking without creating cyclic imports at runtime
# Its like preprocessor code, but not!
from typing import TYPE_CHECKING
if TYPE_CHECKING:  # evaluates to false at runtime
    from exodus import Exodus


class ObjectSelector(ABC):
    """Abstract base class of all selectors."""
    def __init__(self, exodus: Exodus, obj_id: int, obj_type: ObjectType):
        self.exodus = exodus
        self.obj_id = obj_id
        self.obj_type = obj_type

        # probably needs an abstract update method for when exodus changes


class ElementBlockSelector(ObjectSelector):
    """Selects a subset of an element block's components."""
    # input a range
    def __init__(self, exodus: Exodus, obj_id: int, elements=..., variables=..., attributes=..., properties=...):
        """
        Create a new selector object for an element block.

        :param exodus: the exodus object this element block is stored in
        :param obj_id: the id of the element block this represents
        :param elements: the range of elements to select (1-indexed)
        :param variables: the range of variables to select (1-indexed)
        :param attributes: the range of attributes to select (1-indexed)
        :param properties: list of properties to select by name
        """
        ObjectSelector.__init__(self, exodus, obj_id, ELEMBLOCK)
        self.elements = elements
        self.variables = variables
        self.attributes = attributes
        self.properties = properties
        # We ought to bounds check the inputs and also update the bounds if the exodus object changes


class NodeSetSelector(ObjectSelector):
    """Selects a subset of a node set's components."""
    # input a range
    def __init__(self, exodus: Exodus, obj_id: int, nodes=..., variables=..., properties=...):
        """
        Create a new selector object for a node set.

        :param exodus: the exodus object this node set is stored in
        :param obj_id: the id of the node set this represents
        :param nodes: the range of nodes to select (1-indexed)
        :param variables: the range of variables to select (1-indexed)
        :param properties: list of properties to select by name
        """
        ObjectSelector.__init__(self, exodus, obj_id, NODESET)
        self.elements = nodes
        self.variables = variables
        self.properties = properties


class SideSetSelector(ObjectSelector):
    """Selects a subset of a side set's components."""
    # input a range
    def __init__(self, exodus: Exodus, obj_id: int, elements=..., variables=..., properties=...):
        """
        Create a new selector object for a side set.

        :param exodus: the exodus object this side set is stored in
        :param obj_id: the id of the side set this represents
        :param elements: the range of elements to select (1-indexed)
        :param variables: the range of variables to select (1-indexed)
        :param properties: list of properties to select by name
        """
        ObjectSelector.__init__(self, exodus, obj_id, SIDESET)
        self.elements = elements
        self.variables = variables
        self.properties = properties
