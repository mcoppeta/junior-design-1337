"""Allows creation of a new Exodus file by copying selected parts of an opened Exodus file."""

from __future__ import annotations  # use the magic of python 3.7 to let use write Exodus instead of "Exodus"

import warnings
import netCDF4 as nc
import numpy
import util
from selector import ElementBlockSelector, NodeSetSelector, SideSetSelector, PropertySelector
from constants import *
from typing import TYPE_CHECKING, List

# Activate type checking for Exodus by only importing it in the editor
if TYPE_CHECKING:  # evaluates to false at runtime
    from exodus import Exodus


# Writing out a subset of a mesh
def output_subset(input: Exodus, path: str, title: str, eb_selectors: List[ElementBlockSelector],
                  ss_selectors: List[SideSetSelector], ns_selectors: List[NodeSetSelector],
                  prop_selector: PropertySelector, nod_vars: List[int], glo_vars: List[int], time_steps: List[int]):
    """
    Creates a new Exodus file containing a subset of the mesh stored in another Exodus file.

    :param input: exodus object of the file to copy a subset of
    :param path: location of the new exodus file
    :param title: name of the new exodus file
    :param eb_selectors: selectors for element blocks to keep
    :param ss_selectors: selectors for side sets to keep
    :param ns_selectors: selectors for node sets to keep
    :param prop_selector: selector for object properties
    :param nod_vars: list of nodal variable ids to keep (1-indexed)
    :param glo_vars: list of global variable ids to keep (1-indexed)
    :param time_steps: range of time steps to keep
    """
    # TODO you should be able to select variables by name as well as id!
    # Sort lists to maintain input file order in output file
    time_steps.sort()
    nod_vars.sort()
    glo_vars.sort()
    # Check for input validity
    if len(time_steps) > 0 and (time_steps[0] < 1 or time_steps[-1] > input.num_time_steps):
        raise IndexError("Time step selector out of range!")
    if len(nod_vars) > 0 and (nod_vars[0] < 1 or nod_vars[-1] > input.num_node_var):
        raise IndexError("Nodal variable selector out of range!")
    if len(glo_vars) > 0 and (glo_vars[0] < 1 or glo_vars[-1] > input.num_global_var):
        raise IndexError("Global variable selector out of range!")
    output = nc.Dataset(path, 'w')
    output.set_fill_off()

    output.setncattr(ATT_TITLE, title[0:input.max_line_length])
    # This attribute does not include the extra C null character in its size
    output.setncattr(ATT_MAX_NAME_LENGTH, input.max_used_name_length)
    output.setncattr(ATT_API_VER, input.api_version)
    output.setncattr(ATT_VERSION, input.version)
    output.setncattr(ATT_FILE_SIZE, input.large_model)
    output.setncattr(ATT_64BIT_INT, input.int64_status)
    output.setncattr(ATT_WORD_SIZE, input.word_size)
    output.createDimension(DIM_NAME_LENGTH, input.max_allowed_name_length + 1)
    output.createDimension(DIM_STRING_LENGTH, input.max_string_length + 1)
    output.createDimension(DIM_LINE_LENGTH, input.max_line_length + 1)
    output.createDimension(DIM_NUM_DIM, input.num_dim)

    # QA records
    output.createDimension(DIM_FOUR, 4)
    num_qa_rec = input.num_qa + 1
    output.createDimension(DIM_NUM_QA, num_qa_rec)
    var = output.createVariable(VAR_QA, '|S1', (DIM_NUM_QA, DIM_FOUR, DIM_STRING_LENGTH))
    qa = numpy.empty((num_qa_rec, 4, input.max_string_length + 1), '|S1')  # add 1 for null terminator
    if VAR_QA in input.data.variables:
        qa[0:input.num_qa] = input.data.variables[VAR_QA][:]
    qa[-1] = util.generate_qa_rec(input.max_string_length)
    var[:] = qa

    # Info records
    output.createDimension(DIM_NUM_INFO, input.num_info)
    # Don't create a variable if there are no info recs
    if input.num_info > 0:
        var = output.createVariable(VAR_INFO, '|S1', (DIM_NUM_INFO, DIM_LINE_LENGTH))
        # Handle this potential error
        if VAR_INFO in input.data.variables:
            var[:] = input.data.variables[VAR_INFO][:]

    has_time_steps = False
    # Time steps
    time_step_indices = [x - 1 for x in time_steps]
    output.createDimension(DIM_NUM_TIME_STEP, None)  # unlimited
    var = output.createVariable(VAR_TIME_WHOLE, input.float, DIM_NUM_TIME_STEP)
    if len(time_steps) > 0:
        has_time_steps = True
        try:
            var[:] = input.data.variables[VAR_TIME_WHOLE][time_step_indices]
        except IndexError:
            raise IndexError("Time step range provided contains invalid indices")

    # We will keep track of which nodes we add in our selectors for later use
    added_nodes = set()
    # Element Blocks
    # We will keep track of which elements we add so that if the side set selectors select an unadded element we can
    # throw an exception
    output_elem_indices = []
    if len(eb_selectors) > 0:
        if input.num_elem_blk == 0:
            raise ValueError("Element blocks selectors were provided for a database with no element blocks!")
        # Check for duplicate or misplaced selectors
        ids = []  # list of obj ids
        idmap = {}  # dict mapping internal ids to eb selectors
        for sel in eb_selectors:
            if sel.obj_id in ids:
                raise ValueError("Multiple selectors for the same entity were provided!")
            if sel.exodus != input:
                raise ValueError("Provided selector is for a different exodus object!")
            ids.append(sel.obj_id)
            internal_id = input.get_elem_block_number(sel.obj_id)
            idmap[internal_id] = sel
        # This cannot happen until we figure out which elements are being carried over
        output.createDimension(DIM_NUM_EB, len(eb_selectors))

        selected_block_indices = [x - 1 for x in idmap.keys()]

        # EB names
        if VAR_EB_NAMES in input.data.variables:
            var = output.createVariable(VAR_EB_NAMES, '|S1', (DIM_NUM_EB, DIM_NAME_LENGTH))
            var[:] = input.data.variables[VAR_EB_NAMES][selected_block_indices]

        # Status array
        if VAR_EB_STATUS in input.data.variables:
            var = output.createVariable(VAR_EB_STATUS, input.int, DIM_NUM_EB)
            var[:] = input.data.variables[VAR_EB_STATUS][selected_block_indices]

        block_id_map = input.data.variables[VAR_EB_PROP % 1]
        # EB ID map / prop1
        var = output.createVariable(VAR_EB_PROP % 1, input.int, DIM_NUM_EB)
        var.setncattr(ATTR_NAME, 'ID')
        if 'ID' in prop_selector.eb_prop:
            # Keep ID map
            var[:] = block_id_map[selected_block_indices]
        else:
            # Generate ID map
            var[:] = numpy.arange(1, len(eb_selectors) + 1, dtype=input.int)

        # Other EB properties
        propids = {}  # dict mapping property ids to names
        for propname in prop_selector.eb_prop:
            # We've already handled ids so we can skip this
            if propname == 'ID':
                continue
            n = 1
            while True:
                if VAR_EB_PROP % n in input.data.variables:
                    name = input.data.variables[VAR_EB_PROP % n].getncattr(ATTR_NAME)
                    if propname == name:
                        # we've found our property
                        propids[n] = propname
                        break
                    else:
                        # check next property
                        n += 1
                        continue
                else:
                    # We looked at every property and didn't find this one. This should never happen.
                    break

        propid = 1  # we've already handled prop1
        # Loop over all the properties and add them if they were selected
        for i in range(2, input.num_elem_block_prop + 1):
            if i in propids.keys():
                propid += 1  # id of current property in output
                var = output.createVariable(VAR_EB_PROP % propid, input.int, DIM_NUM_EB)
                var[:] = input.data.variables[VAR_EB_PROP % i][selected_block_indices]
                var.setncattr(ATTR_NAME, propids[i])

        # Figure out which variables we're keeping
        vars_to_keep = []
        for eb in eb_selectors:
            for v in eb.variables:
                if v not in vars_to_keep:
                    vars_to_keep.append(v)
        vars_to_keep.sort()  # sort to keep ordering
        has_variables = False
        if len(vars_to_keep) > 0:
            has_variables = True
            output.createDimension(DIM_NUM_ELEM_VAR, len(vars_to_keep))
            # Only copy names if they were previously defined
            if VAR_NAME_ELEM_VAR in input.data.variables:
                var = output.createVariable(VAR_NAME_ELEM_VAR, '|S1', (DIM_NUM_ELEM_VAR, DIM_STRING_LENGTH))
                var[:] = input.data.variables[VAR_NAME_ELEM_VAR][vars_to_keep]
            # Create truth table. We'll set its values in a moment.
            var_truth_tab = output.createVariable(VAR_ELEM_TAB, input.int, (DIM_NUM_EB, DIM_NUM_ELEM_VAR))

        # EB connectivity list
        output_id = 0
        sum_elem = 0
        # Loop over all the input element blocks and add them if they were selected
        for n in range(input.num_elem_blk):
            input_id = n + 1
            # retrieve info for this element block
            num_el, nod_per_el, topology, num_attr = input.get_elem_block_params(block_id_map[n])
            if input_id in idmap.keys():
                output_id += 1  # id of current block in output
                eb = idmap[input_id]  # selector of current block in output

                # Dimensions
                dim_num_el_in_blk = DIM_NUM_EL_IN_BLK % output_id
                output.createDimension(dim_num_el_in_blk, len(eb.elements))
                dim_nod_per_el = DIM_NUM_NOD_PER_EL % output_id
                output.createDimension(dim_nod_per_el, nod_per_el)

                # Connectivity list
                var = output.createVariable(VAR_CONNECT % output_id, input.int, (dim_num_el_in_blk, dim_nod_per_el))
                var.setncattr(ATTR_ELEM_TYPE, topology)
                var[:] = input.data.variables[VAR_CONNECT % input_id][eb.elements, :]
                output_elem_indices.extend([x + sum_elem for x in eb.elements])
                # Compress the masked array
                thing = input.data.variables[VAR_CONNECT % input_id][eb.elements, :]
                thing = thing.compressed()
                added_nodes.update(thing)

                # EB attributes
                if len(eb.attributes) > 0:
                    dim_att_in_blk = DIM_NUM_ATT_IN_BLK % output_id
                    output.createDimension(dim_att_in_blk, len(eb.attributes))
                    var = output.createVariable(VAR_ELEM_ATTRIB % output_id, input.float,
                                                (dim_num_el_in_blk, dim_att_in_blk))
                    var[:] = input.data.variables[VAR_ELEM_ATTRIB % input_id][eb.elements, eb.attributes]
                    var = output.createVariable(VAR_ELEM_ATTRIB_NAME % output_id, '|S1',
                                                (dim_att_in_blk, DIM_NAME_LENGTH))
                    var[:] = input.data.variables[VAR_ELEM_ATTRIB_NAME % input_id][eb.attributes]

                # Variable data and truth table filling
                if has_variables:
                    row = numpy.zeros(len(vars_to_keep), input.int)  # init row
                    for j in eb.variables:
                        out_var_idx = vars_to_keep.index(j)
                        row[out_var_idx] = 1  # Set true in truth table row
                        # We only want to copy over variable values if we're keeping time steps
                        if has_time_steps:
                            var = output.createVariable(VAR_VALS_ELEM_VAR % (out_var_idx + 1, output_id),
                                                        input.float,
                                                        (DIM_NUM_TIME_STEP, dim_num_el_in_blk))
                            var[:] = input.data.variables[VAR_VALS_ELEM_VAR % (j + 1, input_id)][time_step_indices,
                                                                                                 eb.elements]
                    var_truth_tab[output_id - 1] = row  # put row in table
            # Keep track of how many elements we've looked at
            sum_elem += num_el
    # END OF ELEMENT BLOCK PROCESSING


    # Number of elements
    output.createDimension(DIM_NUM_ELEM, len(output_elem_indices))

    # Element ID map
    var = output.createVariable(VAR_ELEM_ID_MAP, input.int, DIM_NUM_ELEM)
    var[:] = input.get_elem_id_map()[output_elem_indices]

    # Optional element order map
    if VAR_ELEM_ORDER_MAP in input.data.variables:
        var = output.createVariable(VAR_ELEM_ORDER_MAP, input.int, DIM_NUM_ELEM)
        var[:] = input.data.variables[VAR_ELEM_ORDER_MAP][output_elem_indices]

    eb_added_elements = [x + 1 for x in output_elem_indices]
    old_new_elem_id_map = {}  # keyed on old, value is new
    newid = 1
    for oldid in eb_added_elements:
        old_new_elem_id_map[oldid] = newid
        newid += 1

    # Side sets
    # If the side set selectors include an element that was not selected in the element blocks, the function will throw
    # an exception. Figuring out which elements are in side sets but not in blocks and then putting them in blocks is
    # pretty complicated, so we make the user do that for us.
    if len(ss_selectors) > 0:
        num_side_sets = len(ss_selectors)
        if input.num_side_sets == 0:
            raise ValueError("Side set selectors were provided for a database with no side sets!")
        # Check for duplicate or misplaced selectors
        ids = []  # list of obj ids
        idmap = {}  # dict mapping internal ids to ns selectors
        for sss in ss_selectors:
            if sss.obj_id in ids:
                raise ValueError("Multiple selectors for the same entity were provided!")
            if sss.exodus != input:
                raise ValueError("Provided selector is for a different exodus object!")
            ids.append(sss.obj_id)
            internal_id = input.get_side_set_number(sss.obj_id)
            idmap[internal_id] = sss
        output.createDimension(DIM_NUM_SS, num_side_sets)

        selected_set_indices = [x - 1 for x in idmap.keys()]

        # SS names
        if VAR_SS_NAMES in input.data.variables:
            var = output.createVariable(VAR_SS_NAMES, '|S1', (DIM_NUM_SS, DIM_NAME_LENGTH))
            var[:] = input.data.variables[VAR_SS_NAMES][selected_set_indices]

        # Status array
        if VAR_SS_STATUS in input.data.variables:
            var = output.createVariable(VAR_SS_STATUS, input.int, DIM_NUM_SS)
            var[:] = input.data.variables[VAR_SS_STATUS][selected_set_indices]

        set_id_map = input.data.variables[VAR_SS_PROP % 1]
        # SS ID map / prop1
        var = output.createVariable(VAR_SS_PROP % 1, input.int, DIM_NUM_SS)
        var.setncattr(ATTR_NAME, 'ID')
        if 'ID' in prop_selector.ss_prop:
            # Keep ID map
            var[:] = set_id_map[selected_set_indices]
        else:
            # Generate ID map
            var[:] = numpy.arange(1, num_side_sets + 1, dtype=input.int)

        # Other SS properties
        propids = {}  # dict mapping property ids to names
        for propname in prop_selector.ss_prop:
            # We've already handled ids so we can skip this
            if propname == 'ID':
                continue
            n = 1
            while True:
                if VAR_SS_PROP % n in input.data.variables:
                    name = input.data.variables[VAR_SS_PROP % n].getncattr(ATTR_NAME)
                    if propname == name:
                        # we've found our property
                        propids[n] = propname
                        break
                    else:
                        # check next property
                        n += 1
                        continue
                else:
                    # We looked at every property and didn't find this one. This should never happen.
                    break

        propid = 1  # we've already handled prop1
        # Loop over all the properties and add them if they were selected
        for i in range(2, input.num_side_set_prop + 1):
            if i in propids.keys():
                propid += 1  # id of current property in output
                var = output.createVariable(VAR_SS_PROP % propid, input.int, DIM_NUM_SS)
                var[:] = input.data.variables[VAR_SS_PROP % i][selected_set_indices]
                var.setncattr(ATTR_NAME, propids[i])

        # Figure out which variables we're keeping
        vars_to_keep = []
        for sel in ss_selectors:
            for v in sel.variables:
                if v not in vars_to_keep:
                    vars_to_keep.append(v)
        vars_to_keep.sort()  # sort to keep ordering
        has_variables = False
        if len(vars_to_keep) > 0:
            has_variables = True
            output.createDimension(DIM_NUM_SS_VAR, len(vars_to_keep))
            # Only copy names if they were previously defined
            if VAR_NAME_SS_VAR in input.data.variables:
                var = output.createVariable(VAR_NAME_SS_VAR, '|S1', (DIM_NUM_SS_VAR, DIM_STRING_LENGTH))
                var[:] = input.data.variables[VAR_NAME_SS_VAR][vars_to_keep]
            # Create truth table. We'll set its values in a moment.
            var_truth_tab = output.createVariable(VAR_SS_TAB, input.int, (DIM_NUM_SS, DIM_NUM_SS_VAR))

        output_id = 0
        # Loop over all the input side sets and add them if they were selected
        for n in range(input.num_side_sets):
            input_id = n + 1
            if input_id in idmap.keys():
                output_id += 1  # id of current block in output
                sel = idmap[input_id]  # selector of current block in output

                # Dimensions
                dim_num_side_ss = DIM_NUM_SIDE_SS % output_id
                output.createDimension(dim_num_side_ss, len(sel.sides))

                # Element list
                var = output.createVariable(VAR_ELEM_SS % output_id, input.int, dim_num_side_ss)
                to_add = input.data.variables[VAR_ELEM_SS % input_id][sel.sides]
                converted_to_add = []
                for id in to_add:
                    try:
                        converted_to_add.append(old_new_elem_id_map[id])
                    except KeyError:
                        raise ValueError(
                            "Side set selector includes an element that is not selected by element block selectors. Put"
                            " this in your element block selection, or remove it from your side set selection. [{0}]"
                                .format(id))
                # The output's elem array needs to have the elem ids for the output!
                var[:] = converted_to_add

                # Confirm that every element used in side sets is in an element block now
                ss_added_elements = to_add
                difference = set(ss_added_elements) - set(eb_added_elements)
                if len(difference) > 0:
                    raise ValueError(
                        "Side set selectors include elements that are not selected by element block selectors. Put"
                        " these in your element block selection, or remove them from your side set selection. {0}"
                            .format(difference))

                # Side list
                var = output.createVariable(VAR_SIDE_SS % output_id, input.int, dim_num_side_ss)
                var[:] = input.data.variables[VAR_SIDE_SS % input_id][sel.sides]

                # Distribution factors
                if VAR_DF_SS % input_id in input.data.variables:
                    dim_num_df_ss = DIM_NUM_DF_SS % output_id
                    node_count_list = input.get_side_set_node_count_list(input_id)
                    # Count how many nodes are on the selected sides only
                    num_nodes_selected = sum(node_count_list[sel.sides])
                    output.createDimension(dim_num_df_ss, num_nodes_selected)

                    var = output.createVariable(VAR_DF_SS % output_id, input.float, dim_num_df_ss)
                    # Now for the fun part...
                    # Grab the old dist facts
                    old_df = input.data.variables[VAR_DF_SS % input_id]
                    # Create an array for the new ones
                    output_df = numpy.empty(num_nodes_selected, input.float)
                    # We're going to iterate over each side in the side set and get the number of nodes that side has.
                    # If we selected it, we're going to copy the next cnt nodes from old_df to output_df. If we did not
                    # we will skip over that many nodes in old_df
                    old_df_idx = 0
                    output_df_idx = 0
                    for k in range(len(node_count_list)):
                        cnt = node_count_list[k]  # number of nodes in this side
                        if k in sel.sides:  # If this is a selected side
                            while cnt > 0:
                                output_df[output_df_idx] = old_df[old_df_idx]
                                output_df_idx += 1
                                old_df_idx += 1
                                cnt -= 1
                        else:
                            old_df_idx += cnt
                    # ...and finally put the output distribution factors in the file
                    var[:] = output_df

                # Variable data and truth table filling
                if has_variables:
                    row = numpy.zeros(len(vars_to_keep), input.int)  # init row
                    for j in sel.variables:
                        out_var_idx = vars_to_keep.index(j)
                        row[out_var_idx] = 1  # Set true in truth table row
                        # We only want to copy over variable values if we're keeping time steps
                        if has_time_steps:
                            var = output.createVariable(VAR_VALS_SS_VAR % (out_var_idx + 1, output_id), input.float,
                                                        (DIM_NUM_TIME_STEP, dim_num_side_ss))
                            var[:] = input.data.variables[VAR_VALS_SS_VAR % (j + 1, input_id)][
                                time_step_indices, sel.sides]
                    var_truth_tab[output_id - 1] = row  # put row in table
    # END SIDE SET PROCESSING

    # Node sets
    if len(ns_selectors) > 0:
        num_side_sets = len(ns_selectors)
        if input.num_node_sets == 0:
            raise ValueError("Node set selectors were provided for a database with no node sets!")
        # Check for duplicate or misplaced selectors
        ids = []  # list of obj ids
        idmap = {}  # dict mapping internal ids to ns selectors
        for sel in ns_selectors:
            if sel.obj_id in ids:
                raise ValueError("Multiple selectors for the same entity were provided!")
            if sel.exodus != input:
                raise ValueError("Provided selector is for a different exodus object!")
            ids.append(sel.obj_id)
            internal_id = input.get_node_set_number(sel.obj_id)
            idmap[internal_id] = sel
        output.createDimension(DIM_NUM_NS, num_side_sets)

        selected_set_indices = [x - 1 for x in idmap.keys()]

        # NS names
        if VAR_NS_NAMES in input.data.variables:
            var = output.createVariable(VAR_NS_NAMES, '|S1', (DIM_NUM_NS, DIM_NAME_LENGTH))
            var[:] = input.data.variables[VAR_NS_NAMES][selected_set_indices]

        # Status array
        if VAR_NS_STATUS in input.data.variables:
            var = output.createVariable(VAR_NS_STATUS, input.int, DIM_NUM_NS)
            var[:] = input.data.variables[VAR_NS_STATUS][selected_set_indices]

        set_id_map = input.data.variables[VAR_NS_PROP % 1]
        # NS ID map / prop1
        var = output.createVariable(VAR_NS_PROP % 1, input.int, DIM_NUM_NS)
        var.setncattr(ATTR_NAME, 'ID')
        if 'ID' in prop_selector.ns_prop:
            # Keep ID map
            var[:] = set_id_map[selected_set_indices]
        else:
            # Generate ID map
            var[:] = numpy.arange(1, num_side_sets + 1, dtype=input.int)

        # Other NS properties
        propids = {}  # dict mapping property ids to names
        for propname in prop_selector.ns_prop:
            # We've already handled ids so we can skip this
            if propname == 'ID':
                continue
            n = 1
            while True:
                if VAR_NS_PROP % n in input.data.variables:
                    name = input.data.variables[VAR_NS_PROP % n].getncattr(ATTR_NAME)
                    if propname == name:
                        # we've found our property
                        propids[n] = propname
                        break
                    else:
                        # check next property
                        n += 1
                        continue
                else:
                    # We looked at every property and didn't find this one. This should never happen.
                    break

        propid = 1  # we've already handled prop1
        # Loop over all the properties and add them if they were selected
        for i in range(2, input.num_node_set_prop + 1):
            if i in propids.keys():
                propid += 1  # id of current property in output
                var = output.createVariable(VAR_NS_PROP % propid, input.int, DIM_NUM_NS)
                var[:] = input.data.variables[VAR_NS_PROP % i][selected_set_indices]
                var.setncattr(ATTR_NAME, propids[i])

        # Figure out which variables we're keeping
        vars_to_keep = []
        for sel in ns_selectors:
            for v in sel.variables:
                if v not in vars_to_keep:
                    vars_to_keep.append(v)
        vars_to_keep.sort()  # sort to keep ordering
        has_variables = False
        if len(vars_to_keep) > 0:
            has_variables = True
            output.createDimension(DIM_NUM_NS_VAR, len(vars_to_keep))
            # Only copy names if they were previously defined
            if VAR_NAME_NS_VAR in input.data.variables:
                var = output.createVariable(VAR_NAME_NS_VAR, '|S1', (DIM_NUM_NS_VAR, DIM_STRING_LENGTH))
                var[:] = input.data.variables[VAR_NAME_NS_VAR][vars_to_keep]
            # Create truth table. We'll set its values in a moment.
            var_truth_tab = output.createVariable(VAR_NS_TAB, input.int, (DIM_NUM_NS, DIM_NUM_NS_VAR))

        # Node set
        output_id = 0
        # Loop over all the input node sets and add them if they were selected
        for n in range(input.num_node_sets):
            input_id = n + 1
            # retrieve info for this node set
            if input_id in idmap.keys():
                output_id += 1  # id of current block in output
                ns = idmap[input_id]  # selector of current set in output

                # Dimensions
                dim_num_node_ns = DIM_NUM_NODE_NS % output_id
                output.createDimension(dim_num_node_ns, len(ns.nodes))

                # Node list
                var = output.createVariable(VAR_NODE_NS % output_id, input.int, dim_num_node_ns)
                var[:] = input.data.variables[VAR_NODE_NS % input_id][ns.nodes]
                added_nodes.update(input.data.variables[VAR_NODE_NS % input_id][ns.nodes])

                # Distribution factors
                if VAR_DF_NS % input_id in input.data.variables:
                    var = output.createVariable(VAR_DF_NS % output_id, input.float, dim_num_node_ns)
                    var[:] = input.data.variables[VAR_DF_NS % input_id][ns.nodes]

                # Variable data and truth table filling
                if has_variables:
                    row = numpy.zeros(len(vars_to_keep), input.int)  # init row
                    for j in ns.variables:
                        out_var_idx = vars_to_keep.index(j)
                        row[out_var_idx] = 1  # Set true in truth table row
                        # We only want to copy over variable values if we're keeping time steps
                        if has_time_steps:
                            var = output.createVariable(VAR_VALS_NS_VAR % (out_var_idx + 1, output_id), input.float,
                                                        (DIM_NUM_TIME_STEP, dim_num_node_ns))
                            var[:] = input.data.variables[VAR_VALS_NS_VAR % (j + 1, input_id)][time_step_indices,
                                                                                               ns.nodes]
                    var_truth_tab[output_id - 1] = row  # put row in table
    # END OF NODE SET PROCESSING

    # Potential improvement: do a pre-pass on the selectors and gather all of the elements and nodes they need.
    # This would allow addition of elements selected in side set selectors that are not in element block selectors since
    # we could add them to a new element block. Doing nodes would save us the effort of remapping the node IDs after
    # we've added the wrong, not remapped IDs to the output file.

    # We need to sort the added nodes to maintain ordering
    added_nodes = list(added_nodes)
    added_nodes.sort()
    # 0-indexed version for indexing arrays later
    added_nodes_indices = [x - 1 for x in added_nodes]

    # Now that we know which nodes are in the output file, we need to go back and change all the indices in the output
    # file from input node indices to output node indices
    old_new_node_id_map = {}  # keyed on old, value is new
    newid = 1
    for oldid in added_nodes:
        old_new_node_id_map[oldid] = newid
        newid += 1

    # Node set node lists
    if DIM_NUM_NS in output.dimensions:  # only if we have node sets
        for i in range(1, output.dimensions[DIM_NUM_NS].size + 1):
            var = output.variables[VAR_NODE_NS % i]
            vararr = var[:]
            num_nodes = output.dimensions[DIM_NUM_NODE_NS % i].size
            new_var = numpy.empty(num_nodes, input.int)
            for j in range(num_nodes):
                new_var[j] = old_new_node_id_map[vararr[j]]
            var[:] = new_var

    # Element block connectivity lists
    if DIM_NUM_EB in output.dimensions:  # only if we have element blocks
        for i in range(1, output.dimensions[DIM_NUM_EB].size + 1):
            var = output.variables[VAR_CONNECT % i]
            vararr = var[:]
            num_elem = output.dimensions[DIM_NUM_EL_IN_BLK % i].size
            num_node = output.dimensions[DIM_NUM_NOD_PER_EL % i].size
            new_var = numpy.empty((num_elem, num_node), input.int)
            for j in range(num_elem):
                for k in range(num_node):
                    new_var[j, k] = old_new_node_id_map[vararr[j, k]]
            var[:] = new_var

    # Dimension for number of nodes
    output.createDimension(DIM_NUM_NODES, len(added_nodes))

    # Node id map
    var = output.createVariable(VAR_NODE_ID_MAP, input.int, DIM_NUM_NODES)
    var[:] = input.get_node_id_map()[added_nodes_indices]

    # Coordinates
    if input.large_model:
        num_dim = input.num_dim
        if num_dim >= 1:
            var = output.createVariable(VAR_COORD_X, input.float, DIM_NUM_NODES)
            var[:] = input.data.variables[VAR_COORD_X][:][added_nodes_indices]
            if num_dim >= 2:
                var = output.createVariable(VAR_COORD_Y, input.float, DIM_NUM_NODES)
                var[:] = input.data.variables[VAR_COORD_Y][:][added_nodes_indices]
                if num_dim >= 3:
                    var = output.createVariable(VAR_COORD_Z, input.float, DIM_NUM_NODES)
                    var[:] = input.data.variables[VAR_COORD_Z][:][added_nodes_indices]
    else:
        var = output.createVariable(VAR_COORD, input.float, (DIM_NUM_DIM, DIM_NUM_NODES))
        var[:] = input.data.variables[VAR_COORD][:, added_nodes_indices]

    if VAR_COORD_NAMES in input.data.variables:
        var = output.createVariable(VAR_COORD_NAMES, '|S1', (DIM_NUM_DIM, DIM_NAME_LENGTH))
        var[:] = input.data.variables[VAR_COORD_NAMES][:]

    # Global Variables
    if len(glo_vars) > 0:
        if VAR_VALS_GLO_VAR not in input.data.variables:
            raise ValueError("Global variables selected, but no global variables exist!")
        output.createDimension(DIM_NUM_GLO_VAR, len(glo_vars))
        var = output.createVariable(VAR_VALS_GLO_VAR, input.float, (DIM_NUM_TIME_STEP, DIM_NUM_GLO_VAR))
        glo_var_idx = [x - 1 for x in glo_vars]
        try:
            # Need to subtract 1 to convert variables ids into indices
            var[:] = input.data.variables[VAR_VALS_GLO_VAR][time_step_indices, glo_var_idx]
        except IndexError:
            raise IndexError("Global variables provided contain invalid indices")
        if VAR_NAME_GLO_VAR in input.data.variables:
            var = output.createVariable(VAR_NAME_GLO_VAR, '|S1', (DIM_NUM_GLO_VAR, DIM_STRING_LENGTH))
            var[:] = input.data.variables[VAR_NAME_GLO_VAR][glo_var_idx]

    # Nodal Variables
    if len(nod_vars) > 0:
        if input.large_model:
            if VAR_VALS_NOD_VAR_LARGE % 1 not in input.data.variables:
                raise ValueError("Nodal variables selected, but no nodal variables exist!")
        else:
            if VAR_VALS_NOD_VAR_SMALL not in input.data.variables:
                raise ValueError("Nodal variables selected, but no nodal variables exist!")
        output.createDimension(DIM_NUM_NOD_VAR, len(nod_vars))
        nod_var_idx = [x - 1 for x in nod_vars]
        if input.large_model:
            output_id = 1
            for id in nod_vars:
                var = output.createVariable(VAR_VALS_NOD_VAR_LARGE % output_id, input.float, (DIM_NUM_TIME_STEP,
                                                                                              DIM_NUM_NODES))
                var[:] = input.data.variables[VAR_VALS_NOD_VAR_LARGE % id][time_step_indices, added_nodes_indices]
                output_id += 1
        else:
            var = output.createVariable(VAR_VALS_NOD_VAR_SMALL, input.float, (DIM_NUM_TIME_STEP, DIM_NUM_NOD_VAR,
                                                                              DIM_NUM_NODES))
            var[:] = input.data.variables[time_step_indices, nod_var_idx, added_nodes_indices]
        if VAR_NAME_NOD_VAR in input.data.variables:
            var = output.createVariable(VAR_NAME_NOD_VAR, '|S1', (DIM_NUM_NOD_VAR, DIM_STRING_LENGTH))
            var[:] = input.data.variables[VAR_NAME_NOD_VAR][nod_var_idx]

    # Warn the user if their file looks strange
    if output.dimensions[DIM_NUM_NODES].size == 0:
        warnings.warn("Output file is likely corrupt since it has 0 nodes!")
    if output.dimensions[DIM_NUM_ELEM].size == 0:
        warnings.warn("Output file is likely corrupt since it has 0 elements!")
    output.close()
