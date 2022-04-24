import numpy as np
import util
import warnings

class SSLedger:
    """
    Initializes the sideset ledger. Loads in any metadata but waits to load in actual data for sideset until later. 
    """
    def __init__(self, ex):
        self.ex = ex

        # Get number of sidesets in exodus file
        # If the dimension does not exist, number of sidesets is 0
        self.num_ss = 0
        if ("num_side_sets" in ex.data.dimensions.keys()):
            self.num_ss = ex.data.dimensions["num_side_sets"].size

        # Get number of sideset variables per sideset in exodus file
        # If dimensions does not exist, the number of sideset variables is 0
        self.num_ss_var = 0
        if ("num_sset_var" in ex.data.dimensions.keys()):
            self.num_ss_var = ex.data.dimensions["num_sset_var"].size

        self.ss_prop1 = [] # this is id for sideset
        self.ss_status = [] # status for each sideset
        self.ss_sizes = [] # number of sides in each sideset
        self.ss_names = [] # name of each sideset
        self.num_dist_fact = [] # number of distribution factors in each sideset
        self.ss_dist_fact = [] # distribution factors in each sideset
        self.ss_elem = [] # internal elem ids of each sideset, each index in this is an array of elem ids
        self.ss_sides = [] # side ids of each sideset, each index in this is an array of side ids
        self.ss_var_names = [] # names for each of the sideset variables
        self.ss_vars = [] # variables for each sideset, each sideset can have multiple variables (will be 4d array)
        self.ss_var_tab = None # this is 2d array that holds the "status" of all sideset variables and is num_ss by num_ss_var
        self.orig_internal_ids = []


        # Fill in lists with sideset data
        for i in range(self.num_ss):
            # load in ids for each sideset
            if ("ss_prop1" in ex.data.variables):
                self.ss_prop1.append(ex.data["ss_prop1"][i])
            else:
                self.ss_prop1.append(i + 1) # if id does not exist, just make one up and add it
            self.orig_internal_ids.append(i + 1)
            
            # load in status for each sideset
            if ("ss_status" in ex.data.variables):
                self.ss_status.append(ex.data["ss_status"][i])
            else: 
                self.ss_status.append(1) # if no status exists just set it to 1
            
            # load in size of each sideset
            if ("num_side_ss" + str(i + 1) in ex.data.dimensions.keys()):
                self.ss_sizes.append(ex.data.dimensions["num_side_ss" + str(i + 1)].size)
            else:
                self.ss_sizes.append(0) # if size variable does not exist, just set it to 0

            # load in names of each sideset
            if ("ss_names" in ex.data.variables): 
                self.ss_names.append(util.lineparse(ex.data["ss_names"][i]))
            else:
                self.ss_names.append("") # if name does not exist, just add empty string
            
            # load number of df for each sideset
            if ("num_df_ss" + str(i + 1) in ex.data.dimensions.keys()):
                self.num_dist_fact.append(self.ex.data.dimensions["num_df_ss" + str(i + 1)].size)
            else:
                self.num_dist_fact.append(0) # if num_df does not exist, just set to 0

            # load in sideset variable names
            if ("name_sset_var" in ex.data.variables):
                self.ss_var_names.append(util.lineparse(ex.data["name_sset_var"][i]))
            else:
                self.ss_var_names.append("") # if variable names do not exist, just append empty string

            # load in sideset variable statuses (tab), if they do not exist, just keep None value that was set at start
            if ("sset_var_tab" in ex.data.variables):
                self.ss_var_tab = ex.data["sset_var_tab"]

            self.ss_vars.append(None) # this is placeholder for actually loading in data later
            self.ss_dist_fact.append(None)  # this is place holder to be filled with real values later
            self.ss_elem.append(None) # this is place holder to be filled with real values later
            self.ss_sides.append(None) # this is place holder to be filled with real values later
    """
    Adds new sideset. Takes in element ids, side ids, id of the new sideset, and name of the new sideset. 
    Can optionally specify distribution factor and variables. If no distribution factors are specified 
    and they are required, placeholder 1s will be inserted. If no variables are specified and they are required, 
    placeholder 0s will be inserted. If specifying distribution factors, they must be of size n * len(elem_ids), where
    n is a positive integer. If specifying variables, they must be of dimensions 
    [number of sideset variables, number of timesteps, number of sides in sideset].
    """
    def add_sideset(self, elem_ids, side_ids, ss_id, ss_name, dist_fact=None, variables=None):

        if (ss_id in self.ss_prop1):
            # already sideset with the same id
            raise Exception("Sideset with the same id already exists")
        
        if len(elem_ids) != len(side_ids):
            # do not have same number of elements and sides, throw error
            raise Exception("Number of elements and number of sides passed in are not equal")

        if len(ss_name) > self.ex._MAX_NAME_LENGTH:
            raise Exception("Passed in name is too long")

        if (dist_fact != None and (len(dist_fact) < len(elem_ids) or (len(dist_fact) % len(elem_ids)) != 0)):
            raise Exception("Number of distribution factors does not match number of sides, \
                number of distribution factors should be a positive integer multiple of number of sides")
        
        if (self.num_ss_var == 0 and variables != None and len(variables) > 0):
            raise Exception("Cannot add variables, this model does not have sideset variables")
        
        if (len(side_ids) == 0 or len(elem_ids) == 0): # there are no ids, so just return
            return
        
        # Need to check variable array size

        # need to convert elem_ids to internal ids
        map = self.ex.get_elem_id_map()
        converted_elem_ids = []
        for id in elem_ids:
            internal_id = np.where(map == id)[0][0] + 1 # conversion, add 1 to the index to get internal id
            converted_elem_ids.append(internal_id)

        # if no variables specified and it requires variables, just use 0
        # this is a 3-d array of num_var by time_step by num_sides
        if (variables is None and self.num_ss_var > 0):
            # make array of all 0s
            # if there are sideset variables, then time_step must exist
            for i in range(self.num_ss_var):
                if i == 0:
                    variables = []
                variables.append(np.zeros([self.ex.data.dimensions["time_step"].size,  len(side_ids)]))

        # if there are sideset variables, append the variables passed in 
        # or the blank array that was just made
        if (self.num_ss_var > 0):
            self.ss_vars.append(variables)
        else:
            self.ss_vars.append(None) # append None to maintain order in array

        # need to update ss_var_tab which is status of each variable
        # append row of num_ss_var 1s to bottom of ss_var_tab array
        if (self.num_ss_var > 0):
            # If there are no sideset variables, no need to update the truth table
            self.ss_var_tab = np.vstack([self.ss_var_tab, np.ones(self.num_ss_var)])

        if (dist_fact is None):
            self.num_dist_fact.append(0)
        else:
            self.num_dist_fact.append(len(dist_fact))
        
        self.ss_dist_fact.append(dist_fact) # append either passed in dist_facts or None to maintain order


        # add sidesets to list
        self.ss_elem.append(converted_elem_ids)
        self.ss_sides.append(side_ids)
        self.ss_prop1.append(ss_id)
        self.ss_sizes.append(len(elem_ids))
        self.ss_status.append(1)
        self.ss_names.append(ss_name)
        self.orig_internal_ids.append(-1)
        
        self.num_ss += 1 
    """
    Removes an existing sideset. Must specify id of sideset for removal.
    """
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
        self.ss_vars.pop(ndx)
        # need to update sideset vars status in ss_var_tab
        # remove row that corresponds to sideset
        self.ss_var_tab = np.delete(self.ss_var_tab, ndx, axis=0)
        self.orig_internal_ids.pop(ndx)
        
        self.num_ss -= 1

    """
    Adds sides to already existing sideset. Must specify the element ids of sides to add, the side ids of sides to add
    the id of the sideset being added to, and optionally the distribution factors and variables. If no distribution 
    factors are specified, and they are required, they will be filled with 1s. If no variables are specified, 
    and they are required, they will be filled with 0s. If specifying distribution factors, they must be of size n * len(elem_ids), 
    where n is a positive integer. If specifying variables, they must be of dimensions 
    [number of sideset variables, number of timesteps, number of sides being added].
    """
    # variables array is of dim (num_var, time_step, num_sides)
    def add_sides_to_sideset(self, elem_ids, side_ids, ss_id, dist_facts=None, variables=None):
        ndx = self.find_sideset_num(ss_id)

        if (self.num_ss_var == 0 and variables != None):
            raise Exception("Trying to add variables to exodus file with no variables")
        

        # if not loaded in yet, need to load in 
        if (self.ss_elem[ndx] is None):
            ss = self.get_side_set(ss_id)
            elems = ss[0]
            sides = ss[1]
            self.ss_elem[ndx] = np.array(elems)
            self.ss_sides[ndx] = np.array(sides)
            self.ss_dist_fact[ndx] = np.array(self.get_side_set_df(ss_id))
            for i in range(self.num_ss_var):
                if i == 0:
                    self.ss_vars[ndx] = list()
                self.ss_vars[ndx].append(self.ex.data["vals_sset_var" + str(i + 1) + "ss" + str(ndx + 1)])

        # need to convert elem_ids to internal ids
        map = self.ex.get_elem_id_map()
        converted_elem_ids = []
        for id in elem_ids:
            internal_id = np.where(map == id)[0][0] + 1
            converted_elem_ids.append(internal_id)
        
        num_df_per_side = self.num_dist_fact[ndx] / self.ss_sizes[ndx]
        if (dist_facts is None and self.num_dist_fact[ndx] > 0): # if no df specified and we have df in this sideset
            dist_facts = np.ones(len(elem_ids) * int(num_df_per_side)) # make enough dist factors for current 1 to n ratio
            self.ss_dist_fact[ndx] = np.append(self.ss_dist_fact[ndx], dist_facts)
            self.num_dist_fact[ndx] += len(dist_facts)
        else:
            self.ss_dist_fact[ndx] = np.append(self.ss_dist_fact[ndx], dist_facts)
            self.num_dist_fact[ndx] += len(dist_facts)


        # need to update sideset variables
        # add column of 0s to each 2d array corresponding to each variable
        # make sure there exist variables before we start adding
        if (variables is None and self.num_ss_var > 0):
            for i in range(self.num_ss_var):
                new_array =  np.hstack((self.ss_vars[ndx][i], np.zeros([self.ex.data.dimensions["time_step"].size, len(elem_ids)])))
                self.ss_vars[ndx][i] = new_array
        elif(self.num_ss_var > 0):
            for i in range(self.num_ss_var):
                 self.ss_vars[ndx][i] = np.hstack((self.ss_vars[ndx][i], variables[i]))

        self.ss_elem[ndx] = np.append(self.ss_elem[ndx], converted_elem_ids)
        self.ss_sides[ndx] = np.append(self.ss_sides[ndx], side_ids)
        self.ss_sizes[ndx] += len(elem_ids)

    """
    Removes sides from the specified sideset id. Takes in element ids and their corresponding side ids, as 
    well as the id of the sideset to remove the sides from. 
    """
    def remove_sides_from_sideset(self, elem_ids, side_ids, ss_id):
        ndx = self.find_sideset_num(ss_id)

        # if not loaded in yet, need to load in 
        if (self.ss_elem[ndx] is None):
            ss = self.get_side_set(ss_id)
            elems = ss[0]
            sides = ss[1]
            self.ss_elem[ndx] = np.array(elems)
            self.ss_sides[ndx] = np.array(sides)
            self.ss_dist_fact[ndx] = np.array(self.get_side_set_df(ss_id))
            for i in range(self.num_ss_var):
                if i == 0:
                    self.ss_vars[ndx] = list()
                self.ss_vars[ndx].append(self.ex.data["vals_sset_var" + str(i + 1) + "ss" + str(ndx + 1)])

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
        for i in range(self.ss_sizes[ndx]):
            side_tuple = (self.ss_elem[ndx][i], self.ss_sides[ndx][i])
            if (side_tuple in tuple_set):
                elem_side_remove_ndx.append(i)
                adjusted_i = i * num_df_per_side # adjust i to account for multiple df
                if (num_df_per_side != 0):
                    df_remove_ndx.extend(range(adjusted_i,  adjusted_i + num_df_per_side))

        # need to update sideset variables
        # remove column of 1s from each 2d variable array of timestep x num_sides
        for i in range(self.num_ss_var):
            self.ss_vars[ndx][i] =  np.delete(self.ss_vars[ndx][i], elem_side_remove_ndx, axis=1)


        # remove all marked indices from arrays
        self.ss_elem[ndx] = np.delete(self.ss_elem[ndx], elem_side_remove_ndx)
        self.ss_sides[ndx] = np.delete(self.ss_sides[ndx], elem_side_remove_ndx)
        self.ss_sizes[ndx] -= len(elem_side_remove_ndx)

        self.ss_dist_fact[ndx] = np.delete(self.ss_dist_fact[ndx], df_remove_ndx)
        self.num_dist_fact[ndx] -= len(df_remove_ndx)
    
    # Create 2 new sidesets from old sideset based on user-specified function.
    # User function should return boolean and take in tuple of (element, side).
    # Function provided here as a model for users to add other split_sideset functions
    # to library with more varied functionality
    # TODO: known bug with bake.e sample file
    # TODO: handle sideset variables
    def split_sideset(self, old_ss, function, ss_id1, ss_id2, delete, ss_name1, ss_name2):
        # Get sideset that will be split
        ndx = self.find_sideset_num(old_ss)

        # if not loaded in yet, need to load in 
        if (self.ss_elem[ndx] is None):
            ss = self.get_side_set(old_ss)
            elems = ss[0]
            sides = ss[1]
            self.ss_elem[ndx] = np.array(elems)
            self.ss_sides[ndx] = np.array(sides)
            self.ss_dist_fact[ndx] = np.array(self.get_side_set_df(old_ss))

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

        # If sideset did not previously have df, set df to a default of 1 for the new sideset
        if len(meet_criteria_df) == 0:
            meet_criteria_df = [1] * len(meet_criteria_side)
        if len(not_met_df) == 0:
            not_met_df = [1] * len(not_met_side)

        # If none of the sides meet the splitting criteria, don't create an empty sideset
        try:
            self.add_sideset(meet_criteria_elem, meet_criteria_side, ss_id1, ss_name1, meet_criteria_df)
        except ZeroDivisionError:
            print("No sides meeting splitting criteria to put in first sideset, no first sideset created")

        # If all of the sides meet the splitting criteria, don't create a second empty sideset
        try:
            self.add_sideset(not_met_elem, not_met_side, ss_id2, ss_name2, not_met_df)
        except ZeroDivisionError:
            print("All sides meet splitting criteria, no sides to put in second sideset, no second sideset created")
        
        #Delete old sideset if desired by user
        if delete:
           self.remove_sideset(old_ss)

    # Creates 2 new sidesets from sides in old sideset based on x-coordinate values.
    # TODO: Test function more thoroughly, most testing informal and only on 'cube_its_mod.e' sample file
    def split_sideset_x_coords(self, old_ss, comparison, x_value, all_nodes, ss_id1, ss_id2, delete, ss_name1, ss_name2):
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
        ndx = self.find_sideset_num(old_ss)

        # if not loaded in yet, need to load in 
        if (self.ss_elem[ndx] is None):
            ss = self.ex.get_side_set(old_ss)
            elems = ss[0]
            sides = ss[1]
            self.ss_elem[ndx] = np.array(elems)
            self.ss_sides[ndx] = np.array(sides)
            self.ss_dist_fact[ndx] = np.array(self.ex.get_side_set_df(old_ss))
            # for i in range(self.num_ss_var):
            #     if i == 0:
            #         self.ss_vars[ndx] = []
            #     self.ss_vars[ndx].append(self.ex.data["vals_sset_var" + str(i + 1) + "ss" + str(ndx + 1)])

        num_df_per_side = int(self.num_dist_fact[ndx] / self.ss_sizes[ndx]) # find number of df per side, if 0 there are no df

        meet_criteria_elem = []
        meet_criteria_side = []
        meet_criteria_df = []
        not_met_elem = []
        not_met_side = []
        not_met_df = []

        ss_nodes = self.ex.get_side_set_node_list(old_ss)

        # Either add sides to new sideset if all nodes in a given side meet x-coord criteria
        if all_nodes:
            node_ndx = 0 # keep track of ID of current node in sideset
            for i in range(len(ss_nodes[1])):
                side_tuple = (self.ss_elem[ndx][i], self.ss_sides[ndx][i])
                nodes_per_side = ss_nodes[1][i] # number of nodes in current side
                flag = True # flag used to determine whether or not all nodes in the side meet criteria
                for j in range(nodes_per_side):
                    node_x_coord = self.ex.get_partial_coord_x(ss_nodes[0][node_ndx], 1) # x-coord of current node
                    if flag and not compare(node_x_coord[0]): # if x-coord doesn't meet criteria
                        flag = False # not all nodes on side meet criteria
                        not_met_elem.append(side_tuple[0])
                        not_met_side.append(side_tuple[1])
                        adjusted_i = i * num_df_per_side # adjust i to account for multiple df
                        if (num_df_per_side != 0):
                            not_met_df.extend(range(adjusted_i,  adjusted_i + num_df_per_side))
                    node_ndx += 1
                if flag:
                    meet_criteria_elem.append(side_tuple[0])
                    meet_criteria_side.append(side_tuple[1])
                    adjusted_i = i * num_df_per_side # adjust i to account for multiple df
                    if (num_df_per_side != 0):
                        meet_criteria_df.extend(range(adjusted_i,  adjusted_i + num_df_per_side))

        # Or add sides to new sideset if at least one node in a given side meets x-coord criteria
        else:
            node_ndx = 0 # keep track of ID of current node in sideset
            for i in range(len(ss_nodes[1])):
                side_tuple = (self.ss_elem[ndx][i], self.ss_sides[ndx][i])
                nodes_per_side = ss_nodes[1][i] # number of nodes in current side
                flag = False # flag used to determine whether or not there is a node on side meeting criteria
                for j in range(nodes_per_side):
                    node_x_coord = self.ex.get_partial_coord_x(ss_nodes[0][node_ndx], 1) # x-coord of current node
                    if not flag and compare(node_x_coord[0]): # if side not yet added and x-coord meets criteria
                        flag = True # at least one node meets criteria
                        meet_criteria_elem.append(side_tuple[0])
                        meet_criteria_side.append(side_tuple[1])
                        adjusted_i = i * num_df_per_side # adjust i to account for multiple df
                        if (num_df_per_side != 0):
                            meet_criteria_df.extend(range(adjusted_i,  adjusted_i + num_df_per_side))
                    node_ndx += 1
                if not flag:
                    not_met_elem.append(side_tuple[0])
                    not_met_side.append(side_tuple[1])
                    adjusted_i = i * num_df_per_side # adjust i to account for multiple df
                    if (num_df_per_side != 0):
                        not_met_df.extend(range(adjusted_i,  adjusted_i + num_df_per_side))

        # If sideset did not previously have df, set df to a default of 1 for the new sideset
        if len(meet_criteria_df) == 0:
            meet_criteria_df = [1] * len(meet_criteria_side)
        if len(not_met_df) == 0:
            not_met_df = [1] * len(not_met_side)

        # If none of the sides meet the splitting criteria, don't create an empty sideset
        try:
            self.add_sideset(meet_criteria_elem, meet_criteria_side, ss_id1, ss_name1, meet_criteria_df)
        except ZeroDivisionError:
            print("No sides meeting splitting criteria to put in first sideset, no first sideset created")

        # If all of the sides meet the splitting criteria, don't create a second empty sideset
        try:
            self.add_sideset(not_met_elem, not_met_side, ss_id2, ss_name2, not_met_df)
        except ZeroDivisionError:
            print("All sides meet splitting criteria, no sides to put in second sideset, no second sideset created")
        
        #Delete old sideset if desired by user
        if delete:
           self.remove_sideset(old_ss)

    # Creates 2 new sidesets from sides in old sideset based on y-coordinate values.
    # TODO: Test function more thoroughly, most testing informal and only on 'cube_its_mod.e' sample file
    def split_sideset_y_coords(self, old_ss, comparison, y_value, all_nodes, ss_id1, ss_id2, delete, ss_name1, ss_name2):
        # Set comparison that will be used
        if comparison == '<':
          compare = lambda coord : coord < y_value
        elif comparison == '>':
          compare = lambda coord : coord > y_value
        elif comparison == '<=':
          compare = lambda coord : coord <= y_value
        elif comparison == '>=':
          compare = lambda coord : coord >= y_value
        elif comparison == '=':
          compare = lambda coord : coord == y_value
        elif comparison == '!=':
          compare = lambda coord : coord != y_value
        else:
          raise Exception("Comparison not valid. Valid comparison inputs: '<', '>', '<=', '>=', '=', '!='")

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
            # for i in range(self.num_ss_var):
            #     if i == 0:
            #         self.ss_vars[ndx] = []
            #     self.ss_vars[ndx].append(self.ex.data["vals_sset_var" + str(i + 1) + "ss" + str(ndx + 1)])

        num_df_per_side = int(self.num_dist_fact[ndx] / self.ss_sizes[ndx]) # find number of df per side, if 0 there are no df

        meet_criteria_elem = []
        meet_criteria_side = []
        meet_criteria_df = []
        not_met_elem = []
        not_met_side = []
        not_met_df = []

        ss_nodes = self.ex.get_side_set_node_list(old_ss)

        # Either add sides to new sideset if all nodes in a given side meet y-coord criteria
        if all_nodes:
            node_ndx = 0 # keep track of ID of current node in sideset
            for i in range(len(ss_nodes[1])):
                side_tuple = (self.ss_elem[ndx][i], self.ss_sides[ndx][i])
                nodes_per_side = ss_nodes[1][i] # number of nodes in current side
                flag = True # flag used to determine whether or not all nodes in the side meet criteria
                for j in range(nodes_per_side):
                    node_y_coord = self.ex.get_partial_coord_y(ss_nodes[0][node_ndx], 1) # y-coord of current node
                    if flag and not compare(node_y_coord[0]): # if y-coord doesn't meet criteria
                        flag = False # not all nodes on side meet criteria
                        not_met_elem.append(side_tuple[0])
                        not_met_side.append(side_tuple[1])
                        adjusted_i = i * num_df_per_side # adjust i to account for multiple df
                        if (num_df_per_side != 0):
                            not_met_df.extend(range(adjusted_i,  adjusted_i + num_df_per_side))
                    node_ndx += 1
                if flag:
                    meet_criteria_elem.append(side_tuple[0])
                    meet_criteria_side.append(side_tuple[1])
                    adjusted_i = i * num_df_per_side # adjust i to account for multiple df
                    if (num_df_per_side != 0):
                        meet_criteria_df.extend(range(adjusted_i,  adjusted_i + num_df_per_side))

        # Or add sides to new sideset if at least one node in a given side meets y-coord criteria
        else:
            node_ndx = 0 # keep track of ID of current node in sideset
            for i in range(len(ss_nodes[1])):
                side_tuple = (self.ss_elem[ndx][i], self.ss_sides[ndx][i])
                nodes_per_side = ss_nodes[1][i] # number of nodes in current side
                flag = False # flag used to determine whether or not there is a node on side meeting criteria
                for j in range(nodes_per_side):
                    node_y_coord = self.ex.get_partial_coord_y(ss_nodes[0][node_ndx], 1) # y-coord of current node
                    if not flag and compare(node_y_coord[0]): # if side not yet added and y-coord meets criteria
                        flag = True # at least one node meets criteria
                        meet_criteria_elem.append(side_tuple[0])
                        meet_criteria_side.append(side_tuple[1])
                        adjusted_i = i * num_df_per_side # adjust i to account for multiple df
                        if (num_df_per_side != 0):
                            meet_criteria_df.extend(range(adjusted_i,  adjusted_i + num_df_per_side))
                    node_ndx += 1
                if not flag:
                    not_met_elem.append(side_tuple[0])
                    not_met_side.append(side_tuple[1])
                    adjusted_i = i * num_df_per_side # adjust i to account for multiple df
                    if (num_df_per_side != 0):
                        not_met_df.extend(range(adjusted_i,  adjusted_i + num_df_per_side))

        # If sideset did not previously have df, set df to a default of 1 for the new sideset
        if len(meet_criteria_df) == 0:
            meet_criteria_df = [1] * len(meet_criteria_side)
        if len(not_met_df) == 0:
            not_met_df = [1] * len(not_met_side)

        # If none of the sides meet the splitting criteria, don't create an empty sideset
        try:
            self.add_sideset(meet_criteria_elem, meet_criteria_side, ss_id1, ss_name1, meet_criteria_df)
        except ZeroDivisionError:
            print("No sides meeting splitting criteria to put in first sideset, no first sideset created")

        # If all of the sides meet the splitting criteria, don't create a second empty sideset
        try:
            self.add_sideset(not_met_elem, not_met_side, ss_id2, ss_name2, not_met_df)
        except ZeroDivisionError:
            print("All sides meet splitting criteria, no sides to put in second sideset, no second sideset created")
        
        #Delete old sideset if desired by user
        if delete:
           self.remove_sideset(old_ss)

    # Creates 2 new sidesets from sides in old sideset based on z-coordinate values.
    # TODO: Test function more thoroughly, most testing informal and only on 'cube_its_mod.e' sample file
    def split_sideset_z_coords(self, old_ss, comparison, z_value, all_nodes, ss_id1, ss_id2, delete, ss_name1, ss_name2):
        # Set comparison that will be used
        if comparison == '<':
          compare = lambda coord : coord < z_value
        elif comparison == '>':
          compare = lambda coord : coord > z_value
        elif comparison == '<=':
          compare = lambda coord : coord <= z_value
        elif comparison == '>=':
          compare = lambda coord : coord >= z_value
        elif comparison == '=':
          compare = lambda coord : coord == z_value
        elif comparison == '!=':
          compare = lambda coord : coord != z_value
        else:
          raise Exception("Comparison not valid. Valid comparison inputs: '<', '>', '<=', '>=', '=', '!='")

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
            # for i in range(self.num_ss_var):
            #     if i == 0:
            #         self.ss_vars[ndx] = []
            #     self.ss_vars[ndx].append(self.ex.data["vals_sset_var" + str(i + 1) + "ss" + str(ndx + 1)])

        num_df_per_side = int(self.num_dist_fact[ndx] / self.ss_sizes[ndx]) # find number of df per side, if 0 there are no df

        meet_criteria_elem = []
        meet_criteria_side = []
        meet_criteria_df = []
        not_met_elem = []
        not_met_side = []
        not_met_df = []

        ss_nodes = self.ex.get_side_set_node_list(old_ss)

        # Either add sides to new sideset if all nodes in a given side meet z-coord criteria
        if all_nodes:
            node_ndx = 0 # keep track of ID of current node in sideset
            for i in range(len(ss_nodes[1])):
                side_tuple = (self.ss_elem[ndx][i], self.ss_sides[ndx][i])
                nodes_per_side = ss_nodes[1][i] # number of nodes in current side
                flag = True # flag used to determine whether or not all nodes in the side meet criteria
                for j in range(nodes_per_side):
                    node_z_coord = self.ex.get_partial_coord_z(ss_nodes[0][node_ndx], 1) # z-coord of current node
                    if flag and not compare(node_z_coord[0]): # if z-coord doesn't meet criteria
                        flag = False # not all nodes on side meet criteria
                        not_met_elem.append(side_tuple[0])
                        not_met_side.append(side_tuple[1])
                        adjusted_i = i * num_df_per_side # adjust i to account for multiple df
                        if (num_df_per_side != 0):
                            not_met_df.extend(range(adjusted_i,  adjusted_i + num_df_per_side))
                    node_ndx += 1
                if flag:
                    meet_criteria_elem.append(side_tuple[0])
                    meet_criteria_side.append(side_tuple[1])
                    adjusted_i = i * num_df_per_side # adjust i to account for multiple df
                    if (num_df_per_side != 0):
                        meet_criteria_df.extend(range(adjusted_i,  adjusted_i + num_df_per_side))

        # Or add sides to new sideset if at least one node in a given side meets z-coord criteria
        else:
            node_ndx = 0 # keep track of ID of current node in sideset
            for i in range(len(ss_nodes[1])):
                side_tuple = (self.ss_elem[ndx][i], self.ss_sides[ndx][i])
                nodes_per_side = ss_nodes[1][i] # number of nodes in current side
                flag = False # flag used to determine whether or not there is a node on side meeting criteria
                for j in range(nodes_per_side):
                    node_z_coord = self.ex.get_partial_coord_y(ss_nodes[0][node_ndx], 1) # z-coord of current node
                    if not flag and compare(node_z_coord[0]): # if side not yet added and z-coord meets criteria
                        flag = True # at least one node meets criteria
                        meet_criteria_elem.append(side_tuple[0])
                        meet_criteria_side.append(side_tuple[1])
                        adjusted_i = i * num_df_per_side # adjust i to account for multiple df
                        if (num_df_per_side != 0):
                            meet_criteria_df.extend(range(adjusted_i,  adjusted_i + num_df_per_side))
                    node_ndx += 1
                if not flag:
                    not_met_elem.append(side_tuple[0])
                    not_met_side.append(side_tuple[1])
                    adjusted_i = i * num_df_per_side # adjust i to account for multiple df
                    if (num_df_per_side != 0):
                        not_met_df.extend(range(adjusted_i,  adjusted_i + num_df_per_side))

        # If sideset did not previously have df, set df to a default of 1 for the new sideset
        if len(meet_criteria_df) == 0:
            meet_criteria_df = [1] * len(meet_criteria_side)
        if len(not_met_df) == 0:
            not_met_df = [1] * len(not_met_side)

        # If none of the sides meet the splitting criteria, don't create an empty sideset
        try:
            self.add_sideset(meet_criteria_elem, meet_criteria_side, ss_id1, ss_name1, meet_criteria_df)
        except ZeroDivisionError:
            print("No sides meeting splitting criteria to put in first sideset, no first sideset created")

        # If all of the sides meet the splitting criteria, don't create a second empty sideset
        try:
            self.add_sideset(not_met_elem, not_met_side, ss_id2, ss_name2, not_met_df)
        except ZeroDivisionError:
            print("All sides meet splitting criteria, no sides to put in second sideset, no second sideset created")
        
        #Delete old sideset if desired by user
        if delete:
           self.remove_sideset(old_ss)

    # return the number of sidesets
    def num_side_sets(self):
        return self.num_ss

    # return id map for sideset
    def get_side_set_id_map(self):
        return self.ss_prop1

    def get_side_set_names(self):
        return self.ss_names

    def get_side_set_name(self, ndx):
        return self.ss_names[ndx]

    # get portion of a sideset's elem and side id's
    def _int_get_partial_side_set(self, obj_id, internal_id, start, count):
        ndx = self.find_sideset_num(obj_id)
        # if not loaded in yet, go to file if it exists
        if (ndx == -1):
            raise KeyError("Failed to retrieve elements of side set with id {} ('{}')".format(obj_id, 'elem_ss%d' % internal_id))

        internal_id = self.orig_internal_ids[ndx]
        
        if (self.ss_elem[ndx] is None):
            try:
                elmset = self.ex.data.variables['elem_ss%d' % internal_id][start - 1:start + count - 1]
            except KeyError:
                raise KeyError(
                    "Failed to retrieve elements of side set with id {} ('{}')".format(obj_id, 'elem_ss%d' % internal_id))
        else:
            try:
                elmset = self.ss_elem[ndx][start - 1:start + count - 1]
            except KeyError:
                raise KeyError(
                    "Failed to retrieve elements of side set with id {} ('{}')".format(obj_id, 'elem_ss%d' % internal_id))
            
        if (self.ss_sides[ndx] is None):
            try:
                sset = self.ex.data.variables['side_ss%d' % internal_id][start - 1:start + count - 1]
            except KeyError:
                raise KeyError(
                    "Failed to retrieve sides of side set with id {} ('{}')".format(obj_id, 'side_ss%d' % internal_id))
        else:
            try:
                sset = self.ss_sides[ndx][start - 1:start + count - 1]
            except KeyError:
                raise KeyError(
                    "Failed to retrieve elements of side set with id {} ('{}')".format(obj_id, 'elem_ss%d' % internal_id))
            

        return elmset, sset

    def _int_get_side_set_params(self, obj_id, internal_id):
        ndx = self.find_sideset_num(obj_id)
        if (ndx == -1):
            raise KeyError("Failed to retrieve elements of side set with id {} ('{}')".format(obj_id, 'elem_ss%d' % internal_id))

        num_entries = self.ss_sizes[ndx]
        num_df = self.num_dist_fact[ndx]
        return num_entries, num_df

    def _int_get_partial_side_set_df(self, obj_id, internal_id, start, count):
        ndx = self.find_sideset_num(obj_id)

        internal_id = self.orig_internal_ids[ndx]

        num_sets = self.num_side_sets
        if num_sets == 0:
            raise KeyError("No side sets are stored in this database!")
        if start < 1:
            raise ValueError("Start index must be greater than 0")
        if count < 0:
            raise ValueError("Count must be a positive integer")

        if (self.num_dist_fact[ndx] == 0):
            warnings.warn("This database does not contain dist factors for side set {}".format(obj_id))
            set = []

        if (self.num_dist_fact[ndx] > 0 and self.ss_dist_fact[ndx] is not None):
            set = self.ss_dist_fact[ndx][start - 1:start + count - 1]

        if (self.num_dist_fact[ndx] > 0 and self.ss_dist_fact[ndx] is None): # has to be an original sideset
            set = self.ex.data.variables['dist_fact_ss%d' % internal_id][start - 1:start + count - 1]

        return set
    def get_side_set(self, obj_id):
        ndx = self.find_sideset_num(obj_id)
        internal_id = self.orig_internal_ids[ndx]
        return self._int_get_partial_side_set(obj_id, internal_id, 1, self.ss_sizes[ndx])
    def get_side_set_df(self, obj_id):
        ndx = self.find_sideset_num(obj_id)
        internal_id = self.orig_internal_ids[ndx]
        return self._int_get_partial_side_set_df(obj_id, internal_id, 1, self.num_dist_fact[ndx])


    """
    Writes out all variables related to sidesets to a new file. 
    """
    def write_variables(self, data):

        if (self.num_ss == 0):
            # nothing to write so done
            return

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
        for i in range(self.num_ss):
            data['ss_names'][i] = util.convert_string(self.ss_names[i] + str('\0'), self.ex.max_allowed_name_length)

        # write out sidset variable status truth table
        if (self.num_ss_var > 0):
            data.createVariable("sset_var_tab", "int32", dimensions=("num_side_sets", "num_sset_var"))
            data["sset_var_tab"][:] = self.ss_var_tab[:]

        # write out sideset variable names
        if (self.num_ss_var > 0):
            data.createVariable("name_sset_var", "|S1", dimensions=("num_sset_var", "len_name"))
            for i in range(self.num_ss_var):
                data["name_sset_var"][i] = util.convert_string(self.ss_var_names[i] + str('\0'), self.ex.max_allowed_name_length)
        
        for i in range(self.num_ss):
            # create elem, sides, and dist facts
            data.createVariable("elem_ss" + str(i+1), "int32", dimensions=("num_side_ss" + str(i+1)))

            if (self.num_dist_fact[i] > 0): # if distribution factors exist for this sideset, make a variable
                data.createVariable("dist_fact_ss" + str(i+1), "int32", dimensions=("num_df_ss" + str(i+1)))
            
            data.createVariable("side_ss" + str(i+1), "int32", dimensions=("num_side_ss" + str(i+1)))
            
            # if None, just copy over old data, otherwise copy over new stuff
            if (self.ss_elem[i] is None):
                data["elem_ss" + str(i+1)][:] = self.get_side_set(self.ss_prop1[i])[0][:]
            else:
                data["elem_ss" + str(i+1)][:] = self.ss_elem[i][:]

            if (self.ss_sides[i] is None):
                data["side_ss" + str(i+1)][:] = self.get_side_set(self.ss_prop1[i])[1][:]
            else:
                data["side_ss" + str(i+1)][:] = self.ss_sides[i][:]
            
            if (self.ss_dist_fact[i] is None and self.num_dist_fact[i] > 0):
                data["dist_fact_ss" + str(i+1)][:] = self.get_side_set_df(self.ss_prop1[i])[:]
            elif(self.num_dist_fact[i] > 0):
                data["dist_fact_ss" + str(i+1)][:] = self.ss_dist_fact[i][:]

            # write out sideset variables
            for j in range(self.num_ss_var):
                data.createVariable("vals_sset_var" + str(j + 1) + "ss" + str(i + 1), "float64", dimensions=("time_step", "num_side_ss" + str(i + 1)))
                # need to copy over from old file if has not been loaded in yet
                if (self.ss_vars[i] is None):
                    data["vals_sset_var" + str(j + 1) + "ss" + str(i + 1)][:] = self.ex.data["vals_sset_var" + str(j + 1) + "ss" + str(i + 1)][:]
                else:
                    data["vals_sset_var" + str(j + 1) + "ss" + str(i + 1)][:] = self.ss_vars[i][j]

    """
    Writes all dimensions related to sidesets to a new exodus file.
    """
    def write_dimensions(self, data):
        if (self.num_ss == 0):
            # nothing to write so done
            return
        data.createDimension("num_side_sets", self.num_ss)

        # write each dimension
        for i in range(self.num_ss):
            if (self.num_dist_fact[i] > 0): # if there are no distribution factors, don't write out the variables
                data.createDimension("num_df_ss" + str(i + 1), self.num_dist_fact[i])
            data.createDimension("num_side_ss" + str(i+1), self.ss_sizes[i])

        # write out num_sset_var dimension
        if (self.num_ss_var > 0):
            data.createDimension("num_sset_var", self.num_ss_var)

            

    # (Based on find_nodeset_num in ns_ledger)
    """
    Find the index in the sideset ledgers arrays for a given sideset id. 
    """
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