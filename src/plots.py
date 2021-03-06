#!/usr/bin/env python
# -*- coding: utf-8 -*-

#MATPLOTLIB
import matplotlib
from matplotlib.figure import Figure
import numpy as np
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas
from mpl_toolkits.mplot3d.axes3d import Axes3D

import wx
from wx.lib.pubsub import Publisher as pub

class BasePlot(object):
    """a base plot class for GPEC"""

    def __init__(self, parent, arrays=None, title=None, xlabel="", ylabel="", system=(), projection="2d", zlabel="", **karg):

        self.title = title

        self.system = system
        self.arrays = arrays

        self.parent = parent
        
        self.fig = Figure()     #dpi=self.dpi
        

        self.canvas = FigCanvas(parent, -1, self.fig)
        

        self.projection = projection
       
        if system:
            case_label = "%s + %s, %s EOS, Kij = %s, Lij = %s" % tuple(system)
            self.fig.text(0.01, 0.01, case_label, fontsize=9,  horizontalalignment='left')
         

        self.properties_check = {'Grid':wx.NewId(), 'Legends':wx.NewId(), 'Log X': wx.NewId(), 'Log Y': wx.NewId(), }
   
        self.properties_normal = {'Set plot title...': wx.NewId()}

        if projection == '3d':
            self.properties_normal['Set perspective...'] = wx.NewId()


        self.curves = []    #curves to plot


    

    def setup_curves (self):
        """each one subtype declare curves as a group of lines2d

            - redefined by each sub class"""

        pass


    def plot(self):
        """plot all visible curves"""
        for curve in self.curves:
            if curve['visible'] and curve.has_key('lines'):
                marker = '' if 'marker' not in curve.keys() else curve['marker']
                curve['lines2d'] = self.axes.plot(*curve['lines'], color=curve['color'], marker=marker, label=curve['name'])
        

        
        self.canvas.draw()


    def OnToggleCurve(self, event):
        wx_id = event.GetId()
        curve = [curve for curve in self.curves  if curve['wx_id'] == wx_id][0]     #TODO better way?        

        curve['visible'] = not curve['visible']
        for line in curve['lines2d']:
            try:
                line.set_visible(curve['visible']) 
            except AttributeError:
                for line_ in line:
                    line_.set_visible(curve['visible']) 
                
        self.canvas.draw()

    def OnSetupProperty(self, event):
        wx_id = event.GetId()
        prop = dict([[v,k] for k,v in self.properties_normal.items()])[wx_id] #inverted dict

        if prop == 'Set perspective...':
            
            dlg = wx.TextEntryDialog(self.parent, u'Azimuthal angle', u'Set Perpective', 
                                            defaultValue=str(self.axes.azim) )            
            r = dlg.ShowModal()
            if  r == wx.ID_CANCEL:
                return 
            elif r  == wx.ID_OK:
                azim = float(dlg.GetValue())
            
            dlg = wx.TextEntryDialog(self.parent, u'Elevation angle', u'Set Perpective', 
                                            defaultValue=str(self.axes.elev) )            
            r = dlg.ShowModal()
            if r  == wx.ID_CANCEL:
                return 
            elif r  == wx.ID_OK:
                elev = float(dlg.GetValue())

            self.axes.view_init(elev, azim)

        elif prop == 'Set plot title...':
            dlg = wx.TextEntryDialog(self.parent, u'Plot title', u'Set plot title', 
                                            defaultValue=self.axes.get_title() )            
            r = dlg.ShowModal()
            if  r == wx.ID_CANCEL:
                return 
            
            self.title = dlg.GetValue()
            self.axes.set_title(self.title)

        self.canvas.draw()    
                


    def OnToggleProperty(self, event):
        wx_id = event.GetId()
        prop = dict([[v,k] for k,v in self.properties_check.items()])[wx_id] #inverted dict

        if prop == 'Grid':
            self.axes.grid()

        elif prop == 'Legends':
            if self.axes.get_legend():
                self.axes.legend_ = None        #a tricky way to remove lengeds 
            else:
                #TODO check and show visible lines only

                self.axes.legend(loc='best')  

                


        elif prop == 'Log X':
            if self.axes.get_xscale() == 'linear':
                self.axes.set_xscale('log')
            else:
                self.axes.set_xscale('linear')

        elif prop == 'Log Y':
            if self.axes.get_yscale() == 'linear':
                self.axes.set_yscale('log')
            else:
                self.axes.set_yscale('linear')

            

        self.canvas.draw()

class Plot2D(BasePlot):
    def __init__ (self, parent, arrays=None, title=None, xlabel="", ylabel="", system=(), projection="2d", zlabel="", **kwargs):

        BasePlot.__init__(self, parent, None, title, xlabel, ylabel, system, projection=projection, zlabel=zlabel, **kwargs)

        self.axes = self.fig.add_subplot(111)
        self.axes.set_title(title)

        self.axes.set_ylabel(ylabel)
        self.axes.set_xlabel(xlabel)

        self.axes.set_autoscale_on(True)

        if arrays:
            self.setup_curves()


class Plot3D(BasePlot):
    def __init__ (self, parent, arrays=None, title=None, xlabel="", ylabel="", system=(), 
                    projection="3d", zlabel="", **kwargs):

        BasePlot.__init__(self, parent, None, title, xlabel, ylabel, system, projection=projection, zlabel=zlabel, **kwargs)

        self.axes = Axes3D(self.fig)
        self.axes.set_ylabel(ylabel)
        self.axes.set_xlabel(xlabel)

        self.axes.set_zlabel(zlabel)
        self.fig.suptitle(title) 

        if arrays:
            self.setup_curves()



class CustomPlot(Plot2D):
    def __init__ (self, parent, title, xlabel, ylabel, projection="2d", zlabel="", system=(), **kwargs):
        Plot2D.__init__(self, parent, None, title, xlabel, ylabel, system, projection=projection, zlabel=zlabel, **kwargs)

    def add_lines(self, *lists_of_lines):
        for lol in lists_of_lines:
            for line in lol:
                name =  line.get_label()
               

                color = line.get_color()
                linestyle = line.get_linestyle()
                marker = line.get_marker()
                label = line.get_label()        

                if self.projection == '3d':
                    x, y, z = line._verts3d  #why the hell there is no get_zdata()
                    self.axes.plot(x,y, z,color=color,linestyle=linestyle, marker=marker, label=label) 
                else:
                    x, y = line.get_data()
                    self.axes.plot(x,y, color=color,linestyle=linestyle, marker=marker, label=label)

                if name != '_nolegend_':
                    self.curves.append( { 'name': name,
                                          'visible':True, 
                                          'lines2d': lol,
                                          'color': line.get_color(), 
                                          'wx_id' : wx.NewId(),
                                           'type': 'CUSTOM',
                                        } )



class PTrho(Plot3D):
    def __init__(self, parent, arrays=None, system=(), **kwargs):

        self.short_title = u"P-T-\u03c1"
        self.title = u'Pressure-Temperature-Density projection of a global phase equilibrium diagram'
        self.xlabel = u'Temperature [K]'
        self.ylabel = u'Density [mol/l]'
        self.zlabel = u'Pressure [bar]'

        Plot3D.__init__(self, parent, arrays, self.title, self.xlabel, self.ylabel, system, projection='3d', zlabel=self.zlabel, **kwargs)        

    def setup_curves(self, arrays, **kwarg):

        
        if 'VAP' in arrays.keys():
            try:
        
                lines = []
                name = u'Pure compound vapor pressure lines'
                for num, vap_curve in enumerate(arrays['VAP']):
                    label = name if num == 0 else '_nolegend_'
                    lines += self.axes.plot(vap_curve[:,0], vap_curve[:,2], vap_curve[:,1], 'g', label=label),
                    lines += self.axes.plot(vap_curve[:,0], vap_curve[:,3], vap_curve[:,1], 'g', label='_nolegend_'),

                self.curves.append( {'name': name,
                                         'visible':True, 
                                         #'lines':( vap_curve[:,0], vap_curve[:,2], vap_curve[:,1]),
                                          'lines2d': lines,
                                          'color' : 'green',
                                          'wx_id' : wx.NewId(),
                                          'type': 'VAP',
                                            } )
            except:
                pub.sendMessage('log', ('error', u'There was an error trying to plot VAP curves on P-T-\u03c1. The diagram could not be accurate.'))



        if 'CRI' in arrays.keys():
            lines = []
            name = u'Critical lines' 
            for num, cri_curve in enumerate(arrays['CRI']):
                label = name if num == 0 else '_nolegend_'
                lines += self.axes.plot(cri_curve[:,0],cri_curve[:,2], cri_curve[:,1], 'k', label=label)


            #axes plot format http://matplotlib.sourceforge.net/api/axes_api.html?highlight=axes.plot#matplotlib.axes.Axes.plot


                #counter = u'' if len(arrays['CRI']) == 1 else u' %i' % (num + 1)
            
            self.curves.append( {'name': name, 
                                     'visible':True, 
                                     #'lines':(cri_curve[:,0],cri_curve[:,2], cri_curve[:,1]),
                                     'lines2d': lines, 
                                     'color' : 'black',
                                     'wx_id' : wx.NewId(),
                                     'type': 'CRI'
                                    } )


        if 'LLV' in arrays.keys():
            lines = []
            name = 'LLV'

            for num, llv_curve in enumerate(arrays['LLV']):
                label_b = 'Liquid in LLV' if num == 0 else '_nolegend_'
                label_r = 'Vapor in LLV' if num == 0 else '_nolegend_'
                lines += self.axes.plot(llv_curve[:,0], llv_curve[:,7], llv_curve[:,1], 'b', label=label_b)
                lines += self.axes.plot(llv_curve[:,0], llv_curve[:,8], llv_curve[:,1], 'b', label='_nolegend_')
                lines += self.axes.plot(llv_curve[:,0], llv_curve[:,9], llv_curve[:,1], 'r', label=label_r)
                



            self.curves.append( { 'name': name, 
                                      'visible':True,
                                      #'lines': (llv_curve[:,0], llv_curve[:,1], llv_curve[:,7]),           #TODO
                                      'lines2d': lines, #self.axes.plot(*lines, label = name),
                                      'color': 'red', 
                                      'wx_id' : wx.NewId(),
                                       'type': 'LLV',
                                    } )

        if 'AZE' in arrays.keys():
            lines = []
            name = u'Azeotropic lines'

            for num, aze_curve in enumerate(arrays['AZE']):
                label = name if num == 0 else '_nolegend_'
                lines += self.axes.plot(aze_curve[:,0], aze_curve[:,4], aze_curve[:,1], 'm', label = label) 
                lines += self.axes.plot(aze_curve[:,0], aze_curve[:,5], aze_curve[:,1], 'm', label= '_nolegend_' ) 


            
            self.curves.append( { 'name': name, 
                                      'visible':True,
                                      #'lines': tuple(lines),
                                      'lines2d': lines,
                                      'color': 'magenta', 
                                      'wx_id' : wx.NewId(),
                                       'type': 'LLV',
                                    } )

      

        if 'ISO' in arrays.keys():

            name = u'Isopleth lines (Z = %s)' % kwarg['z_val']
            lines = []
            for num, iso_curve in enumerate(arrays['ISO']):
                if num == 0:
                    label = name if num == 0 else '_nolegend_'
                    lines += self.axes.plot(iso_curve[:,0], iso_curve[:,4], iso_curve[:,1], 'g--', label=label),
                    lines += self.axes.plot(iso_curve[:,0], iso_curve[:,5], iso_curve[:,1], 'g--', label='_nolegend_'),                                

             
            self.curves.append( { 'name': name, 
                                  'visible':True,
                                  #'lines': tuple(lines),
                                  'lines2d': lines,  #self.axes.plot(*lines, label=name),
                                  'color': 'violet', 
                                  'wx_id' : wx.NewId(),
                                  'type': 'ISO',
                                } )

     


        if 'Txy' in arrays.keys():

            name = u'Isobaric lines (P = %s)' % kwarg['p_val']
            lines = []
            for num, iso_curve in enumerate(arrays['Txy']):
                label = name if num == 0 else '_nolegend_'

                lines += self.axes.plot(iso_curve[:,0], iso_curve[:,5], float(kwarg['p_val']), 'k--', label=label),
                lines += self.axes.plot(iso_curve[:,0], iso_curve[:,6], float(kwarg['p_val']), 'k--', label='_nolegend_'),                                

             
            self.curves.append( { 'name': name, 
                                  'visible':True,
                                  #'lines': tuple(lines),
                                  'lines2d': lines,  #self.axes.plot(*lines, label=name),
                                  'color': 'green', 
                                  'wx_id' : wx.NewId(),
                                  'type': 'ISO',
                                } )




        if 'Pxy' in arrays.keys():

            name = u'Isothermal lines (T = %s)' % kwarg['t_val']
            lines = []
            for num, iso_curve in enumerate(arrays['Pxy']):
                label = name if num == 0 else '_nolegend_'

                t_constant = np.repeat(float(kwarg['t_val']), len(iso_curve[:,0]))

                lines += self.axes.plot(t_constant, iso_curve[:,5], iso_curve[:,0], 'k-.', label=label),
                lines += self.axes.plot(t_constant, iso_curve[:,6], iso_curve[:,0], 'k-.', label='_nolegend_')

             
            self.curves.append( { 'name': name, 
                                  'visible':True,
                                  #'lines': tuple(lines),
                                  'lines2d': lines,  #self.axes.plot(*lines, label=name),
                                  'color': 'green', 
                                  'wx_id' : wx.NewId(),
                                  'type': 'ISO',
                                } )



class PTx(Plot3D):
    """PTx 3D projection"""

    def __init__(self, parent, arrays=None, system=(), **kwargs):

        self.short_title = u"P-T-x"
        self.title = u'Pressure-Temperature-Composition projection of a global phase equilibrium diagram '
        self.xlabel = u'Temperature [K]'
        self.ylabel = u'Composition' if not system else "%s molar fraction" % system[0] if not system else "%s molar fraction" % system[0]
        self.zlabel = u'Pressure [bar]'

        Plot3D.__init__(self, parent, arrays, self.title, self.xlabel, self.ylabel, system, projection='3d', zlabel=self.zlabel, **kwargs)        

    def setup_curves(self, arrays, **kwarg):



        if 'VAP' in arrays.keys():
            lines = []
            name = u'Pure compound vapor pressure lines'
            for num, vap_curve in enumerate(arrays['VAP']):
                label = name if num == 0 else '_nolegend_'
                lines += self.axes.plot(vap_curve[:,0], np.repeat(1-num, len(vap_curve[:,0])) , vap_curve[:,1], 'g', label=label),


            self.curves.append( {'name': name,
                                     'visible':True, 
                                     #'lines':( vap_curve[:,0], vap_curve[:,2], vap_curve[:,1]),
                                      'lines2d': lines,
                                      'color' : 'green',
                                      'wx_id' : wx.NewId(),
                                      'type': 'VAP',
                                        } )    


        if 'CRI' in arrays.keys():
            lines = []

            name = u'Critical lines'

            for num, cri_curve in enumerate(arrays['CRI']):
                label = name if num == 0 else '_nolegend_'
                lines +=  self.axes.plot(cri_curve[:,0],cri_curve[:,3], cri_curve[:,1], 'k', label=label)   #[ () ]

            self.curves.append( {'name': name, # + counter , 
                                     'visible':True, 
                                     'lines2d':  lines, 
                                     'color' : 'black',
                                     'wx_id' : wx.NewId(),
                                     'type': 'CRI'
                                    } )


        if 'LLV' in arrays.keys():

            lines = []
            name = 'LLV'
            for num, llv_curve in enumerate(arrays['LLV']):
                label_b = 'Liquid in LLV' if num == 0 else '_nolegend_'
                label_r = 'Vapor in LLV' if num == 0 else '_nolegend_'
                lines += self.axes.plot(llv_curve[:,0], llv_curve[:,2], llv_curve[:,1], 'b', label=label_b)
                lines += self.axes.plot(llv_curve[:,0], llv_curve[:,3], llv_curve[:,1], 'b', label='_nolegend_')
                lines += self.axes.plot(llv_curve[:,0], llv_curve[:,4], llv_curve[:,1], 'r', label=label_r)

            
            
            self.curves.append( { 'name': name, 
                                      'visible':True,
                                      'lines2d': lines, #self.axes.plot(*lines, label=name),
                                      'color': 'red', 
                                      'wx_id' : wx.NewId(),
                                      'type': 'LLV',
                                    } )

        if 'AZE' in arrays.keys():

            name = u'Azeotropic lines'
            lines = []

            for num, aze_curve in enumerate(arrays['AZE']):
                label = name if num == 0 else '_nolegend_'
                lines += self.axes.plot( aze_curve[:,0], aze_curve[:,2], aze_curve[:,1], 'm', label=label)

            
            self.curves.append( { 'name': name, 
                                      'visible':True,
                                      #'lines': tuple(lines),
                                      'lines2d': lines,  #self.axes.plot(*lines, label=name),
                                      'color': 'magenta', 
                                      'wx_id' : wx.NewId(),
                                       'type': 'AZE',
                                    } )


        if 'ISO' in arrays.keys():


            name = u'Isopleth saturated line  (Z = %s)' % kwarg['z_val']
            lines = []
            for num, iso_curve in enumerate(arrays['ISO']):
                label = name if num == 0 else '_nolegend_'
                
                max_val = max_val if 'max_val' in locals() else np.max(iso_curve[:,2])
                saturated = np.repeat(max_val, len(iso_curve[:,1]))
                lines += self.axes.plot(iso_curve[:,0], saturated, iso_curve[:,1], 'g--', label=label),
                                
            self.curves.append( { 'name': name, 
                                  'visible':True,
                                  #'lines': tuple(lines),
                                  'lines2d': lines,  #self.axes.plot(*lines, label=name),
                                  'color': 'violet', 
                                  'wx_id' : wx.NewId(),
                                  'type': 'ISO',
                                } )

        if 'Txy' in arrays.keys():


            name = u'Isobaric lines (P = %s)' % kwarg['p_val']
            lines = []
            for num, iso_curve in enumerate(arrays['Txy']):
                label = name if num == 0 else '_nolegend_'

                lines += self.axes.plot(iso_curve[:,0], iso_curve[:,1], float(kwarg['p_val']), 'k--', label=label),
                lines += self.axes.plot(iso_curve[:,0], iso_curve[:,2], float(kwarg['p_val']), 'k--', label='_nolegend_'),                                

             
            self.curves.append( { 'name': name, 
                                  'visible':True,
                                  #'lines': tuple(lines),
                                  'lines2d': lines,  #self.axes.plot(*lines, label=name),
                                  'color': 'green', 
                                  'wx_id' : wx.NewId(),
                                  'type': 'ISO',
                                } )




        if 'Pxy' in arrays.keys():

            name = u'Isothermal lines (T = %s)' % kwarg['t_val']
            lines = []
            for num, iso_curve in enumerate(arrays['Pxy']):
                label = name if num == 0 else '_nolegend_'

                t_constant = np.repeat(float(kwarg['t_val']), len(iso_curve[:,0]))

                lines += self.axes.plot(t_constant, iso_curve[:,1], iso_curve[:,0], 'k-.', label=label),
                lines += self.axes.plot(t_constant, iso_curve[:,2], iso_curve[:,0], 'k-.', label='_nolegend_')

             
            self.curves.append( { 'name': name, 
                                  'visible':True,
                                  #'lines': tuple(lines),
                                  'lines2d': lines,  #self.axes.plot(*lines, label=name),
                                  'color': 'green', 
                                  'wx_id' : wx.NewId(),
                                  'type': 'ISO',
                                } )




class IsoPT(Plot2D):
    """Isopleth PT diagram"""
    
    def __init__(self, parent, arrays=None, system=(), **kwarg):

        self.short_title = u"Isopleth P-T"
        self.title = u'Isopleth Graph for a Composition (Z = %s)' % kwarg['z']
        self.xlabel = u'Temperature [K]'
        self.ylabel = u'Pressure [bar]'

        Plot2D.__init__(self, parent, arrays, self.title, self.xlabel, self.ylabel, system, **kwarg)        

    def setup_curves(self, arrays):

        if 'ISO' in arrays.keys():
            lines = []
            name = u'Isopleth lines'
            for num, vap_curve in enumerate(arrays['ISO']):
                label = name if num == 0 else '_nolegend_'
                lines += self.axes.plot(vap_curve[:,0], vap_curve[:,1], 'g', label=label)
                
                

            self.curves.append( {'name': name, 
                                 'visible':True, 
                                 'lines2d': lines,
                                  'color' : 'violet',
                                  'wx_id' : wx.NewId(),
                                  'type': 'ISO',
                                    } )             

        if 'LLV' in arrays.keys():
            for num, llv_curve in enumerate(arrays['LLV']):
        
                if llv_curve.shape == (2,):  
                    #POINT 

                    self.curves.append( { 'name': 'LLV Critical Point', 
                                          'visible':True,
                                          'lines': (llv_curve[0], llv_curve[1]),           #TODO
                                          'color': 'blue', 
                                          'marker': '^',
                                          'wx_id' : wx.NewId(),
                                           'type': 'LLV',
                                           
                                        } )

                else:
                    color = 'blue' if num % 2 == 0 else 'red'
                    name  =  'Liquid in LLV' if num % 2 == 0 else 'Vapor in LLV'

                    self.curves.append( { 'name': name, 
                                          'visible':True,
                                          'lines': (llv_curve[:,0], llv_curve[:,1]),           #TODO
                                          'color': color, 
                                          'wx_id' : wx.NewId(),
                                           'type': 'LLV',
                                        } )
                    


class IsoTx(Plot2D):
    """Isopleth Tx diagram"""
    
    def __init__(self, parent, arrays=None, system=(), **kwarg):

        self.short_title = u"Isopleth T-x"
        self.title = u'T-x projection of the Isopleth Graph for a Composition (Z=%s)' % kwarg['z']
        self.xlabel = u'Composition' if not system else "%s molar fraction" % system[0]
        self.ylabel = u'Temperature [K]'

        Plot2D.__init__(self, parent, arrays, self.title, self.xlabel, self.ylabel, system, **kwarg)        

    def setup_curves(self, arrays):


        if 'ISO' in arrays.keys():
            name = u'Isopleth lines'

            lines_g = []
            lines_r = []
            name_g = u'Incipient Face.'
            name_r = u'Major (Saturated) Face.'
            for num, iso_curve in enumerate(arrays['ISO']):
                label_g = name_g if num == 0 else '_nolegend_'
                label_r = name_r if num == 0 else '_nolegend_'
                lines_g += self.axes.plot(1 - iso_curve[:,3], iso_curve[:,0], 'k', label=label_g)
            
                if num == 0:
                    saturated = np.repeat( np.max(iso_curve[:,2]), len(iso_curve[:,0]))
                    lines_r += self.axes.plot(saturated, iso_curve[:,0], 'g', label=label_r)
            


            self.curves.append( {'name': name_g,
                                     'visible': True, 
                                     'lines2d': lines_g,
                                      'color' : 'green',
                                      'wx_id' : wx.NewId(),
                                      'type': 'ISO',
                                        } )             

            self.curves.append( {'name': name_r,
                                     'visible':True, 
                                     'lines2d': lines_r,
                                      'color' : 'red',
                                      'wx_id' : wx.NewId(),
                                      'type': 'ISO',
                                        } )             


        
class IsoPx(Plot2D):
    """Isopleth Px diagram"""
    
    def __init__(self, parent, arrays=None, system=(), **kwargs):

        self.short_title = u"Isopleth P-x"
        self.title = u'P-x projection of the Isopleth Graph for a Composition (Z=%s)' % kwargs['z']
        self.xlabel = u'Composition' if not system else "%s molar fraction" % system[0]
        self.ylabel = u'Pressure [bar]'

        Plot2D.__init__(self, parent, arrays, self.title, self.xlabel, self.ylabel, system, **kwargs)        

    def setup_curves(self, arrays):

        if 'ISO' in arrays.keys():
            lines_g = []
            lines_r = []
            name_g = u'Incipient Face.'
            name_r = u'Major (Saturated) Face.'

            for num, iso_curve in enumerate(arrays['ISO']):
                label_g = name_g if num == 0 else '_nolegend_'
                label_r = name_r if num == 0 else '_nolegend_'
                color = 'g' #if num == 0 else ''

                counter = u'' if len(arrays['ISO']) == 1 else u' %i' % (num + 1)
                lines_g += self.axes.plot(1 - iso_curve[:,3], iso_curve[:,1], 'k', label=label_g)

                max_val = max_val if 'max_val' in locals() else np.max(iso_curve[:,2])
                saturated = np.repeat(max_val, len(iso_curve[:,1]))

                lines_r += self.axes.plot(saturated, iso_curve[:,1], color, label=label_r)

            pub.sendMessage('register', ('lines_r', lines_r))

            self.curves.append( {'name': name_g,
                                     'visible': True, 
                                     'lines2d': lines_g,
                                      'color' : 'green',
                                      'wx_id' : wx.NewId(),
                                      'type': 'ISO',
                                        } )             

            self.curves.append( {'name': name_r,
                                     'visible':True, 
                                     'lines2d': lines_r,
                                      'color' : 'red',
                                      'wx_id' : wx.NewId(),
                                      'type': 'ISO',
                                        } )     
                


class IsoTrho(Plot2D):
    """Isopleth Trho diagram"""
    
    def __init__(self, parent, arrays=None, **kwarg):

        self.short_title = u"Isopleth T-\u03c1" 
        self.title = u'T-\u03c1 projection of the Isopleth Graph for a Composition (Z=%s)' % kwarg['z']
        self.xlabel = u'Density [mol/l]'
        self.ylabel = u'Temperature [K]'
        

        Plot2D.__init__(self, parent, arrays, self.title, self.xlabel, self.ylabel, **kwarg)        

    def setup_curves(self, arrays):

        if 'ISO' in arrays.keys():
            #lines_g = []
            #lines_r = []

            lines = []
            name_g = u'Incipient Face.'
            name_r = u'Major (Saturated) Face.'

            names = [name_g, name_r]
            styles = ['k', 'g']

            for num, vap_curve in enumerate(arrays['ISO']):
                lines +=  self.axes.plot(vap_curve[:,4], vap_curve[:,0], styles[num], label=names[num])
                lines +=  self.axes.plot(vap_curve[:,5], vap_curve[:,0], styles[num], label='_nolegend_')

                self.curves.append( {'name': names[num], 
                                         'visible':True, 
                                         'lines2d': lines,
                                          'color' : 'green',
                                          'wx_id' : wx.NewId(),
                                          'type': 'ISO',
                                            } )
                lines = []

           
        
                

        
class IsoPrho(Plot2D):
    """Isopleth Prho diagram"""
    
    def __init__(self, parent, arrays=None, system=(), **kwarg):

        self.short_title = u"Isopleth P-\u03c1" 
        self.title = u'P-\u03c1 projection of the Isopleth Graph for a Composition (Z=%s)' % kwarg['z']
        self.xlabel = u'Density [mol/l]'
        self.ylabel = u'Temperature [K]'
        

        Plot2D.__init__(self, parent, arrays, self.title, self.xlabel, self.ylabel, system, **kwarg)        

    def setup_curves(self, arrays):

        if 'ISO' in arrays.keys():
            lines = []
            name_g = u'Incipient Face.'
            name_r = u'Major (Saturated) Face.'

            names = [name_g, name_r]
            styles = ['k', 'g']

            for num, vap_curve in enumerate(arrays['ISO']):
                lines +=  self.axes.plot(vap_curve[:,4], vap_curve[:,1], styles[num], label=names[num])
                lines +=  self.axes.plot(vap_curve[:,5], vap_curve[:,1], styles[num], label='_nolegend_')
                
                self.curves.append( {'name': names[num], 
                                         'visible':True, 
                                         'lines2d': lines,
                                          'color' : 'green',
                                          'wx_id' : wx.NewId(),
                                          'type': 'ISO',
                                            } )
                lines = []     
                

class PT(Plot2D):
    """pressure-temperature diagram"""
    
    def __init__(self, parent, arrays=None, system=(), **kwarg):


        self.short_title = u"P-T"
        self.title = u'Pressure-Temperature projection of a global phase equilibrium diagram'
        self.xlabel = u'Temperature [K]'
        self.ylabel = u'Pressure [bar]'

        Plot2D.__init__(self, parent, arrays, self.title, self.xlabel, self.ylabel, system, **kwarg)        

    def setup_curves(self, arrays):

        if 'VAP' in arrays.keys():
            lines = []
            name = u'Pure compound vapor pressure lines'
            for num, vap_curve in enumerate(arrays['VAP']):
                label = name if num == 0 else '_nolegend_'
                lines += self.axes.plot( vap_curve[:,0], vap_curve[:,1], 'g' , label = label)

            self.curves.append( {'name': name, # + counter , 
                                     'visible':True, 
                                     #'lines':( vap_curve[:,0], vap_curve[:,1]),
                                      'lines2d': lines,
                                      'color' : 'green',
                                      'wx_id' : wx.NewId(),
                                      'type': 'VAP',
                                        } )             

        if 'CRI' in arrays.keys():
            lines = []
            name = u'Critical lines'
            for num, cri_curve in enumerate(arrays['CRI']):
                label = name if num == 0 else '_nolegend_'
                lines += self.axes.plot(cri_curve[:,0],cri_curve[:,1], 'k', label=label)

                
            self.curves.append( {'name': name, 
                                 'visible':True, 
                                 #'lines':(cri_curve[:,0],cri_curve[:,1]),
                                 'lines2d': lines,
                                 'color' : 'black',
                                 'wx_id' : wx.NewId(),
                                 'type': 'CRI'
                                } )


        if 'LLV' in arrays.keys():
            lines = []
            name = 'LLV'
            for num, llv_curve in enumerate(arrays['LLV']):
                label = 'Vapor in LLV' if num == 0 else  'Liquid in LLV'        #TODO check if aren't inverted
                style = 'r' if num == 0 else 'b'
                lines += self.axes.plot(llv_curve[:,0], llv_curve[:,1], style, label=label)

            self.curves.append( { 'name': name, 
                                      'visible':True,
                                      'lines2d': lines, 
                                      'color': 'red',      
                                      'wx_id' : wx.NewId(), 
                                       'type': 'LLV',
                                    } )

        
        if 'AZE' in arrays.keys():
            lines = []
            name = u'Azeotropic lines'

            try:
                for num, aze_curve in enumerate(arrays['AZE']):
                    label = name if num == 0 else '_nolegend_'
                    lines += self.axes.plot( aze_curve[:,0], aze_curve[:,1], 'm', label = label)

                self.curves.append( { 'name': name,
                                      'visible':True,
                                      'lines2d': lines,
                                      'color': 'magenta', 
                                      'wx_id' : wx.NewId(),
                                      'type': 'LLV',
                                    } )
            except:
                pub.sendMessage('log', ('error', 'There was an error trying to plot azeotropic lines. The diagram could not be accurate'))



class Tx(Plot2D):
    """T-x plot"""
    
    def __init__(self, parent, arrays=None, system=(), **kwargs):
        self.short_title = u"T-x"
        self.title = u'Temperature-Composition projection of a global phase equilibrium diagram'
        self.xlabel = u'Composition' if not system else "%s molar fraction" % system[0]    #TODO DEFINE system inside the plot
        self.ylabel = u'Temperature [K]'

        Plot2D.__init__(self, parent, arrays, self.title, self.xlabel, self.ylabel, system, **kwargs)        

    def setup_curves(self, arrays):

        #TODO VAP curves!

               
        
        if 'CRI' in arrays.keys():
            lines = []
            name = u'Critical lines'
            for num, cri_curve in enumerate(arrays['CRI']):
                label = name if num == 0 else '_nolegend_'
                lines += self.axes.plot (cri_curve[:,3], cri_curve[:,0], 'k', label = label)

            

            self.curves.append( {'name': name , # + counter, 
                                 'visible':True, 
                                 'lines2d': lines, 
                                 'color' : 'black',
                                 'wx_id' : wx.NewId(),
                                 'type': 'CRI'
                                } )


        if 'LLV' in arrays.keys():
            lines = []
            for num, llv_curve in enumerate(arrays['LLV']):
                label_b = 'Liquid in LLV' if num == 0 else '_nolegend_'
                label_r = 'Vapor in LLV' if num == 0 else '_nolegend_'
                lines += self.axes.plot (llv_curve[:,2], llv_curve[:,0], 'b', label = label_b)
                lines += self.axes.plot (llv_curve[:,3], llv_curve[:,0], 'b', label = '_nolegend_')
                lines += self.axes.plot (llv_curve[:,4], llv_curve[:,0], 'r', label = label_r)
            


            self.curves.append( { 'name': 'LLV', 
                                      'visible':True,
                                      'lines2d': lines,
                                      'color': 'blue', 
                                      'wx_id' : wx.NewId(),
                                       'type': 'LLV',
                                    } )


        if 'AZE' in arrays.keys():

            name = u'Azeotropic line'
            lines = []
            for num, aze_curve in enumerate(arrays['AZE']):
                label = name if num == 0 else '_nolegend_'
                lines += self.axes.plot( aze_curve[:,2], aze_curve[:,0], 'm', label=label)
            

            self.curves.append( { 'name': name, 
                                  'visible':True,
                                  'lines2d': lines, 
                                  'color': 'magenta', 
                                  'wx_id' : wx.NewId(),
                                   'type': 'LLV',
                                    } )



class Pxy(Plot2D):
    """Pxy Px (isothermal)"""
    
    def __init__(self, parent, arrays=None, system=(), **kwarg):
        self.short_title = u"Pxy (isothermal)"
        self.title = u'Isothermal fluid phase equilibrium for T=%s [k]' % kwarg['t']

        self.ylabel = u'Pressure [bar]'
        self.xlabel = u'Composition' if not system else "%s molar fraction" % system[0]     #TODO DEFINE system inside the plot
        

        Plot2D.__init__(self, parent, arrays, self.title, self.xlabel, self.ylabel, system, **kwarg)        

    def setup_curves(self, arrays):

               
        
        if 'Pxy' in arrays.keys():
            for num, isot_curve in enumerate(arrays['Pxy']):

                counter = u'' if len(arrays['Pxy']) == 1 else u' %i' % (num + 1)

                self.curves.append( {'name': u'Isothermal lines ' + counter, 
                                     'visible':True, 
                                     'lines':(isot_curve[:,1],isot_curve[:,0], isot_curve[:,2],isot_curve[:,0]),
                                     'color' : 'black',
                                     'wx_id' : wx.NewId(),
                                     'type': 'Pxy'
                                    } )



class PxyPrho(Plot2D):
    """Pxy P-Rho projection (isothermal)"""
    
    def __init__(self, parent, arrays=None, system=(), **kwargs):
        self.short_title = u"P-\u03c1 (isothermal)"
        self.title = u'Pressure-Density of the Isothermal fluid phase equilibrium for T=%s [k]' % kwargs['t']

        self.ylabel = u'Pressure [bar]'
        self.xlabel = u'Density [mol/l]'    #TODO DEFINE system inside the plot
        
        Plot2D.__init__(self, parent, arrays, self.title, self.xlabel, self.ylabel, system, **kwargs)        

    def setup_curves(self, arrays):

               
        
        if 'Pxy' in arrays.keys():
            for num, isot_curve in enumerate(arrays['Pxy']):

                counter = u'' if len(arrays['Pxy']) == 1 else u' %i' % (num + 1)

                self.curves.append( {'name': u'Isothermal lines ' + counter, 
                                     'visible':True, 
                                     'lines':(isot_curve[:,5],isot_curve[:,0], isot_curve[:,6], isot_curve[:,0]),
                                     'color' : 'black',
                                     'wx_id' : wx.NewId(),
                                     'type': 'Pxy'
                                    } )



class Txy(Plot2D):
    """Txy Tx (isobaric)"""
    
    def __init__(self, parent, arrays=None, system=(), **kwargs):
        self.short_title = u"Txy (isobaric)"
        self.title = u'Isobaric fluid phase equilibrium for P=%s [bar]' % kwargs['p']

        self.ylabel = u'Temperature [k]'
        self.xlabel = u'Composition' if not system else "%s molar fraction" % system[0]    #TODO DEFINE system inside the plot
        

        Plot2D.__init__(self, parent, arrays, self.title, self.xlabel, self.ylabel, system, **kwargs)        

    def setup_curves(self, arrays):

               
        
        if 'Txy' in arrays.keys():
            for num, isob_curve in enumerate(arrays['Txy']):

                counter = u'' if len(arrays['Txy']) == 1 else u' %i' % (num + 1)

                self.curves.append( {'name': u'Isobaric lines' + counter, 
                                     'visible':True, 
                                     'lines':(isob_curve[:,1],isob_curve[:,0], isob_curve[:,2],isob_curve[:,0]),
                                     'color' : 'black',
                                     'wx_id' : wx.NewId(),
                                     'type': 'Txy'
                                    } )

class TxyTrho(Plot2D):
    """Txy T-Rho projection (isobaric)"""
    
    def __init__(self, parent, arrays=None, system=(), **kwargs):
        self.short_title = u"T-\u03c1 (isobaric)"
        self.title = u'Temperature-Density of the Isobaric fluid phase equilibrium for P=%s [bar]' % kwargs['p']

        self.ylabel = u'Temperature [bar]'
        self.xlabel = u'Density [mol/l]'    #TODO DEFINE system inside the plot
        
        Plot2D.__init__(self, parent, arrays, self.title, self.xlabel, self.ylabel, system, **kwargs)        

    
    def setup_curves(self, arrays):

               
        
        if 'Txy' in arrays.keys():
            for num, isob_curve in enumerate(arrays['Txy']):

                counter = u'' if len(arrays['Txy']) == 1 else u' %i' % (num + 1)

                self.curves.append( {'name': u'Isobaric lines' + counter, 
                                     'visible':True, 
                                     'lines':(isob_curve[:,5],isob_curve[:,0], isob_curve[:,6],isob_curve[:,0]),
                                     'color' : 'black',
                                     'wx_id' : wx.NewId(),
                                     'type': 'Pxy'
                                    } )

                
class Px(Plot2D):
    """P-x diagram"""
    
    def __init__(self, parent, arrays=None, system=(), **kwargs):
        self.short_title = u"P-x"
        self.title = u'Pressure-Composition projection of a global phase equilibrium diagram'

        self.ylabel = u'Pressure [bar]'
        self.xlabel = u'Composition' if not system else "%s molar fraction" % system[0]    #TODO DEFINE system inside the plot
        

        Plot2D.__init__(self, parent, arrays, self.title, self.xlabel, self.ylabel, system, **kwargs)        

    def setup_curves(self, arrays):

        #TODO VAP ?
        
        if 'CRI' in arrays.keys():
            lines = []
            name = u'Critical lines'
            for num, cri_curve in enumerate(arrays['CRI']):
                label = name if num == 0 else '_nolegend_'
                lines += self.axes.plot( cri_curve[:,3],cri_curve[:,1], 'k', label = label)
        

                #counter = u'' if len(arrays['CRI']) == 1 else u' %i' % (num + 1)

            self.curves.append( {'name': name, # + counter, 
                                     'visible':True, 
                                     #'lines': tuple(lines),
                                     'lines2d': lines, 
                                     'color' : 'black',
                                     'wx_id' : wx.NewId(),
                                     'type': 'CRI'
                                    } )

        if 'LLV' in arrays.keys():
            lines = []

            for num, llv_curve in enumerate(arrays['LLV']):
                label_b = 'Liquid in LLV' if num == 0 else '_nolegend_'
                label_r = 'Vapor in LLV' if num == 0 else '_nolegend_'
                lines += self.axes.plot(llv_curve[:,2], llv_curve[:,1], 'b', label = label_b)
                lines += self.axes.plot(llv_curve[:,3], llv_curve[:,1], 'b', label = '_nolegend_')
                lines += self.axes.plot (llv_curve[:,4], llv_curve[:,1], 'r', label = label_r)



            self.curves.append( { 'name': 'LLV',
                                      'visible':True,
                                      'lines2d': lines,
                                      'color': 'red', 
                                      'wx_id' : wx.NewId(),
                                       'type': 'LLV',
                                    } )

        if 'AZE' in arrays.keys():
            lines = []
            name = u'Azeotropic line'

            for num, aze_curve in enumerate(arrays['AZE']):
                label = name if num == 0 else '_nolegend_'
                lines += self.axes.plot(aze_curve[:,2], aze_curve[:,1], 'm', label = label)

            self.curves.append( { 'name': name, 
                                      'visible':True,
                                      'lines2d': lines, 
                                      'color': 'magenta', 
                                      'wx_id' : wx.NewId(),
                                       'type': 'LLV',
                                    } )




class Trho(Plot2D):
    """temperature-density diagram"""
    
    def __init__(self, parent, arrays=None, system=(), **kwargs):

        self.short_title = u'T-\u03c1'
        self.title = u'Temperature-Density projection of a global phase equilibrium diagram'
        self.xlabel = u'Density [mol/l]'
        self.ylabel = u'Temperature [K]'

        Plot2D.__init__(self, parent, arrays, self.title, self.xlabel, self.ylabel, system, **kwargs)        

    def setup_curves(self, arrays):

        if 'VAP' in arrays.keys():
            lines = []
            name = u'Pure compound vapor pressure lines'
            for num, vap_curve in enumerate(arrays['VAP']):
                label = name if num == 0 else '_nolegend_'
                lines += self.axes.plot( vap_curve[:,2], vap_curve[:,0], 'g', label = label)
                lines += self.axes.plot( vap_curve[:,3], vap_curve[:,0], 'g', label = '_nolegend_')



            self.curves.append( {'name': name, 
                                     'visible':True, 
                                      #'lines':(vap_curve[:,2], vap_curve[:,0], vap_curve[:,3], vap_curve[:,0]),
                                      'lines2d': lines,
                                      'color' : 'green',
                                      'wx_id' : wx.NewId(),
                                      'type': 'VAP',
                                        } )      
                
       

        if 'CRI' in arrays.keys():
            lines = []
            name = u'Critical lines' 
            for num, cri_curve in enumerate(arrays['CRI']):
                label = name if num == 0 else '_nolegend_'
                lines += self.axes.plot(cri_curve[:,2],cri_curve[:,0], 'k', label=label)
            

                #counter = u'' if len(arrays['CRI']) == 1 else u' %i' % (num + 1)
            self.curves.append( {'name': name, # + counter , 
                                     'visible':True, 
                                     #'lines':(cri_curve[:,2],cri_curve[:,0]),
                                     'lines2d': lines,
                                     'color' : 'black',
                                     'wx_id' : wx.NewId(),
                                     'type': 'CRI'
                                    } )


        if 'LLV' in arrays.keys():
            lines = []
            name = 'LLV'
            for num, llv_curve in enumerate(arrays['LLV']):
                label = name if num == 0 else '_nolegend_'
                lines += self.axes.plot(llv_curve[:,7], llv_curve[:,0], 'b', label=label)
                lines += self.axes.plot(llv_curve[:,8], llv_curve[:,0], 'b', label='_nolegend_')
                lines += self.axes.plot (llv_curve[:,9], llv_curve[:,0], 'r', label = label)

            #TODO and the red curve?


            self.curves.append( { 'name': name, 
                                  'visible':True,
                                  'lines2d': lines,           #TODO
                                  'color': 'blue', 
                                  'wx_id' : wx.NewId(),
                                   'type': 'LLV',
                                } )


        if 'AZE' in arrays.keys():
            name = u'Azeotropic lines'
            lines = []
            for num, aze_curve in enumerate(arrays['AZE']):
                label = name if num == 0 else '_nolegend_'
                lines += self.axes.plot( aze_curve[:,4], aze_curve[:,0], 'm', label = label)
                lines += self.axes.plot( aze_curve[:,5], aze_curve[:,0], 'm', label = '_nolegend_')
    
                
            self.curves.append( { 'name': name, 
                                  'visible':True,
                                  'lines2d': lines,           #TODO
                                  'color': 'magenta', 
                                  'wx_id' : wx.NewId(),
                                   'type': 'LLV',
                                } )


class Prho(Plot2D):
    """pressure-density diagram"""
    
    def __init__(self, parent, arrays=None, system=(), **kwargs):

        self.short_title = u'P-\u03c1'
        self.title = u'Pressure-Density projection of a global phase equilibrium diagram'
        self.xlabel = u'Density [mol/l]'
        self.ylabel = u'Pressure [bar]'

        Plot2D.__init__(self, parent, arrays, self.title, self.xlabel, self.ylabel, system, **kwargs)        

    def setup_curves(self, arrays):

        if 'VAP' in arrays.keys():
            lines = []
            name = u'Pure compound vapor pressure lines'
            for num, vap_curve in enumerate(arrays['VAP']):
                label = name if num == 0 else '_nolegend_'
                lines += self.axes.plot(vap_curve[:,2], vap_curve[:,1], 'g', label=label)
                lines += self.axes.plot(vap_curve[:,3], vap_curve[:,1], 'g', label='_nolegend_')
        
                
                #counter = u'' if len(arrays['VAP']) == 1 else u' %i' % (num + 1)

            self.curves.append( {'name': name, 
                                 'visible':True, 
                                  'lines2d': lines,
                                  'color' : 'green',
                                  'wx_id' : wx.NewId(),
                                  'type': 'VAP',
                                } )      
        
       

        if 'CRI' in arrays.keys():
            lines = []
            name = u'Critical lines'

            for num, cri_curve in enumerate(arrays['CRI']):
                label = name if num == 0 else '_nolegend_'
                lines += self.axes.plot(cri_curve[:,2],cri_curve[:,1], 'k', label=label)

                
            self.curves.append( {'name': name, 
                                     'visible':True, 
                                     'lines2d': lines,
                                     'color' : 'black',
                                     'wx_id' : wx.NewId(),
                                     'type': 'CRI'
                                    } )


        if 'LLV' in arrays.keys():
            lines = []
            name = 'LLV'
            for num, llv_curve in enumerate(arrays['LLV']):
                label = name if num == 0 else '_nolegend_'
                lines += self.axes.plot(llv_curve[:,7], llv_curve[:,1], 'b', label=label)
                lines += self.axes.plot(llv_curve[:,8], llv_curve[:,1], 'b', label='_nolegend_')
                lines += self.axes.plot (llv_curve[:,9], llv_curve[:,1], 'r', label = label)

            
            self.curves.append( { 'name': name, 
                                  'visible':True,
                                  'lines2d': lines,           #TODO
                                  'color': 'red', 
                                  'wx_id' : wx.NewId(),
                                   'type': 'LLV',
                                } )

        if 'AZE' in arrays.keys():
            lines = []
            name = u'Azeotropic lines'
            for num, aze_curve in enumerate(arrays['AZE']):
                label = name if num == 0 else '_nolegend_'
                lines += self.axes.plot(aze_curve[:,4], aze_curve[:,1], 'm', label=label)
                lines += self.axes.plot(aze_curve[:,5], aze_curve[:,1], 'm', label='_nolegend_')
    

            self.curves.append( { 'name': name, 
                                  'visible':True,
                                  'lines2d': lines,
                                  'color': 'magenta', 
                                  'wx_id' : wx.NewId(),
                                   'type': 'LLV',
                                } )
