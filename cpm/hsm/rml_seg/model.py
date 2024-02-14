#######################
# IMPORT DEPENDENCIES #
#######################


import math, os
from cpm.base import Model, SPF, AF, CF, Sub, Result, Limits, Values, Reference


################
# DEFINE MODEL #
################


model = Model(name='rml_seg')


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
    Limits(key='aadt', vmin=1, vmax=89300, enforce='warn',
        conditions={'factype':['4d']}))
model.add_validator(
    Limits(key='aadt', vmin=1, vmax=33200, enforce='warn', 
        conditions={'factype':['4u']}))

# Facility Type
model.add_validator(
    Values(key='factype', values=('4d','4u'), 
        notes=['4d: 4-lane divided','4u: 4-lane undivided']))

# Geometry
model.add_validator(
    Limits(key='length', vmin=0, vmax=1e2))
model.add_validator(
    Limits(key='lane_width', vmin=6, vmax=18)) 
model.add_validator(
    Limits(key='shld_width', vmin=0, vmax=20)) 
model.add_validator(
    Values(key='shld_type', values=('paved','gravel','composite','turf')))
model.add_validator(
    Limits(key='sideslope', vmin=1, vmax=10, 
        notes='Horizontal run of sideslope (1V:XH)'))
model.add_validator(
    Limits(key='median_width', vmin=0, vmax=100)) 

# Operational Information
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
    Based on HSM Equation 11-7.
    """
    # Perform calculation
    n = math.exp(a + b * math.log(aadt) + math.log(length)) * cf
    return n

@model.add_spf(refs={'spf':{'severity':'kabco'}})
def spf_kabco(factype=None, aadt=None, length=None, **kwargs):
    n = spf(aadt=aadt, length=length, **kwargs)
    return n

@model.add_spf(refs={'spf':{'severity':'kabc'}})
def spf_kabc(factype=None, aadt=None, length=None, **kwargs):
    n = spf(aadt=aadt, length=length, **kwargs)
    return n

@model.add_spf(refs={'spf':{'severity':'kab'}})
def spf_kab(factype=None, aadt=None, length=None, **kwargs):
    n = spf(aadt=aadt, length=length, **kwargs)
    return n

model.add_layer()

@model.add_spf()
def spf_o(spf_kabco=None, spf_kabc=None, **kwargs):
    n = spf_kabco - spf_kabc
    return n


##############
# DEFINE AFS #
##############

@model.add_af()
def af_lane_width(factype=None, lane_width=None, aadt=None, **kwargs):
    """
    Lane Width
    Based on Equations 11-13, 11-16, Tables 11-11, 11-16, Figure 11-8
    """
    # Compute adjustment factor for related crashes based on facility type
    if factype == '4d':
        # Define proportion of related crashes
        p_rel = 0.50
        if lane_width < 10:
            if aadt < 400:
                af_rel = 1.03
            elif aadt > 2000:
                af_rel = 1.25
            else:
                af_rel = 1.03 + (1.38 * 10e-4) * (aadt - 400)
        elif lane_width < 11:
            if aadt < 400:
                af_rel = 1.01
            elif aadt > 2000:
                af_rel = 1.15
            else:
                af_rel = 1.01 + (8.75 * 10e-5) * (aadt - 400)
        elif lane_width < 12:
            if aadt < 400:
                af_rel = 1.01
            elif aadt > 1.03:
                af_rel = 1.03
            else:
                af_rel = 1.01 + (1.25 * 10e-5) * (aadt - 400)
        else:
            af_rel = 1.00
    elif factype == '4u':
        # Define proportion of related crashes
        p_rel = 0.27
        if lane_width < 10:
            if aadt < 400:
                af_rel = 1.04
            elif aadt > 2000:
                af_rel = 1.38
            else:
                af_rel = 1.04 + (2.13 * 10e-4) * (aadt - 400)
        elif lane_width < 11:
            if aadt < 400:
                af_rel = 1.02
            elif aadt > 2000:
                af_rel = 1.23
            else:
                af_rel = 1.02 + (1.31 * 10e-4) * (aadt - 400)
        elif lane_width < 12:
            if aadt < 400:
                af_rel = 1.01
            elif aadt > 2000:
                af_rel = 1.04
            else:
                af_rel = 1.01 + (1.88 * 10e-5) * (aadt - 400)
        else:
            af_rel = 1.00
    # Compute final adjustment factor
    af = (af_rel - 1.00) * p_rel + 1.00
    return af

@model.add_af()
def af_shld(factype=None, shld_type=None, shld_width=None, aadt=None, 
    **kwargs):
    """
    Shoulder Width
    Based on Equation 11-14, Figure 11-9, Tables 11-12, 11-13, 11-18
    """
    # Compute adjustment factor based on facility type
    if factype == '4d':
        if shld_type == 'paved':
            if shld_width < 2:
                af = 1.18
            elif shld_width < 4:
                af = 1.13
            elif shld_width < 6:
                af = 1.09
            elif shld_width < 8:
                af = 1.04
            else:
                af = 1.00
        else:
            # Not defined for unpaved
            af = 1.00
    elif factype == '4u':
        # Compute adjustment factor for width
        if shld_width < 2:
            if aadt < 400:
                af_width = 1.10
            elif aadt > 2000:
                af_width = 1.50
            else:
                af_width = 1.10 + (2.5 * 10e-4) * (aadt - 400)
        elif shld_width < 4:
            if aadt < 400:
                af_width = 1.07
            elif aadt > 2000:
                af_width = 1.30
            else:
                af_width = 1.07 + (1.43 * 10e-4) * (aadt - 400)
        elif shld_width < 6:
            if aadt < 400:
                af_width = 1.02
            elif aadt > 2000:
                af_width = 1.15
            else:
                af_width = 1.02 + (8.125 * 10e-5) * (aadt - 400)
        elif shld_width < 8:
            af_width = 1.00
        else:
            if aadt < 400:
                af_width = 0.98
            elif aadt > 2000:
                af_width = 0.87
            else:
                af_width = 0.98 - (6.875 * 10e-5) * (aadt - 400)
        # Compute adjustment factor for type
        if shld_type == 'paved':
            af_type = 1.00
        elif shld_type == 'gravel':
            if shld_width < 2:
                af_type = 1.00
            elif shld_width < 6:
                af_type = 1.01
            else:
                af_type = 1.02
        elif shld_type == 'composite':
            if shld_width < 1:
                af_type = 1.00
            elif shld_width < 2:
                af_type = 1.01
            elif shld_width < 4:
                af_type = 1.02
            elif shld_width < 6:
                af_type = 1.03
            elif shld_width < 8:
                af_type = 1.04
            else:
                af_type = 1.06
        elif shld_type == 'turf':
            if shld_width < 1:
                af_type = 1.00
            elif shld_width < 2:
                af_type = 1.01
            elif shld_width < 3:
                af_type = 1.03
            elif shld_width < 4:
                af_type = 1.04
            elif shld_width < 6:
                af_type = 1.08
            else:
                af_type = 1.11
        # Combine adjustment factors for width and type
        p_rel = 0.27
        af = (af_width * af_type - 1.00) * p_rel + 1.00
    return af

@model.add_af()
def af_sideslope(factype=None, sideslope=None, **kwargs):
    """
    Sideslopes
    Based on Table 11-14
    """
    # Compute adjustment factor based on facility type
    if factype == '4d':
        af = 1.00
    elif factype == '4u':
        if sideslope < 3:
            af = 1.18
        elif sideslope < 4:
            af = 1.15
        elif sideslope < 5:
            af = 1.12
        elif sideslope < 6:
            af = 1.09
        elif sideslope < 7:
            af = 1.05
        else:
            af = 1.00
    return af

@model.add_af()
def af_lighting(factype=None, lighting=None, **kwargs):
    """
    Lighting
    Based on Tables 11-15, 11-19, Equations 11-15, 11-17
    """
    # Compute adjustment factor based on facility type
    if lighting == 1:
        # Determine night crash proportions
        if factype == '4d':
            p_night_kabc = 0.323
            p_night_o    = 0.677
            p_night      = 0.426
        elif factype == '4u':
            p_night_kabc = 0.361
            p_night_o    = 0.639
            p_night      = 0.255
        af = 1 - ((1 - (0.72 * p_night_kabc) - (0.83 * p_night_o)) * p_night)
    else:
        af = 1.00
    return af

@model.add_af()
def af_ase(factype=None, ase=None, **kwargs):
    """
    Automated Speed Enforcement
    Based on Chapter 11 CMF - Automated Speed Enforcement
    """
    # Compute adjustment factor based on facility type
    if ase == 1:
        if factype == '4d':
            af = 0.94
        elif factype == '4u':
            af = 0.95
    else:
        af = 1.00
    return af

@model.add_af()
def af_median_width(factype=None, median_width=None, **kwargs):
    """
    Median Width
    Based on table 11-18
    """
    # Compute adjustment factor based on facility type
    if factype == '4d':
        if median_width <= 10:
            af = 1.04
        elif median_width <= 20:
            af = 1.02
        elif median_width <= 30:
            af = 1.00
        elif median_width <= 40:
            af = 0.99
        elif median_width <= 50:
            af = 0.97
        elif median_width <= 60:
            af = 0.96
        elif median_width <= 70:
            af = 0.96
        elif median_width <= 80:
            af = 0.95
        elif median_width <= 90:
            af = 0.94
        else:
            af = 0.94
    elif factype == '4u':
        af = 1.00
    return af

model.add_layer()

@model.add_af()
def af_total(af_lane_width=None, af_shld=None, af_sideslope=None, 
    af_lighting=None, af_ase=None, af_median_width=None, **kwargs):
    """
    Combine all adjustment factors.
    """
    # Combine AFs
    af = af_lane_width * af_shld * af_sideslope * af_lighting * af_ase \
        * af_median_width
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
def pred_kabco(spf_kabco=None, af_total=None, cf_total=None, num_years=None, 
    **kwargs):
    res = spf_kabco * af_total * cf_total * num_years
    return res


##########################
# DEFINE EMPIRICAL-BAYES #
##########################

model.add_layer()

@model.add_result(
    refs={'spf':{'severity':'kabco'}},
    comp={'severity':'kabco', 'crash_type':'all'})
def exp_kabco(obs_kabco=None, pred_kabco=None, length=None, c=None, **kwargs):
    """
    Expected Crash Computation
    """
    # Compute overdispersion parameter
    # - Based on HSM Equation 11-10
    k = 1 / (math.exp(c + math.log(length)))
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
