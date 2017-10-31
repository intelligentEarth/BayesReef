# !/usr/bin/python
# MCMC random walk method applied to pyReef-Core
# Authors: Jodie Pall and Danial Azam (2017)
# Adapted from:
# MCMC Random Walk for Feedforward Neural Network for One-Step-Ahead Chaotic Time Series Prediction
# Data (Sunspot and Lazer). Taken' Theorem used for Data Reconstruction (Dimension = 4, Timelag = 2).
# Data procesing file is included.
# RMSE (Root Mean Squared Error)
# based on: https://github.com/rohitash-chandra/FNN_TimeSeries
# based on: https://github.com/rohitash-chandra/mcmc-randomwalk
# Rohitash Chandra, Centre for Translational Data Science
# University of Sydey, Sydney NSW, Australia.  2017 c.rohitash@gmail.conm
# https://www.researchgate.net/profile/Rohitash_Chandra
# Reference for publication for this code
# [Chandra_ICONIP2017] R. Chandra, L. Azizi, S. Cripps, 'Bayesian neural learning via Langevin dynamicsfor chaotic time series prediction', ICONIP 2017.
# (to be addeded on https://www.researchgate.net/profile/Rohitash_Chandra)
import os
import math
import time
import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from pyReefCore.model import Model
import fnmatch
import shutil
from PIL import Image
from io import StringIO
import matplotlib as mpl
from cycler import cycler
from scipy import stats 

cmap=plt.cm.Set2
c = cycler('color', cmap(np.linspace(0,1,8)) )
plt.rcParams["axes.prop_cycle"] = c

class MCMC():
    def __init__(self, simtime, samples, communities, core_data, core_depths,timestep,filename, xmlinput, sedsim, sedlimits, flowsim, flowlimits, vis):
        self.filename = filename
        self.input = xmlinput
        self.communities = communities
        self.samples = samples       
        self.core_data = core_data
        self.core_depths = core_depths
        self.timestep = timestep
        self.vis = vis
        self.sedsim = sedsim
        self.flowsim = flowsim
        self.sedlimits = sedlimits
        self.flowlimits = flowlimits
        self.simtime = simtime
        self.font = 9
        self.width = 1
        self.d_sedprop = float(np.count_nonzero(core_data == 0.571))/core_data.shape[0]
        self.initial_sed = []
        self.initial_flow = []
        self.step_m = 0.002#0.005#0.005#0.01
        self.step_a = 0.002#0.005#0.005#0.005 
        self.step_sed = 0.0001#0.00025#0.00025#0.001 
        self.step_flow = 0.0015#0.015#0.05 
        self.step_eta = 0.001#0.001

    def run_Model(self, reef, input_vector):

        reef.convert_vector(self.communities, input_vector, self.sedsim, self.flowsim) #model.py
        self.initial_sed, self.initial_flow = reef.load_xml(self.input, self.sedsim, self.flowsim)
        if self.vis[0] == True:
            reef.core.initialSetting(size=(8,2.5), size2=(8,3.5)) # View initial parameters
        reef.run_to_time(self.simtime,showtime=100.)
        if self.vis[1] == True:
            from matplotlib.cm import terrain, plasma
            nbcolors = len(reef.core.coralH)+10
            colors = terrain(np.linspace(0, 1.8, nbcolors))
            nbcolors = len(reef.core.layTime)+3
            colors2 = plasma(np.linspace(0, 1, nbcolors))
            reef.plot.drawCore(lwidth = 3, colsed=colors, coltime = colors2, size=(9,8), font=8, dpi=300)
        output_core = reef.plot.core_timetodepth(self.communities, self.core_depths) #modelPlot.py
        predicted_core = reef.convert_core(self.communities, output_core, self.core_depths) #model.py
        return predicted_core 

    def plot_results(self, pos_m, pos_ax, pos_ay, pos_sed1, pos_sed2, pos_sed3, pos_sed4, pos_flow1, pos_flow2, pos_flow3, pos_flow4, burn):
        nb_bins=20
        slen = np.arange(0,pos_m.shape[0],1)

        #   MALTHUS PARAMETER   #
        mmin, mmax = min(pos_m), max(pos_m)
        mspace = np.linspace(mmin,mmax,len(pos_m))
        mm,ms = stats.norm.fit(pos_m)
        pdf_m = stats.norm.pdf(mspace,mm,ms)
        mmin=str(mmin)
        mmax=str(mmax)
        mmean=str(np.mean(pos_m))
        mmedian=str(np.median(pos_m))
        mmode=str(stats.mode(pos_m))
    
        fig = plt.figure(figsize=(6,8))
        ax = fig.add_subplot(111)
        ax.spines['top'].set_color('none')
        ax.spines['bottom'].set_color('none')
        ax.spines['left'].set_color('none')
        ax.spines['right'].set_color('none')
        ax.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
        ax.set_title(' Malthusian Parameter', fontsize= self.font+2)#, y=1.02)
        # ax.axvline(mmean,ymin=0,ymax=1,color='k',linestyle='--')
        # # ax.set_ylim(0,1)
        ax1 = fig.add_subplot(211)
        ax1.set_facecolor('#f2f2f3')
        ax1.hist(pos_m, bins=25, alpha=0.5, facecolor='sandybrown', normed=True)
        ax1.axvline(mm,linestyle='-', color='black', linewidth=1,label='Mean')
        ax1.axvline(mm+ms,linestyle='--', color='black', linewidth=1,label='5th and 95th %ile')
        ax1.axvline(mm-ms,linestyle='--', color='black', linewidth=1,label=None)
        # ax1.plot(mspace,pdf_m,label='Best fit',color='orangered',linestyle='--')
        ax1.grid(True)
        ax1.set_ylabel('Frequency',size=self.font+1)
        ax1.set_xlabel(r'$\varepsilon$', size=self.font+1)
        ax2 = fig.add_subplot(212)
        ax2.set_facecolor('#f2f2f3')
        ax2.plot(slen,pos_m,linestyle='-', linewidth=self.width, color='k', label=None)
        ax2.set_title(r'Trace of $\varepsilon$',size=self.font+2)
        ax2.set_xlabel('Samples',size=self.font+1)
        ax2.set_ylabel(r'$\varepsilon$', size=self.font+1)
        ax2.set_xlim([0,np.amax(slen)])
        fig.tight_layout()
        fig.subplots_adjust(top=0.88)
        plt.savefig('%s/malthus.png'% (self.filename), bbox_inches='tight', dpi=300, transparent=False)
        plt.clf()
        
        #    COMMUNITY MATRIX   #
        a1min, a1max = min(pos_ax), max(pos_ax)
        a1space = np.linspace(a1min,a1max,len(pos_ax))
        a1m,a1s = stats.norm.fit(pos_ax)
        pdf_a1 = stats.norm.pdf(a1space,a1m,a1s)
        a2min, a2max = min(pos_ay), max(pos_ay)
        a2space = np.linspace(a2min,a2max,len(pos_ay))
        a2m,a2s = stats.norm.fit(pos_ay)
        pdf_a2 = stats.norm.pdf(a2space,a2m,a2s)
        a1min=str(a1min)
        a1max=str(a1max)
        a1mean=str(np.mean(pos_ax))
        a1median=str(np.median(pos_ax))
        a1mode=str(stats.mode(pos_ax))
        a2min=str(a2min)
        a2max=str(a2max)
        a2mean=str(np.mean(pos_ay))
        a2median=str(np.median(pos_ay))
        a2mode=str(stats.mode(pos_ay))  

        ####   main diagonal   
        fig = plt.figure(figsize=(6,8))
        ax = fig.add_subplot(111)
        ax.spines['top'].set_color('none')
        ax.spines['bottom'].set_color('none')
        ax.spines['left'].set_color('none')
        ax.spines['right'].set_color('none')
        ax.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
        ax.set_title('Community Interaction Matrix Parameters', fontsize= self.font+2, y=1.03)
        ax1 = fig.add_subplot(211)
        ax1.set_facecolor('#f2f2f3')
        ax1.hist(pos_ax, bins=25, alpha=0.5, facecolor='mediumaquamarine', normed=True)
        # ax1.plot(a1space,pdf_a1,label='Best fit',color='orangered',linestyle='--')
        ax1.axvline(a1m,linestyle='-', color='black', linewidth=1,label='Mean')
        ax1.axvline(a1m+a1s,linestyle='--', color='black', linewidth=1,label='5th and 95th %ile')
        ax1.axvline(a1m-a1s,linestyle='--', color='black', linewidth=1,label=None)
        ax1.grid(True)
        ax1.set_ylabel('Frequency',size=self.font+1)
        ax1.set_title(r'Main diagonal value ($\alpha_{ii}$)',size=self.font+2)
        ax1.set_xlabel(r'$\alpha_{ii}$', size=self.font+1)
        ax2 = fig.add_subplot(212)
        ax2.set_facecolor('#f2f2f3')
        ax2.plot(slen,pos_ax,linestyle='-', linewidth=self.width, color='k', label=None)
        ax2.set_xlabel('Samples',size=self.font+1)
        ax2.set_ylabel(r'$\alpha_{ii}$', size=self.font+1)
        ax2.set_title(r'Trace of $\alpha_{ii}$',size=self.font+2)
        ax2.set_xlim([0,np.amax(slen)])
        fig.tight_layout()
        fig.subplots_adjust(top=0.88)
        plt.savefig('%s/comm_ax.png'% (self.filename),bbox_inches='tight', dpi=300,transparent=False)
        plt.clf()

        ####   sub- and super-diagonal  
        fig = plt.figure(figsize=(6,8))
        ax = fig.add_subplot(111)
        ax.spines['top'].set_color('none')
        ax.spines['bottom'].set_color('none')
        ax.spines['left'].set_color('none')
        ax.spines['right'].set_color('none')
        ax.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
        ax.set_title('Community Interaction Matrix Parameters', fontsize= self.font+2, y=1.03)
        ax1 = fig.add_subplot(211)
        ax1.set_facecolor('#f2f2f3')
        ax1.hist(pos_ay, bins=25, alpha=0.5, facecolor='mediumaquamarine', normed=True)
        ax1.axvline(a2m,linestyle='-', color='black', linewidth=1,label='Mean')
        ax1.axvline(a2m+a2s,linestyle='--', color='black', linewidth=1,label='5th and 95th %ile')
        ax1.axvline(a2m-a2s,linestyle='--', color='black', linewidth=1,label=None)
        # ax1.plot(a2space,pdf_a2,label='Best fit',color='orangered',linestyle='--')
        ax1.grid(True)
        ax1.set_title(r'Super- and sub-diagonal values ($\alpha_{i,i+1}$ and $\alpha_{i+1,i}$)',size=self.font+2)
        ax1.set_xlabel(r'$\alpha_{i,i+1}$ and $\alpha_{i+1,i}$', size=self.font+1)
        ax1.set_ylabel('Frequency',size=self.font+1)
        ax2 = fig.add_subplot(212)
        ax2.set_facecolor('#f2f2f3')
        ax2.plot(slen,pos_ay,linestyle='-', linewidth=self.width, color='k', label=None)
        ax2.set_title(r'Trace of $\alpha_{i,i+1}$ and $\alpha_{i+1,i}$',size=self.font+2)
        ax2.set_xlabel('Samples',size=self.font+1)
        ax2.set_ylabel(r'$\alpha_{i,i+1}$ and $\alpha_{i+1,i}$', size=self.font+1)
        ax2.set_xlim([0,np.amax(slen)])
        fig.tight_layout()
        fig.subplots_adjust(top=0.88)
        plt.savefig('%s/comm_ay.png' % (self.filename), dpi=300, bbox_inches='tight',transparent=False)
        plt.clf()

        if not os.path.isfile(('%s/summ_stats.txt' % (self.filename))):
            with file(('%s/summ_stats.txt' % (self.filename)),'w') as outfile:
                outfile.write('#SUMMARY STATISTICS\n')
                outfile.write('# MIN, MAX, MEAN, MEDIAN, MODE\n')
                outfile.write('# Malthusian parameter\n{0}, {1}, {2}, {3}, \n{4}\n'.format(mmin,mmax,mmean,mmedian,mmode))
                outfile.write('# Ax\n{0}, {1}, {2}, {3}, \n{4}\n'.format(a1min,a1max,a1mean,a1median,a1mode))
                outfile.write('# Ay\n{0}, {1}, {2}, {3}, \n{4}\n'.format(a2min,a2max,a2mean,a2median,a2mode))


        # PLOT SEDIMENT AND FLOW RESPONSE THRESHOLDS #
        a_labels = ['Shallow windward', 'Moderate-deep windward', 'Deep windward', 'Shallow leeward', 'Moderate-deep leeward', 'Deep leeward']
        
        sed1_mu, sed1_ub, sed1_lb, sed2_mu, sed2_ub, sed2_lb, sed3_mu, sed3_ub, sed3_lb, sed4_mu, sed4_ub, sed4_lb = (np.zeros(self.communities) for i in range(12))
        if ((self.sedsim != False)):
            for a in range(0,self.communities):
                sed1_mu[a] = np.mean(pos_sed1[:,a])
                sed1_ub[a] = np.percentile(pos_sed1[:,a], 95, axis=0)
                sed1_lb[a] = np.percentile(pos_sed1[:,a], 5, axis=0)
                
                sed2_mu[a] = np.mean(pos_sed2[:,a])
                sed2_ub[a] = np.percentile(pos_sed2[:,a], 95, axis=0)
                sed2_lb[a] = np.percentile(pos_sed2[:,a], 5, axis=0)
                
                sed3_mu[a] = np.mean(pos_sed3[:,a])
                sed3_ub[a] = np.percentile(pos_sed3[:,a], 95, axis=0)
                sed3_lb[a] = np.percentile(pos_sed3[:,a], 5, axis=0)
                
                sed4_mu[a] = np.mean(pos_sed4[:,a])
                sed4_ub[a] = np.percentile(pos_sed4[:,a], 95, axis=0)
                sed4_lb[a] = np.percentile(pos_sed4[:,a], 5, axis=0)

                sed1_mu_ = sed1_mu[a]
                sed1_mu_ = str(sed1_mu_)
                sed2_mu_ = sed2_mu[a]
                sed2_mu_ = str(sed2_mu_)
                sed3_mu_ = sed3_mu[a]
                sed3_mu_ = str(sed3_mu_)
                sed4_mu_ = sed4_mu[a]
                sed4_mu_ = str(sed4_mu_)
                sed1_min= str(sed1_lb[a])
                sed1_max=str(sed1_ub[a])
                sed1_med=str(np.median(pos_sed1[:,a]))
                sed2_min=str(sed2_lb[a])
                sed2_max=str(sed2_ub[a])
                sed2_med=str(np.median(pos_sed2[:,a]))
                sed3_min=str(sed3_lb[a])
                sed3_max=str(sed3_ub[a])
                sed3_med=str(np.median(pos_sed3[:,a]))
                sed4_min=str(sed4_lb[a])
                sed4_max=str(sed4_ub[a])
                sed4_med=str(np.median(pos_sed4[:,a]))

                with file(('%s/summ_stats.txt' % (self.filename)),'a') as outfile:
                    outfile.write('\n# Sediment threshold: {0}\n'.format(a_labels[a]))
                    outfile.write('#5TH %ILE, 95TH %ILE, MEAN, MEDIAN\n')
                    outfile.write('# Sed1\n{0}, {1}, {2}, {3}\n'.format(sed1_min,sed1_max,sed1_mu_,sed1_med))
                    outfile.write('# Sed2\n{0}, {1}, {2}, {3}\n'.format(sed2_min,sed2_max,sed2_mu_,sed2_med))
                    outfile.write('# Sed3\n{0}, {1}, {2}, {3}\n'.format(sed3_min,sed3_max,sed3_mu_,sed3_med))
                    outfile.write('# Sed4\n{0}, {1}, {2}, {3}\n'.format(sed4_min,sed4_max,sed4_mu_,sed4_med))

                cy = [0,100,100,0]
                cmu = [sed1_mu[a], sed2_mu[a], sed3_mu[a], sed4_mu[a]]
                # c_lb = [sed1_lb[a], sed2_lb[a], sed3_lb[a], sed4_lb[a]]
                # c_ub = [sed1_ub[a], sed2_ub[a], sed3_ub[a], sed4_ub[a]]
                c_lb = [sed1_mu[a]-sed1_lb[a], sed2_mu[a]-sed2_lb[a], sed3_mu[a]-sed3_lb[a], sed4_mu[a]-sed4_lb[a]]
                c_ub = [sed1_ub[a]-sed1_mu[a], sed2_ub[a]-sed2_mu[a], sed3_ub[a]-sed3_mu[a], sed4_ub[a]-sed4_mu[a]]
                
                fig = plt.figure(figsize=(6,4))
                ax = fig.add_subplot(111)
                ax.set_facecolor('#f2f2f3')
                # ax.plot(self.initial_sed[a,:], cy, linestyle='--', linewidth=self.width, marker='.',color='k', label='Synthetic data')
                ax.plot(cmu, cy, linestyle='-', linewidth=self.width,marker='.', color='sandybrown', label='Mean')
                ax.errorbar(cmu[0:2],cy[0:2],xerr=[c_lb[0:2],c_ub[0:2]],capsize=5,elinewidth=1, color='darksalmon',mfc='darksalmon',fmt='.',label=None)
                ax.errorbar(cmu[2:4],cy[2:4],xerr=[c_lb[2:4],c_ub[2:4]],capsize=5,elinewidth=1, color='sienna',mfc='sienna',fmt='.',label=None)
                # ax.plot(c_lb,cy, linestyle='--', linewidth=self.width, marker='.', color='sandybrown', label=None)
                # ax.plot(c_ub,cy, linestyle='--', linewidth=self.width, marker='.', color='sandybrown', label=None)
                # if sed3_lb[a] > sed2_ub[a]:
                #     ax.fill_betweenx(cy,c_lb,c_ub, facecolor='sandybrown', alpha=0.4, label='90% confidence interval')
                plt.title('Sediment exposure threshold function\n(%s assemblage)' % (a_labels[a]), size=self.font+2, y=1.06)
                plt.ylabel('Proportion of maximum growth rate [%]',size=self.font+1)
                plt.xlabel('Sediment input [m/year]',size=self.font+1)
                plt.ylim(-2.,110)
                lgd = plt.legend(frameon=False, prop={'size':self.font+1}, bbox_to_anchor = (1.,0.2))
                plt.savefig('%s/sediment_response_%s.png' % (self.filename, a+1), bbox_extra_artists=(lgd,),bbox_inches='tight',dpi=300,transparent=False)
                plt.clf()

        flow1_mu, flow1_ub,flow1_lb, flow2_mu, flow2_ub,flow2_lb, flow3_mu, flow3_ub,flow3_lb, flow4_mu, flow4_ub,flow4_lb = (np.zeros(self.communities) for i in range(12))
        if (self.flowsim != False):
            for a in range(0,self.communities):
                flow1_mu[a] = np.mean(pos_flow1[:,a])
                flow1_ub[a] = np.percentile(pos_flow1[:,a], 95, axis=0)
                flow1_lb[a] = np.percentile(pos_flow1[:,a], 5, axis=0)
                
                flow2_mu[a] = np.mean(pos_flow2[:,a])
                flow2_ub[a] = np.percentile(pos_flow2[:,a], 95, axis=0)
                flow2_lb[a] = np.percentile(pos_flow2[:,a], 5, axis=0)
                
                flow3_mu[a] = np.mean(pos_flow3[:,a])
                flow3_ub[a] = np.percentile(pos_flow3[:,a], 95, axis=0)
                flow3_lb[a] = np.percentile(pos_flow3[:,a], 5, axis=0)
                
                flow4_mu[a] = np.mean(pos_flow4[:,a])
                flow4_ub[a] = np.percentile(pos_flow4[:,a], 95, axis=0)
                flow4_lb[a] = np.percentile(pos_flow4[:,a], 5, axis=0)

                flow1_mu_ = str(flow1_mu[a])
                flow2_mu_ = str(flow2_mu[a])
                flow3_mu_ = str(flow3_mu[a])
                flow4_mu_ = str(flow4_mu[a])
                flow1_min= str(flow1_lb[a])
                flow1_max=str(flow1_ub[a])
                flow1_med=str(np.median(pos_flow1[:,a]))
                flow2_min=str(flow2_lb[a])
                flow2_max=str(flow2_ub[a])
                flow2_med=str(np.median(pos_flow2[:,a]))
                flow3_min=str(flow3_lb[a])
                flow3_max=str(flow3_ub[a])
                flow3_med=str(np.median(pos_flow3[:,a]))
                flow4_min=str(flow4_lb[a])
                flow4_max=str(flow4_ub[a])
                flow4_med=str(np.median(pos_flow4[:,a]))

                with file(('%s/summ_stats.txt' % (self.filename)),'a') as outfile:
                    outfile.write('\n# Water flow threshold: {0}\n'.format(a_labels[a]))
                    outfile.write('#5TH %ILE, 95TH %ILE, MEAN, MEDIAN\n')
                    outfile.write('# flow1\n{0}, {1}, {2}, {3}\n'.format(flow1_min,flow1_max,flow1_mu_,flow1_med))
                    outfile.write('# flow2\n{0}, {1}, {2}, {3}\n'.format(flow2_min,flow2_max,flow2_mu_,flow2_med))
                    outfile.write('# flow3\n{0}, {1}, {2}, {3}\n'.format(flow3_min,flow3_max,flow3_mu_,flow3_med))
                    outfile.write('# flow4\n{0}, {1}, {2}, {3}\n'.format(flow4_min,flow4_max,flow4_mu_,flow4_med))
                
                cy = [0,100,100,0]
                cmu = [flow1_mu[a], flow2_mu[a], flow3_mu[a], flow4_mu[a]]
                c_lb = [flow1_mu[a]-flow1_lb[a], flow2_mu[a]-flow2_lb[a], flow3_mu[a]-flow3_lb[a], flow4_mu[a]-flow4_lb[a]]
                c_ub = [flow1_ub[a]-flow1_mu[a], flow2_ub[a]-flow2_mu[a], flow3_ub[a]-flow3_mu[a], flow4_ub[a]-flow4_mu[a]]
                # c_ub = [flow1_lb[a], flow2_lb[a], flow3_lb[a], flow4_lb[a]]
                # c_lb = [flow1_ub[a], flow2_ub[a], flow3_ub[a], flow4_ub[a]]

                
                fig = plt.figure(figsize=(6,4))
                ax = fig.add_subplot(111)
                ax.set_facecolor('#f2f2f3')
                # ax.plot(self.initial_flow[a,:], cy, linestyle='--', linewidth=self.width, marker='.', color='k',label='Synthetic data')
                ax.plot(cmu, cy, linestyle='-', linewidth=self.width, marker='.', color='steelblue', label='Mean')
                ax.errorbar(cmu[0:2],cy[0:2],xerr=[c_lb[0:2],c_ub[0:2]],capsize=5,elinewidth=1,color='lightsteelblue',mfc='lightsteelblue',fmt='.',label=None)
                ax.errorbar(cmu[2:4],cy[2:4],xerr=[c_lb[2:4],c_ub[2:4]],capsize=5,elinewidth=1,color='lightslategrey',mfc='lightslategrey',fmt='.',label=None)
                # ax.plot(c_lb,cy, linestyle='--', linewidth=self.width, marker='.', color='lightsteelblue', label=None)
                # ax.plot(c_ub,cy, linestyle='--', linewidth=self.width, marker='.', color='lightsteelblue', label=None)
                # if flow3_lb[a] > flow2_ub[a]:
                #     ax.fill_betweenx(cy,c_lb,c_ub, facecolor='lightsteelblue',alpha=0.4, label='90% confidence interval')
                plt.title('Hydrodynamic energy exposure threshold function\n(%s assemblage)' % (a_labels[a]), size=self.font+2, y=1.06)
                plt.ylabel('Proportion of maximum growth rate [%]', size=self.font+1)
                plt.xlabel('Fluid flow [m/sec]', size=self.font+1)
                plt.ylim(-2.,110.)
                lgd = plt.legend(frameon=False, prop={'size':self.font+1}, bbox_to_anchor = (1.,0.2))
                plt.savefig('%s/flow_response_%s.png' % (self.filename, a+1),  bbox_extra_artists=(lgd,), bbox_inches='tight',dpi=300,transparent=False)
                plt.clf()


    def save_params(self,naccept, pos_sed1, pos_sed2, pos_sed3, pos_sed4, pos_flow1, pos_flow2, pos_flow3, pos_flow4, pos_m, pos_ax, pos_ay, pos_rmse, pos_samples):    ### SAVE RECORD OF ACCEPTED PARAMETERS ###
        if self.sedsim == True:
            seds = str(np.concatenate((pos_sed1,pos_sed2,pos_sed3,pos_sed4)).reshape((4,self.communities)))
            if not os.path.isfile('%s/accept_sed.txt' % (self.filename)):
                with file(('%s/accept_sed.txt' % (self.filename)),'w') as outfile:
                    outfile.write('\n# {0}\n'.format(naccept))
                    outfile.write(seds)
            else:
                with file(('%s/accept_sed.txt' % (self.filename)),'a') as outfile:
                    outfile.write('\n# {0}\n'.format(naccept))
                    outfile.write(seds)
        
        if self.flowsim == True:
            flows = str(np.concatenate((pos_flow1,pos_flow2,pos_flow3,pos_flow4)).reshape((4,self.communities)))
            if not os.path.isfile('%s/accept_flow.txt' % (self.filename)):
                with file(('%s/accept_flow.txt' % (self.filename)),'w') as outfile:
                    outfile.write('\n# {0}\n'.format(naccept))
                    outfile.write(flows)
            else:
                with file(('%s/accept_flow.txt' % (self.filename)),'a') as outfile:
                    outfile.write('\n# {0}\n'.format(naccept))
                    outfile.write(flows)
        
        m__ = str(pos_m)
        if not os.path.isfile(('%s/accept_m.txt' % (self.filename))):
            with file(('%s/accept_m.txt' % (self.filename)),'w') as outfile:
                outfile.write('\n# {0}\t'.format(naccept))    
                outfile.write(m__)
        else:
            with file(('%s/accept_m.txt' % (self.filename)),'a') as outfile:
                outfile.write('\n# {0}\t'.format(naccept))
                outfile.write(m__)

        aij__ = str((pos_ax,pos_ay))
        if not os.path.isfile(('%s/accept_aij.txt' % (self.filename))):
            with file(('%s/accept_aij.txt' % (self.filename)),'w') as outfile:
                outfile.write('\n# {0}\t'.format(naccept))
                outfile.write(aij__)
        else:
            with file(('%s/accept_aij.txt' % (self.filename)),'a') as outfile:
                outfile.write('\n# {0}\t'.format(naccept))
                outfile.write(aij__)

        rmse__ = str(pos_rmse)
        if not os.path.isfile(('%s/accept_rmse.txt' % (self.filename))):
            with file(('%s/accept_rmse.txt' % (self.filename)),'w') as outfile:
                outfile.write('\n# {0}\t'.format(naccept))
                outfile.write(rmse__)
        else:
            with file(('%s/accept_rmse.txt' % (self.filename)),'a') as outfile:
                outfile.write('\n# {0}\t'.format(naccept))
                outfile.write(rmse__)

        fx__ = str(pos_samples)
        if not os.path.isfile(('%s/accept_samples.txt' % (self.filename))):
            with file(('%s/accept_samples.txt' % (self.filename)),'w') as outfile:
                outfile.write('\n# {0}\n'.format(naccept))
                outfile.write(fx__)
        else:
            with file(('%s/accept_samples.txt' % (self.filename)),'a') as outfile:
                outfile.write('\n# {0}\n'.format(naccept))
                outfile.write(fx__)    

    def rmse(self, predictions, targets):
        sed = np.count_nonzero(predictions==0.571)
        p_sedprop = (float(sed)/predictions.shape[0])
        sedprop = np.absolute((self.d_sedprop - p_sedprop)*0.5)
        rmse =(np.sqrt(((predictions - targets) ** 2).mean()))*0.5
        
        return rmse + sedprop

    def likelihood_func(self, reef, core_data, input_v, tausq):
        pred_core = self.run_Model(reef, input_v)
        rmse = self.rmse(pred_core, core_data)
        loss = -0.5 * np.log(2 * math.pi * tausq) - 0.5 * np.square(core_data - pred_core) / tausq
        
        return [np.sum(loss), pred_core, rmse]
        
    def prior_likelihood(self):
        # def prior_likelihood(self, sigma_squared, nu_1, nu_2, v, tausq):
        #     h = self.topology[1]  # number hidden neurons
        #     d = self.topology[0]  # number input neurons
        #     part1 = -1 * ((d * h + h + 2) / 2) * np.log(sigma_squared)
        #     part2 = 1 / (2 * sigma_squared) * (sum(np.square(v)))
        #     log_loss = part1 - part2 - (1 + nu_1) * np.log(tausq) - (nu_2 / tausq)
        #     return log_loss
        return 1
    
    def save_core(self,reef,naccept):
        path = '%s/%s' % (self.filename, naccept)
        if not os.path.exists(path):
            os.makedirs(path)
        
        #     Initial settings     #
        reef.core.initialSetting(size=(8,2.5), size2=(8,4.5), dpi=300, fname='%s/a_thres_%s_' % (path, naccept))
        from matplotlib.cm import terrain, plasma
        nbcolors = len(reef.core.coralH)+10
        colors = terrain(np.linspace(0, 1.8, nbcolors))
        nbcolors = len(reef.core.layTime)+3
        colors2 = plasma(np.linspace(0, 1, nbcolors))
        
        #      Community population evolution    #
        reef.plot.speciesDepth(colors=colors, size=(8,4), font=8, dpi=300, fname =('%s/b_popd_%s.png' % (path,naccept)))
        reef.plot.speciesTime(colors=colors, size=(8,4), font=8, dpi=300,fname=('%s/c_popt_%s.png' % (path,naccept)))
        reef.plot.accomodationTime(size=(8,4), font=8, dpi=300, fname =('%s/d_acct_%s.pdf' % (path,naccept)))
        
        #      Draw core      #
        reef.plot.drawCore(lwidth = 3, colsed=colors, coltime = colors2, size=(9,8), font=8, dpi=300, 
                           figname=('%s/e_core_%s' % (path, naccept)), filename=('%s/core_%s.csv' % (path, naccept)), sep='\t')
        
        # pdflist = [f for f in os.listdir(os.curdir) if fnmatch.fnmatch(f, ('*_%s*.pdf' % (naccept)))]
        # print pdflist
        # merger = PdfFileMerger()
        # for pdf in pdflist:
        #     merger.append(PdfFileReader(file(pdf, 'rb')))
        # merger.write('output_%s.pdf' % (naccept))       
        
        return

    def sampler(self):
        data_size = self.core_data.shape[0]
        samples = self.samples
        x_data = self.core_depths
        y_data = self.core_data
        
        # Create space to store accepted samples for posterior 
        pos_sed1 = np.zeros((samples , self.communities)) # sample rows, self.communities column
        pos_sed2 = np.zeros((samples , self.communities)) 
        pos_sed3 = np.zeros((samples , self.communities))
        pos_sed4 = np.zeros((samples , self.communities))
        pos_flow1 = np.zeros((samples , self.communities))
        pos_flow2 = np.zeros((samples , self.communities))
        pos_flow3 = np.zeros((samples , self.communities))
        pos_flow4 = np.zeros((samples , self.communities))
        pos_ax = np.zeros(samples)
        pos_ay = np.zeros(samples)
        pos_m = np.zeros(samples)
        # Create space to store fx of all samples
        pos_samples = np.zeros((samples, self.core_data.size))
        rmse= np.zeros(samples) # space for Root Mean Squared Error
        
        #      INITIAL PREDICTION       #
        sed1 = np.zeros(self.communities)
        sed2 = np.zeros(self.communities)
        sed3 = np.zeros(self.communities)
        sed4 = np.zeros(self.communities)
        
        if self.sedsim == True:
            for s in range(self.communities):
                sed1[s] = pos_sed1[0,s] = np.random.uniform(0.,0.)
                sed2[s] = pos_sed2[0,s] = np.random.uniform(0.,0.)
                sed3[s] = pos_sed3[0,s] = np.random.uniform(0.005,0.005)
                sed4[s] = pos_sed4[0,s] = np.random.uniform(0.005,0.005)

        flow1 = np.zeros(self.communities)
        flow2 = np.zeros(self.communities)
        flow3 = np.zeros(self.communities)
        flow4 = np.zeros(self.communities)
        
        if self.flowsim == True:
            for s in range(0,self.communities):
                #     relaxed constraints 
                flow1[s] = pos_flow1[0,s] = np.random.uniform(0.,0.)
                flow2[s] = pos_flow2[0,s] = np.random.uniform(0.,0.)
                flow3[s] = pos_flow3[0,s] = np.random.uniform(0.3,0.3)
                flow4[s] = pos_flow4[0,s] = np.random.uniform(0.3,0.3)
        
        max_a = -0.2
        max_m = 0.2
        cm_ax = pos_ax[0] = np.random.uniform(-0.1,0.)
        cm_ay = pos_ay[0] = np.random.uniform(-0.1,0.)
        m = pos_m[0] = np.random.uniform(0.,0.1)

        if (self.sedsim == True) and (self.flowsim == False):
            v_proposal = np.concatenate((sed1,sed2,sed3,sed4))
        elif (self.flowsim == True) and (self.sedsim == False):
            v_proposal = np.concatenate((flow1,flow2,flow3,flow4))
        elif (self.sedsim == True) and (self.flowsim == True):
            v_proposal = np.concatenate((sed1,sed2,sed3,sed4,flow1,flow2,flow3,flow4))
        v_proposal = np.append(v_proposal,(cm_ax,cm_ay,m))
        pos_v = np.zeros((samples, v_proposal.size))
        print v_proposal


        # Declare pyReef-Core and initialize
        reef = Model()

        # Print 'Evaluate initial parameters'
        initial_pred = self.run_Model(reef,v_proposal)
        eta = np.log(np.var(initial_pred - y_data))
        tau_pro = np.exp(eta)
        prior_likelihood = 1

        [likelihood, pred_data, rmse] = self.likelihood_func(reef, self.core_data, v_proposal, tau_pro)
        pos_rmse = np.full(samples,rmse)
        pos_tau = np.full(samples, tau_pro)
        pos_samples[0,:] = pred_data
        print '\tinitial likelihood:', likelihood, 'and rmse:', rmse

        naccept = 0
        count_list = []
        count_list.append(0)
        self.save_core(reef, 'initial')
        self.save_params(naccept, pos_sed1[0,], pos_sed2[0,], pos_sed3[0,], pos_sed4[0,], pos_flow1[0,], pos_flow2[0,], pos_flow3[0,], pos_flow4[0,], 
            pos_m[0], pos_ax[0], pos_ay[0], pos_rmse[0], pos_samples[0,])
        
        # print 'Begin sampling using MCMC random walk'
        x_tick_labels = ['None','W Shallow', 'W Mod-deep', 'W Deep', 'Sediment','L Shallow', 'L Mod-deep', 'L Deep']
        x_tick_values = [0, 0.143, 0.286, 0.429, 0.571,0.714,0.857,1.0]
        fig = plt.figure(figsize=(3,6))
        ax = fig.add_subplot(111)
        ax.set_facecolor('#f2f2f3')
        ax.plot(y_data, x_data, label='Synthetic core', color='k')
        ax.plot(pred_data, x_data, label='Initial predicted core')
        ax.set_title("Data vs Initial Prediction", size=self.font+2)
        plt.xticks(x_tick_values, x_tick_labels,rotation=70, fontsize=self.font+1)
        ax.set_ylabel("Core depth [m]",size=self.font+1)
        # if self.communities == 3:
        #     ax.set_ylim([0,30])
        # elif self.communities == 6:
        ax.set_ylim([0,np.amax(self.core_depths)])
        ax.set_ylim(ax.get_ylim()[::-1])
        plt.legend(frameon=False, prop={'size':self.font+1},bbox_to_anchor = (1.,0.1))
        fig.savefig('%s/begin.png' % (self.filename), bbox_inches='tight',dpi=300,transparent=False)
        plt.clf()
        
        # ACCUMULATED FIGURE SET UP
        final_fig = plt.figure(figsize=(3,6))
        ax_append = final_fig.add_subplot(111)
        ax_append.set_facecolor('#f2f2f3')
        ax_append.plot(y_data, x_data, label='Synthetic core', color='k')
        ax_append.plot(pred_data, x_data)
        ax_append.set_title("Accepted Proposals", size=self.font+2)
        plt.xticks(x_tick_values, x_tick_labels,rotation=70, fontsize=self.font+1)
        ax_append.set_ylabel("Depth [m]",size=self.font+1)
        # if self.communities == 3:
        #     ax_append.set_ylim([0,30])
        # elif self.communities == 6:
        ax_append.set_ylim([0,np.amax(self.core_depths)])
        ax_append.set_ylim(ax_append.get_ylim()[::-1])


        for i in range(samples - 1):
            print '\nSample: ', i
            start = time.time()

            if self.sedsim == True:
                tmat = np.concatenate((sed1,sed2,sed3,sed4)).reshape(4,self.communities)
                tmatrix = tmat.T
                for x in range(0,self.communities):#-3):
                    for s in range(0,tmatrix.shape[1]):
                        tmatrix[x,s] = tmatrix[x,s] + np.random.normal(0,self.step_sed)
                        if tmatrix[x,s] >= self.sedlimits[x,1]:
                            tmatrix[x,s] = self.sedlimits[x,1]
                        elif tmatrix[x,s] <= self.sedlimits[x,0]:
                            tmatrix[x,s] = self.sedlimits[x,0]
                # reorder each row , then transpose back as sed1, etc.
                tmp = np.zeros((self.communities,4))
                for x in range(0,tmatrix.shape[0]):
                    a = np.sort(tmatrix[x,:])
                    tmp[x,:] = a
                tmat = tmp.T
                p_sed1 = tmat[0,:]
                p_sed2 = tmat[1,:]
                p_sed3 = tmat[2,:]
                p_sed4 = tmat[3,:]
                
            if self.flowsim == True:
                tmat = np.concatenate((flow1,flow2,flow3,flow4)).reshape(4,self.communities)
                tmatrix = tmat.T
                for x in range(0,self.communities):#-3):
                    for s in range(0,tmatrix.shape[1]):
                        tmatrix[x,s] = tmatrix[x,s] + np.random.normal(0,self.step_flow)
                        if tmatrix[x,s] >= self.flowlimits[x,1]:
                            tmatrix[x,s] = self.flowlimits[x,1]
                        elif tmatrix[x,s] <= self.flowlimits[x,0]:
                            tmatrix[x,s] = self.flowlimits[x,0]
                # reorder each row , then transpose back as flow1, etc.
                tmp = np.zeros((self.communities,4))
                for x in range(0,tmatrix.shape[0]):
                    a = np.sort(tmatrix[x,:])
                    tmp[x,:] = a
                tmat = tmp.T
                p_flow1 = tmat[0,:]
                p_flow2 = tmat[1,:]
                p_flow3 = tmat[2,:]
                p_flow4 = tmat[3,:]

            p_ax = cm_ax + np.random.normal(0,self.step_a,1)
            if p_ax > 0:
                p_ax = cm_ax
            elif p_ax < max_a:
                p_ax = cm_ax
            p_ay = cm_ay + np.random.normal(0,self.step_a,1)
            if p_ay > 0:
                p_ay = cm_ay
            elif p_ay < max_a:
                p_ay = cm_ay   
            p_m = m + np.random.normal(0,self.step_m,1)
            if p_m < 0:
                p_m = m
            elif p_m > max_m:
                p_m = m
            v_proposal = []
            if (self.sedsim == True) and (self.flowsim == False):
                v_proposal = np.concatenate((p_sed1,p_sed2,p_sed3,p_sed4))
            elif (self.flowsim == True) and (self.sedsim == False):
                v_proposal = np.concatenate((p_flow1,p_flow2,p_flow3,p_flow4))
            elif (self.sedsim == True) and (self.flowsim == True):
                v_proposal = np.concatenate((p_sed1,p_sed2,p_sed3,p_sed4,p_flow1,p_flow2,p_flow3,p_flow4))
            v_proposal = np.append(v_proposal,(p_ax,p_ay,p_m))

            eta_pro = eta + np.random.normal(0, self.step_eta, 1)
            tau_pro = math.exp(eta_pro)
            [likelihood_proposal, pred_data, rmse] = self.likelihood_func(reef, self.core_data, v_proposal, tau_pro)
            diff_likelihood = likelihood_proposal - likelihood # to divide probability, must subtract
            print 'likelihood_proposal:', likelihood_proposal, 'diff_likelihood',diff_likelihood
            mh_prob = min(1, math.exp(diff_likelihood))
            u = random.uniform(0, 1)
            print 'u', u, 'and mh_probability', mh_prob
            
            if u < mh_prob: # accept
                #   Update position
                print i, ' is accepted sample'
                naccept += 1
                count_list.append(i)
                likelihood = likelihood_proposal
                eta = eta_pro
                m = p_m
                cm_ax = p_ax
                cm_ay = p_ay
                if self.sedsim == True:
                    sed1 = p_sed1
                    sed2 = p_sed2
                    sed3 = p_sed3
                    sed4 = p_sed4
                if self.flowsim == True:
                    flow1 = p_flow1
                    flow2 = p_flow2
                    flow3 = p_flow3
                    flow4 = p_flow4
                # self.save_core(reef,naccept)

                print  'likelihood:',likelihood, ' and rmse:', rmse, 'accepted'

                if self.sedsim == True:
                    pos_sed1[i + 1,] = sed1
                    pos_sed2[i + 1,] = sed2
                    pos_sed3[i + 1,] = sed3
                    pos_sed4[i + 1,] = sed4
                if self.flowsim == True:
                    pos_flow1[i + 1,] = flow1
                    pos_flow2[i + 1,] = flow2
                    pos_flow3[i + 1,] = flow3
                    pos_flow4[i + 1,] = flow4
                pos_ax[i + 1] = cm_ax
                pos_ay[i + 1] = cm_ay
                pos_m[i + 1] = m
                pos_v[i + 1,] = v_proposal
                pos_tau[i + 1,] = tau_pro
                pos_samples[i + 1,] = pred_data
                pos_rmse[i + 1,] = rmse
                
                ax_append.plot(pred_data,x_data, label=None)
                self.save_params(naccept, pos_sed1[i + 1,], pos_sed2[i + 1,], pos_sed3[i + 1,], pos_sed4[i + 1,], 
                    pos_flow1[i + 1,], pos_flow2[i + 1,], pos_flow3[i + 1,], pos_flow4[i + 1,],
                    pos_m[i + 1], pos_ax[i + 1], pos_ay[i + 1], pos_rmse[i + 1,], pos_samples[i + 1,])

           
            else: #reject
                pos_v[i + 1,] = pos_v[i,]
                pos_tau[i + 1,] = pos_tau[i,]
                pos_samples[i + 1,] = pos_samples[i,]
                pos_rmse[i + 1,] = pos_rmse[i,]
                print 'REJECTED\nLikelihood:',likelihood,'and RMSE rejected:', pos_rmse[i,]
                #   Copy past accepted state
                if self.sedsim == True:
                    pos_sed1[i + 1,] = pos_sed1[i,]
                    pos_sed2[i + 1,] = pos_sed2[i,]
                    pos_sed3[i + 1,] = pos_sed3[i,]
                    pos_sed4[i + 1,] = pos_sed4[i,]
                if self.flowsim == True:
                    pos_flow1[i + 1,] = pos_flow1[i,]
                    pos_flow2[i + 1,] = pos_flow2[i,]
                    pos_flow3[i + 1,] = pos_flow3[i,]
                    pos_flow4[i + 1,] = pos_flow4[i,]
                pos_ax[i+1] = pos_ax[i]
                pos_ay[i+1] = pos_ay[i]
                pos_m[i+1] = pos_m[i]
                print i, 'rejected and retained'
            end = time.time()
            total_time = end-start
            print 'Time elapsed:', total_time
            
            if i==samples - 2:
                self.save_core(reef, naccept)

        accepted_count =  len(count_list)   
        print accepted_count, ' number accepted'
        print len(count_list) / (samples * 0.01), '% was accepted'
        accept_ratio = accepted_count / (samples * 1.0) * 100

        lgd = ax_append.legend(frameon=False, prop={'size':self.font+1},bbox_to_anchor = (1.,0.1))
        final_fig.savefig('%s/proposals.png'% (self.filename), extra_artists = (lgd,),bbox_inches='tight',dpi=300,transparent=False)
        plt.clf()

        ##### PLOT RMSE EVOLUTION ########
        fig = plt.figure(figsize=(6,4))
        ax= fig.add_subplot(111)
        ax.set_facecolor('#f2f2f3')
        x_rmse = np.arange(0,samples,1)
        plt.plot(x_rmse,pos_rmse,'-',color='orangered',label='RMSE')
        plt.title("RMSE Evolution", size=self.font+2)
        plt.ylabel("RMSE", size=self.font+1)
        plt.xlabel("Number of samples", size=self.font+1)
        plt.xlim(0,len(pos_rmse)-1)
        plt.savefig('%s/rmse_evolution.png' % (self.filename), dpi=300,transparent=False)
        plt.clf()

        return (pos_v, pos_tau, pos_samples, pos_sed1,pos_sed2,pos_sed3,pos_sed4,pos_flow1,pos_flow2,pos_flow3,pos_flow4, pos_ax,pos_ay,pos_m, x_data, pos_rmse, accept_ratio, accepted_count)

#####################################################################
#####################################################################
#####################################################################
#####################################################################
#####################################################################

def main():
    
    #    Set all input parameters    #
    random.seed(time.time())
    samples = 50000
    description = 'max m and a = 0.2, step_m,a = 0.002, stepsed = 0.0001,stepflow=0.006,stepeta=0.0001'
    nCommunities = 6
    simtime = 8500
    timestep = np.arange(0,simtime+1,50)
    xmlinput = 'input_hi3.xml'
    datafile = 'data/hi3_l.txt'
    core_depths, core_data = np.genfromtxt(datafile, usecols=(0,1), unpack = True) 
    vis = [False, False] # first for initialisation, second for cores
    sedsim, flowsim = True, True
    run_nb = 0
    while os.path.exists('mcmcresults_%s' % (run_nb)):
        run_nb+=1
    if not os.path.exists('mcmcresults_%s' % (run_nb)):
        os.makedirs('mcmcresults_%s' % (run_nb))
    filename = ('mcmcresults_%s' % (run_nb))

    #    Save File of Run Description   #
    if not os.path.isfile(('%s/description.txt' % (filename))):
        with file(('%s/description.txt' % (filename)),'w') as outfile:
            outfile.write('Test Description\n')
            outfile.write(description)
            outfile.write('\nSpecifications')
            outfile.write('\n\tmcmc_6.py')
            outfile.write('\n\tSimulation time: {0} yrs'.format(simtime))
            outfile.write('\n\tSediment simulated: {0}'.format(sedsim))
            outfile.write('\n\tFlow simulated: {0}'.format(flowsim))
            outfile.write('\n\tNo. samples: {0}'.format(samples))
            outfile.write('\n\tXML input: {0}'.format(xmlinput))
            outfile.write('\n\tData file: {0}'.format(datafile))
    """"Windward sedlim = 0.005, flowlim = 0.3
            sedlim_1 = [[0., 0.0035]]
            sedlim_2 = [[0.001,0.0035]]
            sedlim_3 = [[0.001,0.005]]
            sedlim_4 = sedlim_5 = sedlim_6 = [[0.,0.]] 
            # sedlim_4 = [[0.001,0.0035]]
            # sedlim_5 = [[0.002,0.004]]
            # sedlim_6 = [[0.002,0.005]]
            flowlim_1 = [[0.02,0.3]]
            flowlim_2 = [[0.005.,0.2]]
            flowlim_3 = [[0.,0.15]]
            flowlim_4 = [[0.005,0.2]]
            flowlim_5 = [[0.002,0.1]]
            flowlim_6 = [[0.,0.1]]
        Leeward sedlim = 0.005, flowlim = 0.2
            # sedlim_1 = [[0.0005,0.0035]]
            # sedlim_2 = [[0,1e-3]]
            # sedlim_3 = [[0,2e-4]]
            sedlim_1 = sedlim_2 = sedlim_3 = [[0.,0.]] 
            sedlim_4 = [[0.0005,0.0035]]
            sedlim_5 = [[0.0005, 0.003]]
            sedlim_6 = [[0. 0.005]]
            flowlim_1 = [[0.05,0.3]]
            flowlim_2 = [[0.05,0.3]]
            flowlim_3 = [[0,0.2]]
            flowlim_4 = [[0.01,0.3]]
            flowlim_5 = [[0,0.2]]
            flowlim_6 = [[0,0.1]]
    """
    ##### max/min values for each assemblage #####
    sedlim_1 = [[0., 0.0035]]
    sedlim_2 = [[0.001,0.0035]]
    sedlim_3 = [[0.001,0.005]]
    sedlim_4 = [[0.001,0.0035]]
    sedlim_5 = [[0.002,0.004]]
    sedlim_6 = [[0.002,0.005]]

    flowlim_1 = [[0.01,0.3]]
    flowlim_2 = [[0.,0.2]]
    flowlim_3 = [[0.,0.1]]
    flowlim_4 = [[0.005,0.2]]
    flowlim_5 = [[0.002,0.1]]
    flowlim_6 = [[0.,0.1]]
    
    sedlimits = []
    flowlimits = []

    if sedsim == True:
        sedlimits = np.concatenate((sedlim_1,sedlim_2,sedlim_3,sedlim_4,sedlim_5,sedlim_6))
    if flowsim == True:
        flowlimits = np.concatenate((flowlim_1,flowlim_2,flowlim_3,flowlim_4,flowlim_5,flowlim_6))

    mcmc = MCMC(simtime, samples, nCommunities, core_data, core_depths, timestep,  filename, xmlinput, 
                sedsim, sedlimits, flowsim,flowlimits, vis)
    [pos_v, pos_tau, fx_train, pos_sed1,pos_sed2,pos_sed3,pos_sed4,pos_flow1,pos_flow2,pos_flow3,pos_flow4, pos_ax,pos_ay,pos_m, x_data, pos_rmse, accept_ratio, accepted_count] = mcmc.sampler()

    print 'successfully sampled'
    
    burnin = 0.1 * samples  # use post burn in samples
    pos_v = pos_v[int(burnin):, ]
    pos_tau = pos_tau[int(burnin):, ]
    pos_sed1 = pos_sed1[int(burnin):, ]
    pos_sed2 = pos_sed2[int(burnin):, ]
    pos_sed3 = pos_sed3[int(burnin):, ]
    pos_sed4 = pos_sed4[int(burnin):, ]
    pos_flow1 = pos_flow1[int(burnin):, ]
    pos_flow2 = pos_flow2[int(burnin):, ]
    pos_flow3 = pos_flow3[int(burnin):, ]
    pos_flow4 = pos_flow4[int(burnin):, ]
    pos_ax = pos_ax[int(burnin):]
    pos_ay = pos_ay[int(burnin):]
    pos_m = pos_m[int(burnin):]
    rmse_mu = np.mean(pos_rmse[int(burnin):])
    rmse_std = np.std(pos_rmse[int(burnin):])
    
    print 'mean rmse:',rmse_mu, 'standard deviation:', rmse_std

    with file(('%s/out_results.txt' % (filename)),'w') as outres:
        outres.write('Mean RMSE: {0}\nStandard deviation: {1}\nAccept ratio: {2} %\nSamples accepted : {3} out of {4}\n'.format(rmse_mu, rmse_std, accept_ratio, accepted_count, samples))

    if not os.path.isfile(('%s/out_GLVE.csv' % (filename))):
        np.savetxt("%s/out_GLVE.csv" % (filename), np.c_[pos_m,pos_ax,pos_ay], delimiter=',')

    if not os.path.isfile(('%s/out_pos.csv' % (filename))):
        np.savetxt("%s/out_pos.csv" % (filename), pos_v, delimiter=',')

    fx_mu = fx_train.mean(axis=0)
    fx_high = np.percentile(fx_train, 95, axis=0)
    fx_low = np.percentile(fx_train, 5, axis=0)

    fig = plt.figure(figsize=(3,6))
    plt.plot(core_data, x_data,label='Synthetic core', color='k')
    plt.plot(fx_mu,x_data, label='Pred. (mean)',linewidth=1,linestyle='--')
    plt.plot(fx_low, x_data, label='Pred. (5th %ile)',linewidth=1,linestyle='--')
    plt.plot(fx_high,x_data, label='Pred. (95th %ile)',linewidth=1,linestyle='--')
    plt.fill_betweenx(x_data, fx_low, fx_high, facecolor='mediumaquamarine', alpha=0.4, label=None)
    plt.title("Core Data vs MCMC Uncertainty", size=mcmc.font+2)
    plt.ylim([0.,np.amax(core_depths)])
    plt.ylim(plt.ylim()[::-1])
    plt.ylabel('Depth [m]', size=mcmc.font+1)
    x_tick_labels = ['None','W Shallow', 'W Mod-deep', 'W Deep', 'Sediment','L Shallow', 'L Mod-deep', 'L Deep']
    x_tick_values = [0, 0.143, 0.286, 0.429, 0.571,0.714,0.857,1.0]
    plt.xticks(x_tick_values, x_tick_labels,rotation=70, fontsize=mcmc.font+1)
    plt.legend(frameon=False, prop={'size':mcmc.font+1}, bbox_to_anchor = (1.,0.2))
    plt.savefig('%s/mcmcres.png' % (filename), bbox_inches='tight', dpi=300,transparent=False)
    plt.clf()

    #      MAKE BOX PLOT     #
    if nCommunities == 3:
        if ((sedsim == True) and (flowsim == False)) or ((sedsim == False) and (flowsim == True)):
            v_glve = np.zeros((pos_v.shape[0],3))
            v_glve[:,0:3] = pos_v[:,12:15]

            com_1=[0,3,6,9]
            com_2=[1,4,7,10]
            com_3=[2,5,8,11]
            new_v = np.zeros((pos_v.shape[0],12))
            
            for i in range(0,4):
                new_v[:,i] = pos_v[:,com_1[i]]
            for i in range(4,8):
                new_v[:,i] = pos_v[:,com_2[i-4]]
            for i in range(8,12):
                new_v[:,i] = pos_v[:,com_3[i-8]]

            mpl_fig = plt.figure(figsize=(8,4))
            ax = mpl_fig.add_subplot(111)
            ax.spines['top'].set_color('none')
            ax.spines['bottom'].set_color('none')
            ax.spines['left'].set_color('none')
            ax.spines['right'].set_color('none')
            ax.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
            ax.set_title('Posterior values', fontsize= mcmc.font+2, y=1.02)
            ax1 = mpl_fig.add_subplot(121)
            ax1.boxplot(v_glve)
            ax1.set_xlabel('GLVE parameters', size=mcmc.font+2)
            ax2 = mpl_fig.add_subplot(122)
            ax2.boxplot(new_v)
            ax2.set_xlabel('Assemblage exposure thresholds', size=mcmc.font+2)
            plt.savefig('%s/v_pos_boxplot.png'% (filename), dpi=300,transparent=False)
            plt.clf()
        elif ((sedsim == True) and (flowsim == True)):
            v_glve = np.zeros((pos_v.shape[0],3))
            v_glve[:,0:3] = pos_v[:,24:27]
            com_1=[0,3,6,9,12,15,18,21]
            com_2=[1,4,7,10,13,16,19,22]
            com_3=[2,5,8,11,14,17,20,23]

            v_sed = np.zeros((pos_v.shape[0],12))
            v_flow = np.zeros((pos_v.shape[0],12))
            for i in range(0,4):
                v_sed[:,i] = pos_v[:,com_1[i]]
            for i in range(4,8):
                v_sed[:,i] = pos_v[:,com_2[i-4]]
            for i in range(8,12):
                v_sed[:,i] = pos_v[:,com_3[i-8]]

            for i in range(0,4):
                v_flow[:,i] = pos_v[:,com_1[i+4]]
            for i in range(4,8):
                v_flow[:,i] = pos_v[:,com_2[i]]
            for i in range(8,12):
                v_flow[:,i] = pos_v[:,com_3[i-4]]


            mpl_fig = plt.figure(figsize=(14,4))
            ax = mpl_fig.add_subplot(111)
            ax.spines['top'].set_color('none')
            ax.spines['bottom'].set_color('none')
            ax.spines['left'].set_color('none')
            ax.spines['right'].set_color('none')
            ax.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
            ax.set_title('Posterior values', fontsize= mcmc.font+2, y=1.02)
            ax1 = mpl_fig.add_subplot(131)
            ax1.boxplot(v_glve)
            ax1.set_xlabel('GLVE parameters', size=mcmc.font+2)
            ax2 = mpl_fig.add_subplot(132)
            ax2.boxplot(v_sed)
            ax2.set_xlabel('Assemblage sediment exposure thresholds', size=mcmc.font+2)
            ax3 = mpl_fig.add_subplot(133)
            ax3.boxplot(v_flow)
            ax3.set_xlabel('Assemblage flow exposure thresholds', size=mcmc.font+2)
            plt.savefig('%s/v_pos_boxplot.png'% (filename), dpi=300,transparent=False)
            # mpl_fig = plt.figure(figsize=(10,4))
            # ax = mpl_fig.add_subplot(111)
            # ax.boxplot(new_v)
            # ax.set_ylabel('Posterior values')
            # ax.set_xlabel('Input vector')
            # plt.title("Boxplot of posterior distribution \nfor GLVE and threshold parameters", size=mcmc.font+2)
            # plt.savefig('%s/v_pos_boxplot.png'% (filename), dpi=300)
            # # plt.savefig('%s/v_pos_boxplot.svg'% (filename), format='svg', dpi=300)
            plt.clf()
    elif nCommunities == 6:
    	if ((sedsim == True) and (flowsim == False)) or ((sedsim == False) and (flowsim == True)):
            v_glve = np.zeros((pos_v.shape[0],3))
            v_glve[:,0:3] = pos_v[:,24:27]

            com_1=[0,6,12,18]
            com_2=[1,7,13,19]
            com_3=[2,8,14,20]
            com_4=[3,9,15,21]
            com_5=[4,10,16,22]
            com_6=[5,11,17,23]
            new_v = np.zeros((pos_v.shape[0],24))
            for i in range(0,4):
                new_v[:,i] = pos_v[:,com_1[i]]
            for i in range(4,8):
                new_v[:,i] = pos_v[:,com_2[i-4]]
            for i in range(8,12):
                new_v[:,i] = pos_v[:,com_3[i-8]]
            for i in range(12,16):
                new_v[:,i] = pos_v[:,com_4[i-12]]
            for i in range(16,20):
                new_v[:,i] = pos_v[:,com_5[i-16]]
            for i in range(20,24):
                new_v[:,i] = pos_v[:,com_6[i-20]]

            mpl_fig = plt.figure(figsize=(8,4))
            ax = mpl_fig.add_subplot(111)
            ax.spines['top'].set_color('none')
            ax.spines['bottom'].set_color('none')
            ax.spines['left'].set_color('none')
            ax.spines['right'].set_color('none')
            ax.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
            ax.set_title('Posterior values', fontsize= mcmc.font+2, y=1.02)
            ax1 = mpl_fig.add_subplot(121)
            ax1.boxplot(v_glve)
            ax1.set_xlabel('GLVE parameters', size=mcmc.font+2)
            ax2 = mpl_fig.add_subplot(122)
            ax2.boxplot(new_v)
            ax2.set_xlabel('Assemblage exposure thresholds', size=mcmc.font+2)
            plt.savefig('%s/v_pos_boxplot.png'% (filename), dpi=300,transparent=False)
            # for i in range(3,7):
            #     new_v[:,i] = pos_v[:,com_1[i-3]]
            # for i in range(7,11):
            #     new_v[:,i] = pos_v[:,com_2[i-7]]
            # for i in range(11,15):
            #     new_v[:,i] = pos_v[:,com_3[i-11]]

            # mpl_fig = plt.figure(figsize=(6,4))
            # ax = mpl_fig.add_subplot(111)
            # print 'pos_v.size',pos_v.size, 'pos_v.shape',pos_v.shape
            # ax.boxplot(new_v)
            # ax.set_ylabel('Posterior values')
            # ax.set_xlabel('Input vector')
            # plt.title("Boxplot of posterior distribution \nfor GLVE and threshold parameters", size=mcmc.font+2)
            # plt.savefig('%s/v_pos_boxplot.png'% (filename), dpi=300)
            # plt.savefig('%s/v_pos_boxplot.svg'% (filename), format='svg', dpi=300)
            plt.clf()
        elif ((sedsim == True) and (flowsim == True)):
            v_glve = np.zeros((pos_v.shape[0],3))
            v_glve[:,0:3] = pos_v[:,48:51]

            com_1=[0,6,12,18,24,30,36,42]
            com_2=[1,7,13,19,25,31,37,43]
            com_3=[2,8,14,20,26,32,38,44]
            com_4=[3,9,15,21,27,33,39,45]
            com_5=[4,10,16,22,28,34,40,46]
            com_6=[5,11,17,23,29,35,41,47]
            v_sed = np.zeros((pos_v.shape[0],24))
            v_flow = np.zeros((pos_v.shape[0],24))

            for i in range(0,4):
                v_sed[:,i] = pos_v[:,com_1[i]]
            for i in range(4,8):
                v_sed[:,i] = pos_v[:,com_2[i-4]]
            for i in range(8,12):
                v_sed[:,i] = pos_v[:,com_3[i-8]]
            for i in range(12,16):
                v_sed[:,i] = pos_v[:,com_4[i-12]]
            for i in range(16,20):
                v_sed[:,i] = pos_v[:,com_5[i-16]]
            for i in range(20,24):
                v_sed[:,i] = pos_v[:,com_6[i-20]]

            for i in range(0,4):
                v_flow[:,i] = pos_v[:,com_1[i+4]]
            for i in range(4,8):
                v_flow[:,i] = pos_v[:,com_2[i]]
            for i in range(8,12):
                v_flow[:,i] = pos_v[:,com_3[i-4]]
            for i in range(12,16):
                v_flow[:,i] = pos_v[:,com_4[i-8]]
            for i in range(16,20):
                v_flow[:,i] = pos_v[:,com_5[i-12]]
            for i in range(20,24):
                v_flow[:,i] = pos_v[:,com_6[i-16]]


            mpl_fig = plt.figure(figsize=(18,4))
            ax = mpl_fig.add_subplot(111)
            ax.spines['top'].set_color('none')
            ax.spines['bottom'].set_color('none')
            ax.spines['left'].set_color('none')
            ax.spines['right'].set_color('none')
            ax.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
            ax.set_title('Posterior values', fontsize= mcmc.font+2, y=1.02)
            ax1 = mpl_fig.add_subplot(131)
            ax1.boxplot(v_glve)
            ax1.set_xlabel('GLVE parameters', size=mcmc.font+2)
            ax2 = mpl_fig.add_subplot(132)
            ax2.boxplot(v_sed)
            ax2.set_xlabel('Assemblage sediment exposure thresholds', size=mcmc.font+2)
            ax3 = mpl_fig.add_subplot(133)
            ax3.boxplot(v_flow)
            ax3.set_xlabel('Assemblage flow exposure thresholds', size=mcmc.font+2)
            plt.savefig('%s/v_pos_boxplot.png'% (filename), dpi=300,transparent=False)
            # mpl_fig = plt.figure(figsize=(10,4))
            # ax = mpl_fig.add_subplot(111)
            # ax.boxplot(new_v)
            # ax.set_ylabel('Posterior values')
            # ax.set_xlabel('Input vector')
            # plt.title("Boxplot of posterior distribution \nfor GLVE and threshold parameters", size=mcmc.font+2)
            # plt.savefig('%s/v_pos_boxplot.pdf'% (filename), dpi=300)
            # # plt.savefig('%s/v_pos_boxplot.svg'% (filename), format='svg', dpi=300)
            plt.clf()
    mcmc.plot_results(pos_m, pos_ax, pos_ay, pos_sed1, pos_sed2, pos_sed3, pos_sed4, pos_flow1, pos_flow2, pos_flow3, pos_flow4,burnin)
    print 'Finished simulations'
if __name__ == "__main__": main()