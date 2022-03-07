from ns_ledger import NSLedger
from ss_ledger import SSLedger
import netCDF4 as nc


class Ledger:

    def __init__(self, ex):
        self.nodeset_ledger = NSLedger(ex)
        self.sideset_ledger = SSLedger(ex)
        self.ex = ex


    def num_node_sets(self):
        """ Returns the number of nodesets present in the file"""
        return self.nodeset_ledger.num_node_sets()

    def get_node_set(self, id):
        """

        :param id: the id of the requested node set
        :return: ndarray of all of the node ids that belong to the specified node set
        """
        return self.nodeset_ledger.get_node_set(id)

    def get_node_set_name(self, id):
        """

        :param id: the id of the requested node set
        :return: the name of the specified node set
        """
        return self.nodeset_ledger.get_node_set_name(id)

    def get_node_set_names(self):
        """
        Returns array of nodeset names
        :return: array of nodeset names
        """
        return self.nodeset_ledger.get_node_set_names()

    def add_nodeset(self, node_ids, nodeset_id, nodeset_name=""):
        """

        :param node_ids: the node ids which will be contained within the new nodeset
        :param nodeset_id: the intended id for the new nodeset
        :param nodeset_name: the intended name for the new nodeset
        :return: None
        """
        self.nodeset_ledger.add_nodeset(node_ids, nodeset_id, nodeset_name)

    def remove_nodeset(self, nodeset_id):
        """
        Removes given nodeset from the Exodus file
        :param nodeset_id: the id of the nodeset being removed
        :return: None
        """
        self.nodeset_ledger.remove_nodeset(nodeset_id)

    def merge_nodesets(self, new_id, ns1, ns2, delete=True):
        """
        Merges 2 nodesets together
        :param new_id: the intended ID for the new nodeset
        :param ns1: the first nodeset to merge
        :param ns2: the second nodeset to merge
        :param delete: a flag which specifies whether the 2 starting nodesets will be removed
        :return: None
        """
        self.nodeset_ledger.merge_nodesets(new_id, ns1, ns2, delete)

    def add_node_to_nodeset(self, node_id, nodeset_id):
        """
        Add one node to the specified nodeset
        :param node_id: the node being added to the nodeset
        :param nodeset_id: the nodeset the node will be added to
        :return: None
        """
        self.nodeset_ledger.add_node_to_nodeset(node_id, nodeset_id)

    def add_nodes_to_nodeset(self, node_ids, nodeset_id):
        """
        Add many nodes to the specified nodeset
        :param node_ids: the nodes being added to the nodeset (List-like)
        :param nodeset_id: the nodeset being added to
        :return: None
        """
        self.nodeset_ledger.add_nodes_to_nodeset(node_ids, nodeset_id)

    def remove_node_from_nodeset(self, node_id, nodeset_id):
        """
        Remove single node from a specified nodeset
        :param node_id: the node being removed from the nodeset
        :param nodeset_id: the nodeset being removed from
        :return: None
        """
        self.nodeset_ledger.remove_node_from_nodeset(node_id, nodeset_id)

    def remove_nodes_from_nodeset(self, node_ids, nodeset_id):
        """
        Remove many nodes from a specified nodeset
        :param node_ids: the nodes being removed from the nodeset (List-like)
        :param nodeset_id: the nodeset being removed from
        :return: None
        """
        self.nodeset_ledger.remove_nodes_from_nodeset(node_ids, nodeset_id)

    # sideset methods
    def add_sideset(self, elem_ids, side_ids, ss_id, ss_name, dist_fact):
        self.sideset_ledger.add_sideset(elem_ids, side_ids, ss_id, ss_name, dist_fact)

    def remove_sideset(self, ss_id):
        self.sideset_ledger.remove_sideset(ss_id)


    def write(self):
        """
        Write from the ledger
        :return: None
        """
        if self.ex.mode == 'w':
            self.w_write()
        elif self.ex.mode == 'a':
            path = self.ex.path.split('.')[:-1]
            self.a_write(path[0] + '_rev.ex2')

    def w_write(self):
        self.nodeset_ledger.write(self.ex.data)

    def a_write(self, path):
        out = nc.Dataset(path, "w", True, format="NETCDF3_CLASSIC")
        old = self.ex.data

        out.setncatts(old.__dict__)

        # copy dimensions
        for dimension in old.dimensions.keys():

            # ignore dimensions that will be written by ns ledger
            if dimension == "num_node_sets" or dimension[:10] == "num_nod_ns":
                continue
            # ignore dimensions that will be written by ss ledger
            if dimension == "num_side_sets" or dimension[:11] == "num_side_ss" or dimension[:9] == "num_df_ss":
                continue

            out.createDimension(dimension, old.dimensions[dimension].size)

        # copy variables
        for var in old.variables:

            # ignore variables that will be written by ns ledger
            if var[:3] == "ns_" or var[:7] == "node_ns" \
                    or var[:12] == "dist_fact_ns":
                continue

            # ingore variables that will be written by ss ledger
            if var[:3] == "ss_" or var[:7] == "side_ss" or var[:7] == "elem_ss" or var[:12] == "dist_fact_ss":
                continue

            var_data = old[var]

            # variable creation data
            varname = var_data.name
            datatype = var_data.dtype
            dimensions = var_data.dimensions
            out.createVariable(varname, datatype, dimensions)
            out[varname][:] = old[var][:]
            out[varname].setncatts(old[varname].__dict__)

        self.nodeset_ledger.write(out)
        self.sideset_ledger.write(out)
        out.close()
