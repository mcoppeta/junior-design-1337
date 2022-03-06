import numpy as np


# Ledger for both element blocks and elements
class ElemLedger:

    def __init__(self, ex):
        self.ex = ex

        #TODO consider making self.blocks an array
        self.blocks = {}  # connectX: data and details of element block X
        self.eb_status = []
        self.eb_prop1 = []  # each block from here gets corresponding entry in self.blocks
        self.elem_num_map = []  # id's of elements
        self.num_blocks = 0

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

        existing_prop1 = self.ex.data.variables['eb_prop1'][:]
        for i in range(self.ex.data.dimensions['num_el_blk'].size):
            blk_num = existing_prop1[i]
            connect_title = "connect{}".format(blk_num)

            block_data = {}
            block_data['blk_num'] = blk_num
            block_data['elements'] = np.array(self.ex.data.variables[connect_title][:].tolist())
            block_data['elem_type'] = self.ex.data.variables[connect_title].elem_type
            block_data['num_nod_per_el'] = self.ex.data.dimensions['num_nod_per_el' + str(blk_num)].size
            block_data['num_el_blk'] = self.ex.data.dimensions['num_el_in_blk' + str(blk_num)].size
            if 'eb_names' in self.ex.data.variables.keys():
                block_data['name'] = self.ex.lineparse(self.ex.data.variables['eb_names'][i])
            else:
                block_data['name'] = "Block {}".format(blk_num)
            self.blocks[connect_title] = block_data

            self.num_blocks += 1

        self.eb_status = self.ex.data.variables['eb_status'][:]

        print(self.blocks)


    def write(self, data):
        elem_count = 0
        for i in self.blocks:
            elem_count += self.blocks[i]['num_el_blk']
        data.createDimension("num_elem", elem_count)

        data.createDimension("num_el_blk", self.num_blocks)

        for i in self.blocks:
            blk_num = self.blocks[i]['blk_num']

            el_in_blk_title = "num_el_in_blk{}".format(blk_num)
            data.createDimension(el_in_blk_title, self.blocks[i]['num_el_blk'])

            nod_per_el_title = "num_nod_per_el{}".format(blk_num)
            data.createDimension(nod_per_el_title, self.blocks[i]['num_nod_per_el'])

        data.createDimension("num_elem_var", self.ex.data.dimensions['num_elem_var'].size)  # TODO -> figure this out


        #TODO VAR: eb_status -> [1 for i in range(num_el_blk)] ?
        #TODO VAR: eb_prop1 -> construct from blk_num in self.blocks
        #TODO VAR: eb_names -> construct from name in self.blocks
        #TODO VAR: elem_num_map -> should be maintained already
        #TODO VAR: connectX -> construct from self.blocks
        #TODO VAR: name_elem_var -> ???
        #TODO VAR: vals_elem_varNebX -> ???
        #TODO VAR: elem_var_tab -> ???
