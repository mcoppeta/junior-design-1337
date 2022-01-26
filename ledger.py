import numpy

from ns_ledger import NSLedger
from exodus import Exodus
import netCDF4 as nc


class Ledger:

    def __init__(self, ex):
        self.nodeset_ledger = NSLedger(ex)
        self.ex = ex

    def add_nodeset(self, node_ids, nodeset_id):
        self.nodeset_ledger.add_nodeset(node_ids, nodeset_id)

    def remove_nodeset(self, nodeset_id):
        self.nodeset_ledger.remove_nodeset(nodeset_id)

    def write(self, path):
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


if __name__ == "__main__":
    ex = Exodus("sample-files/can.ex2", 'r')

    ledger = Ledger(ex)
    new_ns = numpy.array([1,2,3])
    ledger.add_nodeset(new_ns, 10)
    ledger.remove_nodeset(1)
    ledger.write("sample-files/write.ex2")

    ex.close()
