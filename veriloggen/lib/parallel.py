from __future__ import absolute_import
import os
import sys
import collections
import functools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import vtypes

class Parallel(vtypes.VeriloggenNode):
    """ Parallel Assignment Manager """
    def __init__(self, m, name):
        self.m = m
        self.name = name
        
        self.body = []
        self.delay_amount = 0
        self.delayed_body = collections.defaultdict(list)
        self.tmp_count = 0

    #---------------------------------------------------------------------------
    def add_delayed_cond(self, statement, delay):
        prev = statement
        for i in range(delay):
            tmp_name = '_'.join(['', self.name, 'cond', 
                                 str(delay), str(self.tmp_count)])
            self.tmp_count += 1
            tmp = self.m.Reg(tmp_name, initval=0)
            self.add(tmp(prev), delay=i)
            prev = tmp
        return prev
    
    #---------------------------------------------------------------------------
    def add_delayed_subst(self, subst, delay):
        if not isinstance(subst, vtypes.Subst):
            return subst
        left = subst.left
        right = subst.right
        if isinstance(right, (int, float, str, vtypes._Constant, vtypes._ParameterVairable)):
            return subst
        width = left.bit_length()
        prev = right
        name_prefix = ('_' + left.name if isinstance(left, vtypes._Variable) else
                       '_' + self.name + '_sbst')
        for i in range(delay):
            tmp_name = '_'.join([name_prefix,
                                 str(delay), str(self.tmp_count)])
            self.tmp_count += 1
            tmp = self.m.Reg(tmp_name, width, initval=0)
            self.add(tmp(prev), delay=i)
            prev = tmp
        return left(prev)
    
    #---------------------------------------------------------------------------
    def add(self, *statement, **kwargs):
        for k in kwargs.keys():
            if k not in ('keep', 'delay', 'cond', 'lazy_cond', 'eager_val'):
                raise NameError('Keyword argument %s is not supported.' % k)
            
        keep = kwargs['keep'] if 'keep' in kwargs else None
        delay = kwargs['delay'] if 'delay' in kwargs else None
        cond = kwargs['cond'] if 'cond' in kwargs else None
        lazy_cond = kwargs['lazy_cond'] if 'lazy_cond' in kwargs else False
        eager_val = kwargs['eager_val'] if 'eager_val' in kwargs else False
        
        if keep is not None:
            del kwargs['keep']
            for i in range(keep):
                kwargs['delay'] = i if delay is None else delay + i
                self.add(*statement, **kwargs)
            return self
        
        if delay is not None and delay > 0:
            if eager_val:
                statement = [ self.add_delayed_subst(s, delay) for s in statement ]
            if cond is not None:
                if not lazy_cond:
                    cond = self.add_delayed_cond(cond, delay)
                statement = [ vtypes.If(cond)(*statement) ]
            self.delayed_body[delay].extend(statement)
            return self
            
        if cond is not None:
            statement = [ vtypes.If(cond)(*statement) ]
            
        self.body.extend(statement)
        return self

    #---------------------------------------------------------------------------
    def make_code(self):
        ret = []
        
        for delay, body in sorted(self.delayed_body.items(), key=lambda x:x[0],
                                  reverse=True):
            ret.extend(body)
            
        ret.extend(self.body)
        return tuple(ret)
    
    #---------------------------------------------------------------------------
    def make_always(self, clk, rst, reset=(), body=()):
        self.m.Always(vtypes.Posedge(clk))(
            vtypes.If(rst)(
                reset,
                self.m.make_reset()
            )(
                body,
                self.make_code()
            ))
    
    #---------------------------------------------------------------------------
    def __call__(self, *statement):
        return self.add(*statement)
