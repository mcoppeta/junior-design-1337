from exodusutils import *

if __name__ == "__main__":
    ex = Exodus("sample-files/biplane.exo", 'r')
    # Output the propeller to a new file
    # EB: 34, 35, 36, 37, 38
    eb_sels = [ElementBlockSelector(ex, 1), ElementBlockSelector(ex, 3), ElementBlockSelector(ex, 4)]
    output_subset(ex, "sample-files/w/tail.exo", "Biplane Propeller", eb_sels, [], [], PropertySelector(ex))
    ex.close()

    ex = Exodus("sample-files/w/tail.exo", 'a')
    ex.skin(3312, 'Skinned Mesh')
    #ex.add_nodeset([1,2,3,4], 1, 'NS 01')
    ex.split_side_set_x_coords(3312, '>=', 0.849, True, 1111, 2222, False)
    ex.write("sample-files/w/tail-skinned.exo")
    ex.close()