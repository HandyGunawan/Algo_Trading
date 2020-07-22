#!/usr/bin/env python
# coding: utf-8

# In[2]:

from scipy import stats
from statsmodels.tsa import stattools as stt
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from mpl_toolkits.mplot3d import Axes3D 



def diagnosis(Ticker,boxplotyear=2019):
    plt.style.use('ggplot')
    Return = pd.DataFrame(np.log1p(Ticker.Close.pct_change()).dropna())
    Ticker.Close.plot()
    plt.show()
    Return.plot(linewidth=0.25)
    plt.show()
    sns.distplot(Return)
    plt.show()
    Return['month_year'] = pd.to_datetime(Return.index).to_period('M')
    Return[Return.index.year == boxplotyear].boxplot(by='month_year', 
                       column=['Close'], 
                       grid=True)
    plt.show()
    pt = Return
    pt['Month']=pt.index.month
    pt['Year']=pt.index.year
    ptwide = pd.pivot_table(pt,index=['Month'],columns=['Year'],aggfunc=np.sum)
    ptlong = pd.pivot_table(pt,index=['month_year'],aggfunc=np.sum)
    ptlong['Month']=ptlong.index.month
    ptlong['Year']=ptlong.index.year
    ptwide.plot(legend=False)
    plt.show()
    ptlong.boxplot(by='Month', 
                           column=['Close'], 
                           grid=True)
    plt.show()

    
    
    print("Return Mean")
    print(Return.Close.mean()*252)
    print("Return Std")      
    print(Return.Close.std()*(252**0.5))
    print("Return Kurtosis")      
    print(stats.kurtosis(Return.Close.dropna()))
    print("Return skewness")      
    print(stats.skew(Return.Close.dropna()))
    
    return Return

