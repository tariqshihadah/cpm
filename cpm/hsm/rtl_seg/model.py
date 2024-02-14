#######################
# IMPORT DEPENDENCIES #
#######################

import math, os
from cpm.base import Model, SPF, AF, CF, Sub, Result, Limits, Values, Reference


################
# DEFINE MODEL #
################

model = Model(name='rtl_seg')


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
    Limits(key='aadt', vmin=1, vmax=17800, enforce='warn'))

# Geometry
model.add_validator(
    Limits(key='length', vmin=0, vmax=1e2))
model.add_validator(
    Limits(key='lane_width', vmin=6, vmax=24)) 
model.add_validator(
    Limits(key='shld_width', vmin=0, vmax=20)) 
model.add_validator(
    Values(key='shld_type', values=('paved','gravel','composite','turf')))
model.add_validator(
    Values(key='rumble_cl', values=(0,1), 
        notes=['Centerline rumblestrips','0: not present; 1: present'])) 
model.add_validator(
    Values(key='passing_lanes', values=(0,1,2))) 
model.add_validator(
    Values(key='twltl', values=(0,1), 
        notes=['Two-way left-turn lane','0: not present; 1: present']))

# Alignment
model.add_validator(
    Values(key='spiral_transition', values=(0,0.5,1), notes='0: not present; \
0.5: present on one end only; 1: present on both ends'))
model.add_validator(
    Limits(key='curve_length', vmin=0, vmax=lambda length: length, 
        notes='Length of the horizontal curve in miles'))
model.add_validator(
    Limits(key='curve_radius', vmin=0, vmax=1e5, 
        notes='Radius of the horizontal curve in feet'))
model.add_validator(
    Limits(key='se_var', vmin=0, vmax=0.10, notes='Superelevation variance')) 
model.add_validator(
    Limits(key='grade', vmin=-20, vmax=20))

# Location Information
model.add_validator(
    Limits(key='dwy_density', vmin=0, vmax=100, enforce='warn', 
        notes='Number of driveways per mile'))
model.add_validator(
    Values(key='rhr', values=(1,2,3,4,5,6,7), dtype=int,
        notes='Roadside hazard rating'))
model.add_validator(
    Values(key='lighting', values=(0,1), notes='0: not present; 1: present'))  
model.add_validator(
    Values(key='ase', values=(0,1), 
        notes=['Automated speed enforcement','0: not present; 1: present']))

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

def spf(aadt=None, length=None, a=None, b=None, cf=None, **kwargs):
    """
    Based on HSM Equation 10-7. 
    """
    # Perform calculation
    n = a * aadt * length * 365 * 1e-6 * math.exp(b) * cf
    return n

@model.add_spf(refs={'spf':{'severity':'kabco'}})
def spf_kabco(aadt=None, length=None, **kwargs):
    return spf(aadt=aadt, length=length, **kwargs)


##############
# DEFINE AFS #
##############

@model.add_af()
def af_lane_width(lane_width=None, aadt=None, **kwargs):
    """
    Lane Width
    Based on Table 10-8, Equation 10-11.
    """
    # Compute type-specific AF
    if lane_width < 10:
        if aadt < 400:
            af = 1.05
        elif aadt > 2000:
            af = 1.50
        else:
            af = 1.05 + 2.81 * 1e-4 * (aadt - 400)
    elif lane_width < 11:
        if aadt < 400:
            af = 1.02
        elif aadt > 2000:
            af = 1.30
        else:
            af = 1.02 + 1.75 * 1e-4 * (aadt - 400)
    elif lane_width < 12:
        if aadt < 400:
            af = 1.01
        elif aadt > 2000:
            af = 1.05
        else:
            af = 1.01 + 2.50 * 1e-5 * (aadt - 400)
    else:
        af = 1.00
    # Generalize per Equation 10-11
    af = (af - 1.0) * 0.574 + 1
    return af

@model.add_af()
def af_shld(aadt=None, shld_width=None, shld_type=None, **kwargs):
    """
    Shoulder Type and Width
    Based on Tables 10-9, 10-10, Equation 10-12
    """
    # AF for shoulder type
    if shld_width < 1:
        af_typ = 1.00
    elif shld_width < 2:
        if shld_type == 'paved':
            af_typ = 1.00
        elif shld_type == 'gravel':
            af_typ = 1.00
        elif shld_type == 'composite':
            af_typ = 1.01
        elif shld_type == 'turf':
            af_typ = 1.01
    elif shld_width < 3:
        if shld_type == 'paved':
            af_typ = 1.00
        elif shld_type == 'gravel':
            af_typ = 1.01
        elif shld_type == 'composite':
            af_typ = 1.02
        elif shld_type == 'turf':
            af_typ = 1.03
    elif shld_width < 4:
        if shld_type == 'paved':
            af_typ = 1.00
        elif shld_type == 'gravel':
            af_typ = 1.01
        elif shld_type == 'composite':
            af_typ = 1.02
        elif shld_type == 'turf':
            af_typ = 1.04
    elif shld_width < 6:
        if shld_type == 'paved':
            af_typ = 1.00
        elif shld_type == 'gravel':
            af_typ = 1.01
        elif shld_type == 'composite':
            af_typ = 1.03
        elif shld_type == 'turf':
            af_typ = 1.05
    elif shld_width < 8:
        if shld_type == 'paved':
            af_typ = 1.00
        elif shld_type == 'gravel':
            af_typ = 1.02
        elif shld_type == 'composite':
            af_typ = 1.04
        elif shld_type == 'turf':
            af_typ = 1.08
    else:
        if shld_type == 'paved':
            af_typ = 1.00
        elif shld_type == 'gravel':
            af_typ = 1.02
        elif shld_type == 'composite':
            af_typ = 1.06
        elif shld_type == 'turf':
            af_typ = 1.11
    # AF for shoulder width
    if shld_width < 2:
        if aadt < 400:
            af_wth = 1.10
        elif aadt > 2000:
            af_wth = 1.50
        else:
            af_wth = 1.10 + 2.50 * 1e-4 * (aadt - 400)
    elif shld_width < 4:
        if aadt < 400:
            af_wth = 1.07
        elif aadt > 2000:
            af_wth = 1.30
        else:
            af_wth = 1.07 + 1.43 * 1e-4 * (aadt - 400)
    elif shld_width < 6:
        if aadt < 400:
            af_wth = 1.02
        elif aadt > 2000:
            af_wth = 1.15
        else:
            af_wth = 1.02 + 8.125 * 1e-5 * (aadt - 400)
    elif shld_width < 8:
        af_wth = 1.00
    else:
        if aadt < 400:
            af_wth = 0.98
        elif aadt > 2000:
            af_wth = 0.87
        else:
            af_wth = 0.98 - 6.875 * 1e-5 * (aadt - 400)
    # Generalize per Equation 10-12
    af = (af_typ * af_wth - 1.0) * 0.574 + 1
    return af

@model.add_af()
def af_hor_curve(length=None, curve_length=None, curve_radius=None, 
    spiral_transition=None, **kwargs):
    """
    Based on HSM equation 10-13.
    """
    # Check for presence of curve
    if curve_length == 0 and curve_radius == 0:
        af = 1.00
    else:
        # Enforce curve length maximum
        curve_length = min(curve_length, length)
        # Enforce curve length minimum
        curve_length = max(curve_length, 100 / 5280)
        # Enforce curve radius minimum
        curve_radius = max(curve_radius, 100)
        # Compute adjustment factor
        af = ((1.55 * curve_length) + (80.2 / curve_radius) - \
            (0.012 * spiral_transition)) / (1.55 * curve_length)
        # Enforce minimum AF value of 1.00
        af = max(af, 1.00)
    return af

@model.add_af()
def af_se_var(se_var=None, **kwargs):
    """
    Based on HSM equation 10-14, 10-15, 10-16.

    NOTE: Future improvement, code AASHTO SE Tables to automatically calculate 
    variance from input superelevation and other values.
    """
    # Compute adjustment factor
    if se_var < 0.01:
        af = 1.00
    elif se_var >= 0.02:
        af = 1.06 + (3 * (se_var - 0.02))
    else:
        af = 1.00 + (6 * (se_var - 0.01))
    return af

@model.add_af()
def af_grade(grade=None, **kwargs):
    """
    Based on HSM table 10-11.
    """
    # Enforce positive grade
    grade = math.fabs(grade)
    # "Level Grade"
    if grade <= 3.00:
        af = 1.00
    # "Moderate Terrain"
    elif grade <= 6.00:
        af = 1.10
    # "Steep Terrain"
    else:
        af = 1.16
    return af

@model.add_af()
def af_dwy_density(aadt=None, length=None, dwy_density=None, **kwargs):
    """
    Based on HSM equation 10-17
    """
    # Enforce minimum driveway number
    if dwy_density < 5:
        af = 1.00
    else:
        af = (0.322 + (dwy_density * (0.05 - 0.005 * math.log(aadt)))) / \
            (0.322 + (5 * (0.05 - 0.005 * math.log(aadt))))
    return af

@model.add_af()
def af_rumble_cl(rumble_cl=None, **kwargs):
    """
    Based on HSM page 10-29
    """
    # Compute binary adjustment factor
    if rumble_cl == 1:
        af = 0.94
    else:
        af = 1.00
    return af

@model.add_af()
def af_passing_lanes(passing_lanes=None, **kwargs):
    """
    Based on HSM page 10-29
    """
    # Compute adjustment factor based on number of passing lanes present
    if passing_lanes == 0:
        af = 1.00
    elif passing_lanes == 1:
        af = 0.75
    elif passing_lanes == 2:
        af = 0.65
    return af

@model.add_af()
def af_twltl(twltl=None, length=None, dwy_density=None, **kwargs):
    """
    Based on HSM equation 10-18 and 10-19.
    """
    if twltl == 0:
        af = 1.00
    elif dwy_density < 5:
        af = 1.00
    else:
        dwy_prop = ((0.0047 * dwy_density) + (0.0024 * dwy_density ** 2)) / \
            (1.199 + (0.0047 * dwy_density) + (0.0024 * dwy_density ** 2))
        af = 1.0 - (0.7 * dwy_prop * 0.5)
    return af


@model.add_af()
def af_rhr(rhr=None, **kwargs):
    """
    Based on HSM equation 10-20 and the roadside hazard rating in appendix 13A
    """
    # Compute adjustment factor
    af = math.exp(-0.6869 + (0.0668 * rhr)) / math.exp(-0.4865)
    return af

@model.add_af()
def af_lighting(lighting=None, **kwargs):
    """
    Based on HSM equation 10-21 and table 10-12.
    """
    # Compute adjustment factor
    if lighting == 1:
        af = 1.0 - ((1.0 - (0.72 * 0.382) - (0.83 * 0.618)) * 0.370)
    else:
        af = 1.00
    return af

@model.add_af()
def af_ase(ase=None, **kwargs):
    """
    Based on HSM page 10-31.
    """
    # Compute adjustment factor
    if ase == 1:
        af = 0.93
    else:
        af = 1.00
    return af

model.add_layer()

@model.add_af()
def af_total(af_lane_width=None, af_shld=None, af_hor_curve=None, 
    af_se_var=None, af_grade=None, af_dwy_density=None, af_rumble_cl=None, 
    af_passing_lanes=None, af_twltl=None, af_rhr=None, af_lighting=None, 
    af_ase=None, **kwargs):
    # Combine AFs
    af = af_lane_width * af_shld * af_hor_curve * af_se_var * af_grade * \
        af_dwy_density * af_rumble_cl * af_passing_lanes * af_twltl * \
        af_rhr * af_lighting * af_ase
    return af


######################
# DEFINE CALIBRATION #
######################

model.add_layer()

@model.add_cf(refs={'calibration':{}})
def cf_total(cf=None, **kwargs):
    return cf


#####################
# DEFINE PREDICTION #
#####################

model.add_layer()

@model.add_result(comp={'severity':'kabco', 'crash_type':'all'})
def pred_kabco(spf_kabco=None, af_total=None, cf_total=None, num_years=None, 
     **kwargs):
    res = spf_kabco * af_total * cf_total * num_years
    return res


##########################
# DEFINE EMPIRICAL-BAYES #
##########################

model.add_layer()

@model.add_result(refs={'spf':{'severity':'kabco'}},
    comp={'severity':'kabco', 'crash_type':'all'})
def exp_kabco(obs_kabco=None, pred_kabco=None, k=None, length=None, 
    num_years=None, **kwargs):
    """
    Expected Crash Computation
    """
    # Check for observed crash input
    if obs_kabco is None or obs_kabco == -1:
        e = -1
    else:
        # Compute weighted adjustment
        w = 1 / (1 + (k / length) * pred_kabco)
        # Compute expected average crash frequency
        e = w * pred_kabco + ((1 - w) * obs_kabco)
    return e


##############
# LOCK MODEL #
##############

model.lock()
