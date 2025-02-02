import netCDF4 as nc
import numpy as np
from .ns_ledger import NSLedger
from .ss_ledger import SSLedger
from .elem_ledger import ElemLedger
from .constants import *
from . import util


class Ledger:

    _FORMAT_MAP = {'EX_NETCDF4': 'NETCDF4',
                   'EX_LARGE_MODEL': 'NETCDF3_64BIT_OFFSET',
                   'EX_NORMAL_MODEL': 'NETCDF3_CLASSIC',
                   'EX_64BIT_DATA': 'NETCDF3_64BIT_DATA'}
    # Default values
    _MAX_STR_LENGTH = 32
    _MAX_STR_LENGTH_T = 'U32'
    _MAX_NAME_LENGTH = 32
    _MAX_LINE_LENGTH = 80
    _MAX_LINE_LENGTH_T = 'U80'
    _EXODUS_VERSION = 7.22

    def __init__(self, ex):
        self.nodeset_ledger = NSLedger(ex)
        self.sideset_ledger = SSLedger(ex)
        self.element_ledger = ElemLedger(ex)
        self.ex = ex

    def num_node_sets(self):
        """ Returns the number of nodesets present in the file"""
        return self.nodeset_ledger.num_node_sets()

    def get_node_set(self, identifier):
        """Returns an array of the nodes contained in the node set with given identifier"""
        return self.nodeset_ledger.get_node_set(identifier)

    def get_partial_node_set(self, identifier, start, count):
        """
        Returns a partial array of the nodes contained in the node set with given identifier

        Array starts at node number ``start`` (1-based) and contains ``count`` elements.
        """
        return self.nodeset_ledger.get_partial_node_set(identifier, start, count)

    def get_node_set_name(self, nodeset_id):
        """
        Get name of nodeset
        :param nodeset_id: the id of the requested node set
        :return: the name of the specified node set
        """
        return self.nodeset_ledger.get_node_set_name(nodeset_id)

    def get_node_set_id_map(self):
        """Returns the id map for node sets (ns_prop1)."""
        return self.nodeset_ledger.get_node_set_id_map()

    def get_node_set_names(self):
        """
        Returns array of nodeset names
        :return: array of nodeset names
        """
        return self.nodeset_ledger.get_node_set_names()

    def add_nodeset(self, node_ids, nodeset_id, nodeset_name=""):
        """
        add nodeset to file
        :param node_ids: the node ids which will be contained within the new nodeset
        :param nodeset_id: the intended id for the new nodeset
        :param nodeset_name: the intended name for the new nodeset
        :return: None
        """
        self.nodeset_ledger.add_nodeset(node_ids, nodeset_id, nodeset_name)

    def remove_nodeset(self, identifier):
        """
        Removes given nodeset from the Exodus file
        :param identifier: the identifier of the nodeset being removed
        :return: None
        """
        self.nodeset_ledger.remove_nodeset(identifier)

    def merge_nodesets(self, new_id, ns1, ns2, delete=True):
        """
        Merges 2 nodesets together
        :param new_id: the intended ID for the new nodeset
        :param ns1: the first nodeset to merge
        :param ns2: the second nodeset to merge
        :param delete: a flag which specifies whether the 2 starting nodesets will be removed
        :return: None
        """
        self.nodeset_ledger.merge_nodesets(new_id, ns1, ns2, delete)

    def add_node_to_nodeset(self, node_id, identifier):
        """
        Add one node to the specified nodeset
        :param node_id: the node being added to the nodeset
        :param nodeset_id: the nodeset the node will be added to
        :return: None
        """
        self.nodeset_ledger.add_node_to_nodeset(node_id, identifier)

    def add_nodes_to_nodeset(self, node_ids, identifier):
        """
        Add many nodes to the specified nodeset
        :param node_ids: the nodes being added to the nodeset (List-like)
        :param nodeset_id: the nodeset being added to
        :return: None
        """
        self.nodeset_ledger.add_nodes_to_nodeset(node_ids, identifier)

    def remove_node_from_nodeset(self, node_id, identifier):
        """
        Remove single node from a specified nodeset
        :param node_id: the node being removed from the nodeset
        :param nodeset_id: the nodeset being removed from
        :return: None
        """
        self.nodeset_ledger.remove_node_from_nodeset(node_id, identifier)

    def remove_nodes_from_nodeset(self, node_ids, identifier):
        """
        Remove many nodes from a specified nodeset
        :param node_ids: the nodes being removed from the nodeset (List-like)
        :param nodeset_id: the nodeset being removed from
        :return: None
        """
        self.nodeset_ledger.remove_nodes_from_nodeset(node_ids, identifier)

    # sideset methods
    def add_sideset(self, elem_ids, side_ids, ss_id, ss_name, dist_fact=None, variables=None):
        self.sideset_ledger.add_sideset(elem_ids, side_ids, ss_id, ss_name, dist_fact, variables)

    def remove_sideset(self, ss_id):
        self.sideset_ledger.remove_sideset(ss_id)

    def add_sides_to_sideset(self, elem_ids, side_ids, ss_id, dist_facts=None, variables=None):
        self.sideset_ledger.add_sides_to_sideset(elem_ids, side_ids, ss_id, dist_facts, variables)

    def remove_sides_from_sideset(self, elem_ids, side_ids, ss_id):
        self.sideset_ledger.remove_sides_from_sideset(elem_ids, side_ids, ss_id)

    def split_sideset(self, old_ss, function, ss_id1, ss_id2, delete, ss_name1, ss_name2):
        self.sideset_ledger.split_sideset(old_ss, function, ss_id1, ss_id2, delete, ss_name1, ss_name2)

    def num_side_sets(self):
        return self.sideset_ledger.num_side_sets()

    # return id map for sideset
    def get_side_set_id_map(self):
        return self.sideset_ledger.get_side_set_id_map()

    def get_side_set_names(self):
        return self.sideset_ledger.get_side_set_names()

    def get_side_set_name(self, ndx):
        return self.sideset_ledger.get_side_set_name(ndx)

    # get portion of a sideset's elem and side id's
    def _int_get_partial_side_set(self, obj_id, internal_id, start, count):
        return self.sideset_ledger._int_get_partial_side_set(obj_id, internal_id, start, count)

    def _int_get_side_set_params(self, obj_id, internal_id):
        return self.sideset_ledger._int_get_side_set_params(obj_id, internal_id)

    def _int_get_partial_side_set_df(self, obj_id, internal_id, start, count):
        return self.sideset_ledger._int_get_partial_side_set_df(obj_id, internal_id, start, count)

    def split_sideset_x_coords(self, old_ss, comparison, x_value, all_nodes, ss_id1, ss_id2, delete, ss_name1, ss_name2):
        self.sideset_ledger.split_sideset_x_coords(old_ss, comparison, x_value, all_nodes, ss_id1, ss_id2, delete, ss_name1, ss_name2)

    def split_sideset_y_coords(self, old_ss, comparison, y_value, all_nodes, ss_id1, ss_id2, delete, ss_name1, ss_name2):
        self.sideset_ledger.split_sideset_y_coords(old_ss, comparison, y_value, all_nodes, ss_id1, ss_id2, delete, ss_name1, ss_name2)

    def split_sideset_z_coords(self, old_ss, comparison, z_value, all_nodes, ss_id1, ss_id2, delete, ss_name1, ss_name2):
        self.sideset_ledger.split_sideset_z_coords(old_ss, comparison, z_value, all_nodes, ss_id1, ss_id2, delete, ss_name1, ss_name2)


    # element methods
    def num_elem(self):
        return self.element_ledger.num_elem()

    def num_elem_blocks(self):
        return self.element_ledger.num_elem_blocks()

    def num_elem_variable(self):
        return self.element_ledger.num_elem_variable()

    def get_elem_num_map(self):
        return self.element_ledger.get_elem_num_map()

    def get_eb_prop1(self):
        return self.element_ledger.get_eb_prop1()

    def get_connectX(self, id):
        return self.element_ledger.get_connectX(id)

    def get_num_elem_in_block(self, id):
        return self.element_ledger.get_num_elem_in_block(id)

    def get_num_nodes_per_el_block(self, id):
        return self.element_ledger.get_num_nodes_per_el_block(id)

    def get_elem_block_type(self, id):
        return self.element_ledger.get_elem_block_type(id)

    def get_elem_block_name(self, id):
        return self.element_ledger.get_elem_block_name(id)

    def get_elem_block_names(self):
        return self.element_ledger.get_elem_block_names()

    def remove_element(self, elem_id):
        return self.element_ledger.remove_element(elem_id)

    def add_element(self, block_id, nodelist):
        return self.element_ledger.add_element(block_id, nodelist)

    def skin_element_block(self, block_id, skin_id, skin_name, tri='shell'):
        unique_faces = self.element_ledger.skin_block(block_id, tri)
        el_list = []
        face_list = []
        df = []
        for i in unique_faces:
            e, f = i
            el_list.append(e)
            face_list.append(f)
        self.sideset_ledger.add_sideset(el_list, face_list, skin_id, skin_name, df)

    def skin(self, skin_id, skin_name, tri='shell'):
        el_list, face_list = self.element_ledger.skin(tri)
        df = []
        self.sideset_ledger.add_sideset(el_list, face_list, skin_id, skin_name)


    def write(self, path):
        """
        Write from the ledger
        :return: None
        """
        if self.ex.mode == 'w':
            self.w_write()
        elif self.ex.mode == 'a':
            if path is None:
                raise OSError("no path specified")
            self.a_write(path)

    def w_write(self):
        if 'len_name' not in self.ex.data.dimensions:
            self.ex.data.createDimension('len_name', self._MAX_NAME_LENGTH + 1)
        if 'four' not in self.ex.data.dimensions:
            self.ex.data.createDimension('four', 4)

        # QA records
        num_qa_rec = 1
        self.ex.data.createDimension('num_qa_rec', num_qa_rec)
        var = self.ex.data.createVariable('qa_records', '|S1', (DIM_NUM_QA, DIM_FOUR, DIM_STRING_LENGTH))
        qa = np.empty((num_qa_rec, 4, self.ex.max_allowed_name_length + 1), '|S1')  # add 1 for null terminator
        qa[0] = util.generate_qa_rec(self.ex.max_string_length)
        var[:] = qa

        self.nodeset_ledger.write_dimensions(self.ex.data)
        self.nodeset_ledger.write_variables(self.ex.data)
        self.sideset_ledger.write_dimensions(self.ex.data)
        self.sideset_ledger.write_variables(self.ex.data)
        self.element_ledger.write_dimensions(self.ex.data)
        self.element_ledger.write_variables(self.ex.data)

    def a_write(self, path):
        out = nc.Dataset(path, "w", clobber=False, format="NETCDF4")
        old = self.ex.data

        out.setncatts(old.__dict__)

        # copy dimensions
        for dimension in old.dimensions.keys():

            # ignore dimensions that will be written by ns ledger
            if dimension == "num_node_sets" or dimension[:10] == "num_nod_ns":
                continue
            # ignore dimensions that will be written by ss ledger
            if dimension == "num_side_sets" or dimension[:11] == "num_side_ss" or dimension[:9] == "num_df_ss"  or dimension[:12] == "num_sset_var":
                continue

            # ignore dimensions that will be written by elem ledger
            if dimension == "num_elem" or dimension == "num_el_blk" or dimension[:13] == "num_el_in_blk" \
                    or dimension[:14] == "num_nod_per_el" or dimension == "num_elem_var":
                continue

            # ignore for updating QA records
            if dimension == 'num_qa_rec':
                continue

            out.createDimension(dimension, old.dimensions[dimension].size)
            
        if 'len_name' not in out.dimensions:
            out.createDimension('len_name', self._MAX_NAME_LENGTH + 1)

        if 'len_string' not in out.dimensions:
            out.createDimension('len_string', self._MAX_STR_LENGTH + 1)

        if 'len_line' not in out.dimensions:
            out.createDimension('len_line', self._MAX_LINE_LENGTH + 1)

        self.nodeset_ledger.write_dimensions(out)
        self.sideset_ledger.write_dimensions(out)
        self.element_ledger.write_dimensions(out)

        # copy variables
        for var in old.variables:

            # ignore variables that will be written by ns ledger
            if var[:3] == "ns_" or var[:7] == "node_ns" \
                    or var[:12] == "dist_fact_ns":
                continue

            # ignore variables that will be written by ss ledger
            if var[:3] == "ss_" or var[:7] == "side_ss" or var[:7] == "elem_ss" or var[:12] == "dist_fact_ss"\
                or var[:13] == "vals_sset_var" or var[:13] == "name_sset_var" or var[:12] == "sset_var_tab":
                continue

            #TODO -> elem_map is not for IDs
            # ignore variables that will be written by elem ledger
            if var[:3] == "eb_" or var == "elem_map" or var[:7] == "connect" or var == "elem_num_map" \
                    or var == "name_elem_var" or var[:13] == "vals_elem_var" or var == "elem_var_tab":
                continue

            if var == 'qa_records':
                continue

            var_data = old[var]

            # variable creation data
            varname = var_data.name
            datatype = var_data.dtype
            dimensions = var_data.dimensions
            out.createVariable(varname, datatype, dimensions)
            out[varname].setncatts(old[varname].__dict__)
            out[varname][:] = old[var][:]

        
        # QA records
        num_qa_rec = self.ex.num_qa + 1
        out.createDimension(DIM_NUM_QA, num_qa_rec)
        out.createVariable(VAR_QA, '|S1', (DIM_NUM_QA, DIM_FOUR, DIM_STRING_LENGTH))
        qa = np.empty((num_qa_rec, 4, self.ex.max_string_length + 1), '|S1')  # add 1 for null terminator
        qa[0:self.ex.num_qa] = old.variables[VAR_QA][:]
        qa[-1] = util.generate_qa_rec(self.ex.max_string_length)
        out['qa_records'][:] = qa

        self.nodeset_ledger.write_variables(out)
        self.sideset_ledger.write_variables(out)
        self.element_ledger.write_variables(out)
        out.close()
