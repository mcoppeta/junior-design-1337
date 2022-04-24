from abc import ABC, abstractmethod

# All implemented class require self.type, self.num_nodes, and self.face_map
class ElementType(ABC):
	@abstractmethod
	def __init__(self):
		pass

	def list_to_indices(self, l):
		newL = []
		for i in l:
			newL.append(i - 1)
		return newL

	def iterate_element_faces(self, element):
		if len(element) != self.num_nodes:
			raise TypeError("Element type {} should have {} nodes, but {} nodes found in element {}"
				.format(self.type, self.num_nodes, len(element), element))

		faces = []
		for face_no in range(1, len(self.face_map) + 1):
			indices = self.list_to_indices(self.face_map[face_no])
			new_face = []
			for ndx in indices:
				new_face.append(element[ndx])
			faces.append(new_face)
		return faces



class CIRCLE(ElementType):
	def __init__(self):
		self.type = "CIRCLE"
		self.num_nodes = 1
		self.face_map = {
			1: [1]
		}

class BAR2(ElementType):
	def __init__(self):
		self.type = "BAR2"
		self.num_nodes = 2
		self.face_map = {
			1: [1, 2]
		}

class BAR3(ElementType):
	def __init__(self):
		self.type = "BAR3"
		self.num_nodes = 3
		self.face_map = {
			1: [1, 2, 3]
		}

class QUAD4(ElementType):
	def __init__(self):
		self.type = "QUAD4"
		self.num_nodes = 4
		self.face_map = {
			1: [1, 2],
			2: [2, 3],
			3: [3, 4],
			4: [4, 1]
		}

# Assumes same ordering as QUAD4, overwrite here if not
class QUAD5(QUAD4):
	def __init__(self):
		super().__init__()
		self.type = "QUAD5"
		self.num_nodes = 5

class QUAD8(ElementType):
	def __init__(self):
		self.type = "QUAD8"
		self.num_nodes = 8
		self.face_map = {
			1: [1, 2, 5],
			2: [2, 3, 6],
			3: [3, 4, 7],
			4: [4, 1, 8]
		}

# Assumes same ordering as QUAD8, overwrite here if not
class QUAD9(QUAD8):
	def __init__(self):
		super().__init__()
		self.type = "QUAD9"
		self.num_nodes = 9

class SHELL4(ElementType):
	def __init__(self):
		self.type = "SHELL4"
		self.num_nodes = 4
		self.face_map = {
			1: [1, 2, 3, 4],
			2: [1, 4, 3, 2],
			3: [1, 2],
			4: [2, 3],
			5: [3, 4],
			6: [4, 1]
		}

class SHELL8(ElementType):
	def __init__(self):
		self.type = "SHELL8"
		self.num_nodes = 8
		self.face_map = {
			1: [1, 2, 3, 4, 5, 6, 7, 8],
			2: [1, 4, 3, 2, 8, 7, 6, 5],
			3: [1, 2, 5],
			4: [2, 3, 6],
			5: [3, 4, 7],
			6: [4, 1, 8]
		}

class SHELL9(ElementType):
	def __init__(self):
		self.type = "SHELL9"
		self.num_nodes = 9
		self.face_map = {
			1: [1, 2, 3, 4, 5, 6, 7, 8, 9],
			2: [1, 4, 3, 2, 8, 7, 6, 5, 9],
			3: [1, 2, 5],
			4: [2, 3, 6],
			5: [3, 4, 7],
			6: [4, 1, 8]
		}

class TRI3(ElementType):
	def __init__(self):
		self.type = "TRI3"
		self.num_nodes = 3
		self.face_map = {
			1: [1, 2],
			2: [2, 3],
			3: [3, 1]
		}

class TRI6(ElementType):
	def __init__(self):
		self.type = "TRI6"
		self.num_nodes = 6
		self.face_map = {
			1: [1, 2, 4],
			2: [2, 3, 5],
			3: [3, 1, 6]
		}

class TRISHELL3(ElementType):
	def __init__(self):
		self.type = "TRISHELL3"
		self.num_nodes = 3
		self.face_map = {
			1: [1, 2, 3],
			2: [1, 3, 2],
			3: [1, 2],
			4: [2, 3],
			5: [3, 1]
		}

class TRISHELL6(ElementType):
	def __init__(self):
		self.type = "TRISHELL6"
		self.num_nodes = 6
		self.face_map = {
			1: [1, 2, 3, 4, 5, 6],
			2: [1, 3, 2, 6, 5, 4],
			3: [1, 2, 4],
			4: [2, 3, 5],
			5: [3, 1, 6]
		}

class TETRA4(ElementType):
	def __init__(self):
		self.type = "TETRA4"
		self.num_nodes = 4
		self.face_map = {
			1: [1, 2, 4],
			2: [2, 3, 4],
			3: [1, 4, 3],
			4: [1, 3, 2]
		}

class TETRA10(ElementType):
	def __init__(self):
		self.type = "TETRA10"
		self.num_nodes = 10
		self.face_map = {
			1: [1, 2, 4, 5, 9, 8],
			2: [2, 3, 4, 6, 10, 9],
			3: [1, 4, 3, 8, 10, 7],
			4: [1, 3, 2, 7, 6, 5]
		}

class WEDGE6(ElementType):
	def __init__(self):
		self.type = "WEDGE6"
		self.num_nodes = 6
		self.face_map = {
			1: [1, 2, 5, 4],
			2: [2, 3, 6, 5],
			3: [1, 4, 6, 3],
			4: [1, 3, 2],
			5: [4, 5, 6]
		}

class WEDGE15(ElementType):
	def __init__(self):
		self.type = "WEDGE15"
		self.num_nodes = 15
		self.face_map = {
			1: [1, 2, 5, 4, 7, 11, 13, 10],
			2: [2, 3, 6, 5, 8, 12, 14, 11],
			3: [1, 4, 6, 3, 10, 15, 12, 9],
			4: [1, 3, 2, 9, 8, 7],
			5: [4, 5, 6, 13, 14, 15]
		}

# Assumes same ordering as WEDGE15, overwrite here if not
class WEDGE16(WEDGE15):
	def __init__(self):
		super().__init__()
		self.type = "WEDGE16"
		self.num_nodes = 16

class WEDGE20(ElementType):
	def __init__(self):
		self.type = "WEDGE20"
		self.num_nodes = 20
		self.face_map = {
			1: [1, 2, 5, 4, 7, 11, 13, 10, 20],
			2: [2, 3, 6, 5, 8, 12, 14, 11, 18],
			3: [1, 4, 6, 3, 10, 15, 12, 9, 19],
			4: [1, 3, 2, 9, 8, 7, 16],
			5: [4, 5, 6, 13, 14, 15, 17]
		}

# Assumes same ordering as WEDGE20, overwrite here if not
class WEDGE21(WEDGE20):
	def __init__(self):
		super().__init__()
		self.type = "WEDGE21"
		self.num_nodes = 21

class HEX8(ElementType):
	def __init__(self):
		self.type = "HEX8"
		self.num_nodes = 8
		self.face_map = {
			1: [1, 2, 6, 5],
			2: [2, 3, 7, 6],
			3: [3, 4, 8, 7],
			4: [1, 5, 8, 4],
			5: [1, 4, 3, 2],
			6: [5, 6, 7, 8]
		}

# Assumes same ordering as HEX8, overwrite here if not
class HEX9(HEX8):
	def __init__(self):
		super().__init__()
		self.type = "HEX9"
		self.num_nodes = 9

class HEX20(ElementType):
	def __init__(self):
		self.type = "HEX20"
		self.num_nodes = 20
		self.face_map = {
			1: [1, 2, 6, 5, 9, 14, 17, 13],
			2: [2, 3, 7, 6, 10, 15, 18, 14],
			3: [3, 4, 8, 7, 11, 16, 19, 15],
			4: [1, 5, 8, 4, 13, 20, 16, 12],
			5: [1, 4, 3, 2, 12, 11, 10, 9],
			6: [5, 6, 7, 8, 17, 18, 19, 20]
		}

class HEX27(ElementType):
	def __init__(self):
		self.type = "HEX27"
		self.num_nodes = 27
		self.face_map = {
			1: [1, 2, 6, 5, 9, 14, 17, 13, 26],
			2: [2, 3, 7, 6, 10, 15, 18, 14, 25],
			3: [3, 4, 8, 7, 11, 16, 19, 15, 27],
			4: [1, 5, 8, 4, 13, 20, 16, 12, 24],
			5: [1, 4, 3, 2, 12, 11, 10, 9, 22],
			6: [5, 6, 7, 8, 17, 18, 19, 20, 23]
		}

class PYRA5(ElementType):
	def __init__(self):
		self.type = "PYRA5"
		self.num_nodes = 5
		self.face_map = {
			1: [1, 2, 5],
			2: [2, 3, 5],
			3: [3, 4, 5],
			4: [4, 1, 5],
			5: [1, 4, 3, 2]
		}

class PYRA13(ElementType):
	def __init__(self):
		self.type = "PYRA13"
		self.num_nodes = 13
		self.face_map = {
			1: [1, 2, 5, 6, 11, 10],
			2: [2, 3, 5, 7, 12, 11],
			3: [3, 4, 5, 8, 13, 12],
			4: [4, 1, 5, 9, 10, 13],
			5: [1, 4, 3, 2, 9, 8, 7, 6]
		}

# Assumes same ordering as QUAD4, overwrite here if not
class PYRA14(PYRA13):
	def __init__(self):
		super().__init__()
		self.type = "PYRA14"
		self.num_nodes = 14




# Returns an object of type ElementType
# Needed for iterate_element_faces() method
def get_element_type(string, tri='shell'):
	# Takes in uppercase string of type
	# Returns (class, num faces)
	elem_types = {
		"CIRCLE": CIRCLE,
		"SPHERE": CIRCLE, #both 1 node
		"BEAM": BAR2,
		"BAR": BAR2, #???
		"BAR2": BAR2,
		"BAR3": BAR3,
		"QUAD": QUAD4, #Assumption
		"QUAD4": QUAD4,
		"QUAD5": QUAD5,
		"QUAD8": QUAD8,
		"QUAD9": QUAD9,
		"SHELL": SHELL4, #Assumption
		"SHELL4": SHELL4,
		"SHELL8": SHELL8,
		"SHELL9": SHELL9, 

		#"TRI": TRI3, #Assumption
		#"TRI3": TRI3,
		#"TRI6": TRI6,

		# TRI -> TRISHELL
		"TRI": TRISHELL3 if tri=='shell' else TRI3,
		"TRI3": TRISHELL3 if tri=='shell' else TRI3,
		"TRI6": TRISHELL6 if tri=='shell' else TRI6,

		"TRISHELL": TRISHELL3, #Assumption
		"TRISHELL3": TRISHELL3,
		"TRISHELL6": TRISHELL6,
		"TETRA": TETRA4,
		"TETRA4": TETRA4,
		"TETRA10": TETRA10,
		"WEDGE": WEDGE6, #Assumption
		"WEDGE6": WEDGE6,
		"WEDGE15": WEDGE15,
		"WEDGE16": WEDGE16,
		"WEDGE20": WEDGE20, # Assumption
		"WEDGE21": WEDGE21,
		"HEX": HEX8, #Assumption
		"HEX8": HEX8,
		"HEX9": HEX9,
		"HEX20": HEX20,
		"HEX27": HEX27,
		"PYRA": PYRA5, #Assumption
		"PYRA5": PYRA5,
		"PYRA13": PYRA13,
		"PYRA14": PYRA14
	}

	s = string.upper()
	if s in elem_types:
		return elem_types[s]()
	else:
		raise KeyError("{} is an unsupported element type".format(s))