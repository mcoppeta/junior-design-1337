import numpy as np

class ElementBlock:

	def __init__(self, blk_num, connect_title, status, blk_name, elem_type, num_nod_per_el, num_el_in_blk, elements, variables):
		self.blk_num = blk_num
		self.connect_title = connect_title
		self.status = status
		self.blk_name = blk_name
		self.elem_type = elem_type
		self.num_nod_per_el = num_nod_per_el
		self.num_el_in_blk = num_el_in_blk
		self.elements = elements
		self.variables = variables

	def get_num_elements(self):
		return self.num_el_in_blk

	def get_num_nodes_per_element(self):
		return self.num_nod_per_el

	def get_element(self, ndx):
		return self.elements[ndx]

	def get_status(self):
		return self.status

	def get_blk_num(self):
		return self.blk_num

	def get_connect_title(self):
		return self.connect_title

	def get_elem_type(self):
		return self.elem_type

