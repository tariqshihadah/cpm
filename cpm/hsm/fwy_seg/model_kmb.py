# NOTES
# - Are entrance/exit speed change lane lengths combined when computing SPFs? Overdispersion?

#######################
# IMPORT DEPENDENCIES #
#######################

from cmath import exp
import math, os

from pkg_resources import BINARY_DIST
from cpm.base import Model, SPF, AF, CF, Sub, Hidden, Result, Limits, Values, Reference


################
# DEFINE MODEL #
################

model = Model(name='fwy_seg')


#####################
# DEFINE REFERENCES #
#####################

fd = os.path.dirname(os.path.abspath(__file__))
fp = lambda fn: os.path.join(fd,fn)
model.add_reference(fp('spf_mv.json'))
model.add_reference(fp('spf_sv.json'))
model.add_reference(fp('spf_en.json'))
model.add_reference(fp('spf_ex.json'))
model.add_reference(fp('af_curves.json'))
model.add_reference(fp('af_high_volume.json'))
model.add_reference(fp('af_inside_shoulder_width.json'))
model.add_reference(fp('af_lane_change.json'))
model.add_reference(fp('af_lane_width.json'))
model.add_reference(fp('af_median_barrier.json'))
model.add_reference(fp('af_median_width.json'))
model.add_reference(fp('af_outside_barrier.json'))
model.add_reference(fp('af_outside_shoulder_width.json'))
model.add_reference(fp('af_ramp_entrance.json'))
model.add_reference(fp('af_ramp_exit.json'))
#model.add_reference(Reference(fp('calibration.json')))


#####################
# DEFINE VALIDATORS #
#####################

# AADT
model.add_validator(
    Limits(key='aadt', vmin=1, vmax=73000, enforce='snap',
        conditions={'area_type':['rural'], 'lanes':[4]}))
model.add_validator(
    Limits(key='aadt', vmin=1, vmax=130000, enforce='snap',
        conditions={'area_type':['rural'], 'lanes':[6]}))
model.add_validator(
    Limits(key='aadt', vmin=1, vmax=190000, enforce='snap',
        conditions={'area_type':['rural'], 'lanes':[8]}))
model.add_validator(
    Limits(key='aadt', vmin=1, vmax=110000, enforce='snap',
        conditions={'area_type':['urban'], 'lanes':[4]}))
model.add_validator(
    Limits(key='aadt', vmin=1, vmax=180000, enforce='snap',
        conditions={'area_type':['urban'], 'lanes':[6]}))
model.add_validator(
    Limits(key='aadt', vmin=1, vmax=270000, enforce='snap',
        conditions={'area_type':['urban'], 'lanes':[8]}))
model.add_validator(
    Limits(key='aadt', vmin=1, vmax=310000, enforce='snap',
        conditions={'area_type':['urban'], 'lanes':[10]}))

# Area Type
model.add_validator(
    Values(key='area_type', values=('rural','urban')))

# Number of Lanes
model.add_validator(
    Values(key='lanes', values=(4,6,8),
        conditions={'area_type':['rural']}))
model.add_validator(
    Values(key='lanes', values=(4,6,8,10),
        conditions={'area_type':['urban']}))

# Length
model.add_validator(
    Limits(key='length', vmin=0.01, vmax=100,
        notes=['0.01 miles or more']))
model.add_validator(
    Limits(key='length_inc_en', vmin=0, 
        vmax=lambda length: length,
        notes=['Speed change lane areas must be less than the segment length']))
model.add_validator(
    Limits(key='length_inc_ex', vmin=0, 
        vmax=lambda length, length_inc_en: length - length_inc_en,
        notes=['Speed change lane areas must be less than the segment length']))
model.add_validator(
    Limits(key='length_dec_en', vmin=0, 
        vmax=lambda length: length,
        notes=['Speed change lane areas must be less than the segment length']))
model.add_validator(
    Limits(key='length_dec_ex', vmin=0, 
        vmax=lambda length, length_dec_en: length - length_dec_en,
        notes=['Speed change lane areas must be less than the segment length']))

# Curve length
model.add_validator(
    Limits(key='curve_length_1', vmin=0.01, vmax=100,
        notes=['0.01 miles or more']))
model.add_validator(
    Limits(key='curve_length_2', vmin=0.01, vmax=100,
        notes=['0.01 miles or more']))
model.add_validator(
    Limits(key='curve_length_3', vmin=0.01, vmax=100,
        notes=['0.01 miles or more']))

# Curve radius
model.add_validator(
    Limits(key='curve_radius_inc_1', vmin=1000, vmax=9999, enforce='warn',
        notes=['curve radius must be greater than 1000 ft']))
model.add_validator(
    Limits(key='curve_radius_inc_2', vmin=1000, vmax=9999, enforce='warn',
        notes=['curve radius must be greater than 1000 ft']))
model.add_validator(
    Limits(key='curve_radius_inc_3', vmin=1000, vmax=9999, enforce='warn',
        notes=['curve radius must be greater than 1000 ft']))
model.add_validator(
    Limits(key='curve_radius_dec_1', vmin=1000, vmax=9999, enforce='warn',
        notes=['curve radius must be greater than 1000 ft']))
model.add_validator(
    Limits(key='curve_radius_dec_2', vmin=1000, vmax=9999, enforce='warn',
        notes=['curve radius must be greater than 1000 ft']))
model.add_validator(
    Limits(key='curve_radius_dec_3', vmin=1000, vmax=9999, enforce='warn',
        notes=['curve radius must be greater than 1000 ft']))

# Lane Width
model.add_validator(
    Limits(key='lane_width', vmin=10.5, vmax=14, enforce='snap',
        notes=['range: 10.5 to 14 ft']))

# Paved inside shoulder width
model.add_validator(
    Limits(key='inside_shoulder_width', vmin=2, vmax=12, enforce='snap',
        notes=['range: 2 to 12 ft']))

# Paved outside shoulder width
model.add_validator(
    Limits(key='outside_shoulder_width', vmin=4, vmax=14, enforce='snap',
        notes=['range 4 to 14 ft']))

# Clear zone width
model.add_validator(
    Limits(key='clear_zone_width',
        vmin=lambda outside_shoulder_width: outside_shoulder_width,
        vmax=30, enforce='snap',
        notes=['range: outside shoudler width to 30 ft']))

# Median width
model.add_validator(
    Limits(key='median_width', 
        vmin=lambda inside_shoulder_width: inside_shoulder_width * 2,
        vmax=90, enforce='snap',
        notes=['range: 2 * inside shoudler width to 90 ft']))

# Ramp length
model.add_validator(
    Limits(key='length_ramp', vmin=0.04, vmax=0.30, enforce='snap',
        notes=['range: 0.04 to 0.30 mi']))

# Ramp side
model.add_validator(
    Values(key='ramp_side', values=('left', 'right')))

# Proportion of effective segment length with barrier present in median
model.add_validator(
    Limits(key='barrier_proportion', vmin=0, vmax=1, enforce='snap'))

# Distance from edge of inside shoulder to barrier face
model.add_validator(
    Limits(key='median_barrier_distance', 
        vmin=lambda inside_shoulder_width: inside_shoulder_width, 
        vmax=lambda median_width: median_width * 0.5, enforce='snap',
        notes=['range: inside shoulder width to half median width']))

# Distance from edge of outside shoulder to barrier face
model.add_validator(
    Limits(key='outside_barrier_distance', 
        vmin=lambda outside_shoulder_width: outside_shoulder_width, 
        vmax=1e2, enforce='snap',
        notes=['greater than outside shoulder width']))

# Proportion of effective segment length with rumble strips present on the inside shoulders
model.add_validator(
    Limits(key='in_rumble_prop', vmin=0, vmax=1, enforce='snap', dtype=float))

# Proportion of effective segment length with rumble strips present on the outside shoulders
model.add_validator(
    Limits(key='out_rumble_prop', vmin=0, vmax=1, enforce='snap'))

# Proportion of segment length within a Type B weaving section for travel in increasing milepost direction
model.add_validator(
    Limits(key='typeb_prop_inc', vmin=0, vmax=1, enforce='snap'))

# Proportion of segment length within a Type B weaving section for travel in decreasing milepost direction
model.add_validator(
    Limits(key='typeb_prop_dec', vmin=0, vmax=1, enforce='snap'))

# Weaving section length for travel in increasing milepost direction (may extend beyond segment boundaries) (mi)
model.add_validator(
    Limits(key='length_weave_inc', vmin=0.10, vmax=0.85, enforce='snap',
        notes=['range: 0.10 to 0.85 mi']))

# Weaving section length for travel in decreasing milepost direction (may extend beyond segment boundaries) (mi)
model.add_validator(
    Limits(key='length_weave_dec', vmin=0.10, vmax=0.85, enforce='snap',
        notes=['range: 0.10 to 0.85 mi']))

# Distance from segment begin milepost to nearest upstream entrance ramp gore point, for travel in increasing milepost direction (mi)
model.add_validator(
    Limits(key='upstream_ent_inc', vmin=0, vmax=0.5, enforce='snap',
        notes=['range: 0 to 0.5 mi']))

# Distance from segment begin milepost to nearest downstream exit ramp gore point, for travel in decreasing milepost direction (mi)  
model.add_validator(
    Limits(key='downstream_ex_dec', vmin=0, vmax=0.5, enforce='snap',
        notes=['range: 0 to 0.5 mi']))

# Distance from segment end milepost to nearest upstream entrance ramp gore point, for travel in decreasing milepost direction (mi)
model.add_validator(
    Limits(key='upstream_ent_dec', vmin=0, vmax=0.5, enforce='snap',
        notes=['range: 0 to 0.5 mi']))

# Distance from segment end milepost to nearest downstream exit ramp gore point, for travel in increasing milepost direction (miles)
model.add_validator(
    Limits(key='downstream_ex_inc', vmin=0, vmax=0.5, enforce='snap',
        notes=['range: 0 to 0.5 mi']))

# AADT proportion of hours where volume exceeds 1000 veh/h/ln
model.add_validator(
    Limits(key='aadt_prop', vmin=0, vmax=1, enforce='snap', dtype=float))

# AADT volume of entrace ramp 
model.add_validator(
    Limits(key='aadt_ent_inc', vmin=1, vmax=100000,))
model.add_validator(
    Limits(key='aadt_ex_dec', vmin=1, vmax=100000,))
model.add_validator(
    Limits(key='aadt_ent_dec', vmin=1, vmax=100000,))
model.add_validator(
    Limits(key='aadt_ex_inc', vmin=1, vmax=100000,))
model.add_validator(
    Limits(key='aadt_ramp', vmin=1, vmax=100000,))

# Historic Crash Information
model.add_validator(
    Limits(key='obs_mv_kabc', vmin=-1, vmax=1e3,
        notes='If historic crash data is unavailable, enter -1 to skip EB '
            'analysis.'))
model.add_validator(
    Limits(key='obs_mv_o', vmin=-1, vmax=1e3,
        notes='If historic crash data is unavailable, enter -1 to skip EB '
            'analysis.'))
model.add_validator(
    Limits(key='obs_sv_kabc', vmin=-1, vmax=1e3,
        notes='If historic crash data is unavailable, enter -1 to skip EB '
            'analysis.'))
model.add_validator(
    Limits(key='obs_sv_o', vmin=-1, vmax=1e3,
        notes='If historic crash data is unavailable, enter -1 to skip EB '
            'analysis.'))
model.add_validator(
    Limits(key='obs_en_kabc', vmin=-1, vmax=1e3,
        notes='If historic crash data is unavailable, enter -1 to skip EB '
            'analysis.'))
model.add_validator(
    Limits(key='obs_en_o', vmin=-1, vmax=1e3,
        notes='If historic crash data is unavailable, enter -1 to skip EB '
            'analysis.'))
model.add_validator(
    Limits(key='obs_ex_kabc', vmin=-1, vmax=1e3,
        notes='If historic crash data is unavailable, enter -1 to skip EB '
            'analysis.'))
model.add_validator(
    Limits(key='obs_ex_o', vmin=-1, vmax=1e3,
        notes='If historic crash data is unavailable, enter -1 to skip EB '
            'analysis.'))
model.add_validator(
    Limits(key='num_years', vmin=0, vmax=1e2, dtype=float))


###############
# DEFINE SPFS #
###############

model.add_layer()

@model.add_sub()
def length_eff(
    length=None,
    length_inc_en=None,
    length_inc_ex=None,
    length_dec_en=None,
    length_dec_ex=None,
    **kwargs
    ):
    """
    Equation 18-16: Effective length of freeway segment
    """
    return length - \
        0.5 * (length_inc_en + length_dec_en) - \
        0.5 * (length_inc_ex + length_dec_ex)

@model.add_sub()
def length_en(length_inc_en=None, length_dec_en=None, **kwargs):
    return length_inc_en + length_dec_en

@model.add_sub()
def length_ex(length_inc_ex=None, length_dec_ex=None, **kwargs):
    return length_inc_ex + length_dec_ex

model.add_layer()

#@model.add_sub()
def spf(aadt=None, length_i=None, a=None, b=None, c=None, cf=None, **kwargs):
    """
    HSM Equation 18-15: Predicted average multiple-vehicle crash frequency of a 
    freeway segment with base conditions
    """
    n = length_i * math.exp(a + b * math.log(c * aadt)) * cf
    return n

@model.add_spf(refs={'spf_mv':{'severity':'kabc'}})
def spf_mv_kabc(
    area_type=None,
    lanes=None,
    aadt=None,
    length_eff=None,
    **kwargs
    ):
    n = spf(length_i=length_eff, aadt=aadt, **kwargs)
    return n

@model.add_spf(refs={'spf_mv':{'severity':'o'}})
def spf_mv_o(
    area_type=None,
    lanes=None,
    aadt=None,
    length_eff=None,
    **kwargs
    ):
    n = spf(length_i=length_eff, aadt=aadt, **kwargs)
    return n

@model.add_spf(refs={'spf_sv':{'severity':'kabc'}})
def spf_sv_kabc(
    area_type=None,
    lanes=None,
    aadt=None,
    length_eff=None,
    **kwargs
    ):
    n = spf(length_i=length_eff, aadt=aadt, **kwargs)
    return n

@model.add_spf(refs={'spf_sv':{'severity':'o'}})
def spf_sv_o(
    area_type=None,
    lanes=None,
    aadt=None,
    length_eff=None,
    **kwargs
    ):
    n = spf(length_i=length_eff, aadt=aadt, **kwargs)
    return n

@model.add_spf(refs={'spf_en':{'severity':'kabc'}})
def spf_en_kabc(
    area_type=None,
    lanes=None,
    aadt=None,
    length_en=None,
    **kwargs
    ):
    n = spf(length_i=length_en, aadt=aadt, **kwargs)
    return n

@model.add_spf(refs={'spf_en':{'severity':'o'}})
def spf_en_o(
    area_type=None,
    lanes=None,
    aadt=None,
    length_en=None,
    **kwargs
    ):
    n = spf(length_i=length_en, aadt=aadt, **kwargs)
    return n

@model.add_spf(refs={'spf_ex':{'severity':'kabc'}})
def spf_ex_kabc(aadt=None, length_ex=None, **kwargs):
    n = spf(length_i=length_ex, aadt=aadt, **kwargs)
    return n

@model.add_spf(refs={'spf_ex':{'severity':'o'}})
def spf_ex_o(aadt=None, length_ex=None, **kwargs):
    n = spf(length_i=length_ex, aadt=aadt, **kwargs)
    return n


##############
# DEFINE AFS #
##############

model.add_layer()

@model.add_sub()
def af_curve_main(
    curve_radius_inc_1=None,
    curve_radius_inc_2=None,
    curve_radius_inc_3=None,
    curve_radius_dec_1=None,
    curve_radius_dec_2=None,
    curve_radius_dec_3=None,
    curve_length_1=None,
    curve_length_2=None,
    curve_length_3=None,
    length_eff=None,
    **kwargs
    ):
    # Compute equivalent curve radii and lengths
    def _equivalent_curve_radius_length(r1, r2, l):
        if l == 0:
            res = 0
        elif r1 == 0:
            if r2 == 0:
                res = 0
            else:
                res = ((5730 / r2) ** 2) * (l * 0.5 / length_eff)
        elif r2 == 0:
            res = ((5730 / r1) ** 2) * (l * 0.5 / length_eff)
        else:
            r_equiv = ((0.5 / (r1 ** 2)) + (0.5 / (r2 ** 2))) ** -0.5
            res = ((5730 / r_equiv) ** 2) * (l / length_eff)
        return res
    
    af_1 = _equivalent_curve_radius_length(
        curve_radius_inc_1, curve_radius_dec_1, curve_length_1)
    af_2 = _equivalent_curve_radius_length(
        curve_radius_inc_2, curve_radius_dec_2, curve_length_2)
    af_3 = _equivalent_curve_radius_length(
        curve_radius_inc_3, curve_radius_dec_3, curve_length_3)
    
    # Compute main portion of AF equation
    res = af_1 + af_2 + af_3
    return res

model.add_layer()

# Curve adjustment factors
@model.add_af(
    refs={'af_curves':{'crash_type':['mv','sv'],'severity':['kabc','o']}},
    explode_refs=True)
def af_curve(af_curve_main=None, a=None, **kwargs):
    """
    Equation 18-24
    """
    # Compute AF
    af = 1 + a * af_curve_main
    return af

# Lane width adjustment factors
@model.add_af(
    refs={'af_lane_width':{'crash_type':['mv','sv'],'severity':['kabc']}},
    explode_refs=True)
def af_lane_width(lane_width=None, a=None, b=None, **kwargs):
    """
    Equation 18-25, 18-41
    """
    if lane_width < 13:
        af = math.exp(a * (lane_width - 12)) 
    else:
        af = b
    return af

# Inside shoulder width adjustment factors
@model.add_af(
    refs={'af_inside_shoulder_width':{'crash_type':['mv','sv'],'severity':['kabc','o']}},
    explode_refs=True)
def af_in_shoulder_width(inside_shoulder_width=None, a=None, **kwargs):
    """
    Equation 18-26
    """
    af = math.exp(a * (inside_shoulder_width - 6))
    return af

# Median width adjustment factors
@model.add_af(
    refs={'af_median_width':{'crash_type':['mv','sv'],'severity':['kabc','o']}},
    explode_refs=True)
def af_median_width(median_width=None, barrier_proportion=None, median_barrier_distance=None, a=None,**kwargs):
    """
    Equation 18-27, 18-43
    ***USES PROPORTIONS***
    """
    # Compute barrier and non-barrier contributions
    a = (1 - barrier_proportion) * math.exp(a * (median_width - (2 * median_width) - 48))
    b = barrier_proportion * math.exp(a * (2 * median_barrier_distance - 48))
    af = a + b
    return af

# Median barrier adjustment factors
@model.add_af(
    refs={'af_median_barrier':{'crash_type':['mv','sv'],'severity':['kabc','o']}},
    explode_refs=True)
def af_median_barrier(barrier_proportion=None, median_barrier_distance=None, a=None, **kwargs):
    """
    Equation 18-28, 18-44
    ***USES PROPORTIONS***
    Compute Wicb (bar_dist) with equation 18-48??
    """
    af = (1 - barrier_proportion) * 1 + barrier_proportion * math.exp(a / median_barrier_distance) 
    return af

# High volume adjustment factors
@model.add_af(
    refs={'af_high_volume':{'crash_type':['mv','sv'],'severity':['kabc','o']}},
    explode_refs=True)
def af_high_volume(aadt_prop=None, a=None, **kwargs):
    """
    Equation 18-29, 18-45
    """
    af = math.exp(a * aadt_prop)
    return af

# Lane change adjustment factors
@model.add_af(
    refs={'af_lane_change':{'severity':['kabc','o']}},
    explode_refs=True)
def af_lane_change(
    typeb_prop_inc=None,
    typeb_prop_dec=None,
    length_weave_inc=None,
    length_weave_dec=None,
    upstream_ent_inc=None,
    downstream_ex_dec=None,
    upstream_ent_dec=None,
    downstream_ex_inc=None,
    aadt_ent_inc=None,
    aadt_ex_dec=None,
    aadt_ent_dec=None,
    aadt_ex_inc=None,
    length=None,
    a=None,
    b=None, 
    c=None,
    d=None,
    **kwargs):
    """
    Equation 18-30, 18-31, 18-32, 18-33, 18-34
    ***USES PROPORTIONS***
    *** Should be ignored when downstream_ex_dec greater than 0.5?
    """
    # Compute contributing adjustment factors
    af_lane_change_inc = \
        (1 - typeb_prop_inc) * 1 + \
        typeb_prop_inc * math.exp(a / length_weave_inc)
    af_lane_change_dec = \
        (1 - typeb_prop_dec) * 1 + \
        typeb_prop_dec * math.exp(a / length_weave_dec)
    af_weave_inc = \
        (1 + ((math.exp(-b * upstream_ent_inc + d * math.log(c * aadt_ent_inc))) / (b * length)) * (1 - math.exp(-b * length))) * (1 + ((math.exp(-b * downstream_ex_inc + d * math.log(c * aadt_ex_inc))) / (b * length)) * (1 - math.exp(-b * length)))
    af_weave_dec = \
        (1 + ((math.exp(-b * upstream_ent_dec  + d * math.log(c * aadt_ent_dec))) / (b * length)) * (1 - math.exp(-b * length))) * (1 + ((math.exp(-b * downstream_ex_dec + d * math.log(c * aadt_ex_dec))) / (b * length)) * (1 - math.exp(-b * length)))
    # Combine contributions
    af = (0.5 * af_lane_change_inc * af_weave_inc) + \
         (0.5 * af_lane_change_dec * af_weave_dec)
    return af

# Outside shoulder width adjustment factor
@model.add_af(
    refs={'af_outside_shoulder_width':{'severity':['kabc','o']}},
    explode_refs=True)
def af_outside_shoulder_width(
    outside_shoulder_width=None,
    curve_length_1=None,
    curve_length_2=None,
    curve_length_3=None,
    length=None,
    a=None,
    b=None,
    **kwargs):
    """
    Equation 18-35
    """
    curve_prop = ((curve_length_1 + curve_length_2 + curve_length_3) / length)
    af = (1 - curve_prop) * math.exp(a * (outside_shoulder_width - 10)) + \
        curve_prop * math.exp(b * (outside_shoulder_width - 10))

    return af

# Shoulder rumble strips adjustment factor
@model.add_af()
def af_rumble_strips(
    curve_length_1=None,
    curve_length_2=None,
    curve_length_3=None,
    in_rumble_prop=None,
    out_rumble_prop=None,
    length=None,
    **kwargs):
    """
    Equations 18-36, 18-37
    """
    curve_prop = ((curve_length_1 + curve_length_2 + curve_length_3) / length)
    f_tangent = \
        0.5 * ((1 - in_rumble_prop) * 1 + in_rumble_prop * 0.811) + \
        0.5 * ((1 - out_rumble_prop) * 1 + out_rumble_prop * 0.811)
    af = (1 - curve_prop) * f_tangent + curve_prop * 1
    return af

# Outside Clearance
@model.add_af()
def af_outside_clearance(
    barrier_proportion=None,
    clear_zone_width=None,
    outside_barrier_distance=None,
    outside_shoulder_width=None,
    **kwargs):
    """
    Equation 18-38
    """
    af = (1 - barrier_proportion) * math.exp(-0.00451 * (clear_zone_width - outside_shoulder_width - 20)) + barrier_proportion * math.exp(-0.00451 * (outside_barrier_distance - 20))
    return af

# Outside barrier adjustment factors
@model.add_af(
    refs={'af_outside_barrier':{'severity':['kabc','o']}},
    explode_refs=True)
def af_outside_barrier(barrier_proportion=None, outside_barrier_distance=None, a=None, **kwargs):
    """
    Equation 18-39
    ***USES PROPORTIONS***
    """
    af = ((1 - barrier_proportion) * 1) + (barrier_proportion * math.exp(a / outside_barrier_distance))
    return af

# Ramp entrance speed change lane adjustment factor
@model.add_af(
    refs={'af_ramp_entrance':{'severity':['kabc','o']}}, explode_refs=True)
def af_high_volume_en(
    length_ramp=None,
    ramp_side=None,
    aadt_ramp=None,
    a=None,
    b=None,
    c=None,
    d=None,
    **kwargs
    ):
    """
    Equation 18-46
    """
    ramp_side = 1.0 if ramp_side=='left' else 0
    af = math.exp(a * ramp_side + (b / length_ramp) + d * math.log(c * aadt_ramp))
    return af

# Ramp exit speed change lane adjustment factor
@model.add_af(
    refs={'af_ramp_exit':{'severity':['kabc','o']}}, explode_refs=True)
def af_high_volume_ex(
    length_ramp=None,
    ramp_side=None,
    a=None,
    b=None,
    **kwargs
    ):
    """
    Equation 18-47
    """
    ramp_side = 1.0 if ramp_side=='left' else 0
    af = math.exp(a * ramp_side + (b / length_ramp))
    return af


######################
# DEFINE CALIBRATION #
######################

#model.add_layer()
#
#@model.add_element
#@CF.build(refs={'calibration':{}})
#def cf_total(cf=None, **kwargs):
#    return cf


##################
# DEFINE RESULTS #
##################

model.add_layer()

@model.add_result()
def pred_mv_kabc(
    spf_mv_kabc=None,
    af_curve_mv_kabc=None,
    af_lane_width_mv_kabc=None,
    af_in_shoulder_width_mv_kabc=None,
    af_median_width_mv_kabc=None,
    af_median_barrier_mv_kabc=None,
    af_high_volume_mv_kavc=None,
    af_lane_change=None,
    num_years=None,
    cf_total=None,
    **kwargs
    ):
    """
    """
    res = spf_mv_kabc * af_curve_mv_kabc * af_lane_width_mv_kabc * af_in_shoulder_width_mv_kabc * \
        af_median_width_mv_kabc * af_median_barrier_mv_kabc * af_high_volume_mv_kavc * num_years * \
            af_lane_change * cf_total
    return res


@model.add_result()
def pred_mv_o(
    spf_mv_o=None,
    af_curve_mv_o=None,
    af_lane_width_mv_o=None,
    af_in_shoulder_width_mv_o=None,
    af_median_width_mv_o=None,
    af_median_barrier_mv_o=None,
    af_high_volume_mv_o=None,
    af_lane_change_o=None,
    num_years=None,
    cf_total=None,
    **kwargs
    ):
    """
    """
    res = spf_mv_o * af_curve_mv_o * af_lane_width_mv_o * af_in_shoulder_width_mv_o * af_median_width_mv_o * \
        af_median_barrier_mv_o * af_high_volume_mv_o * af_lane_change_o * num_years * cf_total
    return res

@model.add_result()
def pred_sv_kabc(
    spf_sv_kabc=None,
    af_curve_sv_kabc=None,
    af_lane_width_sv_kabc=None,
    af_in_shoulder_width_sv_kabc=None,
    af_median_width_sv_kabc=None,
    af_median_barrier_sv_kabc=None,
    af_high_volume_sv_kavc=None,
    af_outside_shoulder_width_kabc=None,
    af_rumble_strips=None,
    af_outside_clearance=None,
    af_outside_barrier_kabc=None,
    num_years=None,
    cf_total=None,
    **kwargs
    ):
    """
    """
    res = spf_sv_kabc * af_curve_sv_kabc * af_lane_width_sv_kabc * af_in_shoulder_width_sv_kabc * \
        af_median_width_sv_kabc * af_median_barrier_sv_kabc * af_high_volume_sv_kavc * \
            af_outside_shoulder_width_kabc * af_rumble_strips * af_outside_clearance * \
                af_outside_barrier_kabc * num_years * cf_total
    return res

@model.add_result()
def pred_sv_o(
    spf_sv_o=None,
    af_curve_sv_o=None,
    af_lane_width_sv_o=None,
    af_in_shoulder_width_sv_o=None,
    af_median_width_sv_o=None,
    af_median_barrier_sv_o=None,
    af_high_volume_sv_o=None,
    af_outside_shoulder_width_o=None,
    af_rumble_strips=None,
    af_outside_clearance=None,
    af_outside_barrier_o=None,
    num_years=None,
    cf_total=None,
    **kwargs
    ):
    """
    """
    res = spf_sv_o * af_curve_sv_o * af_lane_width_sv_o * af_in_shoulder_width_sv_o * af_median_width_sv_o * \
        af_median_barrier_sv_o * af_high_volume_sv_o * af_outside_shoulder_width_o * af_rumble_strips * \
            af_outside_clearance * af_outside_barrier_o * num_years * cf_total
    return res

@model.add_result()
def pred_en_kabc(
    spf_en_kabc=None,
    af_curve_mv_kabc=None,
    af_lane_width_mv_kabc=None,
    af_in_shoulder_width_mv_kabc=None,
    af_median_width_mv_kabc=None,
    af_median_barrier_mv_kabc=None,
    af_high_volume_mv_kabc=None,
    af_ramp_entrance_kabc=None,
    num_years=None,
    cf_total=None,
    **kwargs
    ):
    """
    """
    res = spf_en_kabc * af_curve_mv_kabc * af_lane_width_mv_kabc * af_in_shoulder_width_mv_kabc * \
        af_median_width_mv_kabc * af_median_barrier_mv_kabc * af_high_volume_mv_kabc * af_ramp_entrance_kabc * \
            num_years * cf_total
    return res

@model.add_result()
def pred_en_o(
    spf_en_o=None,
    af_curve_mv_o=None,
    af_lane_width_mv_o=None,
    af_in_shoulder_width_mv_o=None,
    af_median_width_mv_o=None,
    af_median_barrier_mv_o=None,
    af_high_volume_mv_o=None,
    af_ramp_entrance_o=None,
    num_years=None,
    cf_total=None,
    **kwargs
    ):
    """
    """
    res = spf_en_o * af_curve_mv_o * af_lane_width_mv_o * af_in_shoulder_width_mv_o * af_median_width_mv_o * \
        af_median_barrier_mv_o * af_high_volume_mv_o * af_ramp_entrance_o * num_years * cf_total
    return res

@model.add_result()
def pred_ex_kabc(
    spf_ex_kabc=None,
    af_curve_mv_kabc=None,
    af_lane_width_mv_kabc=None,
    af_in_shoulder_width_mv_kabc=None,
    af_median_width_mv_kabc=None,
    af_median_barrier_mv_kabc=None,
    af_high_volume_mv_kabc=None,
    af_ramp_exit_kabc=None,
    num_years=None,
    cf_total=None,
    **kwargs
    ):
    """
    """
    res = spf_ex_kabc * af_curve_mv_kabc * af_lane_width_mv_kabc * af_in_shoulder_width_mv_kabc * \
        af_median_width_mv_kabc * af_median_barrier_mv_kabc * af_high_volume_mv_kabc * af_ramp_exit_kabc * \
            num_years * cf_total
    return res

@model.add_result()
def pred_ex_o(
    spf_ex_o=None,
    af_curve_mv_o=None,
    af_lane_width_mv_o=None,
    af_in_shoulder_width_mv_o=None,
    af_median_width_mv_o=None,
    af_median_barrier_mv_o=None,
    af_high_volume_mv_o=None,
    af_ramp_exit_o=None,
    num_years=None,
    cf_total=None,
    **kwargs
    ):
    """
    """
    res = spf_ex_o * af_curve_mv_o * af_lane_width_mv_o * af_in_shoulder_width_mv_o * af_median_width_mv_o * \
        af_median_barrier_mv_o * af_high_volume_mv_o * af_ramp_exit_o * num_years * cf_total
    return res

#model.add_layer()
#
#@model.add_element
#@Result.build(comp=dict(severity='kabco', crash_type='mv_dwy'))
#def pred_mv_dwy_kabco(spf_mv_dwy_kabco=None, af_total=None, cf_total=None, 
#    num_years=None, **kwargs):
#    res = spf_mv_dwy_kabco * af_total * cf_total * num_years
#    return res
#
#@model.add_element
#@Result.build(comp=dict(severity='kabco', crash_type='mv_ndwy'))
#def pred_mv_ndwy_kabco(spf_mv_ndwy_kabco=None, af_total=None, cf_total=None, 
#    num_years=None, **kwargs):
#    res = spf_mv_ndwy_kabco * af_total * cf_total * num_years
#    return res
#
#@model.add_element
#@Result.build(comp=dict(severity='kabco', crash_type='sv'))
#def pred_sv_kabco(spf_sv_kabco=None, af_total=None, cf_total=None, 
#    num_years=None, **kwargs):
#    res = spf_sv_kabco * af_total * cf_total * num_years
#    return res
#
#@model.add_element
#@Result.build(comp=dict(severity='kabco', crash_type='all'))
#def pred_kabco(spf_kabco=None, af_total=None, cf_total=None, 
#    num_years=None, **kwargs):
#    res = spf_kabco * af_total * cf_total * num_years
#    return res
#
#@model.add_element
#@Result.build(comp=dict(severity='kabc', crash_type='all'))
#def pred_kabc(spf_kabc=None, af_total=None, cf_total=None, 
#    num_years=None, **kwargs):
#    res = spf_kabc * af_total * cf_total * num_years
#    return res
#
#@model.add_element
#@Result.build(comp=dict(severity='o', crash_type='all'))
#def pred_o(spf_o=None, af_total=None, cf_total=None, 
#    num_years=None, **kwargs):
#    res = spf_o * af_total * cf_total * num_years
#    return res
#
#@model.add_element
#@Result.build(comp=dict(severity='kabco', crash_type='ped'))
#def pred_ped(spf_ped=None, af_total=None, cf_total=None, 
#    num_years=None, **kwargs):
#    res = spf_ped * af_total * cf_total * num_years
#    return res
#
#@model.add_element
#@Result.build(comp=dict(severity='kabco', crash_type='pdc'))
#def pred_pdc(spf_pdc=None, af_total=None, cf_total=None, 
#    num_years=None, **kwargs):
#    res = spf_pdc * af_total * cf_total * num_years
#    return res
#
#
###########################
## DEFINE EMPIRICAL-BAYES #
###########################
#
#model.add_layer()
#
#@model.add_element
#@Result.build(
#    refs={'spf_mv_dwy':{'severity':'kabco'}},
#    comp={'severity':'kabco', 'crash_type':'mv_dwy'}
#)
#def exp_mv_dwy_kabco(obs_mv_dwy_kabco=None, pred_mv_dwy_kabco=None, 
#    k=None, **kwargs):
#    """
#    Expected Crash Computation
#    """
#    # Check for observed crash input
#    if obs_mv_dwy_kabco is None or obs_mv_dwy_kabco == -1:
#        e = -1
#    else:
#        # Compute weighted adjustment
#        w = 1 / (1 + k * pred_mv_dwy_kabco)
#        # Compute expected average crash frequency
#        e = w * pred_mv_dwy_kabco + ((1 - w) * obs_mv_dwy_kabco)
#    return e
#
#@model.add_element
#@Result.build(
#    refs={'spf_mv_ndwy':{'severity':'kabco'}},
#    comp={'severity':'kabco', 'crash_type':'mv_ndwy'})
#def exp_mv_ndwy_kabco(obs_mv_ndwy_kabco=None, pred_mv_ndwy_kabco=None, 
#    k=None, **kwargs):
#    """
#    Expected Crash Computation
#    """
#    # Check for observed crash input
#    if obs_mv_ndwy_kabco is None or obs_mv_ndwy_kabco == -1:
#        e = -1
#    else:
#        # Compute weighted adjustment
#        w = 1 / (1 + k * pred_mv_ndwy_kabco)
#        # Compute expected average crash frequency
#        e = w * pred_mv_ndwy_kabco + ((1 - w) * obs_mv_ndwy_kabco)
#    return e
#
#@model.add_element
#@Result.build(
#    refs={'spf_sv':{'severity':'kabco'}},
#    comp={'severity':'kabco', 'crash_type':'sv'})
#def exp_sv_kabco(obs_sv_kabco=None, pred_sv_kabco=None, 
#    k=None, **kwargs):
#    """
#    Expected Crash Computation
#    """
#    # Check for observed crash input
#    if obs_sv_kabco is None or obs_sv_kabco == -1:
#        e = -1
#    else:
#        # Compute weighted adjustment
#        w = 1 / (1 + k * pred_sv_kabco)
#        # Compute expected average crash frequency
#        e = w * pred_sv_kabco + ((1 - w) * obs_sv_kabco)
#    return e
#
#model.add_layer()
#
#@model.add_element
#@Result.build(
#    comp={'severity':'kabco', 'crash_type':'all'})
#def exp_kabco(exp_mv_dwy_kabco=None, exp_mv_ndwy_kabco=None, 
#    exp_sv_kabco=None, **kwargs):
#    """
#    Expected Crash Computation
#    """
#    e = exp_mv_dwy_kabco + exp_mv_ndwy_kabco + exp_sv_kabco
#    return e


##############
# LOCK MODEL #
##############

model.lock()
