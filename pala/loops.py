import pirel.pcells as pc

import pirel.sketch_tools as pst

import pirel.tools as pt

import phidl.geometry as pg

import phidl.path as pp

import phidl.routing as pr

import phidl.device_layout as dl

from collections.abc import Iterable

from math import ceil,floor

class LoopDefault:

    y=50
    x=50
    w=2
    r=2
    x_gap=6
    y_offset=3
    n=2.5

class QuarterLoop(pc.PartWithLayer):

    x=pt.LayoutParamInterface()
    y=pt.LayoutParamInterface()
    w =pt.LayoutParamInterface()
    r=pt.LayoutParamInterface()

    def __init__(self,*a,**kw):

        super().__init__(*a,**kw)
        self.x=LoopDefault.x
        self.y=LoopDefault.y
        self.w =LoopDefault.w 
        self.r=LoopDefault.r

    def draw(self):

        x=self.x
        y=self.y
        r=self.r

        if self.r==0:

            p=pp.Path([[0,0],[-x,0],[-x,y]])

        else:

            p=pp.Path([[0,0],[-x+r,0],[-x,r],[-x,y]])

        cell=p.extrude(width=self.w ,layer=self.layer)
        
        s=cell.add_port(name='s',midpoint=(0,0),width=self.w,orientation=0)
        n=cell.add_port(name='n',midpoint=(-x,y),width=self.w,orientation=90)

        self.cell=cell
        
        return cell

class HalfLoop(QuarterLoop):

    x_gap=pt.LayoutParamInterface()    

    def __init__(self,*a,**kw):

        super().__init__(*a,**kw)
        self.x_gap=LoopDefault.x_gap

    def draw(self):

        x_gap=self.x_gap
        
        x_orig=self.x

        y_orig=self.y
        
        self.x=x_orig-x_gap/2

        self.y=y_orig/2

        cell=dl.Device(self.name)

        short_corner=cell<<QuarterLoop.draw(self)

        self.x=x_orig+x_gap/2

        long_corner=cell<<QuarterLoop.draw(self)
        
        long_corner.mirror(p1=(0,0),p2=(0,1))
        
        long_corner.connect("n",short_corner.ports["n"])

        cell.add_port(short_corner.ports["s"])

        cell.add_port(port=long_corner.ports["s"],name="n")

        self.cell=cell

        self.x=x_orig

        self.y=y_orig

      
        return cell

class Loop(HalfLoop):

    y_offset=pt.LayoutParamInterface()
   
    def __init__(self,*a,**kw):

        super().__init__(*a,**kw)

        self.y_offset=LoopDefault.y_offset
   
    def draw(self):

        cell=pg.Device(name=self.name)

        y_orig=self.y

        x_orig=self.x

        x_offset_original=self.x_gap

        self.x=self.x/2
    
        h1=cell<<HalfLoop.draw(self)

        self.y=self.y-self.y_offset

        self.x=self.x-self.x_gap/2

        self.x_gap=0

        h2=cell<<HalfLoop.draw(self)

        h2.connect('s',h1.ports['n'])

        self.y=y_orig
        self.x_gap=x_offset_original
        self.x=x_orig

        cell.add_port(port=h1.ports['s'],name='s')
        cell.add_port(port=h2.ports['n'],name='n')
        return cell
    
class Loops(Loop):

    n=pt.LayoutParamInterface()
    
    x_offset=pt.LayoutParamInterface()

    def __init__(self,*a,**kw):

        super().__init__(*a,**kw)

        self.n=LoopDefault.n

        self.y_offset=[15,10,5]
        self.x_offset=[15,10,5]
        
    def draw(self):

        self._check_params()
        
        x0=self.x
        
        y0=self.y

        cell=pg.Device(name=self.name)

        n=ceil(self.n)

        w=self._vectorize_param(self.w)

        xg0=self.x_gap

        x_off=self._vectorize_param(self.x_offset)

        y_off=self._vectorize_param(self.y_offset)
        
        loops=[]

        for i,w,x,y in zip(range(n),w,x_off,y_off):
            
            if i%2==0:

                self.x_gap=xg0
            else:

                self.x_gap=-xg0

            self.w=w
            
            self.y_offset=y

            loops.append(Loop.draw(self))  

            self.y=self.y-2*y

            self.x=self.x-2*x

        loop_refs=[cell<<loops[0]]

        for i in range(1,n):

            print(f"""bum{i}""")

            if not i==n-1:

                loop_refs.append(cell<<loops[i])    

                loop_refs[i].connect('s',loop_refs[i-1].ports['n']) 

            elif i==n-1:

                if self.n%1==0:
                    
                    loop_refs.append(cell<<loops[i])    
            
                    loop_refs[i].connect('s',loop_refs[i-1].ports['n']) 

                elif self.n%1==0.5:

                    self.x=x0/2-sum(x_off[:-1])

                    self.y=y0-2*sum(y_off[:-1])

                    # print(f"""{x} and {y}""")
                    
                    loop_refs.append(cell<<HalfLoop.draw(self))

                    loop_refs[i].connect('s',loop_refs[i-1].ports['n']) 
                
                elif self.n%1==0.25:

                    self.x=x0/2-sum(x_off[:-1])-xg0/2
                    
                    self.y=(y0-2*sum(y_off[:-1]))/2

                    # print(f"""{x} and {y}""")
                    
                    loop_refs.append(cell<<QuarterLoop.draw(self))

                    loop_refs[i].connect('s',loop_refs[i-1].ports['n']) 

                elif self.n%1==0.75:

                    self.x=x0/2-sum(x_off[:-1])

                    self.y=y0-2*sum(y_off[:-1])

                    # print(f"""{x} and {y}""")
                    
                    loop_refs.append(cell<<HalfLoop.draw(self))

                    loop_refs[-1].connect('s',loop_refs[-2].ports['n'])

                    i=i+1

                    self.x=x0/2-sum(x_off[:-1])-xg0/2
                    
                    self.y=(y0-2*sum(y_off[:-1]))/2

                    # print(f"""{x} and {y}""")
                    
                    loop_refs.append(cell<<QuarterLoop.draw(self))

                    loop_refs[-1].connect('s',loop_refs[-2].ports['n'])  

                else:

                    raise ValueError(f"""n needs to be either integer or divisible by 4, {self.n} was passed!""")
                
                self.x=x0
                
                self.y=y0
                
        return cell
    
    def _check_params(self):

        n=ceil(self.n)
        w=self.w
        x_off=self.x_gap
        y_off=self.y_offset

        for x in [w,x_off,y_off]:

            if isinstance(x,Iterable):

                if not len(x)==n:

                    raise ValueError(f"""if {x} is iterable, it needs to have {n} order""")
    
    def _vectorize_param(self,x):

        n=ceil(self.n)

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



    
