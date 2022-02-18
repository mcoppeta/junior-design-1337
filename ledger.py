from ns_ledger import NSLedger
import netCDF4 as nc


class Ledger:

    def __init__(self, ex):
        self.nodeset_ledger = NSLedger(ex)
        self.ex = ex

    def add_nodeset(self, node_ids, nodeset_id):
        self.nodeset_ledger.add_nodeset(node_ids, nodeset_id)

    def remove_nodeset(self, nodeset_id):
        self.nodeset_ledger.remove_nodeset(nodeset_id)

    def merge_nodesets(self, new_id, ns1, ns2, delete):
        self.nodeset_ledger.merge_nodesets(new_id, ns1, ns2, delete)

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

            out.createDimension(dimension, old.dimensions[dimension].size)

        # copy variables
        for var in old.variables:

            # ignore variables that will be written by ns ledger
            if var[:3] == "ns_" or var[:7] == "node_ns" \
                    or var[:12] == "dist_fact_ns":
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
        out.close()
