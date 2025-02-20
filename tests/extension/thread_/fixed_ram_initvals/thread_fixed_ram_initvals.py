from __future__ import absolute_import
from __future__ import print_function
import sys
import os

# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from veriloggen import *
import veriloggen.thread as vthread


def mkLed():
    m = Module('blinkled')
    clk = m.Input('CLK')
    rst = m.Input('RST')

    datawidth = 32
    addrwidth = 10
    numports = 1
    initvals = [i * 0.5 + 10 for i in range(2 ** addrwidth - 100)]
    myram = vthread.FixedRAM(m, 'myram', clk, rst, datawidth, addrwidth,
                             point=8, numports=numports, initvals=initvals)

    def blink(times):
        all_ok = True

        for i in range(times):
            rdata = myram.read(i)
            print('rdata = %f' % rdata)
            expected = (vthread.fixed.cast_to_fixed(i, 8) * vthread.fixed.FixedConst(0.5, 8) +
                        vthread.fixed.FixedConst(10, 8))
            if vthread.verilog.NotEql(rdata, expected):
                all_ok = False

        write_sum = vthread.fixed.FixedConst(0, 8)
        for i in range(times):
            rdata = myram.read(i)

            b = vthread.fixed.FixedConst(0.25, 8)
            wdata = rdata + b
            myram.write(i, wdata)
            write_sum += wdata
            print('wdata = %f' % wdata)

        print('write_sum = %d (%f)' % (write_sum.int_part, write_sum))

        read_sum = vthread.fixed.FixedConst(0, 8)
        for i in range(times):
            rdata = myram.read(i)
            print('rdata = %f' % rdata)
            read_sum += rdata
            expected = (vthread.fixed.cast_to_fixed(i, 8) * vthread.fixed.FixedConst(0.5, 8) +
                        vthread.fixed.FixedConst(10, 8) + vthread.fixed.FixedConst(0.25, 8))
            if vthread.verilog.NotEql(rdata, expected):
                all_ok = False

        print('read_sum = %d (%f)' % (read_sum.int_part, read_sum))

        if vthread.verilog.NotEql(read_sum, write_sum):
            all_ok = False

        if all_ok:
            print('# verify: PASSED')
        else:
            print('# verify: FAILED')

    th = vthread.Thread(m, 'th_blink', clk, rst, blink)
    fsm = th.start(10)

    return m


def mkTest(memimg_name=None):
    m = Module('test')

    # target instance
    led = mkLed()

    # copy paras and ports
    params = m.copy_params(led)
    ports = m.copy_sim_ports(led)

    clk = ports['CLK']
    rst = ports['RST']

    uut = m.Instance(led, 'uut',
                     params=m.connect_params(led),
                     ports=m.connect_ports(led))

    # vcd_name = os.path.splitext(os.path.basename(__file__))[0] + '.vcd'
    # simulation.setup_waveform(m, uut, dumpfile=vcd_name)
    simulation.setup_clock(m, clk, hperiod=5)
    init = simulation.setup_reset(m, rst, m.make_reset(), period=100)

    init.add(
        Delay(10000),
        Systask('finish'),
    )

    return m


def run(filename='tmp.v', simtype='iverilog', outputfile=None):

    if outputfile is None:
        outputfile = os.path.splitext(os.path.basename(__file__))[0] + '.out'

    memimg_name = 'memimg_' + outputfile

    test = mkTest(memimg_name=memimg_name)

    if filename is not None:
        test.to_verilog(filename)

    sim = simulation.Simulator(test, sim=simtype)
    rslt = sim.run(outputfile=outputfile)

    return rslt


if __name__ == '__main__':
    rslt = run(filename='tmp.v')
    print(rslt)
