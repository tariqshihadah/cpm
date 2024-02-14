#######################
# IMPORT DEPENDENCIES #
#######################

import math, os
from cpm.base import Model, SPF, AF, CF, Sub, Result, Limits, Values, Reference


################
# DEFINE MODEL #
################

model = Model(name='rtl_int')


#####################
# DEFINE REFERENCES #
#####################

fd = os.path.dirname(os.path.abspath(__file__))
fp = lambda fn: os.path.join(fd,fn)
model.add_reference(Reference(fp('calibration.json')))
model.add_reference(Reference(fp('spf.json')))
model.add_reference(Reference(fp('dist_all.json')))


#####################
# DEFINE VALIDATORS #
#####################

# AADT
model.add_validator(
    Limits(key='aadt_maj', vmin=1, vmax=19500, enforce='warn',
        conditions={'factype':['3st']}))
model.add_validator(
    Limits(key='aadt_maj', vmin=1, vmax=14700, enforce='warn',
        conditions={'factype':['4st']}))
model.add_validator(
    Limits(key='aadt_maj', vmin=1, vmax=25200, enforce='warn',
        conditions={'factype':['4sg']}))

model.add_validator(
    Limits(key='aadt_min', vmin=1, vmax=4300, enforce='warn',
        conditions={'factype':['3st']}))
model.add_validator(
    Limits(key='aadt_min', vmin=1, vmax=3500, enforce='warn',
        conditions={'factype':['4st']}))
model.add_validator(
    Limits(key='aadt_min', vmin=1, vmax=12500, enforce='warn',
        conditions={'factype':['4sg']}))

# Facility Type
model.add_validator(
    Values(key='factype', values=('3st','4st','4sg'), 
        notes=['3st: 3-leg stop-controlled','4st: 4-leg stop-controlled',
            '4sg: 4-leg signalized']))

# Operational Information
model.add_validator(
    Limits(key='skew', vmin=0, vmax=90))
model.add_validator(
    Values(key='lighting', values=(0,1), notes='0: not present; 1: present'))

model.add_validator(
    Limits(key='left_turn_lanes', vmin=0, vmax=3, dtype=int,
        conditions={'factype':['3st']}))
model.add_validator(
    Limits(key='left_turn_lanes', vmin=0, vmax=4, dtype=int,
        conditions={'factype':['4st','4sg']}))

model.add_validator(
    Limits(key='right_turn_lanes', vmin=0, vmax=3, dtype=int,
        conditions={'factype':['3st']}))
model.add_validator(
    Limits(key='right_turn_lanes', vmin=0, vmax=4, dtype=int,
        conditions={'factype':['4st','4sg']}))

# Historic Crash Information
model.add_validator(
    Limits(key='obs_kabco', vmin=-1, vmax=1e3, enforce='warn',
        notes='If historic crash data is unavailable, enter -1 to skip EB \
analysis.'))
model.add_validator(
    Limits(key='num_years', vmin=0, vmax=1e2, dtype=float, enforce='warn'))


###############
# DEFINE SPFS #
###############

model.add_layer()

def spf(aadt_maj=None, aadt_min=None, a=None, b=None, c=None, cf=None, 
    **kwargs):
    """
    Based on HSM Equations 10-8, 10-9, 10-10. 
    """
    # Perform calculation
    n = math.exp(a + b * math.log(aadt_maj) + \
        c * math.log(aadt_min)) * cf
    return n

@model.add_spf(refs=dict(spf=dict(severity='kabco')))
def spf_kabco(factype=None, aadt_maj=None, aadt_min=None, **kwargs):
    return spf(aadt_maj=aadt_maj, aadt_min=aadt_min, **kwargs)

model.add_layer()

@model.add_spf(refs=dict(dist_all={}))
def spf_kabc(factype=None, spf_kabco=None, k=None, a=None, b=None, c=None, 
    **kwargs):
    n = spf_kabco * (k + a + b + c)
    return n

@model.add_spf(refs=dict(dist_all={}))
def spf_o(factype=None, spf_kabco=None, o=None, **kwargs):
    n = spf_kabco * (o)
    return n


##############
# DEFINE AFS #
##############

@model.add_af()
def af_skew(factype=None, skew=None, **kwargs):
    """
    Intersection Angle
    Based on Equations 10-22, 10-23
    """
    if factype == '3st':
        af = math.exp(0.0040 * skew)
    elif factype == '4st':
        af = math.exp(0.0054 * skew)
    elif factype == '4sg':
        af = 1.00
    return af

@model.add_af()
def af_left_turn_lanes(factype=None, left_turn_lanes=None, **kwargs):
    """
    Left-Turn Lane on Major Road
    Based on Tables 10-13
    """
    # Compute adjustment factor
    if factype == '3st':
        af = 0.56 ** min(2, left_turn_lanes)
    elif factype == '4st':
        af = 0.72 ** min(2, left_turn_lanes)
    elif factype == '4sg':
        af = 0.82 ** min(4, left_turn_lanes)
    return af

@model.add_af()
def af_right_turn_lanes(factype=None, right_turn_lanes=None, **kwargs):
    """
    Right-Turn Lane on Major Road
    Based on Tables 10-14
    """
    # Compute adjustment factor
    if factype == '3st':
        af = 0.86 ** min(2, right_turn_lanes)
    elif factype == '4st':
        af = 0.86 ** min(2, right_turn_lanes)
    elif factype == '4sg':
        af = 0.96 ** min(4, right_turn_lanes)
    return af

@model.add_af()
def af_lighting(factype=None, lighting=None, **kwargs):
    """
    Intersection Lighting
    Based on Table 10-15 and Equation 10-24

    Optional kwargs
    ---------------
    p_night : float
        Proportion of total crashes that occur at night.
    """
    if not lighting:
        af = 1.00
    else:
        if factype == '3st':
            p_night = kwargs.get('p_night', 0.260)
        elif factype == '4st':
            p_night = kwargs.get('p_night', 0.244)
        elif factype == '4sg':
            p_night = kwargs.get('p_night', 0.286)
        af = 1.00 - 0.38 * p_night
    return af

model.add_layer()

@model.add_af()
def af_total(af_skew=None, af_left_turn_lanes=None, 
    af_right_turn_lanes=None, af_lighting=None, **kwargs):
    """
    Combine all adjustment factors.
    """
    # Combine AFs
    af = af_skew * af_left_turn_lanes * af_right_turn_lanes * af_lighting
    return af
    

######################
# DEFINE CALIBRATION #
######################

model.add_layer()

@model.add_cf(refs={'calibration':{}})
def cf_total(cf=None, **kwargs):
    return cf


##################
# DEFINE RESULTS #
##################

model.add_layer()

@model.add_result(comp=dict(severity='kabco', crash_type='all'))
def pred_kabco(spf_kabco=None, af_total=None, cf_total=None, 
    num_years=None, **kwargs):
    res = spf_kabco * af_total * cf_total * num_years
    return res

@model.add_result(comp=dict(severity='kabc', crash_type='all'))
def pred_kabc(spf_kabc=None, af_total=None, cf_total=None, 
    num_years=None, **kwargs):
    res = spf_kabc * af_total * cf_total * num_years
    return res

@model.add_result(comp=dict(severity='o', crash_type='all'))
def pred_o(spf_o=None, af_total=None, cf_total=None, 
    num_years=None, **kwargs):
    res = spf_o * af_total * cf_total * num_years
    return res


##########################
# DEFINE EMPIRICAL-BAYES #
##########################

model.add_layer()

@model.add_result(
    refs={'spf':{'severity':'kabco'}},
    comp={'severity':'kabco', 'crash_type':'all'})
def exp_kabco(obs_kabco=None, pred_kabco=None, k=None, **kwargs):
    """
    Expected Crash Computation
    """
    # Check for observed crash input
    if obs_kabco is None or obs_kabco == -1:
        e = -1
    else:
        # Compute weighted adjustment
        w = 1 / (1 + k * pred_kabco)
        # Compute expected average crash frequency
        e = w * pred_kabco + ((1 - w) * obs_kabco)
    return e


##############
# LOCK MODEL #
##############

model.lock()
