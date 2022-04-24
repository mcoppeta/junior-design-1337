import pytest
import numpy as np
from exodusutils import Exodus, ElementBlockSelector, NodeSetSelector, SideSetSelector, PropertySelector


def test_ns_selector():
    input_file = Exodus("sample-files/cube_with_data.exo", 'r')

    ns_id = input_file.get_node_set_id_map()[0]
    num_nod_ns, _ = input_file.get_node_set_params(ns_id)
    ns_num = input_file.get_node_set_number(ns_id)
    tab_ns = input_file.get_node_set_truth_table()[ns_num - 1]
    num_var_ns = sum(tab_ns)  # Number of 1s in truth table
    nod_ns = input_file.get_node_set(ns_id)

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

    # Empty list selector
    ns = NodeSetSelector(input_file, ns_id, [], [])
    assert ns.nodes == []
    assert ns.variables == []

    # Out of bounds selectors
    with pytest.raises(IndexError):
        ns = NodeSetSelector(input_file, ns_id, nodes=[-1])
    with pytest.raises(IndexError):
        ns = NodeSetSelector(input_file, ns_id, nodes=[1, -1])
    with pytest.raises(IndexError):
        ns = NodeSetSelector(input_file, ns_id, nodes=[input_file.num_nodes + 1])
    with pytest.raises(IndexError):
        ns = NodeSetSelector(input_file, ns_id, nodes=[input_file.num_nodes + 1, 1])
    with pytest.raises(IndexError):
        ns = NodeSetSelector(input_file, ns_id, variables=[-1])
    with pytest.raises(IndexError):
        ns = NodeSetSelector(input_file, ns_id, variables=[1, -1])
    with pytest.raises(IndexError):
        ns = NodeSetSelector(input_file, ns_id, variables=[input_file.num_node_set_var + 1])
    with pytest.raises(IndexError):
        ns = NodeSetSelector(input_file, ns_id, variables=[input_file.num_node_set_var + 1, 1])

    # TODO We do not have a file to test the ValueError thrown when selecting a variable that is NULL for the set

    # Duplicate items in lists
    with pytest.warns(Warning):
        ns = NodeSetSelector(input_file, ns_id, nodes=[1, 1, 1, 2])
    with pytest.warns(Warning):
        ns = NodeSetSelector(input_file, ns_id, variables=[1, 1, 1])

    # Now for real selectors
    # The first node set in cube with data is [22 16  4  5 19 26 14  1  8]
    ns = NodeSetSelector(input_file, ns_id, [1, 3, 2, 5], [2, 1])

    assert np.array_equal(nod_ns[ns.nodes], [22, 16, 4, 19])
    assert ns.variables == [0, 1]

    input_file.close()


def test_ss_selector():
    input_file = Exodus("sample-files/cube_with_data.exo", 'r')

    ss_id = input_file.get_side_set_id_map()[0]
    num_elem_ss, _ = input_file.get_side_set_params(ss_id)
    ss_num = input_file.get_side_set_number(ss_id)
    tab_ss = input_file.get_side_set_truth_table()[ss_num - 1]
    num_var_ss = sum(tab_ss)  # Number of 1s in truth table
    elem_ss, side_ss = input_file.get_side_set(ss_id)

    # Default selector
    ss = SideSetSelector(input_file, ss_id)
    assert len(ss.sides) == num_elem_ss
    assert ss.sides == list(range(num_elem_ss))
    # Number of variables selected should be the number of 1s in the truth table
    assert len(ss.variables) == num_var_ss
    # Assert that the variables selected are the same ones as are true in the truth table
    for idx in ss.variables:
        assert tab_ss[idx]

    # None selector
    ss = SideSetSelector(input_file, ss_id, None, None)
    assert ss.sides == []
    assert ss.variables == []

    # Empty list selector
    ss = SideSetSelector(input_file, ss_id, [], [])
    assert ss.sides == []
    assert ss.variables == []

    # Out of bounds selectors
    with pytest.raises(IndexError):
        ss = SideSetSelector(input_file, ss_id, sides=[-1])
    with pytest.raises(IndexError):
        ss = SideSetSelector(input_file, ss_id, sides=[1, -1])
    with pytest.raises(IndexError):
        ss = SideSetSelector(input_file, ss_id, sides=[input_file.num_elem + 1])
    with pytest.raises(IndexError):
        ss = SideSetSelector(input_file, ss_id, sides=[input_file.num_elem + 1, 1])
    with pytest.raises(IndexError):
        ss = SideSetSelector(input_file, ss_id, variables=[-1])
    with pytest.raises(IndexError):
        ss = SideSetSelector(input_file, ss_id, variables=[1, -1])
    with pytest.raises(IndexError):
        ss = SideSetSelector(input_file, ss_id, variables=[input_file.num_side_set_var + 1])
    with pytest.raises(IndexError):
        ss = SideSetSelector(input_file, ss_id, variables=[input_file.num_side_set_var + 1, 1])

    # TODO We do not have a file to test the ValueError thrown when selecting a variable that is NULL for the set

    # Duplicate items in lists
    with pytest.warns(Warning):
        ss = SideSetSelector(input_file, ss_id, sides=[1, 1, 1, 2])
    with pytest.warns(Warning):
        ss = SideSetSelector(input_file, ss_id, variables=[1, 1, 1])

    # Now for real selectors
    # The first side set in cube with data is elem_list: [5 6 7 8]
    #                                         side_list: [6 6 6 6]
    ss = SideSetSelector(input_file, ss_id, [3, 1], [2, 1])

    assert np.array_equal(elem_ss[ss.sides], [5, 7])
    assert np.array_equal(side_ss[ss.sides], [6, 6])
    assert ss.variables == [0, 1]

    input_file.close()


def test_eb_selector():
    input_file = Exodus("sample-files/bake.e", 'r')

    eb_id = input_file.get_elem_block_id_map()[21 - 1]
    num_elem_eb, _, _, num_attr_eb = input_file.get_elem_block_params(eb_id)
    eb_num = input_file.get_elem_block_number(eb_id)
    tab_eb = input_file.get_elem_block_truth_table()[eb_num - 1]
    num_var_eb = sum(tab_eb)  # Number of 1s in truth table
    connect = input_file.get_elem_block_connectivity(eb_id)

    # Default selector
    eb = ElementBlockSelector(input_file, eb_id)
    assert len(eb.elements) == num_elem_eb
    assert eb.elements == list(range(num_elem_eb))
    # Number of variables selected should be the number of 1s in the truth table
    assert len(eb.variables) == num_var_eb
    # Assert that the variables selected are the same ones as are true in the truth table
    for idx in eb.variables:
        assert tab_eb[idx]
    assert len(eb.attributes) == num_attr_eb
    assert eb.attributes == list(range(num_attr_eb))

    # None selector
    eb = ElementBlockSelector(input_file, eb_id, None, None, None)
    assert eb.elements == []
    assert eb.variables == []
    assert eb.attributes == []

    # Empty list selector
    eb = ElementBlockSelector(input_file, eb_id, [], [], [])
    assert eb.elements == []
    assert eb.variables == []
    assert eb.attributes == []

    # Out of bounds selectors
    with pytest.raises(IndexError):
        eb = ElementBlockSelector(input_file, eb_id, elements=[-1])
    with pytest.raises(IndexError):
        eb = ElementBlockSelector(input_file, eb_id, elements=[1, -1])
    with pytest.raises(IndexError):
        eb = ElementBlockSelector(input_file, eb_id, elements=[input_file.num_elem + 1])
    with pytest.raises(IndexError):
        eb = ElementBlockSelector(input_file, eb_id, elements=[input_file.num_elem + 1, 1])
    with pytest.raises(IndexError):
        eb = ElementBlockSelector(input_file, eb_id, variables=[-1])
    with pytest.raises(IndexError):
        eb = ElementBlockSelector(input_file, eb_id, variables=[1, -1])
    with pytest.raises(IndexError):
        eb = ElementBlockSelector(input_file, eb_id, variables=[input_file.num_elem_block_var + 1])
    with pytest.raises(IndexError):
        eb = ElementBlockSelector(input_file, eb_id, variables=[input_file.num_elem_block_var + 1, 1])
    with pytest.raises(IndexError):
        eb = ElementBlockSelector(input_file, eb_id, attributes=[-1])
    with pytest.raises(IndexError):
        eb = ElementBlockSelector(input_file, eb_id, attributes=[1, -1])
    with pytest.raises(IndexError):
        eb = ElementBlockSelector(input_file, eb_id, attributes=[num_attr_eb + 1])
    with pytest.raises(IndexError):
        eb = ElementBlockSelector(input_file, eb_id, attributes=[num_attr_eb + 1, 1])

    # TODO We do not have a file to test the ValueError thrown when selecting a variable that is NULL for the block

    # Duplicate items in lists
    with pytest.warns(Warning):
        eb = ElementBlockSelector(input_file, eb_id, elements=[1, 1, 1, 2])
    with pytest.warns(Warning):
        eb = ElementBlockSelector(input_file, eb_id, variables=[1, 1, 1])
    with pytest.warns(Warning):
        eb = ElementBlockSelector(input_file, eb_id, attributes=[1, 1, 1])

    # Now for real selectors
    # The first elblock in bake.e is
    # [[6262 6253 6263]
    #  [6134 6143 6133]
    #  [6375 6366 6376]
    #  ...
    #  [6272 6282 6281]
    #  [6307 6298 6308]
    #  [6327 6336 6326]]
    #  and there are 760 elements, but only 1 variable and attribute
    eb = ElementBlockSelector(input_file, eb_id, [1, 3, 2, 759, 760], [1], [1])

    assert np.array_equal(connect[eb.elements], [[6262, 6253, 6263], [6134, 6143, 6133], [6375, 6366, 6376],
                                                 [6307, 6298, 6308], [6327, 6336, 6326]])
    assert eb.variables == [0]
    assert eb.attributes == [0]

    input_file.close()

    # We need to change files to test attribute names
    # TODO we do not have a file with named attributes (biplane has all of its attributes named an empty string)
    input_file = Exodus("sample-files/biplane.exo", 'r')
    eb_id = input_file.get_elem_block_id_map()[8 - 1]

    # Selector with attribute names
    with pytest.warns(Warning):  # We expect a warning that biplane has multiple attributes with the same name
        eb = ElementBlockSelector(input_file, eb_id, attributes=[''])
        assert eb.attributes == [0, 1, 2, 3, 4, 5, 6]
    # Duplicate attribute names in list
    with pytest.warns(Warning):
        eb = ElementBlockSelector(input_file, eb_id, attributes=['', ''])
    # Duplicate attribute names in files
    with pytest.warns(Warning):
        eb = ElementBlockSelector(input_file, eb_id, attributes=[''])
    # This should not emit a warning because we did not select the name that appears multiple times in the file
    eb = ElementBlockSelector(input_file, eb_id, attributes=[])

    input_file.close()


def test_param_selector():
    input_file = Exodus("sample-files/cube_with_data.exo", 'r')
    # Cube with data has only the required ID property
    num_eb_prop = input_file.num_elem_block_prop
    num_ns_prop = input_file.num_node_set_prop
    num_ss_prop = input_file.num_side_set_prop
    eb_prop_names = input_file.get_elem_block_property_names()
    ns_prop_names = input_file.get_node_set_property_names()
    ss_prop_names = input_file.get_side_set_property_names()

    # Default selector
    ps = PropertySelector(input_file)
    assert len(ps.eb_prop) == num_eb_prop
    assert len(ps.ns_prop) == num_ns_prop
    assert len(ps.ss_prop) == num_ss_prop
    assert ps.eb_prop == eb_prop_names
    assert ps.ns_prop == ns_prop_names
    assert ps.ss_prop == ss_prop_names

    # None selector
    ps = PropertySelector(input_file, None, None, None)
    assert len(ps.eb_prop) == 0
    assert len(ps.ns_prop) == 0
    assert len(ps.ss_prop) == 0

    # Empty list selector
    ps = PropertySelector(input_file, [], [], [])
    assert len(ps.eb_prop) == 0
    assert len(ps.ns_prop) == 0
    assert len(ps.ss_prop) == 0

    # Invalid property name
    with pytest.raises(ValueError):
        ps = PropertySelector(input_file, eb_prop=['NONSENSE'])
    with pytest.raises(ValueError):
        ps = PropertySelector(input_file, ns_prop=['NONSENSE'])
    with pytest.raises(ValueError):
        ps = PropertySelector(input_file, ss_prop=['NONSENSE'])

    # Duplicate items in lists
    with pytest.warns(Warning):
        ps = PropertySelector(input_file, eb_prop=['ID', 'ID'])
    with pytest.warns(Warning):
        ps = PropertySelector(input_file, ns_prop=['ID', 'ID'])
    with pytest.warns(Warning):
        ps = PropertySelector(input_file, ss_prop=['ID', 'ID'])

    # Now some real selectors
    ps = PropertySelector(input_file, ['ID'], ['ID'], ['ID'])
    assert len(ps.eb_prop) == 1
    assert len(ps.ns_prop) == 1
    assert len(ps.ss_prop) == 1
    assert ps.eb_prop == ['ID']
    assert ps.ns_prop == ['ID']
    assert ps.ss_prop == ['ID']

    ps = PropertySelector(input_file, ['ID'], [], ...)
    assert len(ps.eb_prop) == 1
    assert len(ps.ns_prop) == 0
    assert len(ps.ss_prop) == num_ss_prop
    assert ps.eb_prop == ['ID']
    assert ps.ns_prop == []
    assert ps.ss_prop == ss_prop_names

    input_file.close()
