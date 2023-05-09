import pirel.pcells as pc

import pirel.sketch_tools as pst

import pirel.tools as pt

import phidl.geometry as pg

import phidl.path as pp

import phidl.routing as pr

from collections.abc import Iterable

class LoopDefault:

    y=100
    x=100
    width=5
    r_edge=5   

class QuarterLoop(pc.PartWithLayer):

    x=pt.LayoutParamInterface()
    y=pt.LayoutParamInterface()
    width=pt.LayoutParamInterface()
    r_edge=pt.LayoutParamInterface()

    def __init__(self,*a,**kw):

        super().__init__(*a,**kw)
        self.x=LoopDefault.x
        self.y=LoopDefault.y
        self.width=LoopDefault.width
        self.r_edge=LoopDefault.r_edge

    def draw(self):

        x=self.x
        y=self.y
        r_edge=self.r_edge

        if self.r_edge==0:

            p=pp.Path([[0,0],[-x,0],[-x,y]])

        else:

            p=pp.Path([[0,0],[-x+r_edge,0],[-x,r_edge],[-x,y-r_edge]])

        cell=p.extrude(width=self.width,layer=self.layer)
        
        s=cell.add_port(name='s',midpoint=(0,0),width=self.width,orientation=0)
        n=cell.add_port(name='n',midpoint=(-x,y),width=self.width,orientation=90)

        self.cell=cell
        
        return cell

class HalfLoop(pc.PartWithLayer):

    x=pt.LayoutParamInterface()
    y=pt.LayoutParamInterface()
    x_gap=pt.LayoutParamInterface()
    width=pt.LayoutParamInterface()
    r_edge=pt.LayoutParamInterface()

    def __init__(self,*a,**kw):

        super().__init__(*a,**kw)
        self.x=LoopDefault.x
        self.x_gap=LoopDefault.x/4
        self.y=LoopDefault.y
        self.width=LoopDefault.width
        self.r_edge=LoopDefault.r_edge

    def draw(self):

        x=self.x
        x_gap=self.x_gap
        x_low=self.x-self.x_gap
        x_high=self.x+self.x_gap
        y=self.y
        r_edge=self.r_edge

        if self.r_edge==0:

            p=pp.Path([[-x_gap,0],[-x,0],[-x,y],[x_gap,y]])

        else:

            p=pp.Path([[-x_gap,0],[-x+r_edge,0],[-x,r_edge],[-x,y-r_edge],[-x+r_edge,y],[x_gap,y]])

        cell=p.extrude(width=self.width,layer=self.layer)
        
        s=cell.add_port(name='s',midpoint=(-x_gap,0),width=self.width,orientation=0)
        n=cell.add_port(name='n',midpoint=(x_gap,y),width=self.width,orientation=0)

        self.cell=cell
        
        return cell

class Loop(HalfLoop):

    y_gap=pt.LayoutParamInterface()

    def __init__(self,*a,**kw):

        super().__init__(*a,**kw)
        self.y_gap=self.x_gap

    def draw(self):

        cell=pg.Device(name=self.name)
        h1=cell<<HalfLoop.draw(self)
        y_orig=self.y
        x_orig=self.x
        self.y=self.y-self.y_gap
        self.x=self.x-self.x_gap
        x_gap=self.x_gap
        self.x_gap=0
        h2=cell<<HalfLoop.draw(self)

        h2.connect('s',h1.ports['n'])

        self.y=y_orig
        self.x_gap=x_gap
        self.x=x_orig

        cell.add_port(port=h1.ports['s'],name='out')
        cell.add_port(port=h2.ports['n'],name='in')
        return cell

class Loops(Loop):

    n=pt.LayoutParamInterface()

    def __init__(self,*a,**kw):

        # self.n=3
        # self.width=[30,20,10]
        # self.y_gap=[5,5,5]
        # self.x_gap=[5,5,5]
        super().__init__(*a,**kw)
        self.width=[30,20,10]
        self.y_gap=[5,5,5]
        self.x_gap=[5,5,5]
        
    def draw(self):

        self._check_params()

        cell=pg.Device(name=self.name)

        n=self.n
        width=self._vectorize_param(self.width)
        x_gap=self._vectorize_param(self.x_gap)
        y_gap=self._vectorize_param(self.y_gap)
        
        loops=[]

        for i,w,x,y in zip(range(n),width,x_gap,y_gap):
            
            if i%2==0:

                self.x_gap=x    

            else:

                self.x_gap=-x

            self.width=w
            
            self.y_gap=y

            loops.append(cell<<Loop.draw(self))    
            self.y=self.y-2*y
            self.x=self.x-2*x

        for i in range(1,n):

            loops[i].connect('out',loops[i-1].ports['in'])

        return cell

    def _check_params(self):

        n=self.n
        width=self.width
        x_gap=self.x_gap
        y_gap=self.y_gap

        for x in [width,x_gap,y_gap]:

            if isinstance(x,Iterable):

                if not len(x)==self.n:

                    raise ValueError(f"""if {x} is iterable, it needs to have {n} order""")

    
    def _vectorize_param(self,x):

        n=self.n

        if not isinstance(x,Iterable):
            
            x=n*[x]

        return x

class Via(pc.PartWithLayer):

    metal_size=pt.LayoutParamInterface()

    cut_size=pt.LayoutParamInterface()

    metal_layers=pt.LayoutParamInterface()

    def __init__(self,*args,**kwargs):

        super().__init__(*args,**kwargs)
        self.metal_size=10
        self.cut_size=8
        self.metal_layers=(1,2)

    def draw(self):

        metal_size=self._vectorize_param(self.metal_size)
        cut_size=self._vectorize_param(self.cut_size)
        # cell=pg.rectangle(size/=metal_size,layer=
            
        return cell

    def _vectorize_param(self,param):

        if len(param)==2:

            return param
        
        elif len(param)==1:

            return (param,param)

        else:

            raise ValueError(f""" {param} sneeds to have dimension 1 or 2""")



    
