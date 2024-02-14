#######################
# IMPORT DEPENDENCIES #
#######################

# Import all dependencies for model definition as well as required libraries to 
# support additional computations such as the math library for exponential 
# functions and the os library for defining filepaths.

# For crash prediciton models in general, required elements will be Model, SPF, 
# AF, CF Sub, Result, Limits, Values, and Reference.

import math, os
from cpm.base import Model, SPF, AF, CF, Sub, Result, Limits, Values, Reference


################
# DEFINE MODEL #
################

# Define the model by instatiating a Model class instance and giving the model 
# a name using the 'name' keyword argument.

model = Model(name='example')


#####################
# DEFINE REFERENCES #
#####################

# Define any reference JSON files which will be used to support computation of 
# any model elements through keyword arguments passed to the references during 
# evaluation. Reference files can be stored anywhere, but should ideally be 
# located in the same folder as the model file. The example below assumes that 
# references are located in the same folder as the model file and use a lambda 
# function to simplify filepath definitions.

# References are added by calling the Model bounded method add_references() and 
# passing it a valid Reference class instance, which can be instantiated with 
# the argument of a valid filepath to a valid JSON file.

# References are valuable to simplify model function definitions which query a 
# table of values based on a selection of arguments, or which require extensive 
# conditional logic which could be better served by querying a static JSON 
# dictionary or nested dictionary.

fd = os.path.dirname(os.path.abspath(__file__))
fp = lambda fn: os.path.join(fd,fn)
model.add_reference(Reference(fp('calibration.json')))
model.add_reference(Reference(fp('spf_mv_dwy.json')))
model.add_reference(Reference(fp('spf_mv_ndwy.json')))
model.add_reference(Reference(fp('spf_sv.json')))
model.add_reference(Reference(fp('spf_ped.json')))
model.add_reference(Reference(fp('spf_pdc.json')))


#####################
# DEFINE VALIDATORS #
#####################

# Validators are not required for model development but provide powerful input-
# checking capabilities which ensure that the bounds and requirements of a 
# model are enforced during evaluation. They help to avoid complicated or 
# unexpected errors during evaluation of model elements, providing directly-
# actionable information to model users to ensure that data inputs are 
# appropriate and accurate.

# Validators also provide automated documentation of model functionality and 
# input requirements, which assist users with understanding the model and 
# interacting with it appropriately. Finally, these validators are extremely 
# valuable for the purposes of debugging models by ensuring full understanding 
# of model inputs and creating a set of developer-defined errors which indicate 
# correct operation of the model, while all other errors indicate incorrect 
# operation of the model.

# Validators can be defined with the Limits subclass which indicates a valid 
# range of numerical values that can be input as well as how the range is 
# enforced; or with the Values subclass which indicates a selection of valid 
# discrete values which can be input as well as how those values are enforced. 
# Each subclass can take a selection of additional parameters, such as a 
# default behavior, conditions under which the validator is enforced, as well 
# as a list of notes which will be provided along with automated documentation 
# of the validator to model users upon request.

# Limits or Values validator subclasses can be added to the model using the 
# model's add_validator() method, which requires a valid Validator subclass 
# instance.

# AADT
model.add_validator(
    Limits(key='aadt', vmin=1, vmax=32600, enforce='snap',
        conditions={'factype':['2u']}))
model.add_validator(
    Limits(key='aadt', vmin=1, vmax=32900, enforce='snap', 
        conditions={'factype':['3t']}))
model.add_validator(
    Limits(key='aadt', vmin=1, vmax=40100, enforce='snap', 
        conditions={'factype':['4u']}))
model.add_validator(
    Limits(key='aadt', vmin=1, vmax=66000, enforce='snap', 
        conditions={'factype':['4d']}))
model.add_validator(
    Limits(key='aadt', vmin=1, vmax=53800, enforce='snap', 
        conditions={'factype':['5t']}))

# Facility Type
model.add_validator(
    Values(key='factype', values=('2u','3t','4u','4d','5t'),
        notes=['2u: 2-lane undivided','3t: 2-lane with TWLTL',
            '4u: 4-lane undivided','4d: 4-lane divided',
            '5st: 4-lane with TWLTL']))

# Driveway Information
model.add_validator(
    Limits(key='n_maj_com', vmin=0, vmax=1e2))
model.add_validator(
    Limits(key='n_min_com', vmin=0, vmax=1e2))
model.add_validator(
    Limits(key='n_maj_ind', vmin=0, vmax=1e2))
model.add_validator(
    Limits(key='n_min_ind', vmin=0, vmax=1e2))
model.add_validator(
    Limits(key='n_maj_res', vmin=0, vmax=1e2))
model.add_validator(
    Limits(key='n_min_res', vmin=0, vmax=1e2))
model.add_validator(
    Limits(key='n_other', vmin=0, vmax=1e2))

# Geometry
model.add_validator(
    Limits(key='length', vmin=0, vmax=1e2))
model.add_validator(
    Values(key='parking_type', values=('parallel_res', 'parallel_com', 
        'angle_res', 'angle_com'), enforce='strict',
        conditions={'parking_prop':(0,1,'right')}))
model.add_validator(
    Values(key='parking_type', values=('none',), default='none', 
        enforce='default', conditions={'parking_prop':(0,0,'both')}))
model.add_validator(
    Limits(key='parking_prop', vmin=0, vmax=1, dtype=float))
model.add_validator(
    Limits(key='fo_density', vmin=0, vmax=1e3))
model.add_validator(
    Limits(key='fo_offset', vmin=0, vmax=30, enforce='snap'))
model.add_validator(
    Limits(key='median_width', vmin=0, vmax=100, enforce='snap'))

# Operational Information
model.add_validator(
    Limits(key='speed', vmin=5, vmax=100, notes='Speed limit in MPH'))
model.add_validator(
    Values(key='lighting', values=(0,1), dtype=int, 
        notes='0: not present; 1: present'))
model.add_validator(
    Values(key='ase', values=(0,1), dtype=int, 
        notes='0: not present; 1: present'))

# Historic Crash Information
model.add_validator(
    Limits(key='obs_mv_dwy_kabco', vmin=-1, vmax=1e3,
        notes='If historic crash data is unavailable, enter -1 to skip EB \
analysis.'))
model.add_validator(
    Limits(key='obs_mv_ndwy_kabco', vmin=-1, vmax=1e3,
        notes='If historic crash data is unavailable, enter -1 to skip EB \
analysis.'))
model.add_validator(
    Limits(key='obs_sv_kabco', vmin=-1, vmax=1e3,
        notes='If historic crash data is unavailable, enter -1 to skip EB \
analysis.'))
model.add_validator(
    Limits(key='num_years', vmin=0, vmax=1e2, dtype=float))


###############
# DEFINE SPFS #
###############

# Model evaluation is completed in discrete layers which are evaluated one by 
# one, with the results of each subsequent layer being fed into the next. For 
# this reason, a new layer must be added to the model to begin construction as 
# well as between each selection of dependent calculations.

# For example, if a selection of calculations are required which rely 
# exclusively on the direct inputs to the model, they should be defined within 
# the first layer of the model. If additional calculations are required which 
# rely on both the direct inputs to the model as well as the outputs of the 
# functions within the first layer, they should be defined within the second 
# layer of the model, and so on.

# All parameters input into one layer will also be passed to all subsequent 
# layers. For this reason, the namespace of the model should be managed to 
# avoid overwriting of input or computed parameters between layers to ensure 
# propegation of computed data throughout the evaluation.

# Functions are added to the model by defining basic pythonic functions which 
# take input keyword arguments which reflect the names of parameters which will 
# be passed directly to the model at evaluation as well as the names of model 
# elements which are defined in previous model layers. All model functions are 
# required to include **kwargs within the function definition. Model functions' 
# returns will be passed as an additional keyword argument to the next model 
# layer with a key value of the function's defined name.

# Functionally, all element types are largely identical, with unique classes 
# defined primarily for management and documentation of model architecture. 
# SPF, AF, CF, should be used to define the core computational elements of the 
# model which will ultimately be documented and logged within the model's 
# outputs after evaluation. These elements must be defined by instatiating a 
# class instance using the class method build(), which returns a decorator 
# which should be used to decorate the function being added to the model. The 
# object can then be added to the model by decorating the element decorator 
# with the add_element class decorator.

# Different from the other basic model element types, the Sub class defines 
# lower level computational functions which feed higher level computations of 
# other element class types. Results of these elements are not logged with the 
# output of the model's evaluation and are purely functional and for 
# convenience and the creation of a factored model design.

# Model elements which should interact with a model reference JSON file can be 
# invoked during the call of the build() class method on the element class 
# being used to decorate the target function. This is done by passing the 
# 'refs' keyword argument to the build() method, structured as a nested 
# dictionary with the key value pairs which indicate the name of the reference 
# being invoked and the dictionary of additional keyword arguments to pass to 
# the reference when calling the function. All keyword arguments passed to the 
# function will also be passed to the reference JSON file, along with the 
# additional keyword arguments defined in the build() method. These parameters 
# will be used to query the JSON file data, returning additional keyword 
# arguments which will then be passed to the function during evaluation.

model.add_layer()

@Sub.build()
def spf_dwy(n_maj_com=None, n_min_com=None, n_maj_ind=None, n_min_ind=None, 
    n_maj_res=None, n_min_res=None, n_other=None, N_maj_com=None, 
    N_min_com=None, N_maj_ind=None, N_min_ind=None, N_maj_res=None, 
    N_min_res=None, N_other=None, aadt=None, t=None, **kwargs):
    # Compute number of multiple-vehicle driveway-related collisions for a given
    # driveway type
    func = lambda n, N, aadt, t: n * N * ((aadt / 15000) ** t)
    # Compute for all driveway types
    n_tot = 0
    n_tot += func(n_maj_com, N_maj_com, aadt, t)
    n_tot += func(n_min_com, N_min_com, aadt, t)
    n_tot += func(n_maj_ind, N_maj_ind, aadt, t)
    n_tot += func(n_min_ind, N_min_ind, aadt, t)
    n_tot += func(n_maj_res, N_maj_res, aadt, t)
    n_tot += func(n_min_res, N_min_res, aadt, t)
    n_tot += func(n_other,   N_other,   aadt, t)
    return n_tot

@model.add_element
@SPF.build(refs={'spf_mv_dwy':{}})
def spf_mv_dwy_kabco(factype=None, aadt=None, n_maj_com=None, n_min_com=None, 
    n_maj_ind=None, n_min_ind=None, n_maj_res=None, n_min_res=None, 
    n_other=None, **kwargs):
    # Compute total crash frequency
    n = spf_dwy(aadt=aadt, n_maj_com=n_maj_com, n_min_com=n_min_com, 
        n_maj_ind=n_maj_ind, n_min_ind=n_min_ind, n_maj_res=n_maj_res, 
        n_min_res=n_min_res, n_other=n_other, **kwargs)
    return n

@Sub.build()
def spf(aadt=None, length=None, a=None, b=None, cf=None, **kwargs):
    """
    Based on HSM Equation 12-10. 
    """
    # Perform calculation
    n = math.exp(a + b * math.log(aadt) + math.log(length)) * cf
    return n

@model.add_element
@SPF.build(refs={'spf_mv_ndwy':{'severity':'kabco'}})
def spf_mv_ndwy_kabco(factype=None, aadt=None, length=None, **kwargs):
    n = spf(factype=factype, aadt=aadt, length=length, **kwargs)
    return n

@model.add_element
@SPF.build(refs={'spf_mv_ndwy':{'severity':'kabc'}})
def spf_mv_ndwy_kabc_unadjusted(factype=None, aadt=None, length=None, **kwargs):
    n = spf(factype=factype, aadt=aadt, length=length, **kwargs)
    return n

@model.add_element
@SPF.build(refs={'spf_mv_ndwy':{'severity':'o'}})
def spf_mv_ndwy_o_unadjusted(factype=None, aadt=None, length=None, **kwargs):
    n = spf(factype=factype, aadt=aadt, length=length, **kwargs)
    return n

@model.add_element
@SPF.build(refs={'spf_sv':{'severity':'kabco'}})
def spf_sv_kabco(factype=None, aadt=None, length=None, **kwargs):
    n = spf(factype=factype, aadt=aadt, length=length, **kwargs)
    return n

@model.add_element
@SPF.build(refs={'spf_sv':{'severity':'kabc'}})
def spf_sv_kabc_unadjusted(factype=None, aadt=None, length=None, **kwargs):
    n = spf(factype=factype, aadt=aadt, length=length, **kwargs)
    return n

@model.add_element
@SPF.build(refs={'spf_sv':{'severity':'o'}})
def spf_sv_o_unadjusted(factype=None, aadt=None, length=None, **kwargs):
    n = spf(factype=factype, aadt=aadt, length=length, **kwargs)
    return n

model.add_layer()

@model.add_element
@SPF.build(refs={'spf_mv_dwy':{}})
def spf_mv_dwy_kabc(spf_mv_dwy_kabco=None, p_kabc=None, **kwargs):
    # Compute severity frequency based on proportion
    n = spf_mv_dwy_kabco * p_kabc
    return n

@model.add_element
@SPF.build(refs={'spf_mv_dwy':{}})
def spf_mv_dwy_o(spf_mv_dwy_kabco=None, p_o=None, **kwargs):
    # Compute severity frequency based on proportion
    n = spf_mv_dwy_kabco * p_o
    return n

@model.add_element
@SPF.build()
def spf_mv_ndwy_kabc(spf_mv_ndwy_kabco=None, 
    spf_mv_ndwy_kabc_unadjusted=None, spf_mv_ndwy_o_unadjusted=None, **kwargs):
    # Compute adjusted frequency prediction
    n = spf_mv_ndwy_kabco * (spf_mv_ndwy_kabc_unadjusted / \
        (spf_mv_ndwy_kabc_unadjusted + spf_mv_ndwy_o_unadjusted))
    return n

@model.add_element
@SPF.build()
def spf_mv_ndwy_o(spf_mv_ndwy_kabco=None, 
    spf_mv_ndwy_kabc_unadjusted=None, spf_mv_ndwy_o_unadjusted=None, **kwargs):
    # Compute adjusted frequency prediction
    n = spf_mv_ndwy_kabco * (spf_mv_ndwy_o_unadjusted / \
        (spf_mv_ndwy_kabc_unadjusted + spf_mv_ndwy_o_unadjusted))
    return n

@model.add_element
@SPF.build()
def spf_sv_kabc(spf_sv_kabco=None, 
    spf_sv_kabc_unadjusted=None, spf_sv_o_unadjusted=None, **kwargs):
    # Compute adjusted frequency prediction
    n = spf_sv_kabco * (spf_sv_kabc_unadjusted / \
        (spf_sv_kabc_unadjusted + spf_sv_o_unadjusted))
    return n

@model.add_element
@SPF.build()
def spf_sv_o(spf_sv_kabco=None, 
    spf_sv_kabc_unadjusted=None, spf_sv_o_unadjusted=None, **kwargs):
    # Compute adjusted frequency prediction
    n = spf_sv_kabco * (spf_sv_o_unadjusted / \
        (spf_sv_kabc_unadjusted + spf_sv_o_unadjusted))
    return n

model.add_layer()

@model.add_element
@SPF.build()
def spf_kabco(spf_mv_dwy_kabco=None, spf_mv_ndwy_kabco=None, 
    spf_sv_kabco=None, **kwargs):
    return spf_mv_dwy_kabco + spf_mv_ndwy_kabco + spf_sv_kabco

@model.add_element
@SPF.build()
def spf_kabc(spf_mv_dwy_kabc=None, spf_mv_ndwy_kabc=None, 
    spf_sv_kabc=None, **kwargs):
    return spf_mv_dwy_kabc + spf_mv_ndwy_kabc + spf_sv_kabc

@model.add_element
@SPF.build()
def spf_o(spf_mv_dwy_o=None, spf_mv_ndwy_o=None, 
    spf_sv_o=None, **kwargs):
    return spf_mv_dwy_o + spf_mv_ndwy_o + spf_sv_o

model.add_layer()

@model.add_element
@Sub.build(refs={'spf_ped':{}})
def spf_ped_ref(spf_kabco=None, speed_cat=None, p_ped=None, **kwargs):
    n = spf_kabco * p_ped
    return n

@model.add_element
@SPF.build()
def spf_ped(speed=None, **kwargs):
    if speed <= 30:
        n = spf_ped_ref(speed_cat='<=30', **kwargs)
    else:
        n = spf_ped_ref(speed_cat='>30', **kwargs)
    return n

@model.add_element
@Sub.build(refs={'spf_pdc':{}})
def spf_pdc_ref(spf_kabco=None, speed_cat=None, p_pdc=None, **kwargs):
    n = spf_kabco * p_pdc
    return n

@model.add_element
@SPF.build()
def spf_pdc(speed=None, **kwargs):
    if speed <= 30:
        n = spf_pdc_ref(speed_cat='<=30', **kwargs)
    else:
        n = spf_pdc_ref(speed_cat='>30', **kwargs)
    return n


##############
# DEFINE AFS #
##############

# AFs are defined in a manner similar to the definition of other elements as 
# documented above and is only separated here for the sake of model readability 
# and documentation. All layer definition and element construction methods are 
# equivalent.

@model.add_element
@AF.build()
def af_parking(factype=None, parking_type=None, parking_prop=None, **kwargs):
    """
    On-Street Parking
    Based on Table 12-19, Equation 12-32.
    """
    # If no parking return default adjustment factor
    if parking_type in ['none', None]:
        return 1.0
    # Determine parking factor based on parking type and facility type
    if factype == "2u" or factype == "3t":
        if parking_type == "parallel_res":
            parking_factor = 1.465
        elif parking_type == "parallel_com":
            parking_factor = 2.074
        elif parking_type == "angle_res":
            parking_factor = 3.428
        elif parking_type == "angle_com":
            parking_factor = 4.853
    elif factype == "4u" or factype == "4d" or factype == "5t":
        if parking_type == "parallel_res":
            parking_factor = 1.100
        elif parking_type == "parallel_com":
            parking_factor = 1.709
        elif parking_type == "angle_res":
            parking_factor = 2.574
        elif parking_type == "angle_com":
            parking_factor = 3.999
    # Compute AF
    af = 1 + parking_prop * (parking_factor - 1)
    return af

@model.add_element
@AF.build()
def af_fo(factype=None, fo_density=None, fo_offset=None, **kwargs):
    """
    Roadside Fixed Objects
    Based on Tables 12-20, 12-21, Equation 12-33.
    """
    if fo_density == 0:
        af = 1.00
    else:
        # Enforce minimum offset value
        fo_offset = max(2.00, fo_offset)
        # Compute the offset factor
        # - Equation based on USA Segment spreadsheet model cell V5
        fo_offset_factor = (fo_offset ** -0.614) * 0.3566
        # Compute proportion of fixed object collisions
        if factype == "2u":
            fo_prop = 0.059
        elif factype == "3t":
            fo_prop = 0.034
        elif factype == "4u":
            fo_prop = 0.037
        elif factype == "4d":
            fo_prop = 0.036
        elif factype == "5t":
            fo_prop = 0.016
        # Compute AF
        af = fo_offset_factor * fo_density * fo_prop + (1 - fo_prop)
        af = max(1.00, af)
    return af

@model.add_element
@AF.build()
def af_median_width(factype=None, median_width=None, **kwargs):
    """
    Median Width
    Based on Tables 12-22
    """
    # Only compute AF for divided roadways, otherwise assume 1.00
    if factype in ['4d']:
        # Determine AF based on median width ranges
        # - Not present
        if median_width == 0:
            af = 1.00
            # Based on page 12-42: "The value of this CMF is 1.00 for undivided 
            # facilities"
        # - equals 10
        elif median_width <= 10:
            af = 1.01
        # - equals 15
        elif median_width < 20:
            af = 1.00
        # - equals 20
        elif median_width < 30:
            af = 0.99
        # - equals 30
        elif median_width < 40:
            af = 0.98
        # - equals 40
        elif median_width < 50:
            af = 0.97
        # - equals 50
        elif median_width < 60:
            af = 0.96
        # - equals 60
        elif median_width < 70:
            af = 0.95
        # - equals 70
        elif median_width < 80:
            af = 0.94
        # - equals 80
        elif median_width < 90:
            af = 0.93
        # - equals 90
        elif median_width < 100:
            af = 0.93
        # - equals 100
        else:
            af = 0.92
    else:
        af = 1.00 # Assumed
    return af

@model.add_element
@AF.build()
def af_lighting(lighting=None, factype=None, **kwargs):
    """
    Lighting
    Based on Tables 12-23, Equation 12-34
    """
    # If lighting is present, compute AF
    if lighting == 1:
        if factype == "2u":
            p_kabc  = 0.424
            p_o     = 0.576
            p_night = 0.316
        elif factype == "3t":
            p_kabc  = 0.429
            p_o     = 0.571
            p_night = 0.304
        elif factype == "4u":
            p_kabc  = 0.517
            p_o     = 0.483
            p_night = 0.365
        elif factype == "4d":
            p_kabc  = 0.364
            p_o     = 0.636
            p_night = 0.410
        elif factype == "5t":
            p_kabc  = 0.432
            p_o     = 0.568
            p_night = 0.274
        af = 1 - (p_night * (1 - 0.72 * p_kabc - 0.83 * p_o))
    # If lighting is not present, assume AF of 1.0
    else:
        af = 1.0
    return af

@model.add_element
@AF.build()
def af_ase(ase=None, **kwargs):
    """
    Automated Speed Enforcement
    Single value based on Chapter 17
    """
    if ase == 1:
        af = 0.95
    else:
        af = 1.0
    return af

model.add_layer()

@model.add_element
@AF.build()
def af_total(af_parking=None, af_fo=None, af_median_width=None, 
    af_lighting=None, af_ase=None, **kwargs):
    # Combine AFs
    af = af_parking * af_fo * af_median_width * af_lighting * af_ase
    return af


######################
# DEFINE CALIBRATION #
######################

# CFs are defined in a manner similar to the definition of other elements as 
# documented above and is only separated here for the sake of model readability 
# and documentation. All layer definition and element construction methods are 
# equivalent.

model.add_layer()

@model.add_element
@CF.build(refs={'calibration':{}})
def cf_total(cf=None, **kwargs):
    return cf


##################
# DEFINE RESULTS #
##################

# Results of model evaluation are defined in a manner somewhat different to all 
# other elements. The Result subclass requires an additional keyword argument 
# to be passed to the build() class method, namely the 'comp' parameter. This 
# requires a dictionary to be passed which defines the composition of the 
# result, that is, explicit designation of the crash type, crash severity, or 
# other defining characteristics of the result which may distinguish it from 
# another result which may be returned from the evaluation.

model.add_layer()

@model.add_element
@Result.build(comp=dict(severity='kabco', crash_type='mv_dwy'))
def pred_mv_dwy_kabco(spf_mv_dwy_kabco=None, af_total=None, cf_total=None, 
    num_years=None, **kwargs):
    res = spf_mv_dwy_kabco * af_total * cf_total * num_years
    return res

@model.add_element
@Result.build(comp=dict(severity='kabco', crash_type='mv_ndwy'))
def pred_mv_ndwy_kabco(spf_mv_ndwy_kabco=None, af_total=None, cf_total=None, 
    num_years=None, **kwargs):
    res = spf_mv_ndwy_kabco * af_total * cf_total * num_years
    return res

@model.add_element
@Result.build(comp=dict(severity='kabco', crash_type='sv'))
def pred_sv_kabco(spf_sv_kabco=None, af_total=None, cf_total=None, 
    num_years=None, **kwargs):
    res = spf_sv_kabco * af_total * cf_total * num_years
    return res

@model.add_element
@Result.build(comp=dict(severity='kabco', crash_type='all'))
def pred_kabco(spf_kabco=None, af_total=None, cf_total=None, 
    num_years=None, **kwargs):
    res = spf_kabco * af_total * cf_total * num_years
    return res

@model.add_element
@Result.build(comp=dict(severity='kabc', crash_type='all'))
def pred_kabc(spf_kabc=None, af_total=None, cf_total=None, 
    num_years=None, **kwargs):
    res = spf_kabc * af_total * cf_total * num_years
    return res

@model.add_element
@Result.build(comp=dict(severity='o', crash_type='all'))
def pred_o(spf_o=None, af_total=None, cf_total=None, 
    num_years=None, **kwargs):
    res = spf_o * af_total * cf_total * num_years
    return res

@model.add_element
@Result.build(comp=dict(severity='kabco', crash_type='ped'))
def pred_ped(spf_ped=None, af_total=None, cf_total=None, 
    num_years=None, **kwargs):
    res = spf_ped * af_total * cf_total * num_years
    return res

@model.add_element
@Result.build(comp=dict(severity='kabco', crash_type='pdc'))
def pred_pdc(spf_pdc=None, af_total=None, cf_total=None, 
    num_years=None, **kwargs):
    res = spf_pdc * af_total * cf_total * num_years
    return res


##########################
# DEFINE EMPIRICAL-BAYES #
##########################

# Empirical Bayes results are defined in a manner similar to the definition of 
# other results as documented above and is only separated here for the sake of 
# model readability and documentation. All layer definition and element 
# construction methods are equivalent.

model.add_layer()

@model.add_element
@Result.build(
    refs={'spf_mv_dwy':{'severity':'kabco'}},
    comp={'severity':'kabco', 'crash_type':'mv_dwy'}
)
def exp_mv_dwy_kabco(obs_mv_dwy_kabco=None, pred_mv_dwy_kabco=None, 
    k=None, **kwargs):
    """
    Expected Crash Computation
    """
    # Check for observed crash input
    if obs_mv_dwy_kabco is None or obs_mv_dwy_kabco == -1:
        e = -1
    else:
        # Compute weighted adjustment
        w = 1 / (1 + k * pred_mv_dwy_kabco)
        # Compute expected average crash frequency
        e = w * pred_mv_dwy_kabco + ((1 - w) * obs_mv_dwy_kabco)
    return e

@model.add_element
@Result.build(
    refs={'spf_mv_ndwy':{'severity':'kabco'}},
    comp={'severity':'kabco', 'crash_type':'mv_ndwy'})
def exp_mv_ndwy_kabco(obs_mv_ndwy_kabco=None, pred_mv_ndwy_kabco=None, 
    k=None, **kwargs):
    """
    Expected Crash Computation
    """
    # Check for observed crash input
    if obs_mv_ndwy_kabco is None or obs_mv_ndwy_kabco == -1:
        e = -1
    else:
        # Compute weighted adjustment
        w = 1 / (1 + k * pred_mv_ndwy_kabco)
        # Compute expected average crash frequency
        e = w * pred_mv_ndwy_kabco + ((1 - w) * obs_mv_ndwy_kabco)
    return e

@model.add_element
@Result.build(
    refs={'spf_sv':{'severity':'kabco'}},
    comp={'severity':'kabco', 'crash_type':'sv'})
def exp_sv_kabco(obs_sv_kabco=None, pred_sv_kabco=None, 
    k=None, **kwargs):
    """
    Expected Crash Computation
    """
    # Check for observed crash input
    if obs_sv_kabco is None or obs_sv_kabco == -1:
        e = -1
    else:
        # Compute weighted adjustment
        w = 1 / (1 + k * pred_sv_kabco)
        # Compute expected average crash frequency
        e = w * pred_sv_kabco + ((1 - w) * obs_sv_kabco)
    return e

model.add_layer()

@model.add_element
@Result.build(
    comp={'severity':'kabco', 'crash_type':'all'})
def exp_kabco(exp_mv_dwy_kabco=None, exp_mv_ndwy_kabco=None, 
    exp_sv_kabco=None, **kwargs):
    """
    Expected Crash Computation
    """
    e = exp_mv_dwy_kabco + exp_mv_ndwy_kabco + exp_sv_kabco
    return e


##############
# LOCK MODEL #
##############

# At the end of the model definition file, the model should be locked using the 
# lock() method. This protects the model from accidental modification once it 
# has been loaded. This can be undone at runtime if necessary using the 
# unlock() method.

model.lock()
