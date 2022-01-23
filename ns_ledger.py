import numpy as np
import netCDF4 as nc
from exodus import Exodus


class NSLedger:

    def __init__(self, ex):
        self.nodeset_map = {}
        self.nodesets = []
        self.nodeset_ids = []
        self.new_nodeset_id = 0

        for i in range(ex.data.dimensions['num_node_sets'].size):
            ns_title = "num_nod_ns" + str(i+1)
            self.nodesets.append(ns_title)
            self.nodeset_map[ns_title] = None

        if "ns_prop1" in ex.data.variables.keys():
            for i in ex.variables['ns_prop1']:
                self.nodeset_ids.append(i)
        else:
            for i in range(len(self.nodesets)):
                self.nodeset_ids.append(i+1)

    def add_nodeset(self, node_ids):

        self.nodesets.append(self.new_nodeset_id)
        self.nodeset_map[self.new_nodeset_id] = np.array(node_ids)
        self.new_nodeset_id += 1

    def remove_nodeset(self, nodeset_num):

        nodeset_id = self.nodesets.pop(nodeset_num + 1)
        self.nodeset_map.pop(nodeset_id)

    def write(self, data):
        data.createDimension("num_node_sets", len(self.nodesets))


if __name__ == "__main__":
    ex = Exodus("sample-files/can.ex2", 'r', False)
    ledger = NSLedger(ex)
    ledger.write()