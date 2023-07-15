import pirel.pcells as pc

import pirel.sketch_tools as pst

import pirel.tools as pt

import phidl.geometry as pg

import phidl.path as pp

import phidl.routing as pr

import phidl.device_layout as dl

from collections.abc import Iterable

from math import ceil,floor

import numpy as np

from pala.loops import Vias

import pdb

from copy import copy,deepcopy

class TLineDefault:

    l=100
    w=5
    d=3
    mesh_w=20
    mesh_gap=20
    mesh_hole=5
    meshnx=3
    meshny=10

class Strip(pc.PartWithLayer):

    w=pt.LayoutParamInterface()

    l=pt.LayoutParamInterface()

    def __init__(self,*a,**kw):

        super().__init__(*a,**kw)

        self.l=TLineDefault.l
        self.w=TLineDefault.w

    def draw(self):

        cell=dl.Device(self.name)
        
        box=cell<<pg.compass(size=(self.l,self.w),layer=self.layer)

        box.movex(self.l/2)
        
        cell.add_port(port=box.ports['W'],name='in')

        cell.add_port(port=box.ports['E'],name='out')

        return cell

class DiffStrip(pc.PartWithLayer):

    d=pt.LayoutParamInterface()

    def __init__(self,*a,**kw):

        super().__init__(*a,**kw)

        self.d=TLineDefault.d

    def draw(self):

        cell=dl.Device(self.name)
        
        pstrip=cell<<self.strip.draw()

        nstrip=cell<<self.strip.draw()
        
        nstrip.movey(-self.strip.w-self.d)

        cell.add_port(port=pstrip.ports['in'],name='in_p')

        cell.add_port(port=nstrip.ports['in'],name='in_n')

        cell.add_port(port=pstrip.ports['out'],name='out_p')

        cell.add_port(port=nstrip.ports['out'],name='out_n')
        
        return cell

    @staticmethod
    def get_components():

        return {'Strip':Strip}

class Mesh(Vias):

    def draw(self):

        viacell=Vias.draw(self)

        cex=pg.extract(viacell,layers=(self.layer,))
        
        cell=pg.boolean(viacell,cex,'A-B',layer=self.metal_layer)

        return cell

class MeshedDiffStrip(DiffStrip):

    def draw(self):

        cell=DiffStrip.draw(self)

        mesh=self.mesh.draw()

        g=dl.Group([mesh,cell])
        g.align(alignment='x')
        g.align(alignment='y')

        cell.add(mesh)

        return cell
    
    @staticmethod
    def get_components():

        l=copy(DiffStrip.get_components())

        l.update({"Mesh":Mesh})

        return l