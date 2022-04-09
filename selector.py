from __future__ import annotations  # use the magic of python 3.7 to let use write Exodus instead of "Exodus"

from abc import ABC, abstractmethod
from constants import *
import warnings

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


# TODO allow variables and attributes (and properties) to be string names or int indices
class ElementBlockSelector(ObjectSelector):
    """Selects a subset of an element block's components."""
    # input a range
    # Data is stored in 0 indexed arrays
    def __init__(self, exodus: Exodus, obj_id: int, elements=..., variables=..., attributes=...):
        """
        Create a new selector object for an element block.

        Pass in ... to select everything, None to select nothing, or a list of specific values.
        Lists will be sorted upon entry to maintain element order consistency.
        elements is a range of elements within this element block. For example, you would select the first 5 elements
        in a block with elements=range(1, 6) or you could select the 1st, 3rd, and 7th element with elements=[1,3,7].

        :param exodus: the exodus object this element block is stored in
        :param obj_id: the id of the element block this represents
        :param elements: the range of elements to select within this block (1-indexed). This is not the same as IDs.
        :param variables: the variable ids to select (1-indexed)
        :param attributes: the attributes ids (1-indexed) or names to select
        """
        ObjectSelector.__init__(self, exodus, obj_id, ELEMBLOCK)

        if elements is None:
            self.elements = []
        elif elements is ...:
            num_elem, _, _, _ = exodus.get_elem_block_params(obj_id)
            self.elements = list(range(num_elem))
        else:
            self.elements = list(set(elements))
            self.elements.sort()
            num_elem, _, _, _ = exodus.get_elem_block_params(obj_id)
            if self.elements[0] < 1 or self.elements[-1] > num_elem:
                raise ValueError("elements out of range!")
            self.elements = [x - 1 for x in self.elements]
            if len(self.elements) != len(elements):
                warnings.warn("Duplicate elements were automatically removed.")

        if variables is None:
            self.variables = []
        elif variables is ...:
            self.variables = list(range(exodus.num_elem_block_var))
        else:
            self.variables = list(set(variables))
            self.variables.sort()
            if self.variables[0] < 1 or self.variables[-1] > exodus.num_elem_block_var:
                raise ValueError("variable index out of range!")
            self.variables = [x - 1 for x in self.variables]
            if len(self.variables) != len(variables):
                warnings.warn("Duplicate elements were automatically removed.")

        if attributes is None:
            self.attributes = []
        elif attributes is ...:
            self.attributes = list(range(exodus.get_num_elem_attrib(obj_id)))
        else:
            if all(isinstance(n, int) for n in attributes):
                self.attributes = attributes
                self.attributes.sort()
                if self.attributes[0] < 1 or self.attributes[-1] > exodus.get_num_elem_attrib(obj_id):
                    raise ValueError("attribute index out of range!")
                self.attributes = [x - 1 for x in self.attributes]
            elif all(isinstance(n, str) for n in attributes):
                name_list = list(exodus.get_elem_attrib_names(obj_id))
                self.attributes = []
                for name in attributes:
                    try:
                        self.attributes.append(name_list.index(name))
                    except ValueError:
                        raise ValueError("Provided attribute %s does not exist!" % name)
                self.attributes.sort()
            else:
                raise TypeError("attributes must contain either all strings or all integers!")

        # We ought to bounds check the inputs and also update the bounds if the exodus object changes


class NodeSetSelector(ObjectSelector):
    """Selects a subset of a node set's components."""
    # input a range
    def __init__(self, exodus: Exodus, obj_id: int, nodes=..., variables=...):
        """
        Create a new selector object for a node set.

        :param exodus: the exodus object this node set is stored in
        :param obj_id: the id of the node set this represents
        :param nodes: the range of nodes to select (1-indexed, internal)
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
        :param elements: the range of elements to select (1-indexed, internal)
        :param variables: the range of variables to select (1-indexed)
        """
        ObjectSelector.__init__(self, exodus, obj_id, SIDESET)
        self.elements = elements
        self.variables = variables


class PropertySelector:
    """Select a subset of object properties."""
    def __init__(self, exodus: Exodus, eb_prop=..., ns_prop=..., ss_prop=...):
        """
        Create a new object property selector.

        :param exodus: the exodus object whose properties this refers to
        :param eb_prop: list of all element block properties to keep by name
        :param ns_prop: list of all node set properties to keep by name
        :param ss_prop: list of all side set properties to keep by name
        """
        self.exodus = exodus

        if eb_prop is None:
            self.eb_prop = []
        elif eb_prop is ...:
            self.eb_prop = exodus.get_elem_block_property_names()
        else:
            # Order of elements does not matter, so we can convert the lists to sets back to lists to remove duplicates
            self.eb_prop = list(set(eb_prop))
            if len(self.eb_prop) != len(eb_prop):
                warnings.warn("Duplicate properties found in eb_prop were automatically removed.")

        if ns_prop is None:
            self.ns_prop = []
        elif ns_prop is ...:
            self.ns_prop = exodus.get_node_set_property_names()
        else:
            self.ns_prop = list(set(ns_prop))
            if len(self.ns_prop) != len(ns_prop):
                warnings.warn("Duplicate properties found in ns_prop were automatically removed.")

        if ss_prop is None:
            self.ss_prop = []
        elif ss_prop is ...:
            self.ss_prop = exodus.get_side_set_property_names()
        else:
            self.ss_prop = list(set(ss_prop))
            if len(self.ss_prop) != len(ss_prop):
                warnings.warn("Duplicate properties found in ss_prop were automatically removed.")
