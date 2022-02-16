from exodus import Exodus

if __name__ == "__main__":
    ex = Exodus("sample-files/cube_1ts_mod.e", 'r')
    ex2 = Exodus("sample-files/w/cube_xmerge.ex2", 'r')
    ex.diff(ex2)
    ex.close()
    ex2.close()

