import numpy as np


class NSLedger:

    def __init__(self, ex):
        # maps the unique name assigned to each nodeset with the actual nodeset
        # maps to None if nodeset exists in original file
        self.nodeset_map = {}
        # inorder list of unique program-specified nodeset names
        # integer value if nodeset is added to existing file
        # name of form node_ns # if nodeset already exists
        self.nodesets = []
        # counter to assign unique program-specified names to nodesets
        self.new_nodeset_name = 0

        # keeps track of nodeset ids according to ns_prop1
        # self.nodeset_ids[i] = j denotes nodeset of id j existing at index i
        self.nodeset_ids = []
        # O(1) lookup for nodeset ids to ensure uniqueness
        self.nodeset_id_set = set()

        # inorder list of user-specified nodeset names
        self.nodeset_names = []
        # O(1) lookup for user-specified nodeset names
        self.nodeset_name_set = set()
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
                self.nodeset_ids.append(int(i))
                self.nodeset_id_set.add(int(i))
        # if not, create id map for consistency
        else:
            for i in range(len(self.nodesets)):
                self.nodeset_ids.append(i+1)
                self.nodeset_id_set.add(i+1)

        # setup user-specified nodeset names
        if "ns_names" in ex.data.variables.keys():
            for name in ex.data.variables['ns_names']:
                n = self.lineparse(name)
                self.nodeset_names.append(n)
                self.nodeset_name_set.add(n)
        else:
            for i in self.nodeset_ids:
                self.nodeset_names.append("NodeSet %d" % i)
                self.nodeset_name_set.add("NodeSet %d" % i)

    def add_nodeset(self, node_ids, nodeset_id, nodeset_name=""):

        if nodeset_id in self.nodeset_id_set:
            raise KeyError("Nodeset ID already in use")
        if nodeset_name in self.nodeset_name_set or "NodeSet %d" % nodeset_id in self.nodeset_name_set:
            raise KeyError("Nodeset name already in use")

        self.nodesets.append(str(self.new_nodeset_name))
        self.nodeset_map[str(self.new_nodeset_name)] = np.unique(np.array(node_ids))
        self.nodeset_ids.append(nodeset_id)
        self.nodeset_id_set.add(nodeset_id)

        if nodeset_name == "":
            self.nodeset_names.append("NodeSet %d" % nodeset_id)
            self.nodeset_name_set.add("NodeSet %d" % nodeset_id)
        else:
            self.nodeset_names.append(nodeset_name)
            self.nodeset_name_set.add(nodeset_name)

        self.new_nodeset_name += 1

    def remove_nodeset(self, nodeset_id):
        nodeset_num = self.find_nodeset_num(nodeset_id)

        # remove all references to removed nodeset
        # O(1) with respect to the actual nodesets
        # O(n) with respect to number of changes in ledger
        nodeset_name = self.nodesets.pop(nodeset_num)
        removed_id = self.nodeset_ids.pop(nodeset_num)
        self.nodeset_id_set.remove(int(removed_id))
        self.nodeset_map.pop(nodeset_name)

        name = self.nodeset_names.pop(nodeset_num)
        self.nodeset_name_set.remove(name)

    def merge_nodesets(self, new_id, nodeset_id1, nodeset_id2, delete=True):
        if new_id in self.nodeset_id_set:
            raise KeyError("Nodeset ID already in use")

        n1 = self.get_node_set(nodeset_id1)
        n2 = self.get_node_set(nodeset_id2)
        n3 = []
        for i in n1:
            n3.append(i)
        for i in n2:
            if i not in n3:
                n3.append(i)

        self.add_nodeset(n3, new_id)
        if delete:
            self.remove_nodeset(nodeset_id1)
            self.remove_nodeset(nodeset_id2)

    def add_node_to_nodeset(self, node_id, nodeset_id):
        self.add_nodes_to_nodeset(np.array(node_id), nodeset_id)

    def remove_node_from_nodeset(self, node_id, nodeset_id):
        self.remove_nodes_from_nodeset(np.array(node_id), nodeset_id)

    # node_ids must be array-like per numpy
    def add_nodes_to_nodeset(self, node_ids, nodeset_id):
        nodeset_num = self.find_nodeset_num(nodeset_id)

        # determine whether nodeset exists in memory or still only exists in the exodus object
        # needs to be pulled into memory regardless
        program_name = self.nodesets[nodeset_num]
        curr_nodeset = self.nodeset_map[program_name]
        if curr_nodeset is None:
            curr_nodeset = self.ex.data[program_name][:]
            program_name = str(self.new_nodeset_name)
            self.nodeset_map[program_name] = curr_nodeset
            self.new_nodeset_name += 1

        new_nodeset = np.unique(np.append(curr_nodeset, node_ids))
        self.nodeset_map[program_name] = new_nodeset

    def remove_nodes_from_nodeset(self, node_ids, nodeset_id):
        nodeset_num = self.find_nodeset_num(nodeset_id)

        # determine whether nodeset exists in memory or still only exists in the exodus object
        # needs to be pulled into memory regardless
        program_name = self.nodesets[nodeset_num]
        curr_nodeset = self.nodeset_map[program_name]
        if curr_nodeset is None:
            curr_nodeset = self.ex.data[program_name][:]
            program_name = str(self.new_nodeset_name)
            self.nodeset_map[program_name] = curr_nodeset
            self.new_nodeset_name += 1

        new_nodeset = np.setdiff1d(curr_nodeset, node_ids)
        if len(curr_nodeset) - len(new_nodeset) != len(node_ids):
            raise IndexError("One or more nodes could not be found in NodeSet " + str(nodeset_id))
        self.nodeset_map[program_name] = new_nodeset

    def write(self, data):

        # if no nodesets exist, no writing needs to be performed
        if len(self.nodesets) == 0:
            return

        # create num_node_sets dimension
        data.createDimension("num_node_sets", len(self.nodesets))

        # add ns_prop1 data
        data.createVariable("ns_prop1", "int32", dimensions=("num_node_sets"))
        data['ns_prop1'].setncattr('name', 'ID')
        data['ns_prop1'][:] = np.array(self.nodeset_ids)

        # add ns_name data
        data.createVariable("ns_names", "|S1", dimensions=("num_node_sets", "len_name"))
        for i in range(len(self.nodeset_names)):
            data['ns_names'][i] = NSLedger.convert_string(self.nodeset_names[i])

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

                if "dist_fact_ns" + nodeset_name[-1:] in self.ex.data.variables.keys():
                    data.createVariable("dist_fact_ns" + str(i+1), "float64", dimensions=("num_nod_ns" + str(i+1)))
                    data["dist_fact_ns" + str(i+1)][:] = self.ex.data["dist_fact_ns" + nodeset_name[-1:]][:]
                else:
                    data.createVariable("dist_fact_ns" + str(i + 1), "float64", dimensions=("num_nod_ns" + str(i + 1)))
                    ns_size = data.dimensions['num_nod_ns' + str(i+1)].size
                    data["dist_fact_ns" + str(i+1)][:] = np.ones(ns_size, dtype=np.float64)[:]

            # else, create according to np array
            else:
                data.createDimension("num_nod_ns" + str(i+1),
                                     len(self.nodeset_map[nodeset_name]))
                data.createVariable("node_ns" + str(i+1), "int32",
                                    dimensions=("num_nod_ns" + str(i+1)))
                data["node_ns"+str(i+1)][:] = self.nodeset_map[nodeset_name][:]
                data.createVariable("dist_fact_ns" + str(i + 1), "float64", dimensions=("num_nod_ns" + str(i + 1)))
                ns_size = data.dimensions['num_nod_ns' + str(i + 1)].size
                data["dist_fact_ns" + str(i + 1)][:] = np.ones(ns_size, dtype=np.float64)[:]

        # TODO: add ns_status

    def find_nodeset_num(self, nodeset_id):
        nodeset_num = -1
        # search for nodeset that corresponds with given ID
        for i in range(len(self.nodeset_ids)):
            if self.nodeset_ids[i] == nodeset_id:
                nodeset_num = i
                break

        # raise IndexError if no nodeset is found
        if nodeset_num == -1:
            raise KeyError("Cannot find nodeset with ID " + str(nodeset_id))

        return nodeset_num

    def num_node_sets(self):
        return len(self.nodesets)

    def get_node_set(self, id):
        num = self.find_nodeset_num(id)
        name = self.nodesets[num]
        if name not in self.nodeset_map.keys():
            raise KeyError(f"NodeSet {id} does not exist")

        if self.nodeset_map[name] is None:
            return np.array(self.ex.data[name])
        return np.array(self.nodeset_map[name])

    def get_node_set_name(self, id):
        num = self.find_nodeset_num(id)
        return self.nodeset_names[num]

    def get_node_set_names(self):
        return np.array(self.nodeset_names)

    @staticmethod
    def lineparse(line):
        s = ""
        for c in line:
            if str(c) != '--':
                s += str(c)[2]

        return s

    # method to convert python string to netcdf4 compatible character array
    @staticmethod
    def convert_string(s):
        arr = np.empty(33, '|S1')
        for i in range(len(s)):
            arr[i] = s[i]

        mask = np.empty(33, bool)
        for i in range(33):
            if i < len(s):
                mask[i] = False
            else:
                mask[i] = True

        out = np.ma.core.MaskedArray(arr, mask)
        return out
