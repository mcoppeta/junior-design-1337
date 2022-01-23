class Ledger:
    
    def __init__(self):
        self.size = 0
        self.dimension_map = {}
        self.variable_map = {}


    def addDimension(self, dim):
        self.dimension_map[dim.name] = dim



    def addVariable(self, var):
        self.variable_map[var.name] = var

    





