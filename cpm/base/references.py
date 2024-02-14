#######################
# IMPORT DEPENDENCIES #
#######################

import pandas as pd
import math, os, json, itertools
from collections import OrderedDict


######################
# DEFINE CPM CLASSES #
######################


class ReferenceCollection(object):
    """
    Object class for managing model references.
    """

    def __init__(self, parent):
        self._parent = parent
        self._collection = OrderedDict()

    def __iter__(self):
        return iter(self.collection.values())

    def __getitem__(self, arg):
        return self.collection[arg]

    @property
    def parent(self):
        return self._parent

    @property
    def collection(self):
        return self._collection
    
    @property
    def num_references(self):
        return len(self._collection)

    @property
    def reference_names(self):
        """
        Return a list of the names of all layers within the collection.
        """
        return list(self.collection.keys())

    @property
    def references(self):
        """
        Return a list of all references within the collection.
        """
        return list(self.collection.values())

    def add_reference(self, obj, **kwargs):
        """
        Add a Reference class instance to the collection.
        """
        # Validate object class
        if isinstance(obj, (str, dict)):
            obj = Reference(obj, **kwargs)
        elif not isinstance(obj, Reference):
            raise ValueError(
                "Input object must be Reference class instance or valid input "
                "to class constructor."
            )
        self._collection[obj.name] = obj

    def _validate_query(self, data):
        """
        Validate an input reference string, list, or dictionary, converting it 
        to the standard query dictionary format.
        """
        # Enforce dictionary format
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
        # Enforce valid reference names
        for key in data.keys():
            if not key in self.collection:
                raise ValueError(
                    f"Reference name {key} does not exist in the collection. "
                    "Ensure that all required reference files are included "
                    "in the model folder."
                )
        # Return validate reference data
        return data

    def _create_callbacks(self, data):
        """
        Create a list of callback functions which will select each named 
        reference in the standard reference dictionary format and retrieve from 
        it when called using the provided kwargs and any additional kwargs 
        provided by the caller. Callbacks will be listed in the same order as 
        they appear in the reference collection.
        """
        # Validate input query data
        data = self._validate_query(data)
        # Iterate over reference dictionaries
        callbacks = []
        names = list(data.keys())
        for name, reference in self.collection.items():
            # Check if any references left
            if len(callbacks) == len(names):
                break
            # Check if the ordered reference is in the provided data
            elif not name in names:
                continue
            # Create function and add to list
            callbacks.append(ReferenceCallback(reference, data[name]))

        # Check if any missing references
        if len(callbacks) != len(names):
            missing = list(set(names) - set(self.reference_names))
            raise ValueError(
                f"Missing ({len(missing)}) references requested by the model "
                f"{missing}."
            )
            
        # Return list of functions
        return callbacks

    def _explode_multireference(self, data):
        """
        Take reference data with multiple level values and explode into a list 
        of single reference dictionaries.
        """
        # Validate input query data
        data = self._validate_query(data)
        # Identify all unique pairs of levels and values for each reference
        all_data = []
        for refname, sub_data in data.items():
            new_data = []
            for level, values in sub_data.items():
                # Coerce list of values
                if not isinstance(values, list):
                    values = [values]
                # Log value options
                new_data.append([{level: value} for value in values])

            # Convert unique pairs to list of reference data, return
            new_data = itertools.product(*new_data)
            new_data = \
                [{refname:{k:v for pair in pairs for k, v in pair.items()}} \
                 for pairs in new_data]
            all_data.append(new_data)
            
        # Combine across all references
        all_data = itertools.product(*all_data)
        all_data = [{k:v for pair in pairs for k, v in pair.items()} \
                    for pairs in all_data]

        # Determine reference data suffixes
        suffixes = []
        for sub_data in all_data:
            suffix = []
            for refname, reference in self.collection.items():
                try:
                    pairs = sub_data[refname]
                    for level in reference.levels:
                        try:
                            suffix.append(str(pairs[level]))
                        except:
                            continue
                except:
                    continue
            suffixes.append('_' + '_'.join(suffix))
        return all_data, suffixes


class ReferenceCallback(object):
    """
    Class for managing and performing callbacks to reference objects from 
    model elements during calls.
    """

    def __init__(self, target, data_kwargs):
        self.target = target
        self.data_kwargs = data_kwargs

    def __call__(self, **kwargs):
        return self.target.retrieve(**kwargs, **self.data_kwargs)

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, obj):
        if not isinstance(obj, Reference):
            raise ValueError("Input callback object must be Reference.")
        self._target = obj

    @property
    def data_kwargs(self):
        return self._data_kwargs

    @data_kwargs.setter
    def data_kwargs(self, obj):
        if not isinstance(obj, dict):
            raise ValueError("Input data_kwargs must be dict.")
        self._data_kwargs = obj

class Reference(object):
    """
    Class for loading, managing, and interacting with reference trees either in 
    nested dictionaries or in JSON-formatted model reference files, which can 
    be queried with a set of keyword arguments, returning a dictionary which 
    can be passed to a related model operator as keyword arguments. This class 
    is used within model files to define connections to reference files or 
    nested dictionaries, loading and preparing these materials at 
    initialization of the model.

    The required reference tree format is a dictionary including a list of 0+
    level names, a list of bottom-level keys, and a (nested) dictionary of
    reference data associated with the provided levels and keys. There must be
    an order of dictionary nesting within the data dictionary that is equal to 
    the number of levels, and the keys in the bottom-level dictionary must be 
    equal to the list of keys provided at the top level.

    Example reference tree:
    {
        "levels": ["colors","numbers"],
        "keys": ["a","b","c"],
        "data": {
            "blue": {
                "one": {
                    "a": 1,
                    "b": 2,
                    "c": 3
                },
                "two": {
                    "a": 11,
                    "b": 22,
                    "c": 33
                }
            },
            "lavender": {
                "one": {
                    "a": 4,
                    "b": 5,
                    "c": 6
                },
                "two": {
                    "a": 44,
                    "b": 55,
                    "c": 66
                }
            }
        }
    }

    When the reference is queried using the retrieve() method, provided kwargs
    will be used to step through the levels of the reference data, returning
    the bottom-level dictionary.

    If no levels are used, the reference can be queried with no kwargs and the 
    data dictionary associated with the reference keys will be returned.

    Parameters
    ----------
    obj : dict or str
        Reference tree as either a nested dictionary of the required format or 
        a JSON file which similarly follows the required format and which will 
        be loaded at initialization of the target model.
    name : str
        Name to be assigned to the class instance. When loading a JSON file, if 
        no name is provided, the filename will be used as the class instance 
        name.
    """
    
    def __init__(self, obj=None, name=None, **kwargs):
        if isinstance(obj, dict):
            self._obj = obj
            self._name = name
        elif isinstance(obj, str):
            ref = Reference.read_json(fp=obj, name=name, **kwargs)
            self.__init__(obj=ref.obj, name=ref.name)

    def __getitem__(self, args):
        # Validate input
        if isinstance(args, str):
            args = (args,)
        # Iterate over levels in order
        try:
            level = self.data
            for arg in args:
                level = level[arg]
        except:
            raise ReferenceError(f"Invalid reference keys for {self._name} "
                f"{args}.")
        return level

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return hash(self) == hash(other)
        
    @property
    def obj(self):
        return self._obj

    @property
    def name(self):
        return self._name

    @property
    def levels(self):
        return tuple(self.obj['levels'])

    @property
    def keys(self):
        return tuple(self.obj['keys'])

    @property
    def data(self):
        return self.obj['data']

    @property
    def domain(self):
        """
        Ordered dictionary of levels and valid key values to provide to the 
        reference operator.
        """
        # Iterate over key levels
        data = self.data
        domain = OrderedDict()
        for level in self.levels:
            domain[level] = list(data.keys())
            data = data[domain[level][0]]
        return domain

    @classmethod
    def read_json(cls, fp=None, name=None, *args, **kwargs):
        """
        Load a JSON file to use as a reference.
        """
        # Validate filepath
        fn, ext = os.path.splitext(os.path.basename(fp))
        if not ext.lower() == '.json':
            raise ValueError("Input filepath must be JSON file type.")
        # Validate ID
        if name is None:
            name = fn
        # Load JSON file in read-only
        try:
            with open(fp, mode='r') as f:
                obj = json.load(f)
        except:
            raise ValueError(f"Unable to read JSON reference file ({fp}).")
        # Generate Reference instance or child instance
        return cls(obj=obj, name=name)

    def retrieve(self, **kwargs):
        """
        Retrieve the output data from a reference using the input kwargs to 
        query the reference data tree.
        """
        # Get list of arguments to pass to item getter
        try:
            # Prepare slicing tuple
            args = tuple([str(kwargs[key]) for key in self.levels])
        except KeyError:
            raise KeyError(
                "Must provide arguments for all reference keywords in "
                f"reference {self.name}. {self.levels} required, "
                f"{tuple(kwargs.keys())} provided."
            )
        # Slice and return
        return self[args]

class ReferenceError(Exception):
    """
    Base exception class for reference errors
    """
    pass
