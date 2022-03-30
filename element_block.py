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
		self.valid = True # will be useful for functionality to remove element blocks (helps retain position in self.blocks)

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

	def invalidate(self):
		self.valid = False
		self.num_el_in_blk = 0

	# Add element to this block
	def add_element(self, nodelist, ex):
		if len(nodelist) != self.num_nod_per_el:
			raise ValueError("The given nodelist contains {} nodes when element of type {} requires {}".format(len(nodelist), self.elem_type, self.num_nod_per_el))

		if nodelist in self.elements.tolist():
			raise ValueError("The given nodelist already exists in this block")

		if len(nodelist) != len(set(nodelist)):
			raise ValueError("The same node is used more than once in the provided nodelist")

		el = self.elements.tolist()
		el.append(nodelist)
		self.elements = np.array(el)

		self.num_el_in_blk += 1

		for variable in self.variables:
			data = self.variables[variable].tolist()
			for row in range(len(data)):
				data[row].append(0)
			self.variables[variable] = np.array(data)
