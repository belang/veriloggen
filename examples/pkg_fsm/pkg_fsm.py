from __future__ import absolute_import
from __future__ import print_function
import sys
import os

# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from veriloggen import *

def pkgFSM():
    pkg = Package('fsm_pkg')
    st = pkg.StructType('counter_t')
    st.Logic('counter1', 12, value=5)
    return pkg

def fsm():
    fsm = Module('fsm')
    fsm.Import('fsm_pkg', 'counter_t')
    fsm.Input('clk', 1)     # TODO: fsm.clock('clk') with default; with no name to remove
    rst_n = fsm.Input('rst_n', 1)   # TODO: fsm.reset('rst_n')
    fsm.Input('i_en', 1)
    o_state = fsm.Output('o_state', 8)

    enum = fsm.ENUMType('state_e')
    enum.sigtype('logic', 3)
    enum.namedecl('IDLE')
    enum.namedecl('ST1')
    enum.namedecl('ST2')
    enum.namedecl('ST3')
    enum.namedecl('OTHER')

    fsm_cs = fsm.Usertype('state_e', 'fsm_cs')
    fsm_ns = fsm.Usertype('state_e', 'fsm_ns')
    counter1 = fsm.Usertype('counter_t', 'counter1')
    counter2 = fsm.Logic('counter2', 4)
    counter3 = fsm.Logic('counter3', 4)

    fsm.AlwaysFF(scope='update_state')(
        If(Not(rst_n))(
            fsm_cs(0)
        ).Else(
            fsm_cs(fsm_ns)
        )
    )

    fsm.AlwaysFF(scope='update_counter')(
        If(Not(rst_n))(
            counter1(0),
            counter2('10'),
            counter3(0)
        ).Else(
            If(fsm_cs == 'ST1')(counter1(counter1+1)),
            If(fsm_cs == 'ST2')(counter2(counter2+1)),
            If(fsm_cs == 'ST3')(counter3(counter3+1))
        )
    )

    fsm.AlwaysComb(scope='func_state')(
        Case(fsm_cs)(
            When('IDLE')(fsm_ns('ST2')),
            When('ST1')(If(counter1 == 100)(fsm_ns('ST2'))),
            When('ST2')(If(counter2 ==  10)(fsm_ns('ST3'))),
            When('ST3')(If(counter2 ==   8)(fsm_ns('ST3'))),
            When()(fsm_ns('OTHER'))
        )
    )

    o_state.assign(fsm_cs)
    return fsm


if __name__ == '__main__':
    #test = mkTest()
    test = pkgFSM()
    verilog = test.to_verilog('tmp.v')
    print(verilog)
    test = fsm()
    verilog = test.to_verilog('tmp.v')
    print(verilog)
