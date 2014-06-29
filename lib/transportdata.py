# -*- coding: utf-8 -*-
"""
Created on Mon Jun 23 13:32:51 2014

Shared functions for processing transport measurement data.

@author: hannes.maierflaig
"""

import numpy as np
    
def symmetrizeSignalZero(y, idx = None):
    """
    Dischard antisymmetric (around center index or around idx) part by 
    taking the sum of the signal at x[idx_centre +n] and x[idx_centre -n]
    
    Parameters
    ----------
    y : array_like 
        numpy array or list of data values to anti symmtetrize
    idx : scalar
        index of center to symmetrize around if ommitted len(y)/2 is taken as idx
    
    Returns
    ----------
    y_symmetrized : ndarray
        numpy array of dimension size(y)/2 of the symmetrized data
    """
    y = np.array(y)
    if not np.size(y)%2:
        raise Exception("Data needs to have an uneven number of elements if no center index (idx) is provided")
    if not idx:
        idx = np.size(y)/2
        idx_end = np.size(y)
    else:
        idx_end = min((np.size(y), idx*2))
        
    y = (y[0:idx] + y[idx+1:idx_end][::-1])/2
    return y


def antiSymmetrizeSignalZero(y, idx = None):
    """
    Dischard symmetric (around center index or around idx) part by 
    taking the difference of the signal at x[idx_centre +n] and x[idx_centre -n]
        
    Parameters
    ----------
    y : array_like 
        numpy array or list of data values to anti symmtetrize
    idx : scalar
        index of center to symmetrize around if ommitted len(y)/2 is taken as idx
    
    Returns
    ----------
    y_symmetrized : ndarray
        numpy array of dimension size(y)/2 of the antisymmetrized data
    """
    y = np.array(y)
    if not np.size(y)%2:
        raise Exception("Data needs to have an uneven number of elements if no center index (idx) is provided")
    if not idx:
        idx = np.size(y)/2
        idx_end = np.size(y)
    else:
        idx_end = min((np.size(y), idx*2))
        
    y = (y[0:idx] - y[idx+1:idx_end][::-1])/2
    return y
    
    
def antiSymmetrizeSignal(y, symmetryStep):
    """    
    Dischard symmetric (around center index or around idx) part of a signal by 
    taking the difference of the signal at x[idx_centre +n] and x[idx_centre +n + symmetry_step]
    get your corresponding x data as x[0:len(y)/]
                
    Parameters
    ----------
    y : array_like 
        numpy array or list of data values to anti symmtetrize
    symmetryStep : scalar
        expected symmetry of the signal at x[n] occurs at x[n+symmetryStep]
    
    Returns
    ----------
    y_symmetrized : ndarray
        numpy array of dimension size(y)/2 of the antisymmetrized data
    """
    y = np.array(y)
        
    s = np.zeros(len(y)-symmetryStep)
    for idx in range(0, len(s)):
        s[idx] = (y[idx] - y[idx+symmetryStep])/2.-(y[0] - y[0+symmetryStep])/2.
    return s


def symmetrizeSignal(y, symmetryStep):
    """
    Dischard antisymmetric (around center index or around idx) part of a signal by 
    taking the sum of the signal at x[idx_centre +n] and x[idx_centre +n + symmetry_step].
    
    Get your corresponding x data as x[0:len(y)/]
    
    Parameters
    ----------
    y : array_like 
        numpy array or list of data values to anti symmtetrize
    symmetryStep : scalar
        expected symmetry of the signal at x[n] occurs at x[n+symmetryStep]
    
    Returns
    ----------
    y_symmetrized : ndarray
        numpy array of dimension size(y)/2 of the symmetrized data
    """
    y = np.array(y)
        
    s = np.zeros(len(y)-symmetryStep)
    for idx in range(0, len(s)):
        s[idx] = (y[idx] + y[idx+symmetryStep])/2.-(y[0] + y[0+symmetryStep])/2.
    return s


def symmetrizeSignalUpDown(y, symmetryStep):
    """
    Symmetrize a signal that is recorded as an up and down sweep by calculating
    the cross sum between up and down sweep of values shifted by symmetry step.
    
    Get the corresponding x data as averageUpDownSweep(x).
        
    Parameters
    ----------
    y : array_like 
        numpy array or list of data values to anti symmtetrize
    symmetryStep : scalar
        expected symmetry of the signal at x[n] occurs at x[n+symmetryStep]
    
    Returns
    ----------
    y_symmetrized : ndarray
        numpy array of dimension size(y)/2 of the symmetrized data
    """
    y=np.array(y)
 
    yL = np.hstack((y[0:len(y)/4], # first quarter compared w/ 
                    y[len(y)/2:3*len(y)/4][::-1] - (y[3*len(y)/4]-y[len(y)/4]))) #third quarter 
                    
    yU = np.hstack((y[3*len(y)/4:][::-1] - (y[3*len(y)/4]-y[len(y)/4]), # fourth quarter cmp w/
                   y[len(y)/4:len(y)/2]))  # second quarter 

    y_sym = np.hstack((symmetrizeSignal(yL, symmetryStep), symmetrizeSignal(yU, symmetryStep))[::-1])
      
    return y_sym
    

def antiSymmetrizeSignalUpDown(y, symmetryStep):
    """
    Antisymmetrize a signal that is recorded as an up and down sweep by calculating
    the cross difference between up and down sweep of values shifted by symmetry step.
    
    Get the corresponding x data as averageUpDownSweep(x).
    
    Parameters
    ----------
    y : array_like 
        numpy array or list of data values to anti symmtetrize
    symmetryStep : scalar
        expected symmetry of the signal at x[n] occurs at x[n+symmetryStep]
    
    Returns
    ----------
    y_symmetrized : ndarray
        numpy array of dimension size(y)/2 of the antisymmetrized data
    """
    import matplotlib.pyplot as plt
    y=np.array(y)

    yL = np.hstack((y[0:len(y)/4], # first quarter compared w/ 
                    y[len(y)/2:3*len(y)/4][::-1] - (y[3*len(y)/4]-y[len(y)/4]))) #third quarter 
                    
    yU = np.hstack((y[3*len(y)/4:][::-1] - (y[3*len(y)/4]-y[len(y)/4]), # fourth quarter cmp w/
                   y[len(y)/4:len(y)/2]))  # second quarter 

    plt.plot(np.arange(0,len(yU)*2,2), yU, 'k', linewidth = 3, color = "b")
    y_sym = np.hstack((antiSymmetrizeSignal(yL, symmetryStep), antiSymmetrizeSignal(yU, symmetryStep)))
    
    return y_sym
    
def separateAlternatingSignal(x):
    """
    Separates each 2nd element of an array into two array

    Returns    
    ----------
    separated_signal : list of two arrays (x[2n], x[2n-1])
    """
    return np.array(x[0::2]), np.array(x[1::2])

    
def averageUpDownSweep(x, num=1):
    """
    Calculate x[center+n] + x[center-n] of a signal thereby data recorded as up,
    then down sweep can be averaged.
       
    Parameters
    ----------
    x : data (list or numpy array) to average
    num : apply algorithm num times to average more than once (default: 1)
    
    Returns    
    ----------
    x_averaged : numpy array of the averaged data
    """
    x = np.array(x)
    for i in range(num):
        x = (x[0:np.size(x)/2] + x[::-1][0:np.size(x)/2])/2
    return x