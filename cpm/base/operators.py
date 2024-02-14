#######################
# IMPORT DEPENDENCIES #
#######################

import pandas as pd
import math, os, json, inspect
from collections import OrderedDict
from cpm.base.references import Reference, ReferenceError


#######################
# DEFINE BASE CLASSES #
#######################

class FuncOperator(object):
    """
    Function operator class.
    """
    def __init__(self, func=None, name=None, parent=None, limits=None, 
                 refs=None, values=None, comp=None, astype=None, 
                 callbacks=None, suffix=None, *args, **kwargs):
        # Validate inputs
        self.func = func
        self.name = name
        self.suffix = suffix
        self._parent = parent
        self._astype = astype
        self.limits = limits
        self.callbacks = callbacks
        # Validate kwarg values
        if values is None:
            self._values = {}
        elif isinstance(values, dict):
            self._values = values
        else:
            raise TypeError("Function values must be passed as a dictionary \
of function kwargs and lists of valid argument values.")
        # Validate output keys
        if comp is None:
            self._comp = {}
        elif isinstance(comp, dict):
            self._comp = comp
        else:
            raise TypeError("Function composition must be passed as a \
dictionary of output keys and composition values.")
        self.refs = refs

    def __call__(self, *args, **kwargs):
        # Validate function inputs
        for key, arg in kwargs.items():
            # Enforce limits
            try:
                limit = self.limits[key]
                if (arg < limit[0]) or (arg > limit[1]):
                    raise ValueError(f"Keyword argument {key}={arg} \
outside limits of model {limit}.")
            except KeyError:
                pass
            # Enforce valid values
            try:
                value = self.values[key]
                if not arg in value:
                    raise ValueError(f"Keyword argument {key}='{arg}' \
is invalid; must be one of {', '.join([str(x) for x in value])}.")
            except KeyError:
                pass

#        # Perform reference operation
#        ref_kwargs = {}
#        for ref, inject in self.refs.items():
#            try:
#                reference = self.parent.refs[self.parent.refs.index(ref)]
#            except ValueError:
#                raise ReferenceError(f"Requested reference {ref} is not "
#                    "present within the defined model.")
#            out = reference.retrieve(**kwargs, **inject)
#            if isinstance(out, dict):
#                ref_kwargs = {**ref_kwargs, **out}
#            else:
#                raise TypeError()

        # Perform callbacks to references and update kwargs
#        all_kwargs = {**kwargs, **ref_kwargs}
        all_kwargs = {**kwargs}
        for callback in self._callbacks:
            all_kwargs = {**all_kwargs, **callback(**all_kwargs)}

        # Perform function operation
        try:
            res = self.func(*args, **all_kwargs)
            if self._astype is None:
                res = ResOperator(res, self)
            else:
                res = self._astype(res)
        except TypeError:
            raise ValueError(f"Unable to evaluate element {self.name}. "
                             "One or more required keyword arguments may be "
                             "missing.")
        return res
    
    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return hash(self) == hash(other)
        
    @property
    def func(self):
        return self._func

    @func.setter
    def func(self, func):
        # Validate callable function
        if not callable(func):
            raise ValueError("Input operator function must be callable.")
        self._func = func

    @property
    def callbacks(self):
        return self._callbacks
    
    @callbacks.setter
    def callbacks(self, funcs):
        # Validate callable functions
        if funcs is None:
            funcs = []
        elif not isinstance(funcs, list):
            raise TypeError("Input callback functions must be list of "
                            "callables.")
        for func in funcs:
            if not callable(func):
                raise ValueError("Input callback functions must be callable.")
        self._callbacks = funcs
    
    @property
    def name(self):
        return f'{self._name}{self._suffix}'

    @name.setter
    def name(self, label):
        if label is None:
            label = self._func.__name__
        self._name = label

    @property
    def suffix(self):
        return self._suffix

    @suffix.setter
    def suffix(self, label):
        if label is None:
            label = ''
        self._suffix = label
    
    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, obj):
        self._parent = obj
    
    @property
    def limits(self):
        return self._limits

    @limits.setter
    def limits(self, data):
        # Validate kwarg limits
        if data is None:
            self._limits = {}
        elif isinstance(data, dict):
            self._limits = data
        else:
            raise TypeError(
                "Function limits must be passed as a dictionary of function "
                "kwargs and two-element tuples of inclusive range values."
            )
    
    @property
    def values(self):
        return self._values
    
    @property
    def comp(self):
        return self._comp
    
    @property
    def refs(self):
        return self._refs

    @refs.setter
    def refs(self, data):
        # Validate references
        if isinstance(data, dict):
            pass
        elif data is None:
            data = {}
        elif isinstance(data, str):
            data = {data:{}}
        elif isinstance(data, list):
            data = {ref:{} for ref in data}
        else:
            raise TypeError(
                "Function references must refer to references which exist in "
                "the parent model and must be provided as a list of reference "
                "strings or a dictionary of reference strings and associated "
                "reference kwargs."
            )
        self._refs = data

    @property
    def kwargs(self):
        try:
            kwargs = self.func.kwargs
        except AttributeError:
            kwargs = self.func.__code__.co_varnames[\
                :self.func.__code__.co_argcount]
        return kwargs

    @property
    def code(self):
        return inspect.getsource(self.func)

    def inspect(self):
        print(self.code)
        

class ResOperator(float):
    """
    Function result operator class for managing FuncOperator numerical outputs.
    """
    def __new__(cls, value, *args, **kwargs):
        return super().__new__(cls, value)

    def __init__(self, value=None, parent=None, *args, **kwargs):
        # Validate input
        self._value = float(value)
        if isinstance(parent, FuncOperator):
            self._parent = parent
        else:
            raise TypeError("Parent class must be subclass of FuncOperator.")

    def __repr__(self):
        return f'<ResOperator.value = {self}>'

    def __str__(self):
        return str(self.value)

    @property
    def value(self):
        return self._value

    @property
    def parent(self):
        return self._parent

    @property
    def keys(self):
        return self.parent.keys

    @property
    def comp(self):
        return self.parent.comp

    def modify(self, value):
        return ResOperator(value, self.parent)

    def current_ref(self, ref=None):
        """
        """
        return ref.retrieve(**self.comp)

    def convert(self, ref=None, comp=None):
        """
        Convert the result value from its current composition to another using 
        the provided reference.

        Parameters
        ----------
        ref : str or Reference
            If provided as a string, must be a valid ID string of the parent 
            model's list of References. If provided as a Reference, must be 
            compatible with the ResOperator's own composition.
        """
        # Validate input reference
        if isinstance(ref, Reference):
            pass
        elif isinstance(ref, str):
            # Get valid references from parent FuncOperator's parent Model
            refs = self.parent.parent.refs
            try:
                ref = refs[refs.index(ref)]
            except ValueError:
                raise ValueError("Provided reference ID string is invalid.")

        # Validate current composition
        try:
            fr = self.current_ref(ref=ref)
        except:
            raise ValueError("ResOperator's composition is not compatible with \
the provided conversion reference.")

        # Validate future composition
        try:
            to = ref.retrieve(**comp)
        except:
            raise ValueError("Requested composition is not compatible with \
the provided conversion reference.")

        # If from and to compositions validate, perform conversion
        modified = self.modify(self.value * (to/fr))
        return modified
