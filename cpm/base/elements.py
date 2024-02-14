#######################
# IMPORT DEPENDENCIES #
#######################

import pandas as pd
import numpy as np
import math, os, json, random
from collections import OrderedDict
from cpm.base.operators import FuncOperator, ResOperator


######################
# DEFINE CPM CLASSES #
######################


class LayerCollection(object):
    """
    Object class for managing model layers.
    """

    def __init__(self, parent):
        self._parent = parent
        self._collection = OrderedDict()

    def __iter__(self):
        return iter(self.collection.values())

    def __getitem__(self, arg):
        """
        Retrieve an element within the collection with the given name. If no 
        element is found, raise a KeyError.
        """
        return self.get_element(arg)

    @property
    def parent(self):
        return self._parent

    @property
    def collection(self):
        return self._collection
    
    @property
    def num_layers(self):
        return len(self._collection)

    @property
    def kwargs(self):
        """
        Return a list of kwargs required to evaluate all elements in all layers 
        within the collection, excluding recursive inputs.
        """
        return sorted(list(set(self.kwargs_all) - set(self.element_names)))

    @property
    def kwargs_all(self):
        """
        Return a list of kwargs required to evaluate all elements in all layers 
        within the collection, including recursive inputs.
        """
        kwargs = []
        for layer in self.collection.values():
            kwargs.extend(layer.kwargs)
        return list(set(kwargs))

    @property
    def layer_names(self):
        """
        Return a list of the names of all layers within the collection.
        """
        return list(self.collection.keys())

    @property
    def layers(self):
        """
        Return a list of all layers within the collection.
        """
        return list(self.collection.values())

    @property
    def element_names(self):
        """
        Return a list of the names of all elements in all layers within the 
        collection.
        """
        names = []
        for layer in self.collection.values():
            names.extend(layer.element_names)
        return list(set(names))

    @property
    def current_layer(self):
        """
        Return the most recently added layer. If no layers have been added,
        return None.
        """
        i = self.num_layers
        if i == 0:
            return None
        else:
            return self.layers[i-1]

    @property
    def elements(self):
        """
        Return a list of all unique elements in all layers within the 
        collection.
        """
        elements = []
        for layer in self.collection.values():
            elements.extend(layer.unsorted)
        return list(set(elements))

    @property
    def constraints(self):
        """
        Return a dictionary of constraint information for all elements within 
        the collection.

        Returns
        -------
        constraints : dict
            A dictionary defining constraint information for each element within 
            the collection, described in a tuple where the first value indicates 
            the type of constraint ('limits' or 'values') and the second value 
            indicates the constraint values. 
            - for limits, the constraint values will be a two-element tuple, 
              indicating the inclusive start and end values of the limits.
            - for values, the constraint values will define all feasible unique 
              values.
        """
        # Identify all model kwarg information
        constraints = {k:(None,None) for k in self.kwargs}
        for e in self.elements:
            # First account for numerical limits
            for k, l in e.limits.items():
                constraints[k] = ('limits', l)
            # Then account for unique values
            for k, v in e.values.items():
                constraints[k] = ('values', v)
        # Return populated dictionary
        return constraints

    def add_layer(self, name=None):
        """
        Add a new Layer class instance to the collection.

        Parameters
        ----------
        name : label
            A unique name for the new layer being created.
        """
        # Get layer index
        i = self.num_layers
        # Validate input
        if name is None:
            name = i
        if name in self.collection:
            raise ValueError("The provided layer name is already in use.")
        # Add new layer to collection
        self._collection[i] = Layer(parent=self.parent, name=name)

    def add_element(self, obj, layer=None, **kwargs):
        """
        Add a new element to the current layer or an indicated layer.

        Parameters
        ----------
        obj : Element subclass
            An object which is an subclass of Element, such as AF, SPF, or Sub, 
            which will be added to the current layer or an indicated layer if 
            a value is provided to the optional layer argument.
        layer : label, optional
            The name of the layer which the Element should be added to.
        """
        # Validate current layer
        if not self.num_layers:
            raise ValueError("No layers in collection. Create a layer using \
LayerCollection.add_layer().")
        # Select the correct layer
        if layer is None:
            select = self.current_layer
        else:
            try:
                select = self[layer]
            except KeyError:
                raise ValueError(f"Selected layer does not exist within the \
collection ({layer})")
        # Add the element to the selected layer
        select.add_element(obj)

    def evaluate(self, **kwargs):
        """
        Evaluate all elements in the collection, stepping through each layer in 
        order.
        """
        # Initialize evaluated kwargs
        evaluated = {**kwargs}
        # Iterate over layers and update kwargs
        for i, layer in self.collection.items():
            evaluated = {**evaluated, **layer.evaluate(**evaluated)}
        return evaluated

    def find_class(self, cls):
        """
        Get a list of all elements within the collection which are of the given 
        class type.
        """
        found = []
        for layer in self.collection.values():
            found.extend(layer[cls])
        return found

    def get_element(self, name):
        """
        Retrieve an element within the collection with the given name. If no 
        element is found, raise a KeyError.
        """
        # Search for the element
        for e in self.elements:
            if e.name == name:
                return e
            else:
                continue
        # If none is found, raise KeyError
        raise KeyError(f"No element found with the name '{name}'")

    def get_layer(self, name):
        """
        Retrieve a layer within the collection with the given name. If no 
        layer is found, raise a KeyError.
        """
        # Search for the layer
        for l in self.layers:
            if l.name == name:
                return l
            else:
                continue
        # If none is found, raise KeyError
        raise KeyError(f"No layer found with the name '{name}'")


class Layer(object):
    """
    Object class for a layer of model elements.
    """

    def __init__(self, parent, name=None):
        self._parent = parent
        self._name = name
        self._elements = {c.__name__:[] for c in self.subclasses()}

    def __getitem__(self, args):
        if issubclass(args, Element):
            return self.elements[args.__name__]
        elif isinstance(args, str):
            return self.elements[args]
        elif isinstance(args, tuple) and len(args) == 2:
            return self.find(args[1], cls=args[0])
        else:
            raise ValueError(f"Invalid argument ({args})")

    def __iter__(self):
        return iter(self.elements.values())

    @property
    def parent(self):
        return self._parent

    @property
    def name(self):
        return self._name

    @property
    def elements(self):
        return self._elements

    @property
    def unsorted(self):
        """
        Return a list of all elements within the layer without sorting by class 
        type.
        """
        elements = []
        for e in self.elements.values():
            elements.extend(list(e))
        return elements

    @property
    def kwargs(self):
        """
        Return a list of kwargs required to evaluate all elements in the layer.
        """
        # Retrieve kwargs for all elements and generate unique set
        kwargs = [set(e.kwargs) for e in self.unsorted \
            if not isinstance(e, Hidden)]
        kwargs = sorted(set().union(*kwargs) - set(self.element_names))
        return kwargs

    @property
    def element_names(self):
        """
        Return a list of the names of all elements in the layer.
        """
        names = sorted([e.name for e in self.unsorted])
        return names

    @staticmethod
    def subclasses():
        return Element.__subclasses__()
    
    @classmethod
    def subclassnames(cls):
        return [sc.__name__ for sc in cls.subclasses()]

    def add_element(self, obj):
        """
        Add the provided object to the collection.
        """
        # Validate input object type
        if not issubclass(obj.__class__, Element):
            raise TypeError(f"Input must be Element subtype ({type(obj)}).")
        # Add object to the collection
        self._elements[obj.__class__.__name__].append(obj)

    def find(self, name=None, cls=None):
        """
        Retrieve an element of a given name, with the option of providing a 
        class type to narrow the search.
        """
        # Validate input
        if cls is None:
            elements = self.unsorted
        elif issubclass(cls, Element):
            elements = self[cls]
        else:
            raise ValueError(f"Invalid class input ({cls})")
        # Iterate through elements
        try:
            found = elements[elements.index(name)]
        except ValueError:
            raise ValueError(f"Input element name not found ({name})")
        return found

    def evaluate(self, **kwargs):
        """
        Evaluate each element in the layer.
        """
        # Evaluate each element
        evaluated = \
            {element.name: element(**kwargs) for element in self.unsorted}
        return evaluated


class Element(FuncOperator):
    """
    General CPM element mixin class.
    """

    @classmethod
    def build(cls, *args, **kwargs):
        # Build a single element
        return lambda func: cls(func=func, *args, **kwargs)


class SPF(Element):
    """
    Safety performance function operator class.
    """
    pass
    

class CF(Element):
    """
    Calibration factor operator class.
    """
    pass


class AF(Element):
    """
    Adjustment factor operator class.
    """
    pass
    

class Sub(Element):
    """
    Sub-functional operator class.
    """
    pass

    
class Hidden(Element):
    """
    Sub-functional operator class that is hidden from the model API. Elements 
    are evaluated when running the model and can be passed to subsequent 
    layers but are not included in output data. Kwargs are 
    documented at the model level
    """
    pass

    
class Result(Element):
    """
    Result operator class.
    """
    pass


##########################
# DEFINE RESULTS MANAGER #
##########################

class Prediction(object):
    """
    Object class for managing model prediction results.
    """

    def __init__(self, parent=None, data=None):
        self._parent = parent
        self._data = data

    def __repr__(self):
        x = ', '.join([f"'{layer.name}':{res: >7,.3f} ({res.comp})" for \
            layer, res in self.res.items()])
        return 'Prediction({' + x + '})'

    def __str__(self):
        return repr(self)

    def __getitem__(self, args):
        return self.data[args]

    @property
    def parent(self):
        return self._parent

    @property
    def elements(self):
        return self.parent.elements

    @property
    def data(self):
        return self._data

    @property
    def series(self):
        return pd.Series(self.data)

    @property
    def res(self):
        return OrderedDict([(e, self.data[e]) for \
            e in self.elements.elements if isinstance(e, Result)])
