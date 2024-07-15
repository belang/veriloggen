from __future__ import absolute_import
from __future__ import print_function
import sys
import os

# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from veriloggen import *

def pkgFSM():
    pkg = Packge('fsm_pkg')
    cn1 = pkg.Logic('counter1', 12)
    cn2 = pkg.Logic('counter2',  8)
    cn3 = pkg.Logic('counter3',  2)
    pkg.StuctType([cn1, cn2, cn3])

if __name__ == '__main__':
    #test = mkTest()
    test = pkgFSM
    verilog = test.to_verilog('tmp.v')
    print(verilog)
