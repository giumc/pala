from tools import *
from devices import *

from phidl import quickplot as qp

# from phidl import export_gds

import pandas as pd

d=addProbe(array(addVia(FBERes,'top'),4),addLargeGnd(GSGProbe))(name="DEF")

# d=addProbe(array(calibration(FBERes,'open'),4),addLargeGnd(GSGProbe))(name="DEF")
base_params=d.export_params()



base_params["IDTPitch"]=7
base_params["IDTN"]=2
base_params["IDTOffset"]=1
base_params["IDTLength"]=100
base_params["IDTCoverage"]=0.5
base_params["BusSizeY"]=5
base_params["EtchPitX"]=10
base_params["IDTActiveAreaMargin"]=1
base_params["AnchorSizeY"]=20
base_params["AnchorSizeX"]=20
base_params["AnchorXOffset"]=0
base_params["AnchorMetalizedX"]=10
base_params["AnchorMetalizedY"]=24
base_params["ViaSize"]=10
base_params["Overvia"]=2
base_params["ViaAreaY"]=30
base_params["ViaAreaX"]= lambda : 3*d.idt.n*d.idt.pitch
d.import_params(base_params)

print(d)

import pathlib

d.draw().write_gds(str(pathlib.Path(__file__).stem))

# d.draw().write_gds("test.gds")

# check_cell(verniers())
# check_cell(alignment_marks_4layers())
# check_cell(resistivity_test_cell())
# check_cell(chip_frame())
# print(d.resistance())
# p=PArraySeries(d)
# v=check_cell(verniers([0.25,0.5,1 ]))
# p.x_param=[\
# SweepParam({'IDTN_fingers':[5,10,15,20]}),\
# SweepParam({'IDTLength':[20,40,60]})]
# SweepParam({'ViaSize':[10,20,50]})]

# p.view()
# rpq=1

# print(d.resistance(res_per_square=rpq))
