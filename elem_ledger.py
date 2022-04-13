import numpy as np
import util
from element_block import ElementBlock


# Ledger for both element blocks and elements
class ElemLedger:

    def __init__(self, ex):
        self.ex = ex

        self.blocks = []

        eb_status = []
        if 'eb_status' in self.ex.data.variables.keys():
            eb_status = self.ex.data.variables['eb_status'][:]
        elif 'num_elem' in self.ex.data.dimensions.keys():
            eb_status = [1 for i in range(self.ex.data.dimensions['num_elem'].size)]

        # TODO: if removing blocks, will need to accomodate here
        self.eb_prop1 = []
        if 'eb_prop1' in self.ex.data.variables.keys():
            self.eb_prop1 = self.ex.data.variables['eb_prop1'][:]  # each block from here gets entry in self.blocks

        # Array of names of elemental variables
        self.name_elem_var = []
        if 'name_elem_var' in self.ex.data.variables.keys():
            self.name_elem_var = self.ex.data.variables['name_elem_var'][:]

        # Variables as table?
        # TODO: if adding blocks in future, need to accomodate this
        self.elem_var_tab = []
        if 'elem_var_tab' in self.ex.data.variables.keys():
            self.elem_var_tab = self.ex.data.variables['elem_var_tab'][:]  # # elem blocks x num_elem_var -- 1's only

        # ID map of individual elements
        self.elem_num_map = []
        if 'elem_num_map' in self.ex.data.variables.keys() and 'elem_map' in self.ex.data.variables.keys():
            # raise NotImplementedError("Both elem_num_map and elem_map variables present. Ambiguous meaning")
            # print("Both elem_num_map and elem_map variables present. Ambiguous meaning")
            self.elem_num_map = self.ex.data.variables['elem_num_map'][:].tolist()
            # self.elem_num_map = self.ex.data.variables['elem_map'][:].tolist()
        if 'elem_num_map' in self.ex.data.variables.keys():
            self.elem_num_map = self.ex.data.variables['elem_num_map'][:].tolist()
        elif 'elem_map' in self.ex.data.variables.keys():
            self.elem_num_map = self.ex.data.variables['elem_map'][:].tolist()
        elif 'num_elem' in self.ex.data.dimensions.keys():
            self.elem_num_map = [i + 1 for i in range(self.ex.data.dimensions['num_elem'].size)]

        self.num_elem_var = 0
        if 'num_elem_var' in self.ex.data.dimensions.keys():
            self.num_elem_var = self.ex.data.dimensions['num_elem_var'].size

        # Assumes all elements must exist in some block
        if 'num_el_blk' not in self.ex.data.dimensions.keys():
            return

        for i in range(1, self.ex.data.dimensions['num_el_blk'].size + 1):
            blk_num = i # does this in ascending connectX order. Use eb_prop1 to find the block later
            connect_title = "connect{}".format(blk_num)
            status = eb_status[blk_num - 1]
            elements = np.array(self.ex.data.variables[connect_title][:].tolist())
            elem_type = self.ex.data.variables[connect_title].elem_type
            num_nod_per_el = self.ex.data.dimensions['num_nod_per_el' + str(blk_num)].size
            num_el_in_blk = self.ex.data.dimensions['num_el_in_blk' + str(blk_num)].size

            if 'eb_names' in self.ex.data.variables.keys():
                blk_name = util.lineparse(self.ex.data.variables['eb_names'][i - 1])
            else:
                blk_name = "Block {}".format(blk_num)

            # TODO -> OPENING WHEN NO VARIABLES GIVES ERROR
            variables = {}  # self.blocks['connect1']['variables']['vals_elem_var1eb1']
            for j in range(self.num_elem_var):
                current_var_name = "vals_elem_var{}eb{}".format(j + 1, blk_num)
                variables[current_var_name] = self.ex.data.variables[current_var_name][:]

            new_block = ElementBlock(blk_num, connect_title, status, blk_name, elem_type, num_nod_per_el, num_el_in_blk, elements, variables)
            self.blocks.append(new_block)
        #print(self.blocks)

    # finds index of element in element number map
    def find_element_num(self, id):
        num = -1
        for i in range(len(self.elem_num_map)):
            if self.elem_num_map[i] == id:
                num = i
                break

        if num == -1:
            raise KeyError("Cannot find element with ID " + str(id))

        return num

    # returns the block its in, and the INDEX to the element within the block
    def find_element_location(self, iid):
        relative_id = iid
        for block in self.blocks:
            if relative_id >= block.get_num_elements():
                relative_id -= block.get_num_elements()
            else:
                return block, relative_id

    def get_element_nodes(self, id):
        block, ndx = self.find_element_location(self.find_element_num(id))
        return block.get_element(ndx)

    # Given the ID of the element, remove it from its corresponding block
    def remove_element(self, id):
        internal_id = self.find_element_num(id)
        e_block, e_id = self.find_element_location(internal_id)

        # Valid element at this point

        e_block.num_el_in_blk -= 1  # 1 fewer element in block

        try:
            index = self.elem_num_map.index(id)
        except ValueError:
            raise ValueError("Element number map does not have entry for node ID {}".format(id))
        self.elem_num_map.pop(index)  # removes element reference from the number map

        elements = e_block.elements.tolist()
        removed_element = elements.pop(e_id)  # removes element from connectX
        e_block.elements = np.array(elements)

        for variable in e_block.variables:
            var_data = e_block.variables[variable].tolist()
            for i in range(len(var_data)):
                var_data[i].pop(e_id)  # Removes associated data from each elemental variable
            e_block.variables[variable] = np.array(var_data)

        return removed_element

    # Given an element block ID, return the block
    def find_element_block(self, block_id):
        blk_num = None
        for i in range(len(self.eb_prop1)):
            if self.eb_prop1[i] == block_id:
                blk_num = i + 1

        for i in self.blocks:
            if i.blk_num == blk_num:
                return i

        raise KeyError("Cannot find block with ID {}".format(block_id))

    # Adds new element formed from nodes in nodelist to block with given ID
    # Returns the element's ID
    def add_element(self, block_id, nodelist):
        block = self.find_element_block(block_id)

        # Add it to the block
        block.add_element(nodelist, self.ex)
        
        # Insert into element number map
        newID = 1 # Find new element id
        for i in range(1, len(self.elem_num_map) + 3):
            if i not in self.elem_num_map:
                newID = i
                break

        blk_num = block.get_blk_num()
        ndx = 0
        for i in range(1, blk_num):
            ndx += self.blocks[i].get_num_elements()
        ndx += block.get_num_elements() - 1 # -1 because it includes new element
        self.elem_num_map.insert(ndx, newID)

        return newID

    # Returns faces of skinned mesh of form [(intern id, face number)]
    def skin_block(self, block_id):
        block = self.find_element_block(block_id)

        i = 1
        shift = 0
        while i < block.blk_num:
            shift += self.blocks[i - 1].num_el_in_blk
            i += 1

        unique_faces = block.skin_block(shift)

        # we have the internal id's, need the elem_num_map id's instead
        converted_unique_faces = []
        for i in unique_faces:
            e, f = i
            e = self.elem_num_map[e]
            converted_unique_faces.append((e, f))
            
        return converted_unique_faces

    # Writes out element dimension data to the new dataset
    def write_dimensions(self, data):

        # Creates dimension for number of elements
        elem_count = 0
        for i in self.blocks:
            elem_count += i.num_el_in_blk
        data.createDimension("num_elem", elem_count)

        # Create dimension for number of element blocks
        data.createDimension("num_el_blk", len(self.blocks))

        for i in self.blocks:
            blk_num = i.blk_num

            # Creates dimension for how many elements are in this element block
            el_in_blk_title = "num_el_in_blk{}".format(blk_num)
            data.createDimension(el_in_blk_title, i.get_num_elements())

            # Creates dimension for how many nodes are in each element in this element block
            nod_per_el_title = "num_nod_per_el{}".format(blk_num)
            data.createDimension(nod_per_el_title, i.get_num_nodes_per_element())

        # Creates dimension for the number of elemental variables
        data.createDimension("num_elem_var", self.num_elem_var)


    # Writes out element variable data to the new dataset
    def write_variables(self, data):
        names = []
        eb_status = []
        for i in self.blocks:
            blk_num = i.blk_num
            eb_status.append(i.get_status())
            names.append(util.convert_string(i.blk_name + str('\0'), self.ex.max_allowed_name_length))  

        data.createVariable("eb_status", "int32", dimensions=("num_el_blk"))
        data['eb_status'][:] = np.array(eb_status)

        data.createVariable("eb_prop1", "int32", dimensions=("num_el_blk"))
        data['eb_prop1'].setncattr('name', 'ID')
        data['eb_prop1'][:] = np.array(self.eb_prop1)

        # Creates variable with names of each element block
        data.createVariable("eb_names", "|S1", dimensions=("num_el_blk", "len_name"))
        data['eb_names'][:] = np.array(names)

        #TODO Make sure this is maintained when adding elements
        data.createVariable("elem_num_map", "int32", dimensions=("num_elem"))
        data['elem_num_map'][:] = np.array(self.elem_num_map)

        # Creates connectX variable for each of X element blocks. This describes the nodes forming each element in block
        for block in self.blocks:
            blk_num = block.get_blk_num()
            connectX = block.get_connect_title()
            data.createVariable(connectX, "int32", dimensions=("num_el_in_blk" + str(blk_num),
                                                               "num_nod_per_el" + str(blk_num)))
            data[connectX].setncattr('elem_type', block.get_elem_type())
            data[connectX][:] = np.array(block.elements)

        # name_elem_var
        data.createVariable("name_elem_var", "|S1", dimensions=("num_elem_var", "len_name"), fill_value=b'\x00')
        data["name_elem_var"][:] = np.array(self.name_elem_var)

        # vals_elem_varNebX
        for block in self.blocks:
            num = block.get_blk_num()
            for variable in block.variables:
                var_data = block.variables[variable]
                data.createVariable(variable, "float64", dimensions=("time_step", "num_el_in_blk{}".format(num)))
                data[variable][:] = np.array(var_data)

        # IF no blocks are variables, don't write out elem_var_tab (can't fit size (x, 0)) 
        if data.dimensions['num_el_blk'].size > 0 and data.dimensions['num_elem_var'].size > 0:
            data.createVariable("elem_var_tab", "int32", dimensions=("num_el_blk", "num_elem_var"))
            data["elem_var_tab"][:] = np.array(self.elem_var_tab)

        #TODO: Add write functionality for element attributes