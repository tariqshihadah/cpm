"""
OVERVIEW
--------
Crash Prediction Models based on the Highway Safety Manual (2010). The AASHTO-
created model spreadsheets were used to verify accuracy and performance of 
these models. When discrepancies occurred between the HSM text and the 
spreadsheets, priority was given to methods described in the HSM text except in 
cases where the methods in the spreadsheets represented more recent or more 
reliable information.

Currently available models include:


MODEL CONTENTS
--------------

Rural Two-Lane Roadway (Segments)
- Based on HSM Chapter 10.
- Import via:
>>> from cpm.hsm import rtl_seg

Rural Two-Lane Roadway (Intersections)
- Based on HSM Chapter 10.
- Import via:
>>> from cpm.hsm import rtl_int

Rural Multilane Roadway (Segments)
- Based on HSM Chapter 11.
- Import via:
>>> from cpm.hsm import rml_seg

Rural Multilane Roadway (Intersections)
- Based on HSM Chapter 11.
- Import via:
>>> from cpm.hsm import rml_int

Urban/Suburban Arterials (Segments)
- Based on HSM Chapter 12.
- Import via:
>>> from cpm.hsm import usa_seg

Urban/Suburban Arterials (Intersections)
- Based on HSM Chapter 12.
- Import via:
>>> from cpm.hsm import usa_int


VERSION INFORMATION
-------------------
Version information:
- v0.1.1
- First draft of defined models with freeway segment models
Version history:
- Created:          7/27/2020 (TJS)
- Last Modified:    11/3/2022 (TJS)


ACKNOWLEDGEMENTS
----------------

Model coding and validation performed by:
- Tariq Shihadah, RSP (Jacobs)
- Kyle Baumann (Jacobs)
- Minh Truong, RSP (Jacobs)
- Brianna Lawton (Jacobs)
- Mahdi Rajabi, RSP (Jacobs)
"""
# Load available models for access via cpm.hsm
from cpm.hsm.rtl_seg.model import model as rtl_seg
from cpm.hsm.rtl_int.model import model as rtl_int
from cpm.hsm.rml_seg.model import model as rml_seg
from cpm.hsm.rml_int.model import model as rml_int
from cpm.hsm.usa_seg.model import model as usa_seg
from cpm.hsm.usa_int.model import model as usa_int
from cpm.hsm.fwy_seg.model import model as fwy_seg

models = {
    'rtl_seg': rtl_seg,
    'rtl_int': rtl_int,
    'rml_seg': rml_seg,
    'rml_int': rml_int,
    'usa_seg': usa_seg,
    'usa_int': usa_int,
    'fwy_seg': fwy_seg,
}