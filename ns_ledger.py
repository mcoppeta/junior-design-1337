import numpy as np


class NSLedger:

    def __init__(self, ex):
        # maps the unique name assigned to each nodeset with the actual nodeset
        self.nodeset_map = {}
        # inorder list of unique nodeset names
        self.nodesets = []
        # keeps track of nodeset ids according to ns_prop1
        self.nodeset_ids = []
        # O(1) lookup for nodeset ids to ensure uniqueness
        self.nodeset_id_set = set()
        # counter to assign unique names to nodesets
        self.new_nodeset_id = 0
        self.ex = ex

        # if no existing nodesets, no need to set up variables
        # beyond initialization
        if 'num_node_sets' not in ex.data.dimensions.keys():
            return

        # setup nodeset map for existing nodesets
        for i in range(ex.data.dimensions['num_node_sets'].size):
            ns_title = "node_ns" + str(i+1)
            self.nodesets.append(ns_title)
            self.nodeset_map[ns_title] = None

        # setup support for ns_prop1 id map if it exists
        if "ns_prop1" in ex.data.variables.keys():
            for i in ex.data.variables['ns_prop1']:
                self.nodeset_ids.append(i)
                self.nodeset_id_set.add(i)
        # if not, create id map for consistency
        else:
            for i in range(len(self.nodesets)):
                self.nodeset_ids.append(i+1)
                self.nodeset_id_set.add(i+1)

    def add_nodeset(self, node_ids, nodeset_id):

        if nodeset_id in self.nodeset_id_set:
            raise KeyError("Nodeset ID already in use")

        self.nodesets.append(str(self.new_nodeset_id))
        self.nodeset_map[str(self.new_nodeset_id)] = np.array(node_ids)
        self.nodeset_ids.append(nodeset_id)
        self.new_nodeset_id += 1

    def remove_nodeset(self, nodeset_id):
        nodeset_num = -1
        # search for nodeset that corresponds with given ID
        for i in range(len(self.nodeset_ids)):
            if self.nodeset_ids[i] == nodeset_id:
                nodeset_num = i
                break

        # raise ValueError if no nodeset is found
        if nodeset_num == -1:
            raise ValueError("Cannot find nodeset with ID " + str(nodeset_id))

        # remove all references to removed nodeset
        # O(1) with respect to the actual nodesets
        # O(n) with respect to number of changes in ledger
        nodeset_name = self.nodesets.pop(nodeset_num)
        removed_id = self.nodeset_ids.pop(nodeset_num)
        self.nodeset_id_set.remove(removed_id)
        self.nodeset_map.pop(nodeset_name)

    def write(self, data):

        # if no nodesets exist, no writing needs to be performed
        if len(self.nodesets) == 0:
            return

        # create num_node_sets dimension
        data.createDimension("num_node_sets", len(self.nodesets))

        # add ns_prop1 data
        data.createVariable("ns_prop1", "int32", dimensions=("num_node_sets"))
        data['ns_prop1'][:] = np.array(self.nodeset_ids)

        # add nodeset data
        for i in range(len(self.nodesets)):
            nodeset_name = self.nodesets[i]
            # if nodeset exists in old file, copy directly
            if self.nodeset_map[nodeset_name] is None:
                dimension = self.ex.data.variables[nodeset_name].dimensions[0]
                data.createDimension("num_nod_ns" + str(i+1),
                                     self.ex.data.dimensions[dimension].size)
                data.createVariable("node_ns" + str(i+1), "int32",
                                    dimensions=("num_nod_ns" + str(i+1)))

                # copy data
                data["node_ns" + str(i+1)][:] = self.ex.data[nodeset_name][:]
            # else, create according to np array
            else:
                data.createDimension("num_nod_ns" + str(i+1),
                                     len(self.nodeset_map[nodeset_name]))
                data.createVariable("node_ns" + str(i+1), "int32",
                                    dimensions=("num_nod_ns" + str(i+1)))
                data["node_ns"+str(i+1)][:] = self.nodeset_map[nodeset_name][:]

        # TODO: add ns_status, dist_fact_ns, ns_names
