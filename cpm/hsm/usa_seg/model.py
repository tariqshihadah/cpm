#######################
# IMPORT DEPENDENCIES #
#######################

import math, os
from cpm.base import Model, SPF, AF, CF, Sub, Hidden, Result, Limits, Values, Reference


################
# DEFINE MODEL #
################

model = Model(name='usa_seg')


#####################
# DEFINE REFERENCES #
#####################

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

# Facility Type
model.add_validator(
    Values(key='factype', values=('2u','3t','4u','4d','5t'),
        notes=['2u: 2-lane undivided','3t: 2-lane with TWLTL',
            '4u: 4-lane undivided','4d: 4-lane divided',
            '5st: 4-lane with TWLTL']))

# AADT
model.add_validator(
    Limits(key='aadt', vmin=1, vmax=32600, enforce='warn',
        conditions={'factype':['2u']}))
model.add_validator(
    Limits(key='aadt', vmin=1, vmax=32900, enforce='warn', 
        conditions={'factype':['3t']}))
model.add_validator(
    Limits(key='aadt', vmin=1, vmax=40100, enforce='warn', 
        conditions={'factype':['4u']}))
model.add_validator(
    Limits(key='aadt', vmin=1, vmax=66000, enforce='warn', 
        conditions={'factype':['4d']}))
model.add_validator(
    Limits(key='aadt', vmin=1, vmax=53800, enforce='warn', 
        conditions={'factype':['5t']}))

# Driveway Information
model.add_validator(
    Limits(key='n_maj_com', vmin=0, vmax=1e2, enforce='warn'))
model.add_validator(
    Limits(key='n_min_com', vmin=0, vmax=1e2, enforce='warn'))
model.add_validator(
    Limits(key='n_maj_ind', vmin=0, vmax=1e2, enforce='warn'))
model.add_validator(
    Limits(key='n_min_ind', vmin=0, vmax=1e2, enforce='warn'))
model.add_validator(
    Limits(key='n_maj_res', vmin=0, vmax=1e2, enforce='warn'))
model.add_validator(
    Limits(key='n_min_res', vmin=0, vmax=1e2, enforce='warn'))
model.add_validator(
    Limits(key='n_other', vmin=0, vmax=1e2, enforce='warn'))

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
    Limits(key='obs_mv_dwy_kabco', vmin=-1, vmax=1e3, enforce='warn',
        notes='If historic crash data is unavailable, enter -1 to skip EB \
analysis.'))
model.add_validator(
    Limits(key='obs_mv_ndwy_kabco', vmin=-1, vmax=1e3, enforce='warn',
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

@model.add_spf(refs={'spf_mv_dwy':{}})
def spf_mv_dwy_kabco(factype=None, aadt=None, n_maj_com=None, n_min_com=None, 
    n_maj_ind=None, n_min_ind=None, n_maj_res=None, n_min_res=None, 
    n_other=None, **kwargs):
    # Compute total crash frequency
    n = spf_dwy(aadt=aadt, n_maj_com=n_maj_com, n_min_com=n_min_com, 
        n_maj_ind=n_maj_ind, n_min_ind=n_min_ind, n_maj_res=n_maj_res, 
        n_min_res=n_min_res, n_other=n_other, **kwargs)
    return n

def spf(aadt=None, length=None, a=None, b=None, cf=None, **kwargs):
    """
    Based on HSM Equation 12-10. 
    """
    # Perform calculation
    n = math.exp(a + b * math.log(aadt) + math.log(length)) * cf
    return n

@model.add_spf(refs={'spf_mv_ndwy':{'severity':'kabco'}})
def spf_mv_ndwy_kabco(factype=None, aadt=None, length=None, **kwargs):
    n = spf(factype=factype, aadt=aadt, length=length, **kwargs)
    return n

@model.add_spf(refs={'spf_mv_ndwy':{'severity':'kabc'}})
def spf_mv_ndwy_kabc_unadjusted(factype=None, aadt=None, length=None, **kwargs):
    n = spf(factype=factype, aadt=aadt, length=length, **kwargs)
    return n

@model.add_spf(refs={'spf_mv_ndwy':{'severity':'o'}})
def spf_mv_ndwy_o_unadjusted(factype=None, aadt=None, length=None, **kwargs):
    n = spf(factype=factype, aadt=aadt, length=length, **kwargs)
    return n

@model.add_spf(refs={'spf_sv':{'severity':'kabco'}})
def spf_sv_kabco(factype=None, aadt=None, length=None, **kwargs):
    n = spf(factype=factype, aadt=aadt, length=length, **kwargs)
    return n

@model.add_spf(refs={'spf_sv':{'severity':'kabc'}})
def spf_sv_kabc_unadjusted(factype=None, aadt=None, length=None, **kwargs):
    n = spf(factype=factype, aadt=aadt, length=length, **kwargs)
    return n

@model.add_spf(refs={'spf_sv':{'severity':'o'}})
def spf_sv_o_unadjusted(factype=None, aadt=None, length=None, **kwargs):
    n = spf(factype=factype, aadt=aadt, length=length, **kwargs)
    return n

model.add_layer()

@model.add_spf(refs={'spf_mv_dwy':{}})
def spf_mv_dwy_kabc(spf_mv_dwy_kabco=None, p_kabc=None, **kwargs):
    # Compute severity frequency based on proportion
    n = spf_mv_dwy_kabco * p_kabc
    return n

@model.add_spf(refs={'spf_mv_dwy':{}})
def spf_mv_dwy_o(spf_mv_dwy_kabco=None, p_o=None, **kwargs):
    # Compute severity frequency based on proportion
    n = spf_mv_dwy_kabco * p_o
    return n

@model.add_spf()
def spf_mv_ndwy_kabc(spf_mv_ndwy_kabco=None, 
    spf_mv_ndwy_kabc_unadjusted=None, spf_mv_ndwy_o_unadjusted=None, **kwargs):
    # Compute adjusted frequency prediction
    n = spf_mv_ndwy_kabco * (spf_mv_ndwy_kabc_unadjusted / \
        (spf_mv_ndwy_kabc_unadjusted + spf_mv_ndwy_o_unadjusted))
    return n

@model.add_spf()
def spf_mv_ndwy_o(spf_mv_ndwy_kabco=None, 
    spf_mv_ndwy_kabc_unadjusted=None, spf_mv_ndwy_o_unadjusted=None, **kwargs):
    # Compute adjusted frequency prediction
    n = spf_mv_ndwy_kabco * (spf_mv_ndwy_o_unadjusted / \
        (spf_mv_ndwy_kabc_unadjusted + spf_mv_ndwy_o_unadjusted))
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
def spf_kabco(spf_mv_dwy_kabco=None, spf_mv_ndwy_kabco=None, 
    spf_sv_kabco=None, **kwargs):
    return spf_mv_dwy_kabco + spf_mv_ndwy_kabco + spf_sv_kabco

@model.add_spf()
def spf_kabc(spf_mv_dwy_kabc=None, spf_mv_ndwy_kabc=None, 
    spf_sv_kabc=None, **kwargs):
    return spf_mv_dwy_kabc + spf_mv_ndwy_kabc + spf_sv_kabc

@model.add_spf()
def spf_o(spf_mv_dwy_o=None, spf_mv_ndwy_o=None, 
    spf_sv_o=None, **kwargs):
    return spf_mv_dwy_o + spf_mv_ndwy_o + spf_sv_o

@model.add_sub(astype=str)
def speed_cat(speed=None, **kwargs):
    return '<=30' if speed <= 30 else '>30'

model.add_layer()

@model.add_spf(refs={'spf_ped':{}})
def spf_ped(spf_kabco=None, speed_cat=None, p_ped=None, **kwargs):
    n = spf_kabco * p_ped
    return n

@model.add_spf(refs={'spf_pdc':{}})
def spf_pdc(spf_kabco=None, speed_cat=None, p_pdc=None, **kwargs):
    n = spf_kabco * p_pdc
    return n


##############
# DEFINE AFS #
##############

@model.add_af()
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

@model.add_af()
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

@model.add_af()
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

@model.add_af()
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

@model.add_af()
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

@model.add_af()
def af_total(af_parking=None, af_fo=None, af_median_width=None, 
    af_lighting=None, af_ase=None, **kwargs):
    # Combine AFs
    af = af_parking * af_fo * af_median_width * af_lighting * af_ase
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

@model.add_result(comp=dict(severity='kabco', crash_type='mv_dwy'))
def pred_mv_dwy_kabco(spf_mv_dwy_kabco=None, af_total=None, cf_total=None, 
    num_years=None, **kwargs):
    res = spf_mv_dwy_kabco * af_total * cf_total * num_years
    return res

@model.add_result(comp=dict(severity='kabco', crash_type='mv_ndwy'))
def pred_mv_ndwy_kabco(spf_mv_ndwy_kabco=None, af_total=None, cf_total=None, 
    num_years=None, **kwargs):
    res = spf_mv_ndwy_kabco * af_total * cf_total * num_years
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
def pred_ped(spf_ped=None, af_total=None, cf_total=None, 
    num_years=None, **kwargs):
    res = spf_ped * af_total * cf_total * num_years
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

@model.add_result(
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

@model.add_result(
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

@model.add_result(
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

model.lock()
