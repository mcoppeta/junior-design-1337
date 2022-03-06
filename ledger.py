from ns_ledger import NSLedger
from ss_ledger import SSLedger
import netCDF4 as nc


class Ledger:

    def __init__(self, ex):
        self.nodeset_ledger = NSLedger(ex)
        self.sideset_ledger = SSLedger(ex)
        self.ex = ex


    def num_node_sets(self):
        return self.nodeset_ledger.num_node_sets()

    def get_node_set(self, id):
        return self.nodeset_ledger.get_node_set(id)

    def get_node_set_name(self, id):
        return self.nodeset_ledger.get_node_set_name(id)

    def get_node_set_names(self):
        return self.nodeset_ledger.get_node_set_names()

    def add_nodeset(self, node_ids, nodeset_id, nodeset_name=""):
        self.nodeset_ledger.add_nodeset(node_ids, nodeset_id, nodeset_name)

    def remove_nodeset(self, nodeset_id):
        self.nodeset_ledger.remove_nodeset(nodeset_id)

    def merge_nodesets(self, new_id, ns1, ns2, delete):
        self.nodeset_ledger.merge_nodesets(new_id, ns1, ns2, delete)

    def add_node_to_nodeset(self, node_id, nodeset_id):
        self.nodeset_ledger.add_node_to_nodeset(node_id, nodeset_id)

    def add_nodes_to_nodeset(self, node_ids, nodeset_id):
        self.nodeset_ledger.add_nodes_to_nodeset(node_ids, nodeset_id)

    def remove_node_from_nodeset(self, node_id, nodeset_id):
        self.nodeset_ledger.remove_node_from_nodeset(node_id, nodeset_id)

    def remove_nodes_from_nodeset(self, node_ids, nodeset_id):
        self.nodeset_ledger.remove_nodes_from_nodeset(node_ids, nodeset_id)

    # sideset methods
    def add_sideset(self, elem_ids, side_ids, ss_id, ss_name, dist_fact):
        self.sideset_ledger.add_sideset(elem_ids, side_ids, ss_id, ss_name, dist_fact)

    def remove_sideset(self, ss_id):
        self.sideset_ledger.remove_sideset(ss_id)

    def add_side_to_ss(self, elem_id, side_id, dist_fact, ss_id):
        self.sideset_ledger.add_side_to_ss(elem_id, side_id, dist_fact, ss_id)

    def remove_side_from_ss(self, elem_id, side_id, ss_id):
        self.sideset_ledger.remove_side_from_ss(elem_id, side_id, ss_id)

    def write(self):
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
