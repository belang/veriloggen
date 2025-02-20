from __future__ import absolute_import
from __future__ import print_function

import os
import veriloggen
import thread_multibank_ram_dma_packed_narrow


def test(request):
    veriloggen.reset()

    simtype = request.config.getoption('--sim')

    rslt = thread_multibank_ram_dma_packed_narrow.run(filename=None, simtype=simtype,
                                                      outputfile=os.path.splitext(os.path.basename(__file__))[0] + '.out')

    verify_rslt = [line for line in rslt.splitlines() if line.startswith('# verify:')][0]
    assert(verify_rslt == '# verify: PASSED')
