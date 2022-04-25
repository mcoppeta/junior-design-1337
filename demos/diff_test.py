from exodusutils import Exodus

if __name__ == "__main__":
    ex = Exodus("sample-files/cube_1ts_mod.e", 'r')
    ex2 = Exodus("sample-files/w/cube_xmerge.ex2", 'r')
    ex.diff(ex2)
    ex.diff_nodeset(4, ex2, 5)
    ex.close()
    ex2.close()

