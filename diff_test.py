from exodus import Exodus

if __name__ == "__main__":
    ex = Exodus("sample-files/cube_1ts_mod.e", 'r')
    
    ex.close()