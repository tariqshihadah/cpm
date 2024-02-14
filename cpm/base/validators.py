#######################
# IMPORT DEPENDENCIES #
#######################

import numpy as np
import math, random, warnings, inspect


##############################
# DEFINE VALIDATION MANAGERS #
##############################

class Validator(object):
    """
    Object class mixin for managing model parameter validators.
    """
    
    @property
    def kwargs(self):
        # Compile condition deep keys
        deep_keys = []
        for key, condition in self.conditions.items():
            deep_keys.append(key)
            if isinstance(condition, Validator):
                deep_keys.extend(condition.kwargs)
        # Get functional limits keys if available
        try:
            deep_keys.extend(self.vmin.keys)
            deep_keys.extend(self.vmax.keys)
        except AttributeError:
            pass
        # Compile all deep and shallow keys
        keys = sorted(set([self.key, *self.conditions.keys(), *deep_keys]))
        return keys

    @property
    def values(self):
        try:
            return self._values
        except AttributeError:
            return None

    @values.setter
    def values(self, values):
        # Enforce iterable
        try:
            values = iter(values)
        except TypeError:
            raise TypeError("Values information must be provided as \
list-like.")
        # Enforce dtype
        try:
            self._values = set(self.as_dtype(v) for v in values)
        except TypeError:
            raise TypeError(f"Values must be of the required dtype \
({self.dtype}).")

    @property
    def dtype(self):
        try:
            return self._dtype
        except AttributeError:
            return None
    
    @dtype.setter
    def dtype(self, dtype):
        if isinstance(dtype, type) or dtype is None:
            self._dtype = dtype
        else:
            raise TypeError("Input dtype must be a class type (e.g., str) or \
None")

    @property
    def notes(self):
        try:
            return self._notes
        except AttributeError:
            return []
    
    @notes.setter
    def notes(self, notes):
        if notes is None:
            self._notes = []
        elif isinstance(notes, str):
            self._notes = [notes]
        elif isinstance(notes, list):
            self._notes = notes
        else:
            raise TypeError(f"Input notes must be provided as a string or a \
list of strings.")

    def check_values(self, x, values=None):
        """
        Check if the value satisfies the validator as defined.
        """
        # Validate input
        if values is None:
            values = self.values
        # Check values list
        return x in values
    
    def check_limits(self, x, vmin=None, vmax=None, closed=None, **kwargs):
        """
        Check if the value satisfies the validator as defined.
        """
        # Validate values
        vmin = self.vmin(**kwargs) if vmin is None else vmin
        vmax = self.vmax(**kwargs) if vmax is None else vmax
        closed = self.closed if not closed else closed
        # Ensure proper type
        try:
            vmin, vmax = float(vmin), float(vmax)
        except ValueError:
            raise TypeError(
                f"Limit values for '{self.key}' must be numerical. Received: "
                f"vmin={vmin}, vmax={vmax}")
        try:
            x = float(x)
        except ValueError:
            raise TypeError(
                f"Check value must be numerical. Received: {self.key}={x}")
        
        # Check for add/subtract keys
        try:
            subtract = self.subtract
            add      = self.add
        except AttributeError:
            subtract = []
            add      = []
        try:
            for key in subtract:
                vmax -= kwargs[key]
            for key in add:
                vmin += kwargs[key]
        except:
            raise KeyError(f"Missing required validation input {s}.")

        # Check left end of validator
        if closed in {'left','both'}:
            left = x >= vmin
        else:
            left = x > vmin
        # Check right end of validator
        if closed in {'right','both'}:
            right = x <= vmax
        else:
            right = x < vmax
            
        # Determine if both satisfied
        res = all((left,right))
        return res

    def check_conditions(self, **kwargs):
        """
        Validate the input keyword arguments against the object's conditions if 
        defined.
        """
        # Check conditions
        for key, condition in self.conditions.items():
            # Condition is Validator-type
            if isinstance(condition, Validator):
                try:
                    # If a condition is met, continue to next condition
                    condition.validate(**kwargs)
                except ValueError:
                    # If any conditions aren't met, return False
                    return False
            # Condition is limits
            elif isinstance(condition, tuple):
                if not self.check_limits(
                    kwargs[key], vmin=condition[0], vmax=condition[1], 
                    closed=condition[2] if len(condition)>2 else 'both'):
                    return False
            # Condition is values
            elif isinstance(condition, list):
                if not self.check_values(kwargs[key], values=condition):
                    return False
            # Invalid condition
            else:
                raise TypeError(f"Condition information for '{key}' is invalid \
type ({type(condition).__name__}), condition must be one of {{Validator, \
tuple, list}}.")
        return True

    def as_dtype(self, x):
        """
        Coerce the input value as the object's defined dtype.
        """
        if self.dtype is None:
            return x
        else:
            try:
                return self.dtype(x)
            except:
                raise TypeError(f'Unable to coerce input value ({x}) as \
{self.dtype} type.')

    def _describe_conditions(self):
        # Review conditions
        texts = []
        for key, condition in self.conditions.items():
            # Describe range condition
            if isinstance(condition, tuple):
                if len(condition) > 2:
                    closed = condition[2]
                    lb = '(' if closed in {'right','neither'} else '['
                    rb = ')' if closed in {'left','neither'}  else ']'
                range_ = f'range={lb}{condition[0]} to {condition[1]}{rb}'
                text_i = f'  - where {key}: {range_}'
            # Describe values condition
            elif isinstance(condition, list):
                condition = [str(x) for x in condition]
                values = f'values={"{"}{", ".join(condition)}{"}"}'
                text_i = f'  - where {key}: {values}'
            # Describe Validator condition
            elif isinstance(condition, Validator):
                text_i =  '  - where ' + condition.describe(printit=False)
            # Append condition description text to list
            texts.append(text_i)
        return texts
            

class Values(Validator):
    """
    Subclass of Validator for set-based parameter validation.

    The Values validator checks numerical inputs against a specified set of 
    valid values, such as strings. Depending on the selected enforcement 
    parameter, when the input value is not one of the defined valid values or 
    is of the wrong type, the validator will raise an error, substitute a 
    default value, or let the value pass through. Validators can also be 
    conditional, only being enforced when another parameter meets a separately 
    defined condition.
    
    Parameters
    ----------
    key : str
        Name of the variable associated with the validators.
    values : list-like
        Set of accepted values to check inputs against.
    dtype : type, optional
        Data type to coerce the input variable to. If not provided, values will 
        not be coerced.
    default : various
        Default value to substitute when validation fails. Only applicable when 
        enforce='default'.
    enforce : {'strict','type','default','none'}
        How to enforce the validator on the input variable.
        - strict: raise an error if the input value does not validate
        - type: only enforce the validator data type
        - default: when validation is unsuccessful, substitute input with a 
          defined default value
        - none: do not enforce the validator
    conditions : dict
        Dictionary of input variable name keys and condition information. 
        Condition information can be provided as (1) a tuple of minimum and 
        maximum values for a closed limit range (e.g., (min, max)); (2) a list 
        of valid input values; or (3) an instance of a Validator subclass.
    notes : str or list
        String or list of strings to provide as documentation or specific 
        instructions on how the validator is used. Notes will be included in 
        validator self-documentation, accessed through the Validator.describe() 
        method.
    """

    def __init__(self, key='x', values=[], dtype=None, default=None, 
        enforce='strict', conditions=None, notes=None):
        # Validate inputs
        # - key
        self.key = str(key)
        # - dtype
        self.dtype = dtype
        # - default
        self.default = default
        # - values
        self.values = values
        # - conditions
        if not conditions is None:
            if not isinstance(conditions, dict):
                raise TypeError("Input condition must be a dictionary of other \
parameter key strings and valid values or other validator subclass instances.")
            self.conditions = conditions
        else:
            self.conditions = {}
        # - enforce
        enforce_options = {'strict','type','default','none'}
        if not enforce in enforce_options:
            raise ValueError(f"Input enforce must be one of {enforce_options}")
        else:
            self.enforce = enforce
        # - notes
        self.notes = notes

    def random(self, seed=None, conditions='pass', **kwargs):
        """
        Initialize a random valid value given the provided keyword arguments 
        and the validator's defined conditions.

        Parameters
        ----------
        conditions : {'pass','raise'}
            How to respond to validator conditions not being met; 'pass' will 
            ignore the validator if conditions are not met; 'raise' will raise 
            a ValueError if conditions are not met.
        **kwargs
            Keyword arguments required for performing validation (see 
            self.kwargs).
        """
        # Create seeded random generator
        rand = random.Random(x=seed)
        # Define random value
        val = rand.choice(tuple(self.values))
        kwargs[self.key] = val
        # Validate random value
        return self.validate(conditions=conditions, **kwargs)
            
    def describe(self, printit=True, fmt=False):
        """
        Return a string describing the parameters of the validator.
        """
        # Format valid value set
        key = f'{Fmt.BOLD if fmt else ""}{self.key}{Fmt.END if fmt else ""}'
        values = f'values={"{"}{", ".join([str(x) for x in self.values])}{"}"}'
        dtype   = '' if self.dtype is None else f', dtype={self.dtype.__name__}'
        default = '' if self.default is None else f', default={self.default}'
        enforce = f', enforce={self.enforce}'
        texts = [f'{key}\n- {values}{dtype}{default}{enforce}']
        
        # Add validator notes
        texts.extend(['  - ' + str(n) for n in self.notes])
        
        # Review conditions
        texts.extend(self._describe_conditions())
        
        # Assemble descriptor text
        text = '\n'.join(texts)
        
        # Print or return text
        if printit:
            print(text)
        else:
            return text

    def validate(self, conditions='pass', **kwargs):
        """
        Validate the input value and keyword arguments according to the 
        object's validators, conditions, and enforcement level.

        Parameters
        ----------
        conditions : {'pass','raise'}
            How to respond to validator conditions not being met; 'pass' will 
            ignore the validator if conditions are not met; 'raise' will raise 
            a ValueError if conditions are not met.
        **kwargs
            Keyword arguments required for performing validation (see 
            self.kwargs).
        """
        # Retrieve input variable
        x = kwargs[self.key]
        
        # Ensure all keyword arguments are provided
        if not all(key in kwargs for key in self.kwargs):
            raise KeyError(f"Must provide all required keyword arguments for \
evaluation of validator and conditions; missing: \
{list(set(self.kwargs) - set(kwargs.keys()))}")

        # Check conditions
        if not self.check_conditions(**kwargs):
            # If conditions are not met, ignore validator and return original 
            # input
            if conditions == 'pass':
                return x
            # If conditions are not met, raise a ValueError
            elif conditions == 'raise':
                raise ConditionError("Validator conditions not met.")
        
        # Check enforcement level
        if self.enforce == 'none':
            return x
        elif self.enforce == 'type':
            # Coerce to required dtype
            x = self.as_dtype(x)
            return x
        elif self.enforce == 'default':
            # Coerce to required dtype
            x = self.as_dtype(x)
            # Check values
            if not self.check_values(x):
                x = self.default
            return x
        elif self.enforce == 'strict':
            # Coerce to required dtype
            x = self.as_dtype(x)
            # Check limits
            if not self.check_values(x):
                raise InvalidValueError(f"Keyword argument {self.key}={x} \
must be one of {self.values}.")
            return x


class Limits(Validator):
    """
    Subclass of Validator for range-based parameter validation.

    The Limits validator checks numerical inputs against minimum and maximum 
    values. Depending on the selected enforcement parameter, when the input 
    value is outside this range or of the wrong type, the validator will raise 
    an error, snap the value to the nearest range edge value, substitute a 
    default value, or let the value pass through. Validators can also be 
    conditional, only being enforced when another parameter meets a separately 
    defined condition.
    
    Parameters
    ----------
    key : str
        Name of the variable associated with the validators.
    vmin, vmax : numeric or callable
        Minimum and maximum valid numeric values of the validator, or callable 
        functions which take parameters with names that correlate to variable 
        name keys and which output a single numeric value.
    closed : {'both','neither','left','right'}
        How to treat the minimum and maximum values at either end of the limit 
        range.
    dtype : type, optional
        Data type to coerce the input variable to. If not provided, values will 
        not be coerced.
    default : various
        Default value to substitute when validation fails. Only applicable when 
        enforce='default'.
    subtract : str or list
        String or list of variable name keys whose values should be subtracted 
        from the validator's vmax value.
    add : str or list
        String or list of variable name keys whose values should be added to  
        the validator's vmin value.
    enforce : {'strict','snap','type','default','none'}
        How to enforce the validator on the input variable.
        - strict: raise an error if the input value does not validate
        - snap: snap values which are outside the limits of the validator to 
          the nearest limit value
        - type: only enforce the validator data type
        - default: when validation is unsuccessful, substitute input with a 
          defined default value
        - none: do not enforce the validator
    conditions : dict
        Dictionary of input variable name keys and condition information. 
        Condition information can be provided as (1) a tuple of minimum and 
        maximum values for a closed limit range (e.g., (min, max)); (2) a list 
        of valid input values ['a','b','c']; or (3) an instance of a Validator 
        subclass.
    notes : str or list
        String or list of strings to provide as documentation or specific 
        instructions on how the validator is used. Notes will be included in 
        validator self-documentation, accessed through the Validator.describe() 
        method.
    """

    def __init__(self, key='x', vmin=None, vmax=None, closed='both', dtype=None, 
        default=None, subtract=None, add=None, enforce='strict', 
        conditions=None, notes=None):
        # Validate inputs
        # - class validators
        self.key = str(key)
        self.dtype = dtype
        self.default = default
        self.vmin = vmin
        self.vmax = vmax
        # - subtract
        if subtract is None:
            self.subtract = []
        elif isinstance(subtract, str):
            self.subtract = [subtract]
        elif isinstance(subtract, list):
            self.subtract = subtract
        else:
            raise TypeError(f"Input subtract must be provided as a string or a \
list of strings.")
        # - add
        if add is None:
            self.add = []
        elif isinstance(add, str):
            self.add = [add]
        elif isinstance(add, list):
            self.add = add
        else:
            raise TypeError(f"Input add must be provided as a string or a \
list of strings.")
        # - closed
        self.closed = closed
        # - conditions
        if not conditions is None:
            if not isinstance(conditions, dict):
                raise TypeError("Input condition must be a dictionary of other \
parameter key strings and valid values or other validator subclass instances.")
            self.conditions = conditions
        else:
            self.conditions = {}
        # - enforce
        self.enforce = enforce
        # - notes
        self.notes = notes

    @property
    def dtype(self):
        return self._dtype

    @dtype.setter
    def dtype(self, dtype):
        if dtype is None:
            dtype = float
        elif not isinstance(dtype, type):
            raise TypeError(f"Input dtype for key {self.key} is invalid.")
        self._dtype = dtype

    @property
    def vmin(self):
        return self._vmin

    @vmin.setter
    def vmin(self, val):
        self._vmin = LimitManager(val, dtype=self.dtype, parent=self)

    @property
    def vmax(self):
        return self._vmax

    @vmax.setter
    def vmax(self, val):
        self._vmax = LimitManager(val, dtype=self.dtype, parent=self)

    @property
    def closed(self):
        return self._closed

    @closed.setter
    def closed(self, label):
        # Define options
        closed_options = {'both','neither','left','right'}
        # Validate input
        if not str(label).lower() in closed_options:
            raise ValueError(
                f"Input closed parameter must be one of {closed_options}.")
        self._closed = label

    @property
    def enforce(self):
        return self._enforce

    @enforce.setter
    def enforce(self, label):
        # Define valid enforcement options
        enforce_options = {'strict','snap','type','default','none','warn'}
        # Validate selection
        if not label in enforce_options:
            raise ValueError(
                f"Provided enforcement parameter for the Validator for "
                f"{self.key} is invalid ({label}). Must be one of "
                f"{enforce_options}")
        self._enforce = label
            
    def random(self, seed=None, conditions='pass', **kwargs):
        """
        Initialize a random valid value given the provided keyword arguments 
        and the validator's defined conditions.

        Parameters
        ----------
        conditions : {'pass','raise'}
            How to respond to validator conditions not being met; 'pass' will 
            ignore the validator if conditions are not met; 'raise' will raise 
            a ValueError if conditions are not met.
        **kwargs
            Keyword arguments required for performing validation (see 
            self.kwargs).
        """
        # Validate values
        try:
            vmin = self.vmin(**kwargs)
            vmax = self.vmax(**kwargs)
        except:
            raise ValidationError(f"Unable to evaluate limits.")
        
        # Check for add/subtract keys
        try:
            subtract = self.subtract
            add      = self.add
        except AttributeError:
            subtract = []
            add      = []
        try:
            for key in subtract:
                vmax -= kwargs[key]
            for key in add:
                vmin += kwargs[key]
        except:
            raise ValidationError(f"Missing required validation input {key}.")

        # Create seeded random generator
        rand = random.Random(x=seed)
        # Define random value
        val = rand.random()
        kwargs[self.key] = val * (vmax - vmin) + vmin
        # Validate random value
        return self.validate(conditions=conditions, **kwargs)

    def range_notation(self):
        """
        Return string notation for the validator's range.
        """
        lb = '(' if self.closed in {'right','neither'} else '['
        rb = ')' if self.closed in {'left','neither'} else ']'
        range_  = f'{lb}{self.vmin} to {self.vmax}{rb}'
        return range_
            
    def describe(self, printit=True, fmt=False):
        """
        Return a string describing the parameters of the validator.
        """
        # Determine range bracket types
        key = f'{Fmt.BOLD if fmt else ""}{self.key}{Fmt.END if fmt else ""}'
        dtype   = '' if self.dtype is None else f', dtype={self.dtype.__name__}'
        enforce = f', enforce={self.enforce}'
        texts = [f'{key}\n- range={self.range_notation()}{dtype}{enforce}']
        
        # Add validator notes
        texts.extend(['  - ' + str(n) for n in self.notes])

        # Add subtract/add notes
        subtract = self.subtract
        if len(subtract) > 0:
            texts.append(f'  - subtracting {", ".join(subtract)} from vmax')
        add      = self.add
        if len(add) > 0:
            texts.append(f'  - adding {", ".join(add)} to vmin')

        # Review conditions
        texts.extend(self._describe_conditions())
        
        # Assemble descriptor text
        text = '\n'.join(texts)
        
        # Print or return text
        if printit:
            print(text)
        else:
            return text

    def validate(self, conditions='pass', **kwargs):
        """
        Validate the input value and keyword arguments according to the 
        object's validators, conditions, and enforcement level.

        Parameters
        ----------
        conditions : {'pass','raise'}
            How to respond to validator conditions not being met; 'pass' will 
            ignore the validator if conditions are not met; 'raise' will raise 
            a ValueError if conditions are not met.
        **kwargs
            Keyword arguments required for performing validation (see 
            self.kwargs).
        """
        # Retrieve input variable
        x = kwargs[self.key]
        
        # Ensure all keyword arguments are provided
        if not all(key in kwargs for key in self.kwargs):
            raise ValidationError(f"Must provide all required keyword \
arguments for evaluation of validator and conditions; missing: \
{list(set(self.kwargs) - set(kwargs.keys()))}")

        # Check conditions
        if not self.check_conditions(**kwargs):
            # If conditions are not met, ignore validator and return original 
            # input
            if conditions == 'pass':
                return x
            # If conditions are not met, raise a ValueError
            elif conditions == 'raise':
                raise ConditionError("Validator conditions not met.")

        # Check enforcement level
        vmin = self.vmin(**kwargs)
        vmax = self.vmax(**kwargs)
        if self.enforce == 'none':
            return x
        elif self.enforce == 'type':
            # Coerce to required dtype
            x = self.as_dtype(x)
            return x
        elif self.enforce == 'default':
            # Coerce to required dtype
            x = self.as_dtype(x)
            # Check limits
            if not self.check_limits(x, **kwargs):
                x = self.default
            return x
        elif self.enforce == 'snap':
            x = self.as_dtype(x)
            return min(max(x, vmin), vmax)
        elif self.enforce == 'strict':
            # Coerce to required dtype
            x = self.as_dtype(x)
            # Check limits
            if not self.check_limits(x, **kwargs):
                raise InvalidValueError(
                    f"Keyword argument {self.key}={x} is outside the limits "
                    f"of the validator [{vmin}, {vmax}].")
            return x
        elif self.enforce == 'warn':
            # Coerce to required dtype
            x = self.as_dtype(x)
            # Check limits
            if not self.check_limits(x, **kwargs):
                warnings.warn(
                    f"Keyword argument {self.key}={x} is outside the limits "
                    f"of the validator {self.range_notation()}.")
            return x


class LimitManager(object):

    def __init__(self, obj, dtype=None, parent=None):
        # Validate
        self.parent = parent
        self.dtype = dtype
        self.obj = obj

    def __call__(self, *args, **kwargs):
        if self._type == 0:
            return
        elif self._type == 1:
            return self.obj
        elif self._type == 2:
            # Prepare kwargs
            try:
                new_kwargs = {k: kwargs[k] for k in self.keys}
            except KeyError:
                missing = [k for k in self.keys if not k in kwargs]
                raise KeyError(
                    f"Unable to evaluate functional limit for "
                    f"{self.key}. Missing kwargs for {missing}.")
            # Evaluate function
            try:
                return self.dtype(self.obj(**new_kwargs))
            except:
                raise ValueError(
                    f"Unable to evaluate functional limit for "
                    f"{self.key}.")

    def __repr__(self):
        if self._type == 0:
            return
        elif self._type == 1:
            return str(self.obj)
        elif self._type == 2:
            return f'function({", ".join(self.keys)})'

    @property
    def obj(self):
        return self._obj

    @obj.setter
    def obj(self, obj):
        if obj is None:
            self._type = 0 # No limit
            self.keys = []
            self._obj = obj
        elif callable(obj):
            self._type = 2 # Callable
            self.keys = inspect.getfullargspec(obj)[0]
            self._obj = obj
        else:
            self._type = 1 # Numerical
            self.keys = []
            self._obj = self.dtype(obj)

    @property
    def dtype(self):
        return self._dtype
    @dtype.setter
    def dtype(self, dtype):
        if dtype is None:
            dtype = float
        elif not isinstance(dtype, type):
            raise TypeError(f"Input dtype for key {self.key} is invalid.")
        self._dtype = dtype

    @property
    def key(self):
        try:
            return self.parent.key
        except:
            return '[unbound validator]'


class Fmt(object):
   PURPLE    = '\033[95m'
   CYAN      = '\033[96m'
   DARKCYAN  = '\033[36m'
   BLUE      = '\033[94m'
   GREEN     = '\033[92m'
   YELLOW    = '\033[93m'
   RED       = '\033[91m'
   BOLD      = '\033[1m'
   UNDERLINE = '\033[4m'
   END       = '\033[0m'


##############
# EXCEPTIONS #
##############

class ValidationError(Exception):
    """
    Base exception class for validation errors
    """
    pass

class InvalidValueError(ValidationError, ValueError):
    pass

class InvalidTypeError(ValidationError, TypeError):
    pass

class ConditionError(ValidationError, ValueError):
    pass
