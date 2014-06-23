# -*- coding: utf-8 -*-
"""
Created on Mon Jun 23 10:27:50 2014

@author: hannes.maierflaig
"""

from guiqwt.plot import CurveDialog
from guiqwt.builder import make

def plot( *items ):
    win = CurveDialog(edit=False, toolbar=True)
    plot = win.get_plot()
    for item in items:
        plot.add_item(item)
    win.show()
    win.exec_()


def previewTransportData():
    """
    Preview transport measurement data
    """
    # -- Create QApplication
    import guidata
    _app = guidata.qapplication()
    # --
    
    from transportDataToolbox  import antiSymmetrizeSignalUpDown
    # onchange text_box_tmds_file: load Tdms File
    
    # onload tmds_file: Read Groups and populate group select box
    
    # onchange group_select_box: read channels of group and populate second select box
    
    # onchange channel_select_box;
    #  read data and plot
    
    # onchange symmetrize(difference, sum, raw); onchange normalize(to 
    # max/min/mean/custom value); onchange average up_down_sweep:
    #   process raw data according to selected options and replace existing plot curve
    #   display signal statistics
    # Bonus points: keep raw data associated with a curve in memory so an arbitrary
    # number of curves can be plotted and individually processed
    
    # Long term: Fit sin/cos
    
    curve = make.curve(x, y, "ab", "b")
    range = make.range(-2, 2)
    disp0 = make.range_info_label(range, 'BR', u"x = %.1f ± %.1f cm",
                                  title="Range infos")

    disp1 = make.computation(range, "BL", "trapz=%g",
                             curve, lambda x,y: trapz(y,x))

    disp2 = make.computations(range, "TL",
                              [(curve, "min=%.5f", lambda x,y: y.min()),
                               (curve, "max=%.5f", lambda x,y: y.max()),
                               (curve, "avg=%.5f", lambda x,y: y.mean())])
    legend = make.legend("TR")
    plot( curve, range, disp0, disp1, disp2, legend)

if __name__ == "__main__":
    previewTransportData()