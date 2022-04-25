from exodusutils.exodus import Exodus

if __name__ == '__main__':
    ex = Exodus("sample-files/biplane.exo", 'r')
    ex.close()
