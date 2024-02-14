#######################
# IMPORT DEPENDENCIES #
#######################

import math, os
from cpm.base import Model, SPF, AF, CF, Sub, Result, Limits, Values, Reference


################
# DEFINE MODEL #
################

model = Model(name='usa_int')


#####################
# DEFINE REFERENCES #
#####################

fd = os.path.dirname(os.path.abspath(__file__))
fp = lambda fn: os.path.join(fd,fn)
model.add_reference(Reference(fp('calibration.json')))
model.add_reference(Reference(fp('spf_mv.json')))
model.add_reference(Reference(fp('spf_sv.json')))
model.add_reference(Reference(fp('spf_ped.json')))
model.add_reference(Reference(fp('spf_pdc.json')))
model.add_reference(Reference(fp('dist_mv.json')))


#####################
# DEFINE VALIDATORS #
#####################

# AADT
model.add_validator(
    Limits(key='aadt_maj', vmin=1, vmax=45700, enforce='warn',
        conditions={'factype':['3st']}))
model.add_validator(
    Limits(key='aadt_maj', vmin=1, vmax=46800, enforce='warn', 
        conditions={'factype':['4st']}))
model.add_validator(
    Limits(key='aadt_maj', vmin=1, vmax=58100, enforce='warn', 
        conditions={'factype':['3sg']}))
model.add_validator(
    Limits(key='aadt_maj', vmin=1, vmax=67700, enforce='warn', 
        conditions={'factype':['4sg']}))

model.add_validator(
    Limits(key='aadt_min', vmin=1, vmax=9300, enforce='warn', 
        conditions={'factype':['3st']}))
model.add_validator(
    Limits(key='aadt_min', vmin=1, vmax=5900,  enforce='warn', 
        conditions={'factype':['4st']}))
model.add_validator(
    Limits(key='aadt_min', vmin=1, vmax=16400, enforce='warn', 
        conditions={'factype':['3sg']}))
model.add_validator(
    Limits(key='aadt_min', vmin=1, vmax=33400, enforce='warn', 
        conditions={'factype':['4sg']}))

# Pedestrian Information
model.add_validator(
    Limits(key='ped_vol', vmin=1, vmax=34200, enforce='warn'))
model.add_validator(
    Limits(key='ped_lanes_crossed', vmin=0, vmax=16, dtype=int,
        notes='Maximum number of lanes to be crossed by a pedestrian'))

# Facility Type
model.add_validator(
    Values(key='factype', values=('3st','4st','3sg','4sg'), 
        notes=['3st: 3-leg stop-controlled','4st: 4-leg stop-controlled',
            '3sg: 3-leg signalized','4sg: 4-leg signalized']))

# Operational Information
model.add_validator(
    Limits(key='left_turn_lanes', vmin=0, vmax=3, dtype=int,
        conditions={'factype':['3st','3sg']}))
model.add_validator(
    Limits(key='left_turn_lanes', vmin=0, vmax=4, dtype=int,
        conditions={'factype':['4st','4sg']}))

model.add_validator(
    Limits(key='left_turn_prot', vmin=0, vmax=3, dtype=int, 
        subtract='left_turn_prot_perm', conditions={'factype':['3st','3sg']}))
model.add_validator(
    Limits(key='left_turn_prot', vmin=0, vmax=4, dtype=int, 
        subtract='left_turn_prot_perm', conditions={'factype':['4st','4sg']}))

model.add_validator(
    Limits(key='left_turn_prot_perm', vmin=0, vmax=3, dtype=int,
        conditions={'factype':['3st','3sg']}))
model.add_validator(
    Limits(key='left_turn_prot_perm', vmin=0, vmax=4, dtype=int,
        conditions={'factype':['4st','4sg']}))

model.add_validator(
    Limits(key='right_turn_lanes', vmin=0, vmax=3, dtype=int,
        conditions={'factype':['3st','3sg']}))
model.add_validator(
    Limits(key='right_turn_lanes', vmin=0, vmax=4, dtype=int,
        conditions={'factype':['4st','4sg']}))

model.add_validator(
    Limits(key='right_on_red_prohibited', vmin=0, vmax=3, dtype=int,
        conditions={'factype':['3st','3sg']}))
model.add_validator(
    Limits(key='right_on_red_prohibited', vmin=0, vmax=4, dtype=int,
        conditions={'factype':['4st','4sg']}))

model.add_validator(
    Values(key='red_light_cameras', values=(0,1), dtype=int, 
        notes='0: not present; 1: present'))

# Location Information
model.add_validator(
    Values(key='lighting', values=(0,1), dtype=int, 
        notes='0: not present; 1: present'))
model.add_validator(
    Limits(key='bus_stops', vmin=0, vmax=20, enforce='snap', dtype=int))
model.add_validator(
    Limits(key='schools', vmin=0, vmax=1, enforce='snap', dtype=int))
model.add_validator(
    Limits(key='alcohol_sales', vmin=0, vmax=20, enforce='snap', dtype=int))

# Historic Crash Information
model.add_validator(
    Limits(key='obs_mv_kabco', vmin=-1, vmax=1e3, enforce='warn',
        notes='If historic crash data is unavailable, enter -1 to skip EB \
analysis.'))
model.add_validator(
    Limits(key='obs_sv_kabco', vmin=-1, vmax=1e3, enforce='warn',
        notes='If historic crash data is unavailable, enter -1 to skip EB \
analysis.'))
model.add_validator(
    Limits(key='num_years', vmin=0, vmax=1e2, dtype=float, enforce='warn'))


###############
# DEFINE SPFS #
###############

model.add_layer()

def spf(aadt_maj=None, aadt_min=None, a=None, b=None, c=None, p_sev=None, 
    cf=None, **kwargs):
    """
    Based on HSM Equation 12-21. 
    """
    # Perform calculation
    n = math.exp(a + b * math.log(aadt_maj) + c * math.log(aadt_min)) \
        * cf * p_sev
    return n

@model.add_spf(refs={'spf_mv':{'severity':'kabco'}})
def spf_mv_kabco(factype=None, aadt_maj=None, aadt_min=None, **kwargs):
    n = spf(factype=factype, aadt_maj=aadt_maj, aadt_min=aadt_min, **kwargs)
    return n

@model.add_spf(refs={'spf_mv':{'severity':'kabc'}})
def spf_mv_kabc_unadjusted(factype=None, aadt_maj=None, aadt_min=None, **kwargs):
    n = spf(factype=factype, aadt_maj=aadt_maj, aadt_min=aadt_min, **kwargs)
    return n

@model.add_spf(refs={'spf_mv':{'severity':'o'}})
def spf_mv_o_unadjusted(factype=None, aadt_maj=None, aadt_min=None, **kwargs):
    n = spf(factype=factype, aadt_maj=aadt_maj, aadt_min=aadt_min, **kwargs)
    return n

@model.add_spf(refs={'spf_sv':{'severity':'kabco'}})
def spf_sv_kabco(factype=None, aadt_maj=None, aadt_min=None, **kwargs):
    n = spf(factype=factype, aadt_maj=aadt_maj, aadt_min=aadt_min, **kwargs)
    return n

@model.add_spf(refs={'spf_sv':{'severity':'kabc'}})
def spf_sv_kabc_unadjusted(factype=None, aadt_maj=None, aadt_min=None, **kwargs):
    n = spf(factype=factype, aadt_maj=aadt_maj, aadt_min=aadt_min, **kwargs)
    return n

@model.add_spf(refs={'spf_sv':{'severity':'o'}})
def spf_sv_o_unadjusted(factype=None, aadt_maj=None, aadt_min=None, **kwargs):
    n = spf(factype=factype, aadt_maj=aadt_maj, aadt_min=aadt_min, **kwargs)
    return n

model.add_layer()

@model.add_spf()
def spf_mv_kabc(spf_mv_kabco=None, 
    spf_mv_kabc_unadjusted=None, spf_mv_o_unadjusted=None, **kwargs):
    # Compute adjusted frequency prediction
    n = spf_mv_kabco * (spf_mv_kabc_unadjusted / \
        (spf_mv_kabc_unadjusted + spf_mv_o_unadjusted))
    return n

@model.add_spf()
def spf_mv_o(spf_mv_kabco=None, 
    spf_mv_kabc_unadjusted=None, spf_mv_o_unadjusted=None, **kwargs):
    # Compute adjusted frequency prediction
    n = spf_mv_kabco * (spf_mv_o_unadjusted / \
        (spf_mv_kabc_unadjusted + spf_mv_o_unadjusted))
    return n

@model.add_spf()
def spf_sv_kabc(spf_sv_kabco=None, 
    spf_sv_kabc_unadjusted=None, spf_sv_o_unadjusted=None, **kwargs):
    # Compute adjusted frequency prediction
    n = spf_sv_kabco * (spf_sv_kabc_unadjusted / \
        (spf_sv_kabc_unadjusted + spf_sv_o_unadjusted))
    return n

@model.add_spf()
def spf_sv_o(spf_sv_kabco=None, 
    spf_sv_kabc_unadjusted=None, spf_sv_o_unadjusted=None, **kwargs):
    # Compute adjusted frequency prediction
    n = spf_sv_kabco * (spf_sv_o_unadjusted / \
        (spf_sv_kabc_unadjusted + spf_sv_o_unadjusted))
    return n

model.add_layer()

@model.add_spf()
def spf_kabco(spf_mv_kabco=None, spf_sv_kabco=None, **kwargs):
    return spf_mv_kabco + spf_sv_kabco

@model.add_spf()
def spf_kabc(spf_mv_kabc=None, spf_sv_kabc=None, **kwargs):
    return spf_mv_kabc + spf_sv_kabc

@model.add_spf()
def spf_o(spf_mv_o=None, spf_sv_o=None, **kwargs):
    return spf_mv_o + spf_sv_o

model.add_layer()

@model.add_sub(refs={'spf_ped':{}})
def spf_ped_sg(factype=None, ped_vol=None, ped_lanes_crossed=None, 
    aadt_maj=None, aadt_min=None, a=None, b=None, c=None, d=None, e=None, 
    cf=None, **kwargs):
    """
    Based on HSM Equation 12-29. 
    """
    # Perform calculation
    n = math.exp(a + b * math.log(aadt_maj + aadt_min) + \
        c * math.log(aadt_min / aadt_maj) + d * math.log(ped_vol) + \
        e * ped_lanes_crossed)
    return n

@model.add_sub(refs={'spf_ped':{}})
def spf_ped_st(spf_kabco=None, factype=None, p_ped=None, **kwargs):
    """
    Based on HSM Equation 12-30.
    """
    n = spf_kabco * p_ped
    return n

model.add_layer()

@model.add_spf()
def spf_ped(factype=None, ped_vol=None, ped_lanes_crossed=None, 
    aadt_maj=None, aadt_min=None, spf_ped_sg=None, spf_ped_st=None, **kwargs):
    # Determine which model to use based on facility type
    if factype in ['3sg','4sg']:
        n = spf_ped_sg
    elif factype in ['3st','4st']:
        n = spf_ped_st
    else:
        raise ValueError("Invalid facility type for computing pedestrian \
crashes.")
    return n

@model.add_spf(refs={'spf_pdc':{}})
def spf_pdc(spf_kabco=None, p_pdc=None, **kwargs):
    """
    Based on HSM Equation 12-31.
    """
    n = spf_kabco * p_pdc
    return n


##############
# DEFINE AFS #
##############

@model.add_af()
def af_left_turn_lanes(factype=None, left_turn_lanes=None, **kwargs):
    """
    Intersection Left-Turn Lanes
    Based on Table 12-24
    """
    # Validate number of left turn lanes
    if left_turn_lanes > int(factype[0]):
        raise ValueError(f'Too many approaches with left-turn lanes for the \
indicated facility type ({left_turn_lanes}, {factype})')
    # Compute adjustment factor
    if factype == '3st':
        af = 0.67 ** min(2, left_turn_lanes)
    elif factype == '4st':
        af = 0.73 ** min(2, left_turn_lanes)
    elif factype == '3sg':
        af = 0.93 ** min(3, left_turn_lanes)
    elif factype == '4sg':
        af = 0.90 ** min(4, left_turn_lanes)
    return af

@model.add_af()
def af_left_turn_phasing(factype=None, left_turn_prot=None, 
    left_turn_prot_perm=None, **kwargs):
    """
    Intersection Left-Turn Signal Phasing
    Based on Table 12-25
    """
    # Validate number of approaches with left-turn phasing
    if left_turn_prot + left_turn_prot_perm > int(factype[0]):
        raise ValueError(f'Too many approaches with left-turn phasing for the \
indicated facility type ({left_turn_prot + left_turn_prot_perm}, {factype})')
    # Compute adjustment factor
    if factype in ['3st','4st']:
        af = 1.00
    elif factype in ['3sg','4sg']:
        af = (0.94 ** left_turn_prot) * (0.99 ** left_turn_prot_perm)
    return af

@model.add_af()
def af_right_turn_lanes(factype=None, right_turn_lanes=None, **kwargs):
    """
    Intersection Right-Turn Lanes
    Based on Table 12-26
    """
    # Validate number of left turn lanes
    if right_turn_lanes > int(factype[0]):
        raise ValueError(f'Too many approaches with right-turn lanes for the \
indicated facility type ({right_turn_lanes}, {factype})')
    # Compute adjustment factor
    if factype == '3st':
        af = 0.86 ** min(2, right_turn_lanes)
    elif factype == '4st':
        af = 0.86 ** min(2, right_turn_lanes)
    elif factype == '3sg':
        af = 0.96 ** min(2, right_turn_lanes)
    elif factype == '4sg':
        af = 0.96 ** min(4, right_turn_lanes)
    return af

@model.add_af()
def af_right_on_red(factype=None, right_on_red_prohibited=None, **kwargs):
    """
    Right-Turn on Red
    Based on Equation 12-35
    """
    # Validate number of approaches with left-turn phasing
    if right_on_red_prohibited > int(factype[0]):
        raise ValueError(f'Too many approaches with right-turn on red \
prohibited for the indicated facility type ({right_on_red_prohibited}, \
{factype})')
    # Compute adjustment factor
    if factype in ['3st','4st']:
        af = 1.00
    elif factype in ['3sg','4sg']:
        af = (0.98 ** right_on_red_prohibited)
    return af

@model.add_af()
def af_lighting(factype=None, lighting=None, **kwargs):
    """
    Lighting
    Based on Tables 12-27, Equation 12-36
    """
    # Check for presence of lighting
    if lighting == 0:
        af = 1.00
    elif lighting == 1:
        # Define proportion of nighttime crashes by facility type
        p_night_factype = {
            '3st': 0.238,
            '4st': 0.229,
            '3sg': 0.235,
            '4sg': 0.235,
        }
        # Identify the proportion for the given facility type
        p_night = p_night_factype[factype]
        # Compute the adjustment factor
        af = 1 - 0.38 * p_night
    return af

@model.add_af(refs={'dist_mv':{}})
def af_red_light_cameras(factype=None, red_light_cameras=None, p_ang_kabc=None, 
    p_ang_o=None, p_re_kabc=None, p_re_o=None, spf_mv_kabc=None, spf_mv_o=None, 
    spf_sv_kabco=None, **kwargs):
    """
    Red-Light Cameras
    Based on Table 12-11, Equations 12-37, 12-38, 12-39
    """
    # Check for presence of red light running cameras
    if not red_light_cameras:
        af = 1.00
    else:
        # Determine adjustment factor
        if factype in ['3st','4st']:
            af = 1.00
        elif factype in ['3sg','4sg']:
            # Compute proportions of angle and rear-end crashes
            p_ang_kabco = ((p_ang_kabc * spf_mv_kabc) + (p_ang_o * spf_mv_o)) \
                / (spf_mv_kabc + spf_mv_o + spf_sv_kabco)
            p_re_kabco  = ((p_re_kabc * spf_mv_kabc) + (p_re_o * spf_mv_o)) \
                / (spf_mv_kabc + spf_mv_o + spf_sv_kabco)
            # Compute adjustment factor
            af_ang = 0.74 # per Chapter 14 reference on page 12-45
            af_re  = 1.18 # per Chapter 14 reference on page 12-45
            af = 1 - p_ang_kabco * (1 - af_ang) - p_re_kabco * (1 - af_re)
    return af

@model.add_af()
def af_bus_stops(factype=None, bus_stops=None, **kwargs):
    """
    Bus Stops
    Based on Table 12-28
    NOTE: Only applicable to vehicle-pedestrian collisions at signalized 
    intersections
    """
    # Compute adjustment factor
    if factype in ['3st','4st']:
        af = 1.00
    elif factype in ['3sg','4sg']:
        if bus_stops == 0:
            af = 1.00
        elif bus_stops < 3:
            af = 2.78
        else:
            af = 4.15
    return af

@model.add_af()
def af_schools(factype=None, schools=None, **kwargs):
    """
    Schools
    Based on Table 12-29
    NOTE: Only applicable to vehicle-pedestrian collisions at signalized 
    intersections
    """
    # Compute adjustment factor
    if factype in ['3st','4st']:
        af = 1.00
    elif factype in ['3sg','4sg']:
        if schools == 0:
            af = 1.00
        else:
            af = 1.35
    return af

@model.add_af()
def af_alcohol_sales(factype=None, alcohol_sales=None, **kwargs):
    """
    Alcohol Sales Establishments
    Based on Table 12-30
    NOTE: Only applicable to vehicle-pedestrian collisions at signalized 
    intersections
    """
    # Compute adjustment factor
    if factype in ['3st','4st']:
        af = 1.00
    elif factype in ['3sg','4sg']:
        if alcohol_sales == 0:
            af = 1.00
        elif alcohol_sales < 9:
            af = 1.12
        else:
            af = 1.56
    return af

model.add_layer()

@model.add_af()
def af_total(af_left_turn_lanes=None, af_left_turn_phasing=None, 
    af_right_turn_lanes=None, af_right_on_red=None, af_lighting=None, 
    af_red_light_cameras=None, **kwargs):
    """
    Combine all adjustment factors which apply to general crash types.
    """
    # Combine AFs
    af = af_left_turn_lanes * af_left_turn_phasing * af_right_turn_lanes * \
        af_right_on_red * af_lighting * af_red_light_cameras
    return af

@model.add_af()
def af_ped(af_bus_stops=None, af_schools=None, af_alcohol_sales=None, **kwargs):
    """
    Combine all adjustment factors which apply to vehicle-pedestrian collisions.
    """
    # Combine AFs
    af = af_bus_stops * af_schools * af_alcohol_sales
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

@model.add_result(comp=dict(severity='kabco', crash_type='mv'))
def pred_mv_kabco(spf_mv_kabco=None, af_total=None, cf_total=None, 
    num_years=None, **kwargs):
    res = spf_mv_kabco * af_total * cf_total * num_years
    return res

@model.add_result(comp=dict(severity='kabco', crash_type='sv'))
def pred_sv_kabco(spf_sv_kabco=None, af_total=None, cf_total=None, 
    num_years=None, **kwargs):
    res = spf_sv_kabco * af_total * cf_total * num_years
    return res

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

@model.add_result(comp=dict(severity='kabco', crash_type='ped'))
def pred_ped(factype=None, spf_ped=None, af_ped=None, af_total=None, 
    cf_total=None, num_years=None, **kwargs):
    # Determine which model to use based on facility type
    if factype in ['3sg','4sg']:
        res = spf_ped * af_ped * cf_total * num_years
    elif factype in ['3st','4st']:
        res = spf_ped * af_total * cf_total * num_years
    else:
        raise ValueError("Invalid facility type for computing pedestrian \
crashes.")
    return res

@model.add_result(comp=dict(severity='kabco', crash_type='pdc'))
def pred_pdc(spf_pdc=None, af_total=None, cf_total=None, 
    num_years=None, **kwargs):
    res = spf_pdc * af_total * cf_total * num_years
    return res


##########################
# DEFINE EMPIRICAL-BAYES #
##########################

model.add_layer()

@model.add_result(
    refs={'spf_mv':{'severity':'kabco'}},
    comp={'severity':'kabco', 'crash_type':'mv'},
)
def exp_mv_kabco(obs_mv_kabco=None, pred_mv_kabco=None, 
    k=None, **kwargs):
    """
    Expected Crash Computation
    """
    # Check for observed crash input
    if obs_mv_kabco is None or obs_mv_kabco == -1:
        e = -1
    else:
        # Compute weighted adjustment
        w = 1 / (1 + k * pred_mv_kabco)
        # Compute expected average crash frequency
        e = w * pred_mv_kabco + ((1 - w) * obs_mv_kabco)
    return e

@model.add_result(
    refs={'spf_sv':{'severity':'kabco'}},
    comp={'severity':'kabco', 'crash_type':'sv'},
)
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

@model.add_result(comp={'severity':'kabco', 'crash_type':'all'})
def exp_kabco(exp_mv_kabco=None, exp_sv_kabco=None, **kwargs):
    """
    Expected Crash Computation
    """
    return exp_mv_kabco + exp_sv_kabco


##############
# LOCK MODEL #
##############

model.lock()
