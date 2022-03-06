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
            block_data['elements'] = self.ex.data.variables[connect_title][:]
            block_data['elem_type'] = self.ex.data.variables[connect_title].elem_type
            block_data['num_nod_per_el'] = self.ex.data.dimensions['num_nod_per_el' + str(blk_num)].size
            block_data['num_el_blk'] = self.ex.data.dimensions['num_el_in_blk' + str(blk_num)].size
            if 'eb_names' in self.ex.data.variables.keys():
                block_data['name'] = self.ex.lineparse(self.ex.data.variables['eb_names'][i])
            else:
                block_data['name'] = "Block {}".format(blk_num)
            self.blocks[connect_title] = block_data

        self.eb_status = self.ex.data.variables['eb_status'][:]

        print("{} element blocks detected".format(len(self.blocks)))
        print(self.blocks)


    def write(self, data):
        pass
