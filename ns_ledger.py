import numpy as np
import util


class NSLedger:

    def __init__(self, ex):
        # maps the unique name assigned to each node set with the actual nodeset
        # maps to None if node set exists in original file
        self.node_set_map = {}
        # inorder list of unique program-specified node set names
        # integer value if node set is added to existing file
        # name of form node_ns # if node set already exists
        self.node_sets = []
        # counter to assign unique program-specified names to node sets
        self.new_node_set_name = 0

        # keeps track of node set ids according to ns_prop1
        # self.nodeset_ids[i] = j denotes nodeset of id j existing at index i
        self.node_set_ids = []
        # O(1) lookup for nodeset ids to ensure uniqueness
        self.node_set_id_set = set()

        # inorder list of user-specified node set names
        self.node_set_names = []
        # O(1) lookup for user-specified node set names
        self.node_set_name_set = set()
        self.ex = ex

        self.node_set_name_lookup = {}

        # if no existing nodesets, no need to set up variables
        # beyond initialization
        if 'num_node_sets' not in ex.data.dimensions.keys():
            return

        # setup nodeset map for existing nodesets
        for i in range(ex.data.dimensions['num_node_sets'].size):
            ns_title = "node_ns" + str(i+1)
            self.node_sets.append(ns_title)
            self.node_set_map[ns_title] = None

        # setup support for ns_prop1 id map if it exists
        if "ns_prop1" in ex.data.variables.keys():
            for i in ex.data.variables['ns_prop1']:
                self.node_set_ids.append(int(i))
                self.node_set_id_set.add(int(i))
        # if not, create id map for consistency
        else:
            for i in range(len(self.node_sets)):
                self.node_set_ids.append(i + 1)
                self.node_set_id_set.add(i + 1)

        # setup user-specified node set names
        if "ns_names" in ex.data.variables.keys():
            i = 0
            for name in ex.data.variables['ns_names']:
                n = util.lineparse(name)
                self.node_set_names.append(n)
                self.node_set_name_set.add(n)
                self.node_set_name_lookup[n] = self.node_set_ids[i]
                i += 1
        else:
            for i in self.node_set_ids:
                self.node_set_names.append("NodeSet %d" % i)
                self.node_set_name_set.add("NodeSet %d" % i)
                self.node_set_name_lookup["NodeSet %d" % i] = int(i)

    def add_nodeset(self, node_ids, node_set_id, node_set_name=""):

        if node_set_id in self.node_set_id_set:
            raise KeyError("Nodeset ID already in use")
        if node_set_name in self.node_set_name_set or "NodeSet %d" % node_set_id in self.node_set_name_set:
            raise KeyError("Nodeset name already in use")

        self.node_sets.append(str(self.new_node_set_name))
        self.node_set_map[str(self.new_node_set_name)] = np.unique(node_ids)
        self.node_set_ids.append(node_set_id)
        self.node_set_id_set.add(node_set_id)

        if node_set_name == "":
            self.node_set_names.append("NodeSet %d" % node_set_id)
            self.node_set_name_set.add("NodeSet %d" % node_set_id)
            self.node_set_name_lookup["NodeSet %d" % node_set_id] = int(node_set_id)
        else:
            self.node_set_names.append(node_set_name)
            self.node_set_name_set.add(node_set_name)
            self.node_set_name_lookup[node_set_name] = int(node_set_id)

        self.new_node_set_name += 1

    def remove_nodeset(self, identifier):
        if isinstance(identifier, str):
            return self._str_remove_nodeset(identifier)
        elif isinstance(identifier, int):
            return self._id_remove_nodeset(identifier)
        else:
            raise TypeError("Identifier must be of type str or int")

    def _str_remove_nodeset(self, name):
        node_set_id = self.node_set_name_lookup[name]
        return self._id_remove_nodeset(node_set_id)

    def _id_remove_nodeset(self, node_set_id):
        node_set_num = self.find_nodeset_num(node_set_id)

        # remove all references to removed node set
        # O(1) with respect to the actual node sets
        # O(n) with respect to number of changes in ledger
        node_set_name = self.node_sets.pop(node_set_num)
        removed_id = self.node_set_ids.pop(node_set_num)
        self.node_set_id_set.remove(int(removed_id))
        self.node_set_map.pop(node_set_name)

        name = self.node_set_names.pop(node_set_num)
        self.node_set_name_set.remove(name)
        self.node_set_name_lookup.pop(name)

    def merge_nodesets(self, new_id, node_set_id1, node_set_id2, delete=True):
        if new_id in self.node_set_id_set:
            raise KeyError("NodeSet ID already in use")

        n1 = self.get_node_set(node_set_id1)
        n2 = self.get_node_set(node_set_id2)
        n3 = []
        for i in n1:
            n3.append(i)
        for i in n2:
            if i not in n3:
                n3.append(i)

        self.add_nodeset(n3, new_id)
        if delete:
            self.remove_nodeset(node_set_id1)
            self.remove_nodeset(node_set_id2)

    def add_node_to_nodeset(self, node_id, identifier):
        if isinstance(identifier, str):
            return self._str_add_node_to_nodeset(node_id, identifier)
        elif isinstance(identifier, int):
            return self._id_add_node_to_nodeset(node_id, identifier)
        else:
            raise TypeError("Identifier must be of type str or int")

    def _str_add_node_to_nodeset(self, node_id, name):
        node_set_id = self.node_set_name_lookup[name]
        return self._id_add_node_to_nodeset(node_id, node_set_id)

    def _id_add_node_to_nodeset(self, node_id, node_set_id):
        self.add_nodes_to_nodeset(np.array(node_id), node_set_id)

    def remove_node_from_nodeset(self, node_id, node_set_id):
        self.remove_nodes_from_nodeset(np.array(node_id), node_set_id)

    def add_nodes_to_nodeset(self, node_ids, identifier):
        if isinstance(identifier, str):
            return self._str_add_nodes_to_nodeset(node_ids, identifier)
        elif isinstance(identifier, int):
            return self._id_add_nodes_to_nodeset(node_ids, identifier)
        else:
            raise TypeError("Identifier must be of type str or int")

    def _str_add_nodes_to_nodeset(self, node_ids, name):
        node_set_id = self.node_set_name_lookup[name]
        return self._id_add_nodes_to_nodeset(node_ids, node_set_id)

    # node_ids must be array-like per numpy
    def _id_add_nodes_to_nodeset(self, node_ids, node_set_id):
        node_set_num = self.find_nodeset_num(node_set_id)

        # determine whether nodeset exists in memory or still only exists in the exodus object
        # needs to be pulled into memory regardless
        program_name = self.node_sets[node_set_num]
        curr_node_set = self.node_set_map[program_name]
        if curr_node_set is None:
            curr_node_set = self.ex.data[program_name][:]
            program_name = str(self.new_node_set_name)
            self.node_set_map[program_name] = curr_node_set
            self.new_node_set_name += 1

        new_node_set = np.unique(np.append(curr_node_set, node_ids))
        self.node_set_map[program_name] = new_node_set

    def remove_nodes_from_nodeset(self, node_ids, identifier):
        if isinstance(identifier, str):
            return self._str_remove_nodes_from_nodeset(node_ids, identifier)
        elif isinstance(identifier, int):
            return self._id_remove_nodes_from_nodeset(node_ids, identifier)
        else:
            raise TypeError("Identifier must be of type str or int")

    def _str_remove_nodes_from_nodeset(self, node_ids, name):
        node_set_id = self.node_set_name_lookup[name]
        return self._id_remove_nodes_from_nodeset(node_ids, node_set_id)

    def _id_remove_nodes_from_nodeset(self, node_ids, node_set_id):
        node_set_num = self.find_nodeset_num(node_set_id)

        # determine whether node set exists in memory or still only exists in the exodus object
        # needs to be pulled into memory regardless
        program_name = self.node_sets[node_set_num]
        curr_node_set = self.node_set_map[program_name]
        if curr_node_set is None:
            curr_node_set = self.ex.data[program_name][:]
            program_name = str(self.new_node_set_name)
            self.node_set_map[program_name] = curr_node_set
            self.new_node_set_name += 1

        new_node_set = np.setdiff1d(curr_node_set, node_ids)
        if len(curr_node_set) - len(new_node_set) != len(node_ids):
            raise IndexError("One or more nodes could not be found in NodeSet " + str(node_set_id))
        self.node_set_map[program_name] = new_node_set

    def write_dimensions(self, data):
        # if no node sets exist, no writing needs to be performed
        if len(self.node_sets) == 0:
            return

        # create num_node_sets dimension
        data.createDimension("num_node_sets", len(self.node_sets))

        for i in range(len(self.node_sets)):
            # if node set exists in old file, copy directly
            node_set_name = self.node_sets[i]
            if self.node_set_map[node_set_name] is None:
                dimension = self.ex.data.variables[node_set_name].dimensions[0]
                data.createDimension("num_nod_ns" + str(i + 1),
                                     self.ex.data.dimensions[dimension].size)

            # else, create according to np array
            else:
                data.createDimension("num_nod_ns" + str(i + 1),
                                     len(self.node_set_map[node_set_name]))

    def write_variables(self, data):

        # if no node sets exist, no writing needs to be performed
        if len(self.node_sets) == 0:
            return

        # add ns_prop1 data
        data.createVariable("ns_prop1", "int32", dimensions="num_node_sets")
        data['ns_prop1'].setncattr('name', 'ID')
        data['ns_prop1'][:] = np.array(self.node_set_ids)

        # add ns_name data
        data.createVariable("ns_names", "|S1", dimensions=("num_node_sets", "len_name"))
        for i in range(len(self.node_set_names)):
            data['ns_names'][i] = util.convert_string(self.node_set_names[i], self.ex.max_allowed_name_length)

        # add node set data
        for i in range(len(self.node_sets)):
            node_set_name = self.node_sets[i]
            # if node set exists in old file, copy directly
            if self.node_set_map[node_set_name] is None:

                data.createVariable("node_ns" + str(i+1), "int32",
                                    dimensions=("num_nod_ns" + str(i+1)))

                # copy data
                data["node_ns" + str(i+1)][:] = self.ex.data[node_set_name][:]

                if "dist_fact_ns" + node_set_name[-1:] in self.ex.data.variables.keys():
                    data.createVariable("dist_fact_ns" + str(i+1), "float64", dimensions=("num_nod_ns" + str(i+1)))
                    data["dist_fact_ns" + str(i+1)][:] = self.ex.data["dist_fact_ns" + node_set_name[-1:]][:]
                else:
                    data.createVariable("dist_fact_ns" + str(i + 1), "float64", dimensions=("num_nod_ns" + str(i + 1)))
                    ns_size = data.dimensions['num_nod_ns' + str(i+1)].size
                    data["dist_fact_ns" + str(i+1)][:] = np.ones(ns_size, dtype=np.float64)[:]

            # else, create according to np array
            else:
                data.createVariable("node_ns" + str(i+1), "int32",
                                    dimensions=("num_nod_ns" + str(i+1)))
                data["node_ns"+str(i+1)][:] = self.node_set_map[node_set_name][:]
                data.createVariable("dist_fact_ns" + str(i + 1), "float64", dimensions=("num_nod_ns" + str(i + 1)))
                ns_size = data.dimensions['num_nod_ns' + str(i + 1)].size
                data["dist_fact_ns" + str(i + 1)][:] = np.ones(ns_size, dtype=np.float64)[:]

        # TODO: add ns_status

    def find_nodeset_num(self, node_set_id):
        node_set_num = -1
        # search for node set that corresponds with given ID
        for i in range(len(self.node_set_ids)):
            if self.node_set_ids[i] == node_set_id:
                node_set_num = i
                break

        # raise IndexError if no node set is found
        if node_set_num == -1:
            raise KeyError("Cannot find node set with ID " + str(node_set_id))

        return node_set_num

    #############################################
    #                                           #
    #          Read Shadow Methods              #
    #                                           #
    #############################################

    def num_node_sets(self):
        return len(self.node_sets)

    def get_node_set(self, identifier):
        if isinstance(identifier, str):
            return self._str_get_node_set(identifier)
        elif isinstance(identifier, int):
            return self._id_get_node_set(identifier)
        else:
            raise TypeError("Identifier must be of type str or int")

    def _str_get_node_set(self, name):
        node_set_id = self.node_set_name_lookup[name]
        return self._id_get_node_set(node_set_id)

    def _id_get_node_set(self, node_set_id):
        num = self.find_nodeset_num(node_set_id)
        name = self.node_sets[num]
        if name not in self.node_set_map.keys():
            raise KeyError(f"Node Set {node_set_id} does not exist")

        if self.node_set_map[name] is None:
            return np.array(self.ex.data[name])
        return np.array(self.node_set_map[name])

    def get_partial_node_set(self, identifier, start, count):
        if isinstance(identifier, str):
            return self._str_get_partial_node_set(identifier, start, count)
        elif isinstance(identifier, int):
            return self._id_get_partial_node_set(identifier, start, count)
        else:
            raise TypeError("Identifier must be of type str or int")

    def _str_get_partial_node_set(self, node_set_name, start, count):
        node_set_id = self.node_set_name_lookup[node_set_name]
        print(node_set_id)
        return self._id_get_partial_node_set(node_set_id, start, count)

    def _id_get_partial_node_set(self, node_set_id, start, count):
        num = self.find_nodeset_num(node_set_id)
        name = self.node_sets[num]
        if name not in self.node_set_map.keys():
            raise KeyError(f"Node Set {node_set_id} does not exist")

        if self.node_set_map[name] is None:
            return np.unique(self.ex.data[name])[start - 1:start + count - 1]
        return np.unique(self.node_set_map[name])[start - 1:start + count - 1]

    def get_node_set_id_map(self):
        """ Returns the id map for node sets (ns_prop1). """
        return np.array(self.node_set_ids)

    def get_node_set_name(self, node_set_id):
        num = self.find_nodeset_num(node_set_id)
        return self.node_set_names[num]

    def get_node_set_names(self):
        return np.array(self.node_set_names)
