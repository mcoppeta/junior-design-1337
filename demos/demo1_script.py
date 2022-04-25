import exodusutils as eu
from exodusutils.ledger import Ledger

if __name__ == "__main__":
    ex = eu.Exodus("sample-files/cube_1ts_mod.e", 'r')
    ledger = Ledger(ex)
    ledger.merge_nodesets(4444, 1, 2, True)
    ledger.write("sample-files/w/cube_xmerge.ex2")
    ex.close()