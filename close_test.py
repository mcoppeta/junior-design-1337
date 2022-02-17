import numpy as np
from netCDF4 import Dataset
from exodus import Exodus

ex = Exodus('sample-files/w/close.ex2','w', clobber=True)
ex.add_nodeset(np.array([1,2,3]), 10)
ex.write()
ex.close()
ex.close()

data = Dataset('sample-files/w/close.ex2','r')
print(data)