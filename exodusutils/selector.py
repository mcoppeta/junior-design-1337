"""
Selectors are used to select a subset of an Exodus file's features.

These are used extensively in `exodusutils.output_subset`. See that documentation for more details on how to use
members of this module.
"""

from __future__ import annotations  # use the magic of python 3.7 to let use write Exodus instead of "Exodus"
from typing import TYPE_CHECKING

from abc import ABC, abstractmethod
import warnings
from .constants import *

# Give us some handy type checking without creating cyclic imports at runtime
# Its like preprocessor code, but not!

if TYPE_CHECKING:  # evaluates to false at runtime
    from .exodus import Exodus


class _ObjectSelector(ABC):
    """Abstract base class of all selectors."""

    def __init__(self, exodus: Exodus, obj_id: int, obj_type: ObjectType):
        self.exodus = exodus
        self.obj_id = obj_id
        self.obj_type = obj_type

        # probably needs an abstract update method for when exodus changes


# TODO name support for variables?
class ElementBlockSelector(_ObjectSelector):
    """Selects a subset of an element block's components."""

    def __init__(self, exodus: Exodus, obj_id: int, elements=..., variables=..., attributes=...):
        """
        Create a new selector object for an element block.

        Pass in ``...`` to select everything, ``None`` to select nothing, or a list of specific values.
        Lists will be sorted upon entry to maintain element order consistency.

        ``elements``, ``variables``, and ``attributes`` take 1-based indices, meaning to select the first and second
        element you would pass in the list [1, 2].

        ``attributes`` accepts attribute names as well, but you cannot use names and indices together!

        :param exodus: the exodus object this element block is stored in
        :param obj_id: the id of the element block this represents
        :param elements: list of elements to select within this block (1-based)
        :param variables: the variable indices to select (1-based)
        :param attributes: the attribute indices (1-based) or a list of attribute names to select
        """
        _ObjectSelector.__init__(self, exodus, obj_id, ELEMBLOCK)

        if elements is None:
            self.elements = []
        elif elements is ...:
            num_elem, _, _, _ = exodus.get_elem_block_params(obj_id)
            self.elements = list(range(num_elem))
        else:
            # Order of elements does not matter, so we can convert the lists to sets back to lists to remove duplicates
            self.elements = list(set(elements))
            self.elements.sort()
            num_elem, _, _, _ = exodus.get_elem_block_params(obj_id)
            if len(self.elements) > 0 and (self.elements[0] < 1 or self.elements[-1] > num_elem):
                raise IndexError("elements out of range!")
            self.elements = [x - 1 for x in self.elements]
            if len(self.elements) != len(elements):
                warnings.warn("Duplicate elements were automatically removed.")

        if variables is None:
            self.variables = []
        elif variables is ...:
            # Get the truth table
            internal_id = exodus.get_elem_block_number(obj_id)
            tab = exodus.get_elem_block_truth_table()[internal_id - 1]
            self.variables = []
            # Go over every variable. If it's in the truth table, add its index to the variables list
            for i in range(exodus.num_elem_block_var):
                if tab[i]:
                    self.variables.append(i)
        else:
            self.variables = list(set(variables))
            self.variables.sort()
            if len(self.variables) > 0 and (self.variables[0] < 1 or self.variables[-1] > exodus.num_elem_block_var):
                raise IndexError("variable index out of range!")
            self.variables = [x - 1 for x in self.variables]
            # Get the truth table
            internal_id = exodus.get_elem_block_number(obj_id)
            tab = exodus.get_elem_block_truth_table()[internal_id - 1]
            # Go over selected variables. If it's not in the truth table, throw an error
            for idx in self.variables:
                if not tab[idx]:
                    raise ValueError("variable %d is not set for element block %d!" % (idx, obj_id))
            if len(self.variables) != len(variables):
                warnings.warn("Duplicate variables were automatically removed.")

        if attributes is None:
            self.attributes = []
        elif attributes is ...:
            self.attributes = list(range(exodus.get_num_elem_attrib(obj_id)))
        else:
            if len(attributes) == 0:
                self.attributes = []
            elif all(isinstance(n, int) for n in attributes):
                self.attributes = list(set(attributes))
                self.attributes.sort()
                if self.attributes[0] < 1 or self.attributes[-1] > exodus.get_num_elem_attrib(obj_id):
                    raise IndexError("attribute index out of range!")
                if len(self.attributes) != len(attributes):
                    warnings.warn("Duplicate attributes were automatically removed.")
                self.attributes = [x - 1 for x in self.attributes]
            elif all(isinstance(n, str) for n in attributes):
                name_list = list(exodus.get_elem_attrib_names(obj_id))
                unique_attributes = list(set(attributes))
                self.attributes = []
                # Make sure that the names the user provided are valid
                for name in unique_attributes:
                    if name not in name_list:
                        raise ValueError("Provided attribute %s does not exist!" % name)
                # Add the index of all attributes with the given names to the list
                # Exodus doesn't seem to enforce needing unique attribute names, so this gets around that weird rule
                # and will warn the user if the file has multiple attributes with the same name.
                selected_names = []
                dupes = False
                for i in range(len(name_list)):
                    if name_list[i] in unique_attributes:
                        self.attributes.append(i)
                        if name_list[i] not in selected_names:
                            selected_names.append(name_list[i])
                        else:
                            dupes = True
                # Doing things this way already sorts the attributes
                # self.attributes.sort()
                if len(unique_attributes) != len(attributes):
                    warnings.warn("Duplicate attributes were automatically removed.")
                if dupes:
                    warnings.warn("Multiple attributes with the same name were selected. Consider using indices.")
            else:
                raise TypeError("attributes must contain either all strings or all integers!")


class NodeSetSelector(_ObjectSelector):
    """Selects a subset of a node set's components."""

    def __init__(self, exodus: Exodus, obj_id: int, nodes=..., variables=...):
        """
        Create a new selector object for a node set.

        Pass in ``...`` to select everything, ``None`` to select nothing, or a list of specific values.
        Lists will be sorted upon entry to maintain node order consistency.

        ``nodes`` and ``variables`` take 1-based indices, meaning to select the first and second node you would pass in
        the list [1, 2].

        :param exodus: the exodus object this node set is stored in
        :param obj_id: the id of the node set this represents
        :param nodes: list of nodes to select within this set (1-based)
        :param variables: the variable indices to select (1-based)
        """
        _ObjectSelector.__init__(self, exodus, obj_id, NODESET)

        if nodes is None:
            self.nodes = []
        elif nodes is ...:
            num_nod, _ = exodus.get_node_set_params(obj_id)
            self.nodes = list(range(num_nod))
        else:
            self.nodes = list(set(nodes))
            self.nodes.sort()
            num_nod, _ = exodus.get_node_set_params(obj_id)
            if len(self.nodes) > 0 and (self.nodes[0] < 1 or self.nodes[-1] > num_nod):
                raise IndexError("nodes out of range!")
            self.nodes = [x - 1 for x in self.nodes]
            if len(self.nodes) != len(nodes):
                warnings.warn("Duplicate nodes were automatically removed.")

        if variables is None:
            self.variables = []
        elif variables is ...:
            # Get the truth table
            internal_id = exodus.get_node_set_number(obj_id)
            tab = exodus.get_node_set_truth_table()[internal_id - 1]
            self.variables = []
            # Go over every variable. If it's in the truth table, add its index to the variables list
            for i in range(exodus.num_node_set_var):
                if tab[i]:
                    self.variables.append(i)
        else:
            self.variables = list(set(variables))
            self.variables.sort()
            if len(self.variables) > 0 and (self.variables[0] < 1 or self.variables[-1] > exodus.num_node_set_var):
                raise IndexError("variable index out of range!")
            self.variables = [x - 1 for x in self.variables]
            # Get the truth table
            internal_id = exodus.get_node_set_number(obj_id)
            tab = exodus.get_node_set_truth_table()[internal_id - 1]
            # Go over selected variables. If it's not in the truth table, throw an error
            for idx in self.variables:
                if not tab[idx]:
                    raise ValueError("variable %d is not set for node set %d!" % (idx, obj_id))
            if len(self.variables) != len(variables):
                warnings.warn("Duplicate variables were automatically removed.")


class SideSetSelector(_ObjectSelector):
    """Selects a subset of a side set's components."""

    def __init__(self, exodus: Exodus, obj_id: int, sides=..., variables=...):
        """
        Create a new selector object for a side set.

        Pass in ``...`` to select everything, ``None`` to select nothing, or a list of specific values.
        Lists will be sorted upon entry to maintain node order consistency.

        ``sides`` and ``variables`` take 1-based indices, meaning to select the first and second side you would pass in
         the list [1, 2].

        :param exodus: the exodus object this side set is stored in
        :param obj_id: the id of the side set this represents
        :param sides: list of sides to select within this set (1-based)
        :param variables: the variable indices to select (1-based)
        """
        _ObjectSelector.__init__(self, exodus, obj_id, SIDESET)

        if sides is None:
            self.sides = []
        elif sides is ...:
            num_el, _ = exodus.get_side_set_params(obj_id)
            self.sides = list(range(num_el))
        else:
            self.sides = list(set(sides))
            self.sides.sort()
            num_el, _ = exodus.get_side_set_params(obj_id)
            if len(sides) > 0 and (self.sides[0] < 1 or self.sides[-1] > num_el):
                raise IndexError("sides out of range!")
            self.sides = [x - 1 for x in self.sides]
            if len(self.sides) != len(sides):
                warnings.warn("Duplicate sides were automatically removed.")

        if variables is None:
            self.variables = []
        elif variables is ...:
            # Get the truth table
            internal_id = exodus.get_side_set_number(obj_id)
            tab = exodus.get_side_set_truth_table()[internal_id - 1]
            self.variables = []
            # Go over every variable. If it's in the truth table, add its index to the variables list
            for i in range(exodus.num_side_set_var):
                if tab[i]:
                    self.variables.append(i)
        else:
            self.variables = list(set(variables))
            self.variables.sort()
            if len(self.variables) > 0 and (self.variables[0] < 1 or self.variables[-1] > exodus.num_side_set_var):
                raise IndexError("variable index out of range!")
            self.variables = [x - 1 for x in self.variables]
            # Get the truth table
            internal_id = exodus.get_side_set_number(obj_id)
            tab = exodus.get_side_set_truth_table()[internal_id - 1]
            # Go over selected variables. If it's not in the truth table, throw an error
            for idx in self.variables:
                if not tab[idx]:
                    raise ValueError("variable %d is not set for side set %d!" % (idx, obj_id))
            if len(self.variables) != len(variables):
                warnings.warn("Duplicate variables were automatically removed.")


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
            self.eb_prop = list(set(eb_prop))
            props = exodus.get_elem_block_property_names()
            for propname in self.eb_prop:
                if propname not in props:
                    raise ValueError("Provided element block property %s does not exist!" % propname)
            if len(self.eb_prop) != len(eb_prop):
                warnings.warn("Duplicate properties found in eb_prop were automatically removed.")

        if ns_prop is None:
            self.ns_prop = []
        elif ns_prop is ...:
            self.ns_prop = exodus.get_node_set_property_names()
        else:
            self.ns_prop = list(set(ns_prop))
            props = exodus.get_node_set_property_names()
            for propname in self.ns_prop:
                if propname not in props:
                    raise ValueError("Provided node set property %s does not exist!" % propname)
            if len(self.ns_prop) != len(ns_prop):
                warnings.warn("Duplicate properties found in ns_prop were automatically removed.")

        if ss_prop is None:
            self.ss_prop = []
        elif ss_prop is ...:
            self.ss_prop = exodus.get_side_set_property_names()
        else:
            self.ss_prop = list(set(ss_prop))
            props = exodus.get_side_set_property_names()
            for propname in self.ss_prop:
                if propname not in props:
                    raise ValueError("Provided node set property %s does not exist!" % propname)
            if len(self.ss_prop) != len(ss_prop):
                warnings.warn("Duplicate properties found in ss_prop were automatically removed.")
