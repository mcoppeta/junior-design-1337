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
        self.ss_status = [] # status for each sideset
        self.ss_sizes = [] # number of sides in each sideset
        self.ss_names = [] # name of each sideset
        self.num_dist_fact = [] # number of distribution factors in each sideset
        self.ss_dist_fact = [] # distribution factors in each sideset
        self.ss_elem = [] # internal elem ids of each sideset, each index in this is an array of elem ids
        self.ss_sides = [] # side ids of each sideset, each index in this is an array of side ids


        # Fill in lists with sideset data
        for i in range(self.num_ss):
            self.ss_prop1.append(ex.data["ss_prop1"][i]) 
            self.ss_status.append(ex.data["ss_status"][i])
            self.ss_sizes.append(ex.data.dimensions["num_side_ss" + str(i + 1)].size)
            if ("ss_names" in ex.data.variables):
                self.ss_names.append(util.lineparse(ex.data["ss_names"][i]))
            else:
                self.ss_names.append("")
            # if df do not exist, add size 0 arrays for them
            self.num_dist_fact.append(ex.get_side_set_params(self.ss_prop1[i])[1])
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
        
        # need to convert elem_ids to internal ids
        map = self.ex.get_elem_id_map()
        converted_elem_ids = []
        for id in elem_ids:
            internal_id = np.where(map == id)[0][0] + 1
            converted_elem_ids.append(internal_id)

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

    #TODO Replaced start of this with find_sideset_num, we should check that this still works
    def remove_sideset(self, ss_id):
        ndx = self.find_sideset_num(ss_id)
        
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

    def add_sides_to_sideset(self, elem_ids, side_ids, dist_facts, ss_id):
        ndx = self.find_sideset_num(ss_id)

        # if not loaded in yet, need to load in 
        if (self.ss_elem[ndx] is None):
            ss = self.ex.get_side_set(ss_id)
            elems = ss[0]
            sides = ss[1]
            self.ss_elem[ndx] = np.array(elems)
            self.ss_sides[ndx] = np.array(sides)
            self.ss_dist_fact[ndx] = np.array(self.ex.get_side_set_df(ss_id))

        # need to convert elem_ids to internal ids
        map = self.ex.get_elem_id_map()
        converted_elem_ids = []
        for id in elem_ids:
            internal_id = np.where(map == id)[0][0] + 1
            converted_elem_ids.append(internal_id)
        
        self.ss_elem[ndx] = np.append(self.ss_elem[ndx], converted_elem_ids)
        self.ss_sides[ndx] = np.append(self.ss_sides[ndx], side_ids)
        self.ss_dist_fact[ndx] = np.append(self.ss_dist_fact[ndx], dist_facts)
        self.ss_sizes[ndx] += len(elem_ids)
        self.num_dist_fact[ndx] += len(dist_facts)
    
    def remove_sides_from_sideset(self, elem_ids, side_ids, ss_id):
        ndx = self.find_sideset_num(ss_id)

        # if not loaded in yet, need to load in 
        if (self.ss_elem[ndx] is None):
            ss = self.ex.get_side_set(ss_id)
            elems = ss[0]
            sides = ss[1]
            self.ss_elem[ndx] = np.array(elems)
            self.ss_sides[ndx] = np.array(sides)
            self.ss_dist_fact[ndx] = np.array(self.ex.get_side_set_df(ss_id))

        num_df_per_side = int(self.num_dist_fact[ndx] / self.ss_sizes[ndx]) # find number of df per side, if 0 there are no df

        # convert elem_ids
        # need to convert elem_ids to internal ids
        map = self.ex.get_elem_id_map()
        converted_elem_ids = []
        for id in elem_ids:
            internal_id = np.where(map == id)[0][0] + 1
            converted_elem_ids.append(internal_id)

        # create set of tuples of side and elem ids for quick lookup
        tuple_set = set()
        for i in range(len(converted_elem_ids)):
            tuple_set.add((converted_elem_ids[i], side_ids[i]))
        
        # iterate through each side in sideset
        # if it matches one of the passed in sides, mark for removal
        elem_side_remove_ndx = []
        df_remove_ndx = []
        print(num_df_per_side)
        for i in range(self.ss_sizes[ndx]):
            side_tuple = (self.ss_elem[ndx][i], self.ss_sides[ndx][i])
            if (side_tuple in tuple_set):
                elem_side_remove_ndx.append(i)
                adjusted_i = i * num_df_per_side # adjust i to account for multiple df
                if (num_df_per_side != 0):
                    df_remove_ndx.extend(range(adjusted_i,  adjusted_i + num_df_per_side))
        
        print(elem_side_remove_ndx)
        print(df_remove_ndx)


        # remove all marked indices from arrays
        self.ss_elem[ndx] = np.delete(self.ss_elem[ndx], elem_side_remove_ndx)
        self.ss_sides[ndx] = np.delete(self.ss_sides[ndx], elem_side_remove_ndx)
        self.ss_sizes[ndx] -= len(elem_side_remove_ndx)

        self.ss_dist_fact[ndx] = np.delete(self.ss_dist_fact[ndx], df_remove_ndx)
        self.num_dist_fact[ndx] -= len(df_remove_ndx)
    
    # Create 2 new sidesets from old sideset based on user-specified function
    # User function should return boolean and take in tuple of (element, side)
    #TODO: Was getting an error (shown below) during write() at runtime when creating second sideset
    # ss_ledger.py in write: "data.createDimension("num_side_ss" + str(i+1), self.ss_sizes[i])"
    # (Some calls to netCDF4)
    # "RuntimeError: NetCDF: NC_UNLIMITED size already in use"
    def split_sideset(self, old_ss, function, ss_id1, ss_id2, delete, ss_name1, ss_name2):
        # Get sideset that will be split
        ndx = self.find_sideset_num(old_ss)

        # if not loaded in yet, need to load in 
        if (self.ss_elem[ndx] is None):
            ss = self.ex.get_side_set(old_ss)
            elems = ss[0]
            sides = ss[1]
            self.ss_elem[ndx] = np.array(elems)
            self.ss_sides[ndx] = np.array(sides)
            self.ss_dist_fact[ndx] = np.array(self.ex.get_side_set_df(old_ss))

        #Original approach below, switched to a different approach based on iteration in
        #remove_sides_from_sideset, approach 1 could be a different way to do this function
        #where sides are added individually to new sidesets during iteration but approach 1
        #is not currently working as written

        #START OF APPROACH 1
        # Create new sideset that will contain sides meeting user-specified criteria
        # self.add_sideset([], [], ss_id1, ss_name1, [])

        # Create new sideset that will contain sides NOT meeting user-specified criteria
        # self.add_sideset([], [], ss_id2, ss_name2, [])

        #Iterate through sides in sideset and check if they match user-specified criteria
        # for i in self.ss_sides[ndx]:
        #   if function(i): #Side returns true, add to sideset 1 
        #       self.add_sides_to_sideset([self.ss_elem[ndx][i]], [self.ss_sides[ndx][i]], [self.ss_dist_fact[ndx][i]], ss_id1)
        #   else: #Side returns false, add to sideset 2
        #       self.add_sides_to_sideset([self.ss_elem[ndx][i]], [self.ss_sides[ndx][i]], [self.ss_dist_fact[ndx][i]], ss_id2)
        #END OF APPROACH 1

        #START OF APPROACH 2 (based on iteration for remove sides)
        num_df_per_side = int(self.num_dist_fact[ndx] / self.ss_sizes[ndx]) # find number of df per side, if 0 there are no df

        meet_criteria_elem = []
        meet_criteria_side = []
        meet_criteria_df = []
        not_met_elem = []
        not_met_side = []
        not_met_df = []
        for i in range(self.ss_sizes[ndx]):
            side_tuple = (self.ss_elem[ndx][i], self.ss_sides[ndx][i])
            if function(side_tuple):
                meet_criteria_elem.append(side_tuple[0])
                meet_criteria_side.append(side_tuple[1])
                adjusted_i = i * num_df_per_side # adjust i to account for multiple df
                if (num_df_per_side != 0):
                    meet_criteria_df.extend(range(adjusted_i,  adjusted_i + num_df_per_side))
            else:
                not_met_elem.append(side_tuple[0])
                not_met_side.append(side_tuple[1])
                adjusted_i = i * num_df_per_side # adjust i to account for multiple df
                if (num_df_per_side != 0):
                    not_met_df.extend(range(adjusted_i,  adjusted_i + num_df_per_side))

        self.add_sideset(meet_criteria_elem, meet_criteria_side, ss_id1, ss_name1, meet_criteria_df)
        #TODO Was getting error writing second sideset, not sure how it resolved so may come up again
        self.add_sideset(not_met_elem, not_met_side, ss_id2, ss_name2, not_met_df)
        #END OF APPROACH 2
        
        #Delete old sideset if desired by user
        if delete:
           self.remove_sideset(old_ss)

    # Creates 2 new sidesets from sides in old sideset based on x-coordinate values
    #TODO Redo this function based on generic split_sideset function implementation
    #And what is the best way to get and check all nodes in the sideset?
    def split_sideset_x_coords(self, old_ss, comparison, x_value, all_nodes, ss_id1, ssid_2, delete, ss_name1="", ss_name2=""):
        # Set comparison that will be used
        if comparison == '<':
          compare = lambda coord : coord < x_value
        elif comparison == '>':
          compare = lambda coord : coord > x_value
        elif comparison == '<=':
          compare = lambda coord : coord <= x_value
        elif comparison == '>=':
          compare = lambda coord : coord >= x_value
        elif comparison == '=':
          compare = lambda coord : coord == x_value
        elif comparison == '!=':
          compare = lambda coord : coord != x_value
        else:
          raise Exception("Comparison not valid. Valid comparison inputs: '<', '>', '<=', '>=', '=', '!='")

        # Get sideset that will be split
        ss_num = self.find_sideset_num(old_ss)
        
        # Create new sideset that will contain sides meeting user-specified criteria
        # dist_fact? create sideset before or after elems/sides found?
        #self.add_sideset([], [], ss_id1, ss_name1, [])

        # Create new sideset that will contain sides NOT meeting user-specified criteria
        # dist_fact? create sideset before or after elems/sides found?
        #self.add_sideset([], [], ss_id2, ss_name2, [])

        # Get all sides in old sideset
        # ???

        # Either add sides to new sideset if all nodes in a given side meet x-coord criteria
        #if all_nodes:
        #   For each side in old sideset
        #       flag = True
        #       For each node in side
        #           if not compare(current node x-coord):
        #               flag = False
        #               break
        #       if flag:
        #           self.add_side_to_ss(elem id of curr side, curr side id, ss_id1)
        #       else:
        #           self.add_side_to_ss(elem id of curr side, curr side id, ss_id2)

        # Or add sides to new sideset if at least one node in a given side meets x-coord criteria
        #else:
        #   For each side in old sideset
        #       flag = False
        #       For each node in side
        #           if compare(current node x-coord):
        #               flag = True
        #               break
        #       if flag:
        #           self.add_side_to_ss(elem id of curr side, curr side id, ss_id1)
        #       else:
        #           self.add_side_to_ss(elem id of curr side, curr side id, ss_id2)

        #Delete old sideset if desired by user
        # if delete:
        #    self.remove_sideset(old_ss)

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

    # (Based on find_nodeset_num in ns_ledger)
    def find_sideset_num(self, ss_id):
        ndx = -1
        # search for sideset that corresponds with given ID
        for i in range(self.num_ss):
            if ss_id == self.ss_prop1[i]:
                # found id
                ndx = i
                break

        # raise IndexError if no nodeset is found
        if ndx == -1:
            raise IndexError("Cannot find sideset with ID " + str(ss_id))

        return ndx
        