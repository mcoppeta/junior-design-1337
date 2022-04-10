import numpy
import pytest
import numpy as np
from exodus import Exodus, output_subset
from selector import ElementBlockSelector, NodeSetSelector, SideSetSelector, PropertySelector
from constants import *
import util
import netCDF4 as nc


def test_ns_selector():
    input_file = Exodus("sample-files/cube_with_data.exo", 'r')

    ns_id = input_file.get_node_set_id_map()[0]
    num_nod_ns, num_df_ns = input_file.get_node_set_params(ns_id)
    ns_num = input_file.get_node_set_number(ns_id)
    tab_ns = input_file.get_node_set_truth_table()[ns_num - 1]
    num_var_ns = sum(tab_ns)  # Number of 1s in truth table
    nod_ns = input_file.get_node_set(ns_id)
    df_ns = input_file.get_node_set_df(ns_id)

    # Default selector
    ns = NodeSetSelector(input_file, ns_id)
    assert len(ns.nodes) == num_nod_ns
    assert ns.nodes == list(range(num_nod_ns))
    # Number of variables selected should be the number of 1s in the truth table
    assert len(ns.variables) == num_var_ns
    # Assert that the variables selected are the same ones as are true in the truth table
    for idx in ns.variables:
        assert tab_ns[idx]

    # None selector
    ns = NodeSetSelector(input_file, ns_id, None, None)
    assert ns.nodes == []
    assert ns.variables == []

    # Out of bounds selectors
    with pytest.raises(IndexError):
        ns = NodeSetSelector(input_file, ns_id, nodes=[-1])
    with pytest.raises(IndexError):
        ns = NodeSetSelector(input_file, ns_id, nodes=[1, -1])
    with pytest.raises(IndexError):
        ns = NodeSetSelector(input_file, ns_id, nodes=[input_file.num_nodes])
    with pytest.raises(IndexError):
        ns = NodeSetSelector(input_file, ns_id, nodes=[input_file.num_nodes, 1])
    with pytest.raises(IndexError):
        ns = NodeSetSelector(input_file, ns_id, variables=[-1])
    with pytest.raises(IndexError):
        ns = NodeSetSelector(input_file, ns_id, variables=[1, -1])
    with pytest.raises(IndexError):
        ns = NodeSetSelector(input_file, ns_id, variables=[input_file.num_node_set_var])
    with pytest.raises(IndexError):
        ns = NodeSetSelector(input_file, ns_id, variables=[input_file.num_node_set_var, 1])

    # TODO We do not have a file to test the ValueError thrown when selecting a variable that is NULL for the set

    # Duplicate items in lists
    with pytest.warns(Warning):
        ns = NodeSetSelector(input_file, ns_id, nodes=[1, 1, 1, 2])
    with pytest.warns(Warning):
        ns = NodeSetSelector(input_file, ns_id, variables=[1, 1, 1])

    # Now for real selectors
    # The first node set in cube with data is [22 16  4  5 19 26 14  1  8]
    ns = NodeSetSelector(input_file, ns_id, [1, 3, 2, 5], [2, 1])
    assert nod_ns[ns.nodes] == [22, 16, 4, 19]
    assert ns.variables == [0, 1]

    input_file.close()

# TODO test side set, elblock, and parameter selectors
# TODO copy changes to variable processing over to other selectors
# TODO fix descriptions of other selectors
# TODO key checking in property selector
