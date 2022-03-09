import numpy as np
import util

class SSLedger:

    def __init__(self, ex):
        self.ex = ex

        # Create lists for sideset data
        self.num_ss = 0
        if ("num_side_sets" in ex.data.dimensions.keys()):
            self.num_ss = ex.data.dimensions["num_side_sets"].size
        self.ss_prop1 = [] # this is id for sideset
        self.ss_status = []
        self.ss_sizes = []
        self.ss_names = []
        self.num_dist_fact = []
        self.ss_dist_fact = []
        self.ss_elem = []
        self.ss_sides = []


        # Fill in lists with sideset data
        for i in range(self.num_ss):
            self.ss_prop1.append(ex.data["ss_prop1"][i]) 
            self.ss_status.append(ex.data["ss_status"][i])
            self.ss_sizes.append(ex.data.dimensions["num_side_ss" + str(i + 1)].size)
            if ("ss_names" in ex.data.variables):
                self.ss_names.append(util.lineparse(ex.data["ss_names"][i]))
            else:
                self.ss_names.append("ss" + str(i))
            self.num_dist_fact.append(ex.data.dimensions["num_df_ss" + str(i + 1)].size)
            self.ss_dist_fact.append(None)
            self.ss_elem.append(None) # this is place holder to be filled with real values later
            self.ss_sides.append(None) # this is place holder to be filled with real values later


    def add_sideset(self, elem_ids, side_ids, ss_id, ss_name, dist_fact):

        if (ss_id in self.ss_prop1):
            # already sideset with the same id
            raise Exception("Sideset with the same id already exists")
        
        if len(elem_ids) != len(side_ids):
            # do not have same number of elements and sides, throw error
            raise Exception("Number of element and number of sides do not match")

        if len(ss_name) > self.ex._MAX_NAME_LENGTH:
            raise Exception("Passed in name is too long")
        
        converted_elem_ids = elem_ids
        # converted_elem_ids = self.ex.lookup_id(elem_ids)

        # add sidesets to list
        self.ss_elem.append(converted_elem_ids)
        self.ss_sides.append(side_ids)
        self.ss_prop1.append(ss_id)
        self.ss_sizes.append(len(elem_ids))
        self.ss_status.append(1)
        self.ss_names.append(ss_name)
        self.num_dist_fact.append(len(dist_fact))
        self.ss_dist_fact.append(dist_fact)
        self.num_ss += 1 

    def remove_sideset(self, ss_id):
        # find sideset id
        ndx = -1
        for i in range(self.num_ss):
            if ss_id == self.ss_prop1[i]:
                # found id
                ndx = i
                break

        if ndx == -1:
            raise Exception("Sideset with given id does not exist")
        
        # remove sideset from lists
        self.ss_prop1.pop(ndx)
        self.ss_status.pop(ndx)
        self.ss_names.pop(ndx)
        self.ss_elem.pop(ndx)
        self.ss_sizes.pop(ndx)
        self.ss_sides.pop(ndx)
        self.num_dist_fact.pop(ndx)
        self.ss_dist_fact.pop(ndx)
        self.num_ss -= 1

    def add_side_to_ss(self, elem_id, side_id, ss_id):
        pass
    
    def remove_side_from_ss(self, elem_id, side_id, ss_id):
        pass

    def write(self, data):

        if (self.num_ss == 0):
            # nothing to write so done
            return

        # write each dimension
        data.createDimension("num_side_sets", self.num_ss)
        for i in range(self.num_ss):
            data.createDimension("num_df_ss" + str(i + 1), self.num_dist_fact[i])
            data.createDimension("num_side_ss" + str(i+1), self.ss_sizes[i])

        # write each variable
        # copy over statuses
        data.createVariable("ss_status", "int32", dimensions=("num_side_sets"))
        data["ss_status"][:] = np.array(self.ss_status)
        # copy over ids
        data.createVariable("ss_prop1", "int32", dimensions=("num_side_sets"))
        data['ss_prop1'].setncattr('name', 'ID')
        data['ss_prop1'][:] = np.array(self.ss_prop1)

        # copy over names
        data.createVariable("ss_names", "|S1", dimensions=("num_side_sets", "len_name"))
        for i in range(len(self.ss_names)):
            data['ss_names'][i] = util.convert_string(self.ss_names[i] + str('\0'), self.ex.max_allowed_name_length)

        for i in range(self.num_ss):
            # create elem, sides, and dist facts
            data.createVariable("elem_ss" + str(i+1), "int32", dimensions=("num_side_ss" + str(i+1)))
            data.createVariable("dist_fact_ss" + str(i+1), "int32", dimensions=("num_df_ss" + str(i+1)))
            data.createVariable("side_ss" + str(i+1), "float64", dimensions=("num_side_ss" + str(i+1)))
            
            # if None, just copy over old data, otherwise copy over new stuff
            if (self.ss_elem[i] is None):
                 data["elem_ss" + str(i+1)][:] = self.ex.get_side_set(self.ss_prop1[i])[0][:]
            else:
                data["elem_ss" + str(i+1)][:] = self.ss_elem[i][:]

            if (self.ss_sides[i] is None):
                data["side_ss" + str(i+1)][:] = self.ex.get_side_set(self.ss_prop1[i])[1][:]
            else:
                data["side_ss" + str(i+1)][:] = self.ss_sides[i][:]
            
            if (self.ss_dist_fact[i] is None):
                data["dist_fact_ss" + str(i+1)][:] = self.ex.get_side_set_df(self.ss_prop1[i])[:]
            else:
                data["dist_fact_ss" + str(i+1)][:] = self.ss_dist_fact[i][:]

