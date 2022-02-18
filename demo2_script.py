from exodus import Exodus


# This part of the demo does the following:
#   1. Create a new nodeset with id 99, containing the same nodes as ns2 (+X face)
#   2. Add to this nodeset the nodes from ns6 (+Z face)
#   3. Remove the intersecting nodes between ns2 and ns6, i.e. the edge of the cube
#   4. Writes out the new exodus file to cube_1ts_mod_rev.e
def merge_adjacent_nodesets(path):
    ex = Exodus(path, 'a')

    ns2_node_ids = ex.get_node_set(2) # The node ids for ns2 (+X)
    ex.add_nodeset(ns2_node_ids, 99, "AdjacentNS")

    ns6_node_ids = ex.get_node_set(6)  # The node ids for ns6 (+Z)
    ex.add_nodes_to_nodeset(ns6_node_ids, 99)

    intersection_ids = list(set(ns2_node_ids) & set(ns6_node_ids))
    print("Intersection (cube edge):\n{}".format(intersection_ids))  # Print these IDs out for reference later
    ex.remove_nodes_from_nodeset(intersection_ids, 99)

    ex.write()
    ex.close()


# This part of the demo reviews the changes made above (in addition to Cubit visualization):
#   1. General Diff
#   2. NS2 diff
#   3. NS6 diff
def review_changes(path, path2):
    ex = Exodus(path, 'r')
    ex2 = Exodus(path2, 'r')

    # General printout
    # Other (ex2) should have an extra nodeset
    ex.diff(ex2)

    # Show difference between ns2 and new ns99
    # ns2 should include intersection from above
    ex.diff_nodeset(2, ex2, 99)

    # Show difference between ns6 and new ns99
    # ns6 should include intersection from above
    ex.diff_nodeset(6, ex2, 99)

    ex.close()
    ex2.close()


if __name__ == "__main__":
    path = "sample-files/cube_1ts_mod.e"
    path_rev = "sample-files/cube_1ts_mod_rev.ex2"

    merge_adjacent_nodesets(path)
    input()
    review_changes(path, path_rev)


