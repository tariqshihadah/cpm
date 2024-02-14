#######################
# IMPORT DEPENDENCIES #
#######################

import pandas as pd
import math, os, json, random
from collections import OrderedDict
from cpm.base.elements import SPF, AF, CF, Sub, Result, Prediction, \
    LayerCollection, Element
from cpm.base.validators import Validator, Limits, Values, ValidationError
from cpm.base.operators import FuncOperator, ResOperator
from cpm.base.references import ReferenceCollection, Reference


########################
# DEFINE MODEL CLASSES #
########################

class Model(object):
    """
    Crash prediction model class for managing and performing safety 
    performance function and adjustment factor operations as well as combining 
    these elements into a single crash prediction result.
    
    To build a model, call the Model class with Model() and use the Model.spf 
    and Model.af decorators on functions for performing individual SPF and AF 
    calculations. Once the model is built, the Model.predict() function can be 
    used to perform crash predictions for a single record using **kwargs or 
    for many records using a pandas DataFrame whose columns correspond with 
    the keyword arguments in the individual SPF and AF functions.
    """
    
    def __init__(self, name='cpm'):
        # Unlock the model
        self.unlock()
        # Log input parameters
        self.name = name
        # Initialize attributes
        self.refs = []
        self.validators = {}
        self.elements = LayerCollection(parent=self)
        self.references = ReferenceCollection(parent=self)
        # Build helpers
        self._build_helpers()
    
    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        num_spfs    = len(self.elements.find_class(SPF))
        num_afs     = len(self.elements.find_class(AF))
        num_results = len(self.elements.find_class(Result))
        num_kwargs  = len(self.kwargs)
        spfs = '\n - '.join( \
            [e.name for e in self.elements.find_class(SPF)])
        afs  = '\n - '.join( \
            [e.name for e in self.elements.find_class(AF)])
        results = '\n - '.join( \
            [e.name for e in self.elements.find_class(Result)])
        kwargs = '\n - '.join(self.kwargs)
        # Format message
        msg = f"""\
CRASH PREDICTION MODEL
----------------------
Model ID: {self.name}
Number of Layers: {self.elements.num_layers}
Safety Performance Functions ({num_spfs}):
 - {spfs}
Adjustment Factors ({num_afs}):
 - {afs}
Result Functions ({num_results}):
 - {results}
Model Keyword Arguments ({num_kwargs}):
 - {kwargs}
----------------------\
"""
        return msg

    def __getitem__(self, arg):
        """
        Retrieve an element within the model's collection with the given name. 
        If no element is found, raise a KeyError.
        """
        return self.get_element(arg)

    def _build_helpers(self):
        """
        Build methods to easily add elements to the model.
        """
        # Create function generator
        def gen(cls):
            # Define the element creation wrapper
            def builder(*args, explode_ref=False, **kwargs):
                """
                Add a model element to the active model by providing a pythonic 
                function and any required operational parameters such as JSON 
                references, composition dictionaries, and more.
        
                Parameters
                ----------
                obj : Element subtype
                    Function or other callable object to operate over model 
                    inputs.
                name : str, optional
                    Unique identifying name for the model element. If not 
                    provided, func.__name__ value will be used.
                layer : int, optional
                    Unique layer index to add the element to. If not provided, 
                    will be added to the active layer.
                explode_refs : bool, default False
                """
                def wrapper(func):
                    # Check model state
                    self._check_lock()
                    # Prepare iterators based on input
                    ref_data = kwargs.get('refs')
                    if kwargs.get('explode_refs'):
                        ref_data = zip(*self.references \
                            ._explode_multireference(ref_data))
                    else:
                        ref_data = zip([ref_data], [''])
                    # Prepare references
                    for data, suffix in ref_data:
                        callbacks = \
                            self.references._create_callbacks(data)
                        # Build requested element subclass
                        obj = cls(
                            func=func, parent=self, callbacks=callbacks,
                            suffix=suffix, *args, **kwargs
                        )
                        # Add element to model collection
                        self.elements.add_element(obj, **kwargs)
                return wrapper
            return builder
        # Iterate over element subclasses and create builders
        for subclass in Element.__subclasses__():
            # Add helper method to model
            setattr(self, f'add_{subclass.__name__.lower()}', gen(subclass))

    @property
    def locked(self):
        return self._locked

    @property
    def kwargs(self):
        """
        Return a list of the required keyword arguments for running model 
        predictions.
        """
        # Retrieve kwargs for all elements in the layer collection
        return sorted(set(self.elements.kwargs) - set(self.ref_keys))

    @property
    def constraints(self):
        """
        Return a dictionary of constraint information for all elements within 
        the model.

        Returns
        -------
        constraints : dict
            A dictionary defining constraint information for each element within 
            the model, described in a tuple where the first value indicates 
            the type of constraint ('limits' or 'values') and the second value 
            indicates the constraint values. 
            - for limits, the constraint values will be a two-element tuple, 
              indicating the inclusive start and end values of the limits.
            - for values, the constraint values will define all feasible unique 
              values.
        """
        # Filter for only required model inputs
        constraints = self.elements.constraints
        return {k: constraints[k] for k in self.kwargs}

    @property
    def ref_keys(self):
        """
        Return a list of the key values provided by all references included 
        in the model.
        """
        # Identify all reference key values
        keys = sorted(set().union(*[ref.keys for ref in self.refs]))
        return keys

    @property
    def element_ids(self):
        return list(e.name for e in self.elements)

    def lock(self):
        """
        Lock the model design from all additions or modifications.
        """
        self._locked = True

    def unlock(self):
        """
        Unlock the model design, allowing additions or modifications.
        """
        self._locked = False

    def _check_lock(self):
        """
        Check whether the model is currently locked and raise an error if it 
        is.
        """
        if self.locked:
            raise ModelLockedError("Model cannot be modified when locked.")

    def how(self):
        """
        Return general instructions on how to use the model.
        """
        # Identify all validator information
        texts = []
        validators = self.validators
        for  kwarg in self.kwargs:
            # Get all validators associated with each model keyword argument
            try:
                validators_list = validators[kwarg]
                texts.extend([v.describe(printit=False) for \
                    v in validators_list])
            except KeyError:
                texts.append(f'- {kwarg:16} unconstrained')
            
        # Generate information string
        texts = '\n'.join(texts)
        text = \
f"""\
HOW-TO
------
To perform a prediction, call the model's predict method and pass all required \
independent variable parameters according to the constraints below.

MODEL PARAMETERS
----------------
{texts}
"""
        print(text)

    def get_element(self, name):
        """
        Retrieve an element within the model's collection with the given name. 
        If no element is found, raise a KeyError.
        """
        # Search for the element
        for e in self.elements.elements:
            if e.name == name:
                return e
            else:
                continue
        # If none is found, raise KeyError
        raise KeyError(f"No element found with the name '{name}'")

    def get_layer(self, name):
        """
        Retrieve a layer within the model's collection with the given name. 
        If no layer is found, raise a KeyError.
        """
        # Search for the layer
        for l in self.elements.layers:
            if l.name == name:
                return l
            else:
                continue
        # If none is found, raise KeyError
        raise KeyError(f"No layer found with the name '{name}'")

    def add_reference(self, obj, name=None):
        """
        Decorator for adding a reference class to a model instance.
        
        Parameters
        ----------
        obj : Reference or subclass
            Reference operator for managing model references to static files.
        name : str, optional
            Unique identifying name for the reference operator. If not 
            provided, ref's name (ref.name) will be used.
        """
        # Check model state
        self._check_lock()
        # Add to reference collection
        self.references.add_reference(obj, name=name)
        # Validate reference class
        if isinstance(obj, (str, dict)):
            obj = Reference(obj, name=name)
        elif not isinstance(obj, Reference):
            raise TypeError("Input obj must be Reference or subclass.")
        # Get reference ID
        if name is None:
            name = obj.name
        self.refs.append(obj)
        return obj

    def add_validator(self, obj):
        """
        Method for adding a validation manager to the model to validate input 
        parameters prior to evaluating model elements.

        Parameters
        ----------
        obj : Validator subclass
            Validation manager for validating input parameters.
        """
        # Check model state
        self._check_lock()
        # Validate input object
        if not isinstance(obj, Validator):
            raise TypeError("Input object must be Constraint subtype (e.g., \
Limits or Values).")
        # Retrieve the constraint key value and add to collection
        try:
            self.validators[obj.key].append(obj)
        except KeyError:
            self.validators[obj.key] = [obj]

    def add_layer(self, name=None):
        """
        Method for adding a layer to the model's layer collection. This allows 
        for a new set of dependent functions which will take inputs of the 
        model's kwargs as well as the outputs of previous layer elements.

        Parameters
        ----------
        name : str, optional
            Unique identifying name for the model layer. If not provided, 
            the layer's level (an integer from 0 to LayerCollection.num_layers) 
            will be used.
        """
        # Check model state
        self._check_lock()
        # Add layer
        self.elements.add_layer(name=name)
    
    def add_element(self, obj, name=None, layer=None):
        """
        DEPRECATED
        Method for adding a model element to the model instance. Element 
        keyword arguments should correspond to the ultimate inputs which will 
        be passed to the built model to perform predictions as well as the 
        unique identifying names of the top-level model elements as well as 
        prior levels within the built model.
        
        Parameters
        ----------
        obj : Element subtype
            Function or other callable object to operate over model inputs.
        name : str, optional
            Unique identifying name for the model element. If not provided, 
            func.__name__ value will be used.
        layer : int, optional
            Unique layer index to add the element to. If not provided, will be 
            added to the active layer.
        """
        raise Exception(
            "Adding elements by add_element() method is deprecated. Please "
            "use subclass-specific element adders (e.g., add_spf()).")

    def validate(self, **kwargs):
        """
        Perform validation of input keyword arguments using the model's defined 
        validators. Validators can be added using the .add_validator() method.
        """
        # Check kwargs against model validators
        validated = kwargs.copy()
        for key, arg in kwargs.items():
            try:
                # Get a list of all validators for the selected key
                validator_list = self.validators[key]
                # Iterate over validators
                for validator in validator_list:
                    validated[key] = validator.validate(**validated)
                    try:
                        validated[key] = validator.validate(
                            conditions='raise', **validated)
                    except:
                        continue
            except KeyError:
                validated[key] = arg
        # Return validated kwargs
        return validated

    def predict_one(self, **kwargs):
        """
        Perform a crash prediction using the built model with a single record 
        input via **kwargs which correspond with the keyword arguments in the 
        individual SPF and AF functions used to build the model. A list of the 
        model's keyword arguments can be obtained using the Model.kwargs 
        property.
        """
        # Validate input kwargs
        validated = self.validate(**kwargs)
        # Evaluate all model layers using the provided kwargs
        evaluated = self.elements.evaluate(**validated)
        # Summarize results
        p = Prediction(parent=self, data=evaluated)
        return p

    def predict(self, obj=None, merge=True, **kwargs):
        """
        Perform a crash prediction using the built model with either a single 
        record input via a dictionary, pandas Series, or **kwargs, or many 
        records input via a pandas DataFrame whose columns correspond with the 
        keyword arguments in the individual model elements used to build the 
        model. See Model.kwargs for a full list of model keyword arguments.

        Parameters
        ----------
        obj : dict, pd.Series, or pd.DataFrame, optional
            Input model parameters to be evaluated. Can be passed as a single 
            record using a dictionary or pandas series of parameter name and 
            value pairs, or as multiple records using a pandas dataframe where 
            columns represent multiple records to predict on and column labels 
            represent parameter names.
        merge : bool, default True
            Whether to merge output result operators into a single dataframe 
            where columns represent the computed elements of the model for each 
            input record. If False, results will be returned as a series of 
            result operators.
        """
        # Check for input type
        if obj is None:
            # Perform prediction for single record using kwargs
            predicted = self.predict_one(**kwargs)
            return predicted
        elif isinstance(obj, dict):
            # Perform prediction for single record using a dictionary
            predicted = self.predict_one(**obj)
            return predicted
        elif isinstance(obj, pd.Series):
            # Perform prediction for single record using a pandas series
            predicted = self.predict_one(**obj.to_dict())
            return predicted
        elif isinstance(obj, pd.DataFrame):
            # Perform prediction for all records in the dataframe, returning
            # a dataframe if merge=True else a series of Prediction objects
            predicted = obj.apply(lambda r: self.predict_one(**r), axis=1)
            if merge:
                predicted = predicted.apply(lambda x: pd.Series(x.data))
            return predicted
        else:
            raise TypeError("Input obj variable must be pd.DataFrame or dict \
type.")

    def init_one(self, fill=None, attempts=10, seed=None):
        """
        Create a single dictionary for the model's input parameters, filled 
        with randomly selected values based on the model's defined validators.
        """
        # Iterate through all parameters to generate a feasible value
        res = {}
        for attempt in range(attempts):
            # Identify remaining keyword arguments to initialize
            remaining = [k for k in self.kwargs if not k in res]
            for kwarg in remaining:
                # Retrieve validators for the selected keyword argument
                try:
                    validator_list = self.validators[kwarg]
                except KeyError:
                    res[kwarg] = fill
                    continue
                # Validate kwargs
                for validator in validator_list:
                    try:
                        res[kwarg] = validator.random(
                            conditions='raise', seed=seed, **res)
                    except (KeyError, ValueError, ValidationError):
                        continue
            # Review progress
            if len(res) == len(self.kwargs):
                break
            elif attempt < attempts - 1:
                continue
            else:
                raise ValueError(f"Unable to successfully initialize \
feasible conditions based on model validators for {remaining}. Validator \
logic may be invalid or too complex for the requested number of attempts \
({attempts}).")
        # Return the completed dictionary if achieved
        return res
    
    def init_feasible(self, num_rows=10, fill=None, attempts=10):
        """
        Create a pandas dataframe template for the model's input parameters, 
        filling with randomly selected values based on the model's defined 
        validators.
        """
        # Initialize one set of input parameters per requested row
        records = [self.init_one(fill=fill, attempts=attempts) for \
            i in range(num_rows)]
        df = pd.DataFrame(records) \
            .reindex_like(self.template(num_rows=num_rows))
        return df
    
    def template(self, num_rows=10):
        """
        Create a pandas dataframe template for data collection and input into 
        the model.

        Parameters
        ----------
        num_rows : integer, default 10
            The number of rows to include in the dataframe template.
        """
        # Create dataframe
        df = pd.DataFrame(columns=self.kwargs, index=range(0,num_rows))
        return df

    def save_template(self, fp, num_rows=10):
        """
        Save an empty CSV or XLSX template for data collection and input into 
        the model.

        Parameters
        ----------
        num_rows : integer, default 10
            The number of rows to include in the created template file.
        """
        # Create dataframe
        df = self.template(num_rows=num_rows)
        # Save template
        ext = os.path.splitext(fp)[-1].lower()
        if ext in ['.xlsx','.xls']:
            df.to_excel(fp, index=True)
        elif ext in ['.csv','.tsv']:
            df.to_csv(fp, index=True)
        else:
            raise ValueError("Invalid file extension, must be one of .csv, \
.tsv, .xlsx, .xls.")


##############
# EXCEPTIONS #
##############

class ModelError(Exception):
    pass

class ModelLockedError(ModelError):
    pass