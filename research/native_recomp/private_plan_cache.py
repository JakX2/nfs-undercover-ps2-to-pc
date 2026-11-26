"""Opt-in, process-local memoization for pure private image analysis.

No files, serialization, shared cache or logs. Outside an explicit scope all
calls run normally. Cache keys require immutable image bytes and simple
immutable parameters; returned mutable structures are always independent.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from functools import wraps

_active=ContextVar('private_plan_cache',default=None)

@contextmanager
def plan_cache_scope(*,limit=96):
    if not 1<=limit<=128:raise ValueError('private plan cache limit')
    if _active.get() is not None:
        yield
        return
    cache={}
    token=_active.set((cache,limit))
    try:yield
    finally:
        cache.clear()
        _active.reset(token)

def memoized_plan(fn):
    @wraps(fn)
    def call(d,e,*args,**kwargs):
        active=_active.get()
        if active is None or type(d) is not bytes or type(e) is not bytes:
            return fn(d,e,*args,**kwargs)
        if any(type(x) not in (int,bool,str,type(None)) for x in (*args,*kwargs.values())):
            return fn(d,e,*args,**kwargs)
        cache,limit=active
        key=(fn,d,e,args,tuple(sorted(kwargs.items())))
        if key in cache:return deepcopy(cache[key])
        result=fn(d,e,*args,**kwargs)
        if len(cache)<limit:cache[key]=deepcopy(result)
        return result
    return call
