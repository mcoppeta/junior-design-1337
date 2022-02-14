from ast import Pass
import numpy as np

class SS_ledger:

    def __init__(self, ex):
        print(ex.data)
        # Sideset metadata
        self.num_ss = ex.data.dimensions["num_side_sets"].size
        self.ss_status = ex.data["ss_status"][:]
        self.ss_prop1 = ex.data["ss_prop1"][:] # this is id for sideset
        self.ss_names = ex.data["ss_names"][:]

        # map ids to sidesets
        self.id_map = {}
        for i in range(self.num_ss):
            # set everything to None, when changed update to new array
            self.id_map[self.ss_prop1[i]] = None



        # pull this in later
        # self.ss_size = []
        # for i in range(1, self.num_ss + 1):
        #     self.ss_size.append(ex.data.dimensions["num_side_ss" + str(i)].size)
        

        # # Sideset data
        # self.elem_ss = []   
        # self.side_ss = []
        # self.dist_fact_ss = []

        # for i in range(1, self.num_ss + 1):
        #     self.elem_ss.append(ex.data["elem_ss" + str(i)][:])    
        #     self.side_ss.append(ex.data["side_ss" + str(i)][:])
        #     self.dist_fact_ss.append(ex.data["dist_fact_ss" + str(i)][:])

    def add_sideset(self):
        Pass

    def remove_sideset(self):
        Pass

    def add_side_to_ss(self):
        Pass
    
    def remove_side_from_ss(self):
        Pass

    def write(self, data):
        Pass





