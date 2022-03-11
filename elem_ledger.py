import numpy as np
import util


# Ledger for both element blocks and elements
class ElemLedger:

    def __init__(self, ex):
        self.ex = ex

        #TODO consider making self.blocks an array
        self.blocks = {}  # connectX: data and details of element block X
        self.eb_status = self.ex.data.variables['eb_status'][:]
        self.eb_prop1 = self.ex.data.variables['eb_prop1'][:]  # each block from here gets entry in self.blocks
        self.elem_num_map = []  # id's of elements
        self.num_blocks = 0
        self.name_elem_var = self.ex.data.variables['name_elem_var'][:]
        self.elem_var_tab = self.ex.data.variables['elem_var_tab'][:]  # # elem blocks x num_elem_var -- 1's only

        # Assumes all elements must exist in some block
        if 'num_el_blk' not in self.ex.data.dimensions.keys():
            return

        if 'elem_map' in self.ex.data.variables.keys() and 'elem_num_map' in self.ex.data.variables.keys():
            raise ValueError('Dataset contains both an elem_num_map and elem_map - causes ambiguity')
        elif 'elem_map' in self.ex.data.variables.keys():
            self.elem_num_map = self.ex.data.variables['elem_map'][:]
        elif 'elem_num_map' in self.ex.data.variables.keys():
            self.elem_num_map = self.ex.data.variables['elem_num_map'][:]
        else:
            self.elem_num_map = [i for i in range(self.ex.data.dimensions['num_elem'].size)]

        for i in range(self.ex.data.dimensions['num_el_blk'].size):
            blk_num = self.eb_prop1[i]
            connect_title = "connect{}".format(blk_num)

            block_data = {}
            block_data['blk_num'] = blk_num
            block_data['elements'] = np.array(self.ex.data.variables[connect_title][:].tolist())
            block_data['elem_type'] = self.ex.data.variables[connect_title].elem_type
            block_data['num_nod_per_el'] = self.ex.data.dimensions['num_nod_per_el' + str(blk_num)].size
            block_data['num_el_blk'] = self.ex.data.dimensions['num_el_in_blk' + str(blk_num)].size
            if 'eb_names' in self.ex.data.variables.keys():
                block_data['name'] = util.lineparse(self.ex.data.variables['eb_names'][i])
            else:
                block_data['name'] = "Block {}".format(blk_num)

            variables = {}  # self.blocks['connect1']['variables']['vals_elem_var1eb1']
            for j in range(self.ex.data.dimensions['num_elem_var'].size):
                current_var_name = "vals_elem_var{}eb{}".format(j + 1, blk_num)
                variables[current_var_name] = self.ex.data.variables[current_var_name][:]
            block_data['variables'] = variables

            self.blocks[connect_title] = block_data
            self.num_blocks += 1

        #print(self.blocks)

    # Writes out element data to the new dataset
    def write(self, data):

        # Creates dimension for number of elements
        elem_count = 0
        for i in self.blocks:
            elem_count += self.blocks[i]['num_el_blk']
        data.createDimension("num_elem", elem_count)

        # Create dimension for number of element blocks
        data.createDimension("num_el_blk", self.num_blocks)

        names = []
        for i in self.blocks:
            blk_num = self.blocks[i]['blk_num']
            names.append(util.convert_string(self.blocks[i]['name'] + str('\0'), self.ex.max_allowed_name_length))

            # Creates dimension for how many elements are in this element block
            el_in_blk_title = "num_el_in_blk{}".format(blk_num)
            data.createDimension(el_in_blk_title, self.blocks[i]['num_el_blk'])

            # Creates dimension for how many nodes are in each element in this element block
            nod_per_el_title = "num_nod_per_el{}".format(blk_num)
            data.createDimension(nod_per_el_title, self.blocks[i]['num_nod_per_el'])

        # Creates dimension for the number of elemental variables
        data.createDimension("num_elem_var", self.ex.data.dimensions['num_elem_var'].size)  # TODO -> figure this out


        #TODO Make sure this implementation makes sense
        data.createVariable("eb_status", "int32", dimensions=("num_el_blk"))
        data['eb_status'][:] = np.array(self.eb_status)


        #TODO Make sure this stays consistent with implementation above
        data.createVariable("eb_prop1", "int32", dimensions=("num_el_blk"))
        data['eb_prop1'].setncattr('name', 'ID')
        data['eb_prop1'][:] = np.array(self.eb_prop1)

        # Creates variable with names of each element block
        data.createVariable("eb_names", "|S1", dimensions=("num_el_blk", "len_name"))
        data['eb_names'][:] = np.array(names)

        #TODO Make sure this is maintained above
        data.createVariable("elem_num_map", "int32", dimensions=("num_elem"))
        data['elem_num_map'][:] = np.array(self.elem_num_map)

        # Creates connectX variable for each of X element blocks. This describes the nodes forming each element in block
        for connectX in self.blocks:
            blk_num = self.blocks[connectX]['blk_num']
            data.createVariable(connectX, "int32", dimensions=("num_el_in_blk" + str(blk_num),
                                                               "num_nod_per_el" + str(blk_num)))
            data[connectX].setncattr('elem_type', self.blocks[connectX]['elem_type'])
            data[connectX][:] = np.array(self.blocks[connectX]['elements'])

        #TODO VAR: name_elem_var -> ???
        data.createVariable("name_elem_var", "|S1", dimensions=("num_elem_var", "len_name"), fill_value=b'\x00')
        data["name_elem_var"][:] = np.array(self.name_elem_var)

        #TODO VAR: vals_elem_varNebX -> ???
        for connectX in self.blocks:
            num = self.blocks[connectX]["blk_num"]
            for variable in self.blocks[connectX]['variables']:
                var_data = self.blocks[connectX]['variables'][variable]
                data.createVariable(variable, "float64", dimensions=("time_step", "num_el_in_blk{}".format(num)))
                data[variable][:] = np.array(var_data)

        #TODO VAR: maintain with new functions
        data.createVariable("elem_var_tab", "int32", dimensions=("num_el_blk", "num_elem_var"))
        data["elem_var_tab"][:] = np.array(self.elem_var_tab)