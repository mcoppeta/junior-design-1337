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
    def __init__(self, exodus: Exodus, obj_id: int, elements=..., variables=..., attributes=...):
        """
        Create a new selector object for an element block.

        :param exodus: the exodus object this element block is stored in
        :param obj_id: the id of the element block this represents
        :param elements: the range of elements to select (1-indexed)
        :param variables: the range of variables to select (1-indexed)
        :param attributes: the range of attributes to select (1-indexed)
        """
        ObjectSelector.__init__(self, exodus, obj_id, ELEMBLOCK)
        self.elements = elements
        self.variables = variables
        self.attributes = attributes
        # We ought to bounds check the inputs and also update the bounds if the exodus object changes


class NodeSetSelector(ObjectSelector):
    """Selects a subset of a node set's components."""
    # input a range
    def __init__(self, exodus: Exodus, obj_id: int, nodes=..., variables=...):
        """
        Create a new selector object for a node set.

        :param exodus: the exodus object this node set is stored in
        :param obj_id: the id of the node set this represents
        :param nodes: the range of nodes to select (1-indexed)
        :param variables: the range of variables to select (1-indexed)
        """
        ObjectSelector.__init__(self, exodus, obj_id, NODESET)
        self.elements = nodes
        self.variables = variables


class SideSetSelector(ObjectSelector):
    """Selects a subset of a side set's components."""
    # input a range
    def __init__(self, exodus: Exodus, obj_id: int, elements=..., variables=...):
        """
        Create a new selector object for a side set.

        :param exodus: the exodus object this side set is stored in
        :param obj_id: the id of the side set this represents
        :param elements: the range of elements to select (1-indexed)
        :param variables: the range of variables to select (1-indexed)
        """
        ObjectSelector.__init__(self, exodus, obj_id, SIDESET)
        self.elements = elements
        self.variables = variables


class PropertySelector:
    """Select a subset of object properties."""
    def __init__(self, exodus: Exodus, eb_prop=..., ns_prop=..., ss_prop=...):
        """
        Create a new object property selector

        :param exodus: the exodus object whose properties this refers to
        :param eb_prop: list of all element block properties to keep by name
        :param ns_prop: list of all node set properties to keep by name
        :param ss_prop: list of all side set properties to keep by name
        """
        self.exodus = exodus
        self.eb_prop = eb_prop
        self.ns_prop = ns_prop
        self.ss_prop = ss_prop
