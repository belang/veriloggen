from __future__ import absolute_import
from __future__ import print_function
import os
import sys
import collections
import copy
import re

import veriloggen.core.vtypes as vtypes
import veriloggen.core.function as function
import veriloggen.core.task as task
import veriloggen.core.rename_visitor as rename_visitor
import veriloggen.core.module as module

class Package(module.Module):
    """ Verilog Package class """

    def __init__(self, name=None, tmp_prefix='_tmp'):
        super(Package, self).__init__(name, tmp_prefix)

