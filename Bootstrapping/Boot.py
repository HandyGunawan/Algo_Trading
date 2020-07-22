#!/usr/bin/env python
# coding: utf-8

# In[2]:

import random
import numpy as np
import pandas as pd
import scipy, scipy.stats
from scipy.stats import norm,geom
from sklearn.preprocessing import scale
import datetime  
import multiprocessing as mp


# MEBOOT Part

def shuffle_Initial(x,n,z,xmin,xmax,desintxb,reachbound):
    p=np.random.uniform(size=n)
    q=np.full((n),-99999.0)
    for i in range(n-2):
        if(((p>((i+1)/n)) & (p<=((i+2)/n) )).any):
            ref23 = np.where( (p>((i+1)/n)) & (p<=((i+2)/n) ))[0]
            for j in range(len(ref23)):
                k = ref23[j]
                qq = z[i] + (z[i+1]-z[i]) / (1/n) *(p[k] - (i+1)/n)
                q[k] = qq + desintxb[i+1] - 0.5 * ( z[i] + z[i+1])
    ref1 = np.where(p<=(1/n))
    if(len(ref1)>0):
        qq = np.interp(p[ref1],[0,1/n],[xmin,z[1]])
        q[ref1] = qq
        if(reachbound==False):
            q[ref1] = qq + desintxb[0] - 0.5 * (z[0] +xmin)

    ref4 = np.where(p == ((n-1)/n))
    if (len(ref4) >0):
        q[ref4] = z[-2]
    ref5 = np.where(p > ((n-1)/n))
    if (len(ref5)>0):
        qq = np.interp(p[ref5],[(n-1)/n,1],[z[-2],xmax])
        q[ref5] = qq
        if (reachbound==False):
            q[ref5] = qq +desintxb[-1] - 0.5 *(z[-2] + xmax)

    return(q)

def expand_std(x, ensemble, fiv = 5):
    sdx = np.std(x,axis=0)
    sdf = np.insert(np.std(ensemble,axis=1),0,sdx)
    sdfa = sdf/sdf[0]
    sdfd = sdf[0]/sdf
    mx = 1 + fiv/100
    id = np.where(sdfa<1)
    if (len(id)>0):
        sdfa[id] = np.random.uniform(size=len(id),low=1,high=mx)
    sdfdXsdfa = sdfd[1:] *sdfa[1:]
    id = np.where(np.floor(sdfdXsdfa) > 0)
    if (len(id)>0):
         ensemble[id,:][0] = ensemble[id,:][0].T.dot(np.diag(sdfdXsdfa[id])).T
    return(ensemble)

def force_clt(x, ensemble):
    bigj,n = ensemble.shape
    gm = np.mean(x)
    s = np.std(x,axis=0)
    smean = s/np.sqrt(bigj)
    xbar = np.mean(ensemble,axis=1)
    sortxbar = np.sort(xbar)
    oo = np.argsort(xbar)
    newbar = gm + norm.ppf(np.arange(1,bigj+1)/(bigj+1)) * smean
    scn = scale(newbar)
    newm = scn*smean + gm
    meanfix = newm - sortxbar
    out = ensemble
    out[oo,:] = ensemble[oo,:] +np.array([meanfix] * n).T
    return(out)


def ME_bootstrap(x, reps = 999, trim = {'trimval' : 0.1, 'xmin' : None,'xmax' : None}, reachbound = True, expand_standard_deviation = True, force_central_limit = True, scl_adjustment = True, elaps = True):
    if isinstance(x, pd.DataFrame):
        index = x.index
        x = x.to_numpy(dtype=object).T[0]
        y = True
    elif isinstance(x, pd.Series):
        index = x.index
        x = x.to_numpy(dtype=object).T[0]
        y = True
    elif isinstance(x, np.ndarray):
        x = x
        y = True
    else: print("only accept series, dataframe and arrays")

    if (y):
        current_time1 = datetime.datetime.now()
        n = len(x)
        xx = np.sort(x)
        order_x = np.argsort(x)
        z = np.array(pd.Series(xx).rolling(2).mean().dropna())
        dv = abs(np.diff(x))

        if trim['trimval'] ==None : trimval = 0.1
        else : trimval = trim['trimval']

        dvtrim = scipy.stats.trim_mean(dv, trimval)

        if trim['xmin'] ==None : xmin = xx[0] - dvtrim
        else : xmin = trim['xmin']

        if trim['xmax'] ==None : xmax = xx[-1] + dvtrim
        else : xmax = trim['xmax']



        aux = pd.DataFrame([xx*0.25,pd.Series(xx).shift(1)*0.5,pd.Series(xx).shift(2)*0.25]).dropna(axis=1).sum(axis=0)
        desintxb = aux
        desintxb.loc[1]=0.75 * xx[0] + 0.25 * xx[1];desintxb.loc[len(desintxb)+1]=0.25 * xx[-2]+ 0.75 * xx[-1]
        desintxb.index = desintxb.index - 1 ; desintxb = np.array(desintxb.sort_index())  # shifting index
#       desintxb is the desired mean

        ensemble = np.repeat(np.matrix(x),reps,axis=0)
        ensemble = np.array([shuffle_Initial(np.array(p)[0],n=len(np.array(p)[0]),z=z,xmin=xmin,xmax=xmax,desintxb=desintxb,reachbound=reachbound) for p in ensemble])
        current_time2 = datetime.datetime.now()  
        qseq = np.sort(ensemble)
        ensemble[:,order_x] =qseq

        if (expand_standard_deviation):
            ensemble = expand_std(x = x, ensemble = ensemble, fiv = 5)
            current_time3 = datetime.datetime.now()  
        if (force_central_limit):
            ensemble = force_clt(x = x, ensemble = ensemble)
            current_time4 = datetime.datetime.now()  
        if (scl_adjustment):
            zz = np.insert(z,0,xmin) ; zz = np.insert(zz,-1,xmax)
            v = np.diff(zz**2)/12
            xb = np.mean(x)
            s1 = np.sum((desintxb - xb)**2)
            uv = (s1 + np.sum(v))/n
            desired_sd = np.std(x)
            actualME_sd = np.sqrt(uv)
            out = desired_sd/actualME_sd
            kappa = out - 1
            ensemble = ensemble + kappa * (ensemble - xb)
        else:
            kappa = None
        current_time5 = datetime.datetime.now()  
        elapsr = [current_time2 - current_time1,current_time3 - current_time2,current_time4 - current_time3,current_time5 - current_time4]

        if (elaps):print("Elapsed Time:", elapsr)

        if not isinstance(x, np.ndarray):
            x = pd.DataFrame({'Values' :x},index=index)
            ensemble = pd.DataFrame(ensemble.T,index=index)
        return{'x' : x, 'ensemble' : ensemble, 'xx' : xx, 'z' : z, 'dv' : dv, 
           'dvtrim' : dvtrim, 'xmin' : xmin, 'xmax' : xmax, 'desintxb' : desintxb, 
           'order_x' : order_x, 'kappa' : kappa, 'elaps' : elapsr}

# Block Bootstrap

def ts_array(n,n_sim,R,l,sim,endcorr):
    end_part = n if endcorr else n-l+1
    cont = True
    if (sim =="geom"): 
        len_tot = np.repeat(0,R)
        lens = np.array(([None]*R))
        while (cont):
            temp = 1 + geom.rvs(1/l,size = R)
            temp = np.min(np.array([temp,n_sim-len_tot]),axis=0)
            lens = np.vstack((lens,temp))
            len_tot = len_tot + temp
            cont= (any(len_tot < n_sim))
        lens = lens[1:]
        nn = lens.shape[0]
        st = np.random.randint(end_part,size=(nn,R))
    else :
        nn = int(np.ceil(n_sim/l))
        lens = np.hstack((np.repeat(l,nn-1),1 + (n_sim - 1)%l))
        st = np.random.randint(end_part,size=(nn,R))
    return({'starts' : st, 'lengths' : lens})

def make_ends(a,n):
    def mod(i,n): return(1+(i-1) % n)    
    return(mod(np.arange(a[0],a[0]+a[1]),n))


def statistic (x) : return(x)

def ran_gen (x,n_sim,*args) : return(x)

def tsboot(tseries, statistic = statistic, R=999, l = 20, sim = "model", endcorr = True, n_sim = None, original_t = True, ran_gen = ran_gen, ran_args = None, normal = True, parallel = ["no", "multicore", "snow"][0]):
    t0 = statistic(tseries) if original_t else None 
    original_ts = np.array(tseries).T if not isinstance(tseries, np.ndarray) else tseries
    n = original_ts.shape[1]
    n_sim = n if n_sim == None else n_sim
    # original_ts = ts_class(original_ts)
    original_ts
    if sim == 'model':
        def r():return(statistic(ran_gen(tseries,n_sim,ran_args)))
    elif sim in ["fixed","geom"]:
        if sim=="geom": endcorr=True
        def r():
            i_a = ts_array(n,n_sim,R,l,sim,endcorr)
            ends = np.array([i_a['starts'][:,0],i_a['lengths'][:,0]]) if sim=="geom" else np.array([i_a['starts'][:,0],i_a['lengths']])
            inds = np.concatenate(np.array([make_ends(i,n=n-1) for i in ends.T]))
            return statistic(ran_gen(tseries.iloc[inds,:].reset_index(drop=True),n_sim,ran_args))
    res = [r() for x in range(R)]
    return(res)