from __future__ import absolute_import
from __future__ import print_function
import sys
import os

# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

from veriloggen import *
import veriloggen.thread as vthread
import veriloggen.types.axi as axi
import veriloggen.types.util as util


def mkLed():
    m = Module('blinkled')
    clk = m.Input('CLK')
    rst = m.Input('RST')

    datawidth = 32
    addrwidth = 10
    myaxi = vthread.AXIM(m, 'myaxi', clk, rst, datawidth)
    ram_a = vthread.RAM(m, 'ram_a', clk, rst, datawidth, addrwidth)
    ram_b = vthread.RAM(m, 'ram_b', clk, rst, datawidth, addrwidth)
    ram_c = vthread.RAM(m, 'ram_c', clk, rst, datawidth, addrwidth)

    strm = vthread.Stream(m, 'mystream', clk, rst)
    cnt1 = strm.Counter()
    cnt2 = strm.Counter(initval=1)
    cnt3 = strm.Counter(initval=2, size=5)
    cnt4 = strm.Counter(initval=3, interval=3)
    cnt5 = strm.Counter(initval=4, interval=3, size=7)
    cnt6 = strm.Counter(initval=4, step=2, interval=2)
    a = strm.source('a')
    b = strm.source('b')
    c = a + b - a - b + cnt1 + cnt2 + cnt3 + cnt4 + cnt5 + cnt6
    strm.sink(c, 'c')

    # add a stall condition
    count = m.Reg('count', 4, initval=0)
    seq = Seq(m, 'seq', clk, rst)
    seq(
        count.inc()
    )

    util.add_disable_cond(strm.oready, 1, count == 0)

    def comp_stream(size, offset):
        strm.set_source('a', ram_a, offset, size)
        strm.set_source('b', ram_b, offset, size)
        strm.set_sink('c', ram_c, offset, size)
        strm.run()
        strm.join()

    def comp_sequential(size, offset):
        cnt = 0
        for i in range(size):
            cnt1 = cnt
            cnt2 = 1 + cnt
            cnt3 = (cnt + 2) % 5
            cnt4 = (cnt // 3) + 3
            cnt5 = ((cnt // 3) + 4) % 7
            cnt6 = (cnt // 2) * 2 + 4
            a = ram_a.read(i + offset)
            b = ram_b.read(i + offset)
            sum = a + b - a - b + cnt1 + cnt2 + cnt3 + cnt4 + cnt5 + cnt6
            ram_c.write(i + offset, sum)
            cnt += 1

    def check(size, offset_stream, offset_seq):
        all_ok = True
        for i in range(size):
            st = ram_c.read(i + offset_stream)
            sq = ram_c.read(i + offset_seq)
            if vthread.verilog.NotEql(st, sq):
                all_ok = False
        if all_ok:
            print('# verify: PASSED')
        else:
            print('# verify: FAILED')

    def comp(size):
        # stream
        offset = 0
        myaxi.dma_read(ram_a, offset, 0, size)
        myaxi.dma_read(ram_b, offset, 512, size)
        comp_stream(size, offset)
        myaxi.dma_write(ram_c, offset, 1024, size)

        # sequential
        offset = size
        myaxi.dma_read(ram_a, offset, 0, size)
        myaxi.dma_read(ram_b, offset, 512, size)
        comp_sequential(size, offset)
        myaxi.dma_write(ram_c, offset, 1024 * 2, size)

        # verification
        check(size, 0, offset)

        vthread.finish()

    th = vthread.Thread(m, 'th_comp', clk, rst, comp)
    fsm = th.start(32)

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

    memory = axi.AxiMemoryModel(m, 'memory', clk, rst, memimg_name=memimg_name)
    memory.connect(ports, 'myaxi')

    uut = m.Instance(led, 'uut',
                     params=m.connect_params(led),
                     ports=m.connect_ports(led))

    # vcd_name = os.path.splitext(os.path.basename(__file__))[0] + '.vcd'
    # simulation.setup_waveform(m, uut, dumpfile=vcd_name)
    simulation.setup_clock(m, clk, hperiod=5)
    init = simulation.setup_reset(m, rst, m.make_reset(), period=100)

    init.add(
        Delay(1000000),
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
