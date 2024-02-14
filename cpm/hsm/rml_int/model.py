#######################
# IMPORT DEPENDENCIES #
#######################

import math, os
from cpm.base import Model, SPF, AF, CF, Sub, Result, Limits, Values, Reference


################
# DEFINE MODEL #
################

model = Model(name='rml_int')


#####################
# DEFINE REFERENCES #
#####################

fd = os.path.dirname(os.path.abspath(__file__))
fp = lambda fn: os.path.join(fd,fn)
model.add_reference(Reference(fp('calibration.json')))
model.add_reference(Reference(fp('spf.json')))


#####################
# DEFINE VALIDATORS #
#####################

# AADT
model.add_validator(
    Limits(key='aadt_maj', vmin=1, vmax=78300, enforce='warn',
        conditions={'factype':['3st']}))
model.add_validator(
    Limits(key='aadt_maj', vmin=1, vmax=78300, enforce='warn', 
        conditions={'factype':['4st']}))
model.add_validator(
    Limits(key='aadt_maj', vmin=1, vmax=43500, enforce='warn', 
        conditions={'factype':['4sg']}))

model.add_validator(
    Limits(key='aadt_min', vmin=1, vmax=23000, enforce='warn', 
        conditions={'factype':['3st']}))
model.add_validator(
    Limits(key='aadt_min', vmin=1, vmax=7400,  enforce='warn', 
        conditions={'factype':['4st']}))
model.add_validator(
    Limits(key='aadt_min', vmin=1, vmax=18500, enforce='warn', 
        conditions={'factype':['4sg']}))
    
# Facility Type
model.add_validator(
    Values(key='factype', values=('3st','4st','4sg'), 
        notes=['3st: 3-leg stop-controlled','4st: 4-leg stop-controlled',
            '4sg: 4-leg signalized']))

# Operational Information
model.add_validator(
    Limits(key='skew', vmax=90, vmin=-90))
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


def spf(aadt_maj=None, aadt_min=None, a=None, b=None, c=None, d=None, cf=None, 
    **kwargs):
    """
    Based on HSM Equations 11-11 and 11-12. 
    """
    # Perform calculation
    n = math.exp(a + b * math.log(aadt_maj) + \
        c * math.log(aadt_min) + d * math.log(aadt_maj + aadt_min)) * cf
    return n

@model.add_spf(refs=dict(spf=dict(severity='kabco')))
def spf_kabco(factype=None, aadt_maj=None, aadt_min=None, **kwargs):
    return spf(aadt_maj=aadt_maj, aadt_min=aadt_min, **kwargs)
        
@model.add_spf(refs=dict(spf=dict(severity='kabc')))
def spf_kabc(factype=None, aadt_maj=None, aadt_min=None, **kwargs):
    return spf(aadt_maj=aadt_maj, aadt_min=aadt_min, **kwargs)
        
@model.add_spf(refs=dict(spf=dict(severity='kab')))
def spf_kab(factype=None, aadt_maj=None, aadt_min=None, **kwargs):
    return spf(aadt_maj=aadt_maj, aadt_min=aadt_min, **kwargs)
        

##############
# DEFINE AFS #
##############

# KABCO
@model.add_af()
def af_skew_kabco(factype=None, skew=None, **kwargs):
    """
    Intersection Angle
    Based on Tables 11-20, 11-21, Equations 11-18, 11-19
    """
    if factype == '3st':
        af = (0.016 * skew) / (0.98 + 0.016 * skew) + 1.00 
    elif factype == '4st':
        af = (0.053 * skew) / (1.43 + 0.053 * skew) + 1.00
    elif factype == '4sg':
        af = 1.00
    return af

@model.add_af()
def af_left_turn_lanes_kabco(factype=None, left_turn_lanes=None, **kwargs):
    """
    Left-Turn Lane on Major Road
    Based on Tables 11-20, 11-21, 11-22
    """
    # Compute adjustment factor
    if factype == '3st':
        af = 0.56 ** min(1, left_turn_lanes)
    elif factype == '4st':
        af = 0.72 ** min(2, left_turn_lanes)
    elif factype == '4sg':
        af = 1.00
    return af

@model.add_af()
def af_right_turn_lanes_kabco(factype=None, right_turn_lanes=None, **kwargs):
    """
    Right-Turn Lane on Major Road
    Based on Tables 11-20, 11-21, 11-23
    """
    # Compute adjustment factor
    if factype == '3st':
        af = 0.86 ** min(1, right_turn_lanes)
    elif factype == '4st':
        af = 0.86 ** min(2, right_turn_lanes)
    elif factype == '4sg':
        af = 1.00
    return af

# KABC
@model.add_af()
def af_skew_kabc(factype=None, skew=None, **kwargs):
    """
    Intersection Angle
    Based on Tables 11-20, 11-21, Equations 11-20, 11-21
    """
    if factype == '3st':
        af = (0.017 * skew) / (0.52 + 0.017 * skew) + 1.00
    elif factype == '4st':
        af = (0.048 * skew) / (0.72 + 0.048 * skew) + 1.00
    elif factype == '4sg':
        af = 1.00
    return af

@model.add_af()
def af_left_turn_lanes_kabc(factype=None, left_turn_lanes=None, **kwargs):
    """
    Left-Turn Lane on Major Road
    Based on Tables 11-20, 11-21, 11-22
    """
    # Compute adjustment factor
    if factype == '3st':
        af = 0.45 ** min(1, left_turn_lanes)
    elif factype == '4st':
        af = 0.65 ** min(2, left_turn_lanes)
    elif factype == '4sg':
        af = 1.00
    return af

@model.add_af()
def af_right_turn_lanes_kabc(factype=None, right_turn_lanes=None, **kwargs):
    """
    Right-Turn Lane on Major Road
    Based on Tables 11-20, 11-21, 11-23
    """
    # Compute adjustment factor
    if factype == '3st':
        af = 0.77 ** min(1, right_turn_lanes)
    elif factype == '4st':
        af = 0.77 ** min(2, right_turn_lanes)
    elif factype == '4sg':
        af = 1.00
    return af

# Other
@model.add_af()
def af_lighting(factype=None, lighting=None, **kwargs):
    """
    Intersection Lighting
    Based on Tables 11-20, 11-21, Equations 11-22

    Optional kwargs
    ---------------
    p_night : float
        Proportion of total crashes that occur at night.
    """
    if not lighting:
        af = 1.00
    else:
        if factype == '3st':
            p_night = kwargs.get('p_night', 0.276)
        elif factype == '4st':
            p_night = kwargs.get('p_night', 0.273)
        else:
            p_night = 0.00
        af = 1.00 - 0.38 * p_night
    return af

model.add_layer()

@model.add_af()
def af_total_kabco(af_skew_kabco=None, af_left_turn_lanes_kabco=None, 
    af_right_turn_lanes_kabco=None, af_lighting=None, **kwargs):
    """
    Combine all adjustment factors which apply to all crash severities.
    """
    # Combine AFs
    af = af_skew_kabco * af_left_turn_lanes_kabco * af_right_turn_lanes_kabco \
        * af_lighting
    return af
    
@model.add_af()
def af_total_kabc(af_skew_kabc=None, af_left_turn_lanes_kabc=None, 
    af_right_turn_lanes_kabc=None, af_lighting=None, **kwargs):
    """
    Combine all adjustment factors which apply to fatal and injury crash 
    severities.
    """
    # Combine AFs
    af = af_skew_kabc * af_left_turn_lanes_kabc * af_right_turn_lanes_kabc \
        * af_lighting
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
def pred_kabco(spf_kabco=None, af_total_kabco=None, cf_total=None, 
    num_years=None, **kwargs):
    res = spf_kabco * af_total_kabco * cf_total * num_years
    return res

@model.add_result(comp=dict(severity='kabc', crash_type='all'))
def pred_kabc(spf_kabc=None, af_total_kabc=None, cf_total=None, 
    num_years=None, **kwargs):
    res = spf_kabc * af_total_kabc * cf_total * num_years
    return res

model.add_layer()

@model.add_result(comp=dict(severity='o', crash_type='all'))
def pred_o(pred_kabco=None, pred_kabc=None, **kwargs):
    res = pred_kabco - pred_kabc
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
