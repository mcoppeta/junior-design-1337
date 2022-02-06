from exodus import Exodus

# first open the file
ex = Exodus('sample-files/can copy.ex2', 'a')

# lets get all the nodes in element block 2, which is the square
ids = ex.get_nodes_in_elblock(2)

# add 8 to each y coordinate for every node in the square
#ex.edit_coords(ids, 'y', 8)  #This function has been removed

# close the file
ex.close()
