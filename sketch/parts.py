from building_blocks import *

from layout_tools import *

ld=LayoutDefault()

import pandas as pd

import warnings

def Scaled(res):

    class Scaled(res):

        def __init__(self,*args,**kwargs):

            res.__init__(self,*args,**kwargs)

        def draw(self):

            selfcopy=deepcopy(self)

            p=selfcopy.idt.pitch

            selfcopy.idt.y_offset=self.idt.y_offset*p

            selfcopy.idt.y=self.idt.y*p

            selfcopy.bus.size.y=self.bus.size.y*p

            selfcopy.etchpit.x=self.etchpit.x*selfcopy.idt.active_area.x

            selfcopy.anchor.size.x=self.anchor.size.x*selfcopy.idt.active_area.x

            selfcopy.anchor.size.y=self.anchor.size.y*p

            selfcopy.anchor.etch_margin.x=self.anchor.etch_margin.x*selfcopy.anchor.size.x

            selfcopy.anchor.etch_margin.y=self.anchor.etch_margin.y*p

            cell=res.draw(selfcopy)

            del selfcopy

            self.cell=cell

            return cell

        def resistance(self,res_per_square=0.1):

            ridt=self.idt.resistance(res_per_square)*self.idt.pitch
            rbus=self.bus.resistance(res_per_square)/self.idt.pitch/2
            ranchor=self.anchor.resistance(res_per_square)\
                *self.idt.pitch/self.idt.active_area.x/\
                (1-2*self.anchor.etch_margin.x)

            return ridt+rbus+ranchor

    return Scaled

def addVia(res,side='top',bottom_conn=False):

    if isinstance(side,str):

        side=[side]

    side=[(_).lower() for _ in side]

    class addVia(res):

        def __init__(self,*args,**kwargs):

            # import pdb; pdb.set_trace()

            res.__init__(self,*args,**kwargs)
            self.via=Via(name=self.name+'Via')
            self.padlayers=[ld.layerTop,ld.layerBottom]
            self.overvia=2
            self.viadistance=100
            self.via_area=Point(100,100)

        def draw(self):

            # import pdb; pdb.set_trace()

            rescell=res.draw(self)

            active_width=rescell.xsize

            nvias_x,nvias_y=self.get_n_vias()

            viacell=draw_array(self._draw_padded_via(),nvias_x,nvias_y)

            cell=Device(name=self.name)

            cell<<rescell

            try:

                top_port=rescell.ports['top']

            except Exception:

                top_port=None

            try:

                bottom_port=rescell.ports['bottom']

            except Exception:

                bottom_port=None

            for sides in side:

                if sides=='top':

                    try :

                        top_port=rescell.ports['top']

                    except Exception:

                        raise ValueError ("Cannot add a top via in a cell with no top port")

                    pad=pg.compass(size=(top_port.width,self.viadistance),layer=self.padlayers[0])

                    top_port=self._attach_instance(cell, pad, pad.ports['S'], viacell, top_port)

                if sides=='bottom':

                    try :

                        bottom_port=rescell.ports['bottom']

                    except Exception:

                        raise ValueError ("Cannot add a bottom via in a cell with no bottom port")

                    pad=pg.compass(size=(bottom_port.width,self.viadistance),layer=self.padlayers[0])

                    bottom_port=self._attach_instance(cell, pad, pad.ports['N'], viacell, bottom_port)

            cell=join(cell)

            if top_port is not None:

                cell.add_port(top_port)

            if bottom_port is not None:

                cell.add_port(bottom_port)

            if bottom_conn==False:

                cell.remove_layers(layers=[self.padlayers[1]])

            self.cell=cell

            return cell

        def export_params(self):

            t=res.export_params(self)

            t_via=self.via.export_params().drop(columns=['Type'])

            t_via=t_via.rename(columns=lambda x: "Via"+x)

            t_via['Overvia']=self.overvia
            t_via['ViaDistance']=self.viadistance
            t_via['ViaAreaX']=self.via_area.x
            t_via['ViaAreaY']=self.via_area.y
            t=LayoutPart._add_columns(t,t_via)

            return t

        def import_params(self, df):

            res.import_params(self, df)

            for col in df.columns:

                if_match_import(self.via,col,"Via",df)

                if col=='Overvia':

                    self.overvia=df[col].iat[0]

                if col=='ViaDistance':

                    self.viadistance=df[col].iat[0]

                if col=='ViaAreaX':

                    self.via_area.x=df[col].iat[0]

                if col=='ViaAreaY':

                    self.via_area.y=df[col].iat[0]

        def bbox_mod(self,bbox):

            LayoutPart.bbox_mod(self,bbox)

            ll=Point().from_iter(bbox[0])

            ur=Point().from_iter(bbox[1])

            nvias_x,nvias_y=self.get_n_vias()

            if any([_=='top' for _ in side]):

                ur=ur-Point(0,float(self.via.size*self.overvia*nvias_y-self.viadistance))

            if any([_=='bottom' for _ in side]):

                ll=ll+Point(0,float(self.via.size*self.overvia*nvias_y+self.viadistance))

            return (ll(),ur())

        def _draw_padded_via(self):

            viacell=self.via.draw()

            size=float(self.via.size*self.overvia)

            port=viacell.get_ports()[0]

            trace=pg.rectangle(size=(size,size),layer=self.padlayers[0])

            trace.move(origin=trace.center.tolist(),\
                destination=viacell.center.tolist())

            trace2=pg.copy_layer(trace,layer=self.padlayers[0],new_layer=self.padlayers[1])

            cell=Device(name=self.name)

            cell.absorb((cell<<trace))

            cell.absorb((cell<<trace2))

            cell.absorb(cell<<viacell)

            port.midpoint=(port.midpoint[0],cell.ymax)

            port.width=size

            cell=join(cell)

            cell.add_port(port)

            return cell

        def _attach_instance(self,cell,padcell,padport,viacell,port):

            padref=cell<<padcell

            padref.connect(padport,\
                    destination=port)

            cell.absorb(padref)

            viaref=cell<<viacell

            viaref.connect(viacell.get_ports()[0],\
            destination=port,\
            overlap=-self.viadistance)

            return port

        def get_n_vias(self):

            import numpy as np

            nvias_x=max(1,int(np.floor(self.via_area.x/self.via.size/self.overvia)))
            nvias_y=max(1,int(np.floor(self.via_area.y/self.via.size/self.overvia)))

            return nvias_x,nvias_y

    return addVia

def addPad(res):

    class addPad(res):

        def __init__(self,*args,**kwargs):

            res.__init__(self,*args,**kwargs)
            self.pad=Pad(name=self.name+'Pad')

        def draw(self):

            destcell=res.draw(self)

            for port in destcell.get_ports():

                self.pad.port=port

                ref=destcell<<self.pad.draw()

                ref.connect(ref.ports['conn'],\
                    destination=port)

                destcell.absorb(ref)

            self.cell=destcell

            return destcell

        def export_params(self):

            t_pad=self.pad.export_params().drop(columns=['Type'])

            t_pad=t_pad.rename(columns=lambda x: "Pad"+x)

            t=res.export_params(self)

            t=LayoutPart._add_columns(t,t_pad)

            return t

        def import_params(self, df):

            res.import_params(self,df)

            for col in df.columns:

                if_match_import(self.pad,col,"Pad",df)

        def resistance(self,res_per_square=0.1):

            r0=super().resistance(res_per_square)

            for port in res.draw(self).get_ports():

                self.pad.port=port

                r0=r0+self.pad.resistance(res_per_square)

            return r0

    return addPad

def addProbe(res,probe):

    class addProbe(res):

        def __init__(self,*args,**kwargs):

            res.__init__(self,*args,**kwargs)

            # import pdb; pdb.set_trace()

            self.probe=probe(self.name+"Probe")

            self.gnd_routing_width=ld.DUTrouting_width

            # self.signal_routing_width=ld.DUTrouting_width

            self.probe_dut_distance=ld.DUTprobe_dut_distance

        def draw(self):

            device_cell=res.draw(self)

            probe_cell=self.probe.draw()

            cell=Device(name=self.name)

            probe_dut_distance=Point(0,self.probe_dut_distance)

            cell<<device_cell

            bbox=cell.bbox

            probe_ref=cell<<probe_cell

            import pdb; pdb.set_trace()

            probe_ref.connect(probe_cell.ports['sig'],\
            destination=device_cell.ports['bottom'],overlap=-probe_dut_distance.y)

            dut_port_bottom=device_cell.ports['bottom']
            dut_port_top=device_cell.ports['top']

            bbox=super().bbox_mod(bbox)

            if isinstance(self.probe,GSGProbe):

                probe_port_lx=probe_ref.ports['gnd_left']
                probe_port_center=probe_ref.ports['sig']
                probe_port_rx=probe_ref.ports['gnd_right']

                routing_lx=self._route(bbox,probe_port_lx,dut_port_top)

                self._routing_lx_length=routing_lx.area()/self.gnd_routing_width

                routing_c=pg.compass(size=(dut_port_bottom.width,\
                    self.probe_dut_distance),layer=self.probe.layer)

                routing_rx=self._route(bbox,probe_port_rx,dut_port_top)

                self._routing_rx_length=routing_rx.area()/self.gnd_routing_width

                routing_tot=pg.boolean(routing_lx,routing_rx,'or',layer=self.probe.layer)

                cell<<routing_tot

                center_routing=cell<<routing_c

                center_routing.connect(center_routing.ports['S'],destination=dut_port_bottom)

            elif isinstance(self.probe,GSProbe):

                raise ValueError("DUT with GSprobe to be implemented ")

            else:

                raise ValueError("DUT without GSG/GSprobe to be implemented ")

            del probe_cell,device_cell,routing_lx,routing_rx,routing_c,routing_tot

            cell.flatten()

            cell=join(cell)

            self.cell=cell

            return cell

        def _route(self,bbox,p1,p2):

            routing=Routing()
            routing.layer=self.probe.layer
            routing.clearance=bbox
            routing.trace_width=self.gnd_routing_width
            routing.ports=(p1,p2)
            cell=routing.draw()
            del routing
            return cell

        def export_params(self):

            t=super().export_params()

            t=t.rename(columns={"Type":"DUT_Type"})

            t_probe=self.probe.export_params()

            t_probe=t_probe.rename(columns=lambda x : "Probe"+x )

            t=self._add_columns(t,t_probe)

            t["GNDRoutingWidth"]=self.gnd_routing_width

            # t["SignalRoutingWidth"]=self.signal_routing_width

            t["ProbeDistance"]=self.probe_dut_distance

            t.index=[self.name]

            t=t.reindex(columns=["Type"]+[cols for cols in t.columns if not cols=="Type"])

            return t

        def import_params(self,df):

            super().import_params(df)

            for col in df.columns:

                if_match_import(self.probe,col,"Probe",df)

                if col == "GNDRoutingWidth" :
                    # import pdb; pdb.set_trace()
                    self.gnd_routing_width=df[col].iat[0]

                if col == "ProbeDistance" :

                    self.probe_dut_distance=df[col].iat[0]

                # if col =="SignalRoutingWidth":
                #
                #     self.signal_routing_width=df[col].iat[0]

        def resistance(self,res_per_square=0.1):

            self.draw()

            rdut=res.resistance(self,res_per_square=res_per_square)

            rprobe_gnd=res_per_square*(self._routing_lx_length/self.gnd_routing_width+\
                self._routing_rx_length/self.gnd_routing_width)/2

            sig_width=res.draw(self).ports['bottom'].width

            rprobe_sig=res_per_square*(self.probe_dut_distance/sig_width)

            return rprobe_sig+rdut+rprobe_gnd

    return addProbe

def addLargeGnd(probe):

    class addLargeGnd(probe):

        def __init__(self,*args,**kwargs):

            probe.__init__(self,*args,**kwargs)

            self.groundsize=ld.GSGProbe_LargePadground_size

        def draw(self):

            cell=probe.draw(self)

            oldports=[_ for _ in cell.get_ports()]

            groundpad=pg.compass(size=(self.groundsize,self.groundsize),\
            layer=self.layer)

            [_,_,ul,ur]=get_corners(groundpad)

            for p in cell.get_ports():

                name=p.name

                if 'gnd' in name:

                    groundref=cell<<groundpad

                    if 'left' in name:

                        groundref.move(origin=ur(),\
                        destination=p.endpoints[1])

                        left_port=groundref.ports['N']
                        left_port.name=p.name

                    elif 'right' in name:

                        groundref.move(origin=ul(),\
                        destination=p.endpoints[0])

                        right_port=groundref.ports['N']
                        right_port.name=p.name

                    cell.absorb(groundref)

            cell=join(cell)

            [cell.add_port(_) for _ in oldports]

            for p in cell.get_ports():

                name=p.name

                # import pdb; pdb.set_trace()

                if 'gnd' in name:

                    if 'left' in name:

                        cell.remove(cell.ports[name])
                        cell.add_port(left_port)

                    elif 'right' in name:

                        cell.remove(cell.ports[name])
                        cell.add_port(right_port)

            self.cell=cell

            return cell

        def export_params(self):

            t=probe.export_params(self)

            t["GroundPadSize"]=self.groundsize

            return t

        def import_params(self,df):

            probe.import_params(self,df)

            for cols in df.columns:

                if cols=='GroundPadSize':

                    self.groundsize=df[cols].iat[0]

    return addLargeGnd

def array(res,n):

    class array(res):

        def __init__(self,*args,**kwargs):

            res.__init__(self,*args,**kwargs)
            self.bus_ext=Bus(name=self.name+'ExtBus')
            self.n=n

        def export_params(self):

            t=res.export_params(self)

            t["NArrays"]=self.n
            t["ExtConnLength"]=self.bus_ext.size.y

            return t

        def import_params(self,df):

            res.import_params(self,df)

            for cols in df.columns:

                if cols=='NCopies':

                    self.n=df[cols].iat[0]

                if cols=='ExtConnLength':

                    self.bus_ext.size.y=df[cols].iat[0]

        def draw(self):

            unit_cell=res.draw(self)

            cell=draw_array(unit_cell,\
                self.n,1)

            port=cell.get_ports()[0]

            celly=cell.ysize

            self.bus_ext.size.x=port.width
            self.bus_ext.distance=Point(0,celly+self.bus_ext.size.y)
            self.bus_ext.layer=self.idt.layer

            buscell=self.bus_ext.draw()

            busres=cell<<buscell

            busres.connect(buscell.get_ports()[0],\
                destination=port)

            cell=join(cell)

            cell.add_port(Port(name='top',\
            midpoint=(port.midpoint[0],port.midpoint[1]+self.bus_ext.size.y),
            width=port.width,\
            orientation=90))

            cell.add_port(Port(name='bottom',\
            midpoint=(port.midpoint[0],port.midpoint[1]-self.bus_ext.size.y-celly),
            width=port.width,\
            orientation=-90))

            self.cell=cell

            check_cell(cell)

            return cell

    return array

class LFERes(LayoutPart):

    def __init__(self,*args,**kwargs):

        LayoutPart.__init__(self,*args,**kwargs)

        self.layer=ld.IDTlayer

        self.idt=IDT(name=self.name+'IDT')

        self.bus=Bus(name=self.name+'Bus')

        self.etchpit=EtchPit(name=self.name+'EtchPit')

        self.anchor=Anchor(name=self.name+'Anchor')

    def draw(self):

        o=self.origin

        self.idt.origin=o

        self.idt.layer=self.layer

        idt_cell=self.idt.draw()

        cell=Device(name=self.name)

        idt_ref=cell<<idt_cell

        self.bus.size=Point(\
            2*self.idt.pitch*(self.idt.n-1)+(self.idt.coverage)*self.idt.pitch,\
            self.bus.size.y)

        self.bus.distance=Point(\
            self.idt.pitch,self.bus.size.y+self.idt.y+self.idt.y_offset)

        self.bus.layer=self.layer

        bus_cell = self.bus.draw()

        bus_ref= cell<<bus_cell

        ports=cell.get_ports()

        bus_ref.connect(port=ports[1],\
        destination=ports[0])

        cell.absorb(idt_ref)

        self.etchpit.active_area=Point().from_iter(cell.size)+\
        Point(self.idt.pitch*(1-self.idt.coverage),self.anchor.etch_margin.y*2)

        etch_cell=self.etchpit.draw()

        etch_ref=cell<<etch_cell

        ports=cell.get_ports()
        etch_ref.connect(ports[2],\
        destination=ports[0])

        etch_ref.move(origin=etch_ref.center,\
        destination=(Point().from_iter(etch_ref.center)+\
            Point(self.idt.pitch/2,-self.bus.size.y-self.anchor.etch_margin.y))())

        cell.absorb(bus_ref)

        # return cell

        self.anchor.etch_x=self.etchpit.x*2+self.etchpit.active_area.x

        self.anchor.layer=self.layer

        if self.anchor.size.x>self.bus.size.x:

            self.anchor.size=Point(self.bus.size.x,self.anchor.size.y)
            warnings.warn("Anchor is too wide, reduced to Bus width size")

        anchor_cell=self.anchor.draw()

        anchor_bottom=cell<<anchor_cell

        ports=cell.get_ports()

        anchor_bottom.connect(ports[2],
        destination=ports[1],overlap=self.anchor.etch_margin.y)
        anchor_bottom.move(origin=(0,0),\
        destination=(-self.anchor.x_offset,0))

        anchor_top=(cell<<anchor_cell)
        anchor_top.move(origin=anchor_top.center,\
        destination=anchor_bottom.center)
        anchor_pivot=ports[2]

        anchor_top.rotate(angle=180,center=ports[1].center)
        anchor_top.move(origin=(0,0),\
        destination=(0,self.etchpit.active_area.y))

        cell.absorb(etch_ref)

        ports=cell.get_ports()
        ports[0].rotate(180,center=ports[0].center)
        ports[1].rotate(180,center=ports[1].center)

        cell.absorb(anchor_top)
        cell.absorb(anchor_bottom)

        cell_out=join(cell)

        cell_out.add_port(Port(name="top",\
        midpoint=(Point().from_iter(ports[1].center)+\
        Point(0,self.anchor.size.y))(),\
        width=self.anchor.size.x-2*self.anchor.etch_margin.x,\
        orientation=90))

        cell_out.add_port(Port(name="bottom",\
        midpoint=(Point().from_iter(ports[0].center)-\
        Point(0,self.anchor.size.y))(),\
        width=self.anchor.size.x-2*self.anchor.etch_margin.x,\
        orientation=-90))

        del idt_cell,bus_cell,etch_cell,anchor_cell

        self.cell=cell_out

        return cell_out

    def export_params(self):

        t=super().export_params()

        t_res=self.idt.export_params().drop(columns=['Type'])

        t_res=t_res.rename(columns=lambda x: "IDT"+x)

        t=self._add_columns(t,t_res)

        t_bus=self.bus.export_params().drop(columns=['Type','DistanceX','DistanceY','Width'])
        t_bus=t_bus.rename(columns=lambda x: "Bus"+x)

        t=self._add_columns(t,t_bus)

        t_etch=self.etchpit.export_params().drop(columns=['Type','ActiveArea'])
        t_etch=t_etch.rename(columns=lambda x: "Etch"+x)

        t=self._add_columns(t,t_etch)

        t_anchor=self.anchor.export_params().drop(columns=['Type','EtchWidth','Offset','EtchChoice'])
        t_anchor=t_anchor.rename(columns=lambda x: "Anchor"+x)

        t=self._add_columns(t,t_anchor)

        t.index=[self.name]

        t=t.reindex(columns=['Type']+[col for col in t.columns if not col=='Type'])

        return t

    def import_params(self,df):

        LayoutPart.import_params(self,df)

        for col in df.columns:

            if_match_import(self.idt,col,"IDT",df)
            if_match_import(self.bus,col,"Bus",df)
            if_match_import(self.etchpit,col,"Etch",df)
            if_match_import(self.anchor,col,"Anchor",df)

    def resistance(self,res_per_square=0.1):

        self.draw()

        ridt=self.idt.resistance(res_per_square)
        rbus=self.bus.resistance(res_per_square)
        ranchor=self.anchor.resistance(res_per_square)

        return ridt+rbus+ranchor

class FBERes(LFERes):

    def __init__(self,*args,**kwargs):

        super().__init__(*args,**kwargs)

        self.platelayer=ld.FBEResplatelayer

    def draw(self):

        cell=LFERes.draw(self)

        plate=pg.rectangle(size=self.etchpit.active_area(),\
        layer=self.platelayer)

        plate_ref=cell<<plate

        transl_rel=Point(self.etchpit.x,self.anchor.size.y-self.anchor.etch_margin.y)
        lr_cell=get_corners(cell)[0]
        lr_plate=get_corners(plate_ref)[0]
        plate_ref.move(origin=lr_plate(),\
        destination=(lr_plate+lr_cell+transl_rel)())

        cell.absorb(plate_ref)

        del plate

        self.cell=cell

        return cell

class TFERes(LFERes):

    def __init__(self,*args,**kwargs):

        super().__init__(*args,**kwargs)

        self.bottomlayer=ld.TFEResbottomlayer

    def draw(self):

        cell=LFERes.draw(self)

        idt_bottom=copy(self.idt)
        idt_bottom.layer=self.bottomlayer

        idt_ref=cell<<idt_bottom.draw()

        idt_ref.mirror(p1=(idt_ref.xmin,idt_ref.ymin),\
        p2=(idt_ref.xmin,idt_ref.ymax))

        idt_ref.move(origin=(0,0),\
        destination=(idt_bottom.pitch*(idt_bottom.n*2-(1-idt_bottom.coverage)),0))

        cell.absorb(idt_ref)

        bus_bottom=copy(self.bus)
        bus_bottom.layer=self.bottomlayer

        bus_ref=cell<<bus_bottom.draw()

        bus_ref.mirror(p1=(bus_ref.xmin,bus_ref.ymin),\
         p2=(bus_ref.xmin,bus_ref.ymax))

        bus_ref.move(origin=(0,0),\
        destination=\
            (idt_bottom.pitch*(idt_bottom.n*2-(1-idt_bottom.coverage)),\
            -bus_bottom.size.y))

        cell.absorb(bus_ref)

        anchor_bottom=copy(self.anchor)

        anchor_bottom.layer=self.bottomlayer
        anchor_bottom.etch_choice=False

        anchor_ref=cell<<anchor_bottom.draw()
        anchor_ref.rotate(angle=180)

        ports=cell.get_ports()
        anchor_ref.connect(ports[2],ports[0])

        cell.absorb(anchor_ref)

        anchor_ref_2=cell<<anchor_bottom.cell
        anchor_ref_2.rotate(angle=180)
        ports=cell.get_ports()

        anchor_ref_2.connect(ports[2],ports[1])

        cell.absorb(anchor_ref_2)

        join(cell)

        # anchor_ref.move(origin=(0,0),\
        # destination=(50,0))

        del idt_bottom

        del bus_bottom

        del anchor_bottom

        self.cell=cell

        return cell

class WBArray(LayoutPart):

    def __init__(self,*args,**kwargs):

        super().__init__(*args,**kwargs)

        try:

            if isinstance(args[0],LayoutPart):

                self.device=args[0]

        except Exception:

            self.device=LFERes(name=self.name+'Device')

        self.n=ld.Stackn

        self.gnd_width=self.device.pad.size*1.5

        self.test=True

    @property
    def device(self):

        self._unpadded_device.import_params(self._padded_device.export_params())
        return self._padded_device

    @device.setter
    def device(self,dev):

        self._unpadded_device=dev

        device_with_pads=addPad(dev.__class__)()

        device_with_pads.import_params(dev.export_params())

        self._padded_device=device_with_pads

    def export_params(self):

        t=self.device.export_params()
        t["NCopies"]=self.n
        t["GndWidth"]=self.gnd_width

        return t

    def import_params(self,df):

        self.device.import_params(df)

        for cols in df.columns:

            if cols=='NCopies':

                self.n=df[cols].iat[0]

            if cols=='GndWidth':

                self.gnd_width=df[cols].iat[0]

    def draw(self):

        device=self.device

        cell=draw_array(device.draw(),\
            self.n,1)

        port=cell.get_ports()[0]

        cell=join(cell)

        out_port=Port(name='bottom',\
        midpoint=(port.midpoint[0],port.midpoint[1]-cell.ysize+device.pad.size),\
        width=cell.xsize,\
        orientation=-90)

        cell.add_port(out_port)

        gnd_width=self.gnd_width

        gndpad=pg.compass(size=(cell.xsize,gnd_width),layer=device.pad.layer)

        gnd_ref=cell<<gndpad

        gnd_ref.connect(gndpad.ports['N'],\
            destination=out_port)

        cell.absorb(gnd_ref)

        cell=join(cell)

        cell.add_port(out_port)

        if self.test:

            dut=addProbe(self.device,GSGProbe())

            # import pdb; pdb.set_trace()

            dut.import_params(self._unpadded_device.export_params())

            dut.draw()

            cell.add(dut.cell)

            import pdb; pdb.set_trace()

            self.text_params.update({'location':'left'})
            self.add_text(cell,\
            text_opts=self.text_params)

            g=Group([cell,dut.cell])

            g.distribute(direction='x',spacing=150)

            cell=join(cell)

            cell.name=dut.name

        self.cell=cell

        return cell
