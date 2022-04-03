from exodus import Exodus


# This method skins the element block
def remove_elements_demo(path, path_out):
    ex = Exodus(path, 'a')

    # Skin cube
    ex.skin_element_block(1, 4, 'Skinned Block') # skins block 1, gives ID=4, sideset name 
    
    ex.write(path_out)
    ex.close()

# This method prints some information about the skinned mesh
# 1. The element IDs and face numbers
# 2. The number of sides in the skin
def review_changes(path):
    ex = Exodus(path, 'r')
    ss = ex.get_side_set(4)
    print(ss) # Gives element IDs in skin, and the corresponding mask is the corresponding face number

    print("\n\nNum sides:\t{}".format(len(ss[:][0]))) # 384 = length^3 which is expected
    
    ex.close()


if __name__ == "__main__":
    path = "sample-files/cube_1ts_mod.e"
    path_rev = "sample-files/demo4.e"

    skin_block(path, path_rev)
    review_changes(path_rev)


