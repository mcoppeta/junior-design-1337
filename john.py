from exodus import Exodus


ex = Exodus('sample-files/cube_with_data.exo', 'a')
ex.close()

ex2 = Exodus('sample-files/cube_with_data.exo', 'r')
