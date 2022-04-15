import pytest
import numpy as np
from exodus import Exodus
from netCDF4 import Dataset
import util
from iterate import SampleFiles


# Disables all warnings in this module
pytestmark = pytest.mark.filterwarnings('ignore')


def test_open():
    # Test that we can open a file without any errors
    for file in SampleFiles():
        exofile = Exodus(file, 'r')
        assert exofile.data
        exofile.close()
        exofile = Exodus(file, 'a')
        assert exofile.data
        exofile.close()


def test_create(tmpdir):
    # Test that we can create a file without any errors
    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'w')
    assert exofile.data
    exofile.close()


def test_exodus_init_exceptions(tmp_path, tmpdir):
    # Test that the Exodus.__init__() errors all work
    with pytest.raises(FileNotFoundError):
        Exodus('some fake directory/notafile.xxx', 'r')
    with pytest.raises(ValueError):
        Exodus('sample-files/disk_out_ref.ex2', 'z')
    with pytest.raises(ValueError):
        Exodus(str(tmpdir) + '\\test.ex2', 'w', True, format="NOTAFORMAT")
    with pytest.raises(OSError):
        Exodus('sample-files/can.ex2', 'w', True)
    with pytest.raises(ValueError):
        Exodus(str(tmpdir) + '\\test2.ex2', 'w', True, "NETCDF4", 7)


def test_float(tmpdir):
    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'w', word_size=4)
    assert type(exofile.to_float(1.2)) == np.single
    exofile = Exodus(str(tmpdir) + '\\test2.ex2', 'w', word_size=8)
    assert type(exofile.to_float(1.2)) == np.double
    exofile.close()


def test_parameters():
    exofile = Exodus('sample-files/disk_out_ref.ex2', 'r')
    assert exofile.title
    assert exofile.version
    assert exofile.api_version
    assert exofile.word_size
    exofile.close()


def test_get_node_set():
    # Testing that get_node_set returns accurate info based on info from Coreform Cubit
    # 'can.ex2' has 1 nodeset (ID 1) with 444 nodes and 1 nodeset (ID 100) with 164 nodes
    exofile = Exodus('sample-files/can.ex2', 'r')
    assert len(exofile.get_node_set(1)) == 444
    assert len(exofile.get_node_set(100)) == 164
    exofile.close()
    # 'cube_1ts_mod.e' has 6 nodesets (ID 1-6) with 81 nodes and 1 nodeset (ID 7) with 729 nodes
    exofile = Exodus('sample-files/cube_1ts_mod.e', 'r')
    i = 1
    while i <= 6:
        nodeset = exofile.get_node_set(i)
        assert len(nodeset) == 81
        i += 1
    assert len(exofile.get_node_set(7)) == 729
    exofile.close()
    # Nodeset 1 in 'disk_out_ref.ex2' has 1 node with ID 7210
    exofile = Exodus('sample-files/disk_out_ref.ex2', 'r')
    nodeset = exofile.get_node_set(1)
    assert nodeset[0] == 7210
    exofile.close()


def test_get_side_set():
    # Testing that get_side_set returns accurate info based on info from Coreform Cubit
    # 'can.ex2' has 1 sideset (ID 4) with 120 elements and 120 sides
    exofile = Exodus('sample-files/can.ex2', 'r')
    sideset = exofile.get_side_set(4)
    assert len(sideset[0]) == 120
    assert len(sideset[1]) == 120
    exofile.close()
    # Elem+side counts found in Cubit using "list sideset #" command where # is ID
    # 'disk_out_ref.ex2' has 7 sidesets (ID 1-7) with varying amounts of elements/sides
    exofile = Exodus('sample-files/disk_out_ref.ex2', 'r')
    # ID 1: 418 elements (209 * 2 surfaces), 418 side count
    sideset = exofile.get_side_set(1)
    assert len(sideset[0]) == 418
    assert len(sideset[1]) == 418
    # ID 2: 180 elements (90 * 2 surfaces), 180 side count
    sideset = exofile.get_side_set(2)
    assert len(sideset[0]) == 180
    assert len(sideset[1]) == 180
    # ID 3: 828 elements (414 * 2 surfaces), 828 side count
    sideset = exofile.get_side_set(3)
    assert len(sideset[0]) == 828
    assert len(sideset[1]) == 828
    # ID 4: 238 elements (119 * 2 surfaces), 238 side count
    sideset = exofile.get_side_set(4)
    assert len(sideset[0]) == 238
    assert len(sideset[1]) == 238
    # ID 5: 108 elements (54 * 2 surfaces), 108 side count
    sideset = exofile.get_side_set(5)
    assert len(sideset[0]) == 108
    assert len(sideset[1]) == 108
    # ID 6: 216 elements (108 * 2 surfaces), 216 side count
    sideset = exofile.get_side_set(6)
    assert len(sideset[0]) == 216
    assert len(sideset[1]) == 216
    # ID 7: 482 elements (482 * 1 surface), 482 side count
    # BUT along one face in Cubit so 2 sides/elements counted as 1
    # Technically 964 elements and 964 sides in Exodus file
    sideset = exofile.get_side_set(7)
    assert len(sideset[0]) == 964
    assert len(sideset[1]) == 964
    exofile.close()


def test_get_elem_block():
    # Test that get_elem_blk_connectivity()/params() return accurate results
    exofile = Exodus('sample-files/can.ex2', 'r')
    # ID 1: 4800 elements, 0 attributes, HEX (8 nodes/elem)
    conn = exofile.get_elem_block_connectivity(1)
    assert len(conn) == 4800
    num, node, topo, attrb = exofile.get_elem_block_params(1)
    assert num == 4800
    assert node == 8
    assert topo == 'HEX'
    assert attrb == 0
    # ID 1: 2352 elements, 0 attributes, HEX (8 nodes/elem)
    conn = exofile.get_elem_block_connectivity(2)
    assert len(conn) == 2352
    num, node, topo, attrb = exofile.get_elem_block_params(2)
    assert num == 2352
    assert node == 8
    assert topo == 'HEX'
    assert attrb == 0
    exofile.close()


def test_get_coords():
    # Testing that get_coords returns accurate info based on info from Coreform Cubit
    # 'cube_1ts_mod.e' has 729 coords (ID 1-729) and 3 dimensions (xyz)
    exofile = Exodus('sample-files/cube_1ts_mod.e', 'r')
    coords = exofile.get_coords()
    # 3 coordinates per node
    assert sum(len(dim_arr) for dim_arr in coords) == (729*3)
    # x, y, and z coordinates for each node
    assert len(coords[0]) == len(coords[1]) == len(coords[2])
    # Test coords read correctly for some nodes
    # (Array index from 0, IDs start at 1)
    # Node ID 133 coords: (.125, -.25, -.5)
    assert coords[0][132] == .125
    assert coords[1][132] == -.25
    assert coords[2][132] == -.5
    # Node ID 337 coords: (-.375, .5, -.375)
    assert coords[0][336] == -.375
    assert coords[1][336] == .5
    assert coords[2][336] == -.375
    exofile.close()


def test_get_coord_x():
    # Testing that get_coord_x returns accurate info based on info from Coreform Cubit
    # 'cube_1ts_mod.e' has 729 coords (ID 1-729) and 3 dimensions (xyz)
    exofile = Exodus('sample-files/cube_1ts_mod.e', 'r')
    xcoords = exofile.get_coord_x()
    # 729 nodes
    assert len(xcoords) == 729
    # Test x coord is read correctly for some nodes
    # (Array index from 0, IDs start at 1)
    # Node ID 11 x coord: .375
    assert xcoords[10] == .375
    # Node ID 194 x coord: -.125
    assert xcoords[193] == -.125
    exofile.close()


def test_get_coord_y():
    # Testing that get_coord_y returns accurate info based on info from Coreform Cubit
    # 'cube_1ts_mod.e' has 729 coords (ID 1-729) and 3 dimensions (xyz)
    exofile = Exodus('sample-files/cube_1ts_mod.e', 'r')
    ycoords = exofile.get_coord_y()
    # 729 nodes
    assert len(ycoords) == 729
    # Test y coord is read correctly for some nodes
    # (Array index from 0, IDs start at 1)
    # Node ID 22 y coord: 0
    assert ycoords[21] == 0
    # Node ID 202 y coord: -.5
    assert ycoords[201] == -.5
    exofile.close()


def test_get_coord_z():
    # Testing that get_coord_z returns accurate info based on info from Coreform Cubit
    # 'cube_1ts_mod.e' has 729 coords (ID 1-729) and 3 dimensions (xyz)
    exofile = Exodus('sample-files/cube_1ts_mod.e', 'r')
    zcoords = exofile.get_coord_z()
    # 729 nodes
    assert len(zcoords) == 729
    # Test z coord is read correctly for some nodes
    # (Array index from 0, IDs start at 1)
    # Node ID 365 z coord: -.375
    assert zcoords[364] == -.375
    # Node ID 563 z coord: .25
    assert zcoords[562] == .25
    exofile.close()


def test_write_exceptions(tmpdir):
    exofile = Exodus(str(tmpdir) + '\\test.exo', 'w')
    exofile.add_nodeset([1, 2, 3], 30, "This is a ns")

    with pytest.raises(AttributeError):
        exofile.write(str(tmpdir) + '\\newfile.exo')

    exofile.write()
    exofile.close()

    exofile = Exodus(str(tmpdir) + '\\test.exo', 'a')
    exofile.remove_nodeset(30)

    with pytest.raises(AttributeError):
        exofile.write()

    # Uncomment when Element Ledger bug fixes are pushed
    # exofile.write(str(tmpdir) + '\\newfile.exo')
    exofile.close()


#############################################################################
#                                                                           #
#                            NodeSet Tests                                  #
#                                                                           #
#############################################################################

def test_init_ledger(tmpdir):
    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'w')
    assert exofile.ledger
    exofile.close()
    exofile = Exodus('sample-files/test_ledger.ex2', 'a')
    assert exofile.ledger
    exofile.close()


def test_init_ns_ledger(tmpdir):
    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'w')
    assert exofile.ledger.nodeset_ledger
    exofile.close()
    exofile = Exodus('sample-files/test_ledger.ex2', 'a')
    assert exofile.ledger.nodeset_ledger
    exofile.close()


def test_add_ns_write(tmpdir):
    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'w')

    exofile.add_nodeset([10, 11, 12], 50)
    exofile.add_nodeset([13, 14, 15, 100], 51, "2nd NodeSet")
    exofile.write()
    exofile.close()

    data = Dataset(str(tmpdir) + '\\test.ex2', 'r')

    # check to see the number of node sets increased
    assert data.dimensions['num_node_sets'].size == 2
    # check to see that there are 3 elements in the 1st added nodeset
    assert data.dimensions['num_nod_ns1'].size == 3
    # check to see that there are 4 elements in the 2nd added nodeset
    assert data.dimensions['num_nod_ns2'].size == 4
    # ensure the correct elements are in the 1st new nodeset
    assert np.array_equal(data['node_ns1'], np.array([10, 11, 12]))
    # ensure the correct elements are in the 2nd new nodeset
    assert np.array_equal(data['node_ns2'], np.array([13, 14, 15, 100]))
    # ensure the 1st new nodeset has the correct ID
    assert data['ns_prop1'][0] == 50
    # ensure the 2nd new nodeset has the correct ID
    assert data['ns_prop1'][1] == 51
    # ensure the correct default name is assigned to the new nodeset
    assert util.lineparse(data['ns_names'][0][:]) == "NodeSet 50"
    # ensure the correct specified name is assigned to the new nodeset
    assert util.lineparse(data['ns_names'][1][:]) == "2nd NodeSet"


def test_remove_ns_empty(tmpdir):
    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'w')
    with pytest.raises(KeyError):
        exofile.remove_nodeset(1)


def test_remove_ns_nonexistent(tmpdir):
    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'w')
    exofile.add_nodeset([1, 2, 3], 0, "Test Name")

    with pytest.raises(KeyError):
        exofile.remove_nodeset(1)


def test_remove_ns_existing(tmpdir):
    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'w')

    exofile.add_nodeset([10, 11, 12], 50)
    exofile.add_nodeset([13, 14, 15, 100], 51, "2nd NodeSet")
    exofile.remove_nodeset(51)

    # ensure only one node set remains
    assert exofile.num_node_sets == 1

    # ensure old ID (51) is gone
    with pytest.raises(KeyError):
        exofile.get_node_set(51)

    exofile.write()
    exofile.close()

    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'r')

    # ensure only one node set remains
    assert exofile.num_node_sets == 1

    # ensure old ID (51) is gone
    with pytest.raises(KeyError):
        exofile.get_node_set(51)


def test_add_node_to_nodeset(tmpdir):
    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'w')

    exofile.add_nodeset([10, 11, 12], 99)
    exofile.add_node_to_nodeset(15, 99)
    exofile.write()

    assert exofile.num_node_sets == 1
    assert len(exofile.get_node_set(99)) == 4
    assert np.array_equal(exofile.get_node_set(99), np.array([10, 11, 12, 15]))

    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'r')
    assert exofile.num_node_sets == 1
    assert exofile.data.dimensions['num_nod_ns1'].size == 4
    assert len(exofile.get_node_set(99)) == 4
    assert np.array_equal(exofile.get_node_set(99), np.array([10, 11, 12, 15]))


def test_add_nodes_to_nodeset(tmpdir):
    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'w')

    exofile.add_nodeset([10, 11, 12], 99)
    exofile.add_nodes_to_nodeset([15, 16, 17], 99)
    exofile.write()

    assert exofile.num_node_sets == 1
    assert exofile.data.dimensions['num_nod_ns1'].size == 6
    assert np.array_equal(exofile.get_node_set(99), np.array([10, 11, 12, 15, 16, 17]))

    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'r')

    assert exofile.num_node_sets == 1
    assert exofile.data.dimensions['num_nod_ns1'].size == 6
    assert len(exofile.get_node_set(99)) == 6
    assert np.array_equal(exofile.get_node_set(99), np.array([10, 11, 12, 15, 16, 17]))


def test_remove_from_nonexistent_ns(tmpdir):
    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'w')

    exofile.add_nodeset([10, 11, 12], 99)
    exofile.add_nodeset([13, 14, 15], 100)

    with pytest.raises(KeyError):
        exofile.remove_node_from_nodeset(100, 1)

    exofile.close()


def test_ns_prewrite_read(tmpdir):
    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'w')

    assert exofile.num_node_sets == 0

    exofile.add_nodeset([10, 11, 12], 99)

    assert exofile.num_node_sets == 1
    assert np.array_equal(exofile.get_node_set(99), np.array([10, 11, 12]))

    exofile.add_nodeset([13, 14, 15], 100)

    assert exofile.num_node_sets == 2
    assert np.array_equal(exofile.get_node_set(100), np.array([13, 14, 15]))

    assert np.array_equal(exofile.get_node_set_names(), np.array(['NodeSet 99', 'NodeSet 100']))

    assert exofile.get_node_set_name(99) == 'NodeSet 99'
    assert exofile.get_node_set_name(100) == 'NodeSet 100'


def test_add_duplicate_nodes(tmpdir):
    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'w')

    exofile.add_nodeset([10,  11, 12], 99)
    exofile.add_nodes_to_nodeset([10, 11, 12], 99)
    exofile.add_node_to_nodeset(11, 99)
    exofile.add_node_to_nodeset(12, 99)
    exofile.add_node_to_nodeset(10, 99)

    exofile.write()
    data = Dataset(str(tmpdir) + '\\test.ex2', 'r')
    assert data.dimensions['num_nod_ns1'].size == 3
    assert np.array_equal(np.array([10, 11, 12]), data['node_ns1'])


def test_merge_ns_with_duplicate_nodes(tmpdir):
    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'w')
    exofile.add_nodeset([12, 11, 10], 1)
    exofile.add_nodeset([10, 9, 8, 7, 6, 5, 1], 2)

    # test pre-write read
    exofile.merge_nodeset(3, 1, 2)
    assert len(exofile.get_node_set(3)) == 9
    assert np.array_equal([1, 5, 6, 7, 8, 9, 10, 11, 12], exofile.get_node_set(3))

    # test post write read
    exofile.write()
    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'r')
    assert len(exofile.get_node_set(3)) == 9
    assert np.array_equal([1, 5, 6, 7, 8, 9, 10, 11, 12], exofile.get_node_set(3))


def test_get_nodeset_by_name(tmpdir):
    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'w')
    exofile.add_nodeset([10, 11, 12], 1, "def")
    exofile.add_nodeset([1, 2, 3, 4, 5, 100], 2, "abc")

    ns_1 = exofile.ledger.nodeset_ledger.get_node_set("def")
    assert np.array_equal(ns_1, [10, 11, 12])

    ns_2 = exofile.ledger.nodeset_ledger.get_node_set("abc")
    assert np.array_equal(ns_2, [1, 2, 3, 4, 5, 100])

    ns_1 = exofile.ledger.nodeset_ledger.get_node_set(1)
    assert np.array_equal(ns_1, [10, 11, 12])

    ns_2 = exofile.ledger.nodeset_ledger.get_node_set(2)
    assert np.array_equal(ns_2, [1, 2, 3, 4, 5, 100])

    ns_1_partial = exofile.ledger.nodeset_ledger.get_partial_node_set("def", 1, 2)
    assert np.array_equal(ns_1_partial, [10, 11])

    ns_2_partial = exofile.ledger.nodeset_ledger.get_partial_node_set("abc", 3, 4)
    assert np.array_equal(ns_2_partial, [3, 4, 5, 100])


def test_remove_duplicate_nodes(tmpdir):
    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'w')
    exofile.add_nodeset([10, 9, 8, 7, 6, 5, 1], 2)

    with pytest.raises(IndexError):
        exofile.remove_nodes_from_nodeset([8, 8], 2)


def test_basic_ns_append(tmpdir):
    exofile = Exodus('sample-files/can.ex2', 'a', clobber=False)
    exofile.add_nodeset([1, 2, 3, 4, 5], 10)

    with pytest.raises(AttributeError):
        exofile.write()

    exofile.write(str(tmpdir) + '\\test.ex2')
    exofile.close()

    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'r')
    original = Exodus('sample-files/can.ex2', 'r', clobber=False)

    print("\n", exofile.data.dimensions['num_node_sets'])

    assert original.num_node_sets + 1 == exofile.num_node_sets
    assert np.array_equal(exofile.get_node_set(10), np.array([1, 2, 3, 4, 5]))


def test_permissions():
    exofile = Exodus('sample-files/cube_1ts_mod.e', 'r')

    with pytest.raises(PermissionError):
        exofile.add_nodeset([1, 2, 3, 4], 10)

    with pytest.raises(PermissionError):
        exofile.remove_nodeset(10)

    with pytest.raises(PermissionError):
        exofile.write()

    with pytest.raises(PermissionError):
        exofile.add_sideset([10, 11, 12, 13, 14, 15], [1, 2, 3, 4], 3, "sideset1", [10, 1, 1, 1, 1])

    with pytest.raises(PermissionError):
        exofile.remove_sideset(10)

    with pytest.raises(PermissionError):
        exofile.add_node_to_nodeset(11, 3)

    with pytest.raises(PermissionError):
        exofile.add_nodes_to_nodeset([10, 11, 12], 3)

    with pytest.raises(PermissionError):
        exofile.remove_node_from_nodeset(13, 14)

    with pytest.raises(PermissionError):
        exofile.remove_nodes_from_nodeset([12, 13, 14], 12)

#############################################################################
#                                                                           #
#                            SideSet Tests                                  #
#                                                                           #
#############################################################################


def test_empty_sideset_remove(tmpdir):
    exofile = Exodus(str(tmpdir) + '\\test.ex2', 'w')
    with pytest.raises(IndexError):
        exofile.remove_sideset(10)


# Below tests are based on what can be read according to current C Exodus API.
# The contents, names, and number of tests are subject to change as work on the library progresses
# and we figure out how closely the functions in this library match the C one.

# MODEL DESCRIPTION READ TESTS
def test_get_coords_comprehensive():
    for file in SampleFiles():
        ex = Exodus(file, 'r')
        data = Dataset(file, 'r')
        if 'coord' in data.variables:
            assert np.array_equal(ex.get_coords(), data['coord'][:])

# def test_get_coord_names():
# def test_get_node_num_map():
# def test_get_elem_num_map():
# def test_get_elem_order_map():
# def test_get_elem_blk_params():
# def test_get_elem_blk_IDs():
# def test_get_elem_blk_connect():
# def test_get_nodeset_params():
# def test_get_nodeset_dist_fact():
# def test_get_nodeset_IDs():
# def test_get_concat_nodesets():
# def test_get_sideset_params():
# def test_get_sideset():
# def test_get_sideset_dist_fact():
# def test_get_sideset_IDs():
# def test_get_sideset_node_list():
# def test_get_concat_sidesets():
# def test_get_prop_names():
# def test_get_prop():
# def test_get_prop_array():

# RESULTS DATA READ TESTS
# def test_get_variable_params():
# def test_get_variable_names():
# def test_get_time():
# def test_get_all_times():
# def test_get_elem_var_table():
# def test_get_elem_var():
# def test_get_elem_var_time():
# def test_get_glob_vars():
# def test_get_glob_var_time():
# def test_get_nodal_var():
# def test_get_nodal_var_time():
