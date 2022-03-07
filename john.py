from exodus import Exodus

ex = Exodus('sample-files/can.ex2', 'a')
print(type(ex.get_node_set(1)))