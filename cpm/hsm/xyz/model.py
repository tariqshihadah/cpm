# Logical Operations
# == equal to
# != not equal to
# >=
# <=
# 



#######################
# IMPORT DEPENDENCIES #
#######################

import math, os
from cpm.base.operators import Reference, FuncOperator
from cpm.base.elements import SPF, AF, Sub, Result
from cpm.base.model import Model


################
# DEFINE MODEL #
################

model = Model(name='_________')


#####################
# DEFINE REFERENCES #
#####################

fd = os.path.dirname(os.path.abspath(__file__))
fp = lambda fn: os.path.join(fd,fn)
#model.add_reference(Reference.read_json(fp=fp('spf.json')))


###############
# DEFINE SPFS #
###############

model.add_layer()

@Sub.build()
def spf(______________, cf=None, **kwargs):
    """
    Based on HSM Equations __________
    """
    n = _____________
    return n

@model.add_element
@SPF.build(limits=dict(________), values=dict(________))
def spf_______(factype=None, aadt_maj=None, aadt_min=None, **kwargs):
    n = _________
    return n
        

##############
# DEFINE AFS #
##############

@model.add_element
@AF.build(values=dict(________))
def af______(__________, **kwargs):
    """
    _____________
    Based on Tables _______, Equations _____________
    """
    af = ___________
    return af


##################
# DEFINE RESULTS #
##################

model.add_layer()

@model.add_element
@Result.build(comp=dict(sevtype='kabco', cshtype='all'))
#                                ^^^^^            ^^^
#              Change if composition will be different
def agg_____(__________, **kwargs):
    #   ^^^^ ^^^^^^^^^^
    # Arguments for agg functions should be all AFs and SPFs defined above as 
    # well as any additional Subs if applicable. Additionally, allude to the 
    # composition in the agg function name if applicable (e.g., agg_kabco if 
    # there is also an agg_kabc)

    # Combine AFs
    af = af_int_angle_kabco * af_major_ltl_kabco * af_major_rtl_kabco * \
        af_lighting
    res = af * spf_kabco
    return res
