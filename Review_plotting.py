# -*- coding: utf-8 -*-
"""
Created on Mon Feb 15 22:06:51 2021

@author: stefa + Truffles

Evolutionary game for the emergence of reviews for a prescribed product domain (some specific camera). 
These emergent reviews are collectively evaluated against a ground-truth review from Which? magazine.
The motivation for the evaluation is to identify conditions under which the emergent reviews are more or
less likely to be aligned with the ground-truth. Such conditions, can suggest ways to construct
reliable review platforms (or unreliable platforms). This version (v1-0) does not enable to platform
to vary the helpful_policy which is assumed to have the value "Pos".

Consider evaluating under three types of agent setups:
1. Agents examine M most recent reviews.
2. Agents examine M most helpful reviews.
3. Agents examine a mixture of M reviews by rating.

Other ideas:
1. How number, quality, and positivity of reviews influences user engagement and purchase.

*Argument From Position To Know*
CQ1: Is a in position to know whether A is true (false)?
CQ2: Is a an honest (trustworthy, reliable) source?
CQ3: Did a assert that A is true (false)?

*Argument From Popular Opinion*
CQ1: What evidence like a poll or an appeal to common knowledge, supports
the claim that A is generally accepted as true?
CQ2: Even if A is generally accepted as true, are there any good reasons for
doubting that it is true?
"""

############## Voluntary Argumentation Game ######################

from __future__ import division
import math
import matplotlib.pyplot as plt
import numpy as np
import random
from numpy import exp
from operator import attrgetter
import os
import pandas as pd
from Review_parameters import *
import Review_EAA as EAA
from scipy.special import binom
import sys
from tqdm import tqdm

## Using rnd_seed from Review_parameters.py
np.random.seed(rnd_seed)
random.seed(rnd_seed)

## Save the initial state of the random number generator
initial_state_np = np.random.get_state()
initial_state_py = random.getstate()
  
## Produces the iterations of the evolutionary game and records results for analysis
def run_experiments(analysis_type, initial_state_np, initial_state_py):

    ## Getting results for metrics based on experiment setup.
    def get_results(variable, validate_policy):

        ## invite_review, and expected_rating are regarded as fixed parameters
        invite_review = 0.1 
        expected_rating = 1
        
        ## Variable Policy setup
        select_policy = 'Best Quality'
        helpful_policy = 'Positive'
        sample_size = 5
        if variable == 'Select Policy':
            variable_policies = ['Random', 'Most Helpful', 'Most Recent', 'Best Quality']
        elif variable == 'Helpful Policy':
            variable_policies = ['No Feedback', 'Positive', 'Both']
        elif variable == 'Sample Policy':
            variable_policies = [2, 5, 10, 20]
        else:
            print('Variable Policy not represented')
            sys.exit()
        
        ## Initialising metric dataframes.
        quality_df = pd.DataFrame(columns=['No. Reviews'])
        fitness_df = pd.DataFrame(columns=['No. Reviews'])
        rating_df = pd.DataFrame(columns=['No. Reviews'])
        #print('Variable policies:', variable_policies)
        
        for policy in variable_policies:   
            np.random.set_state(initial_state_np)
            random.setstate(initial_state_py)
            #print('Policies:', policy)
            
            ## Creating the Platform for the experiment and running through the iterations T.
            if variable == 'Validate Policy':
                Platform_x = EAA.Platform(invite_review, policy, helpful_policy, select_policy, expected_rating, sample_size)
            elif variable == 'Select Policy':
                Platform_x = EAA.Platform(invite_review, validate_policy, helpful_policy, policy, expected_rating, sample_size)
            elif variable == 'Helpful Policy':
                Platform_x = EAA.Platform(invite_review, validate_policy, policy, select_policy, expected_rating, sample_size)
            elif variable == 'Sample Policy':
                Platform_x = EAA.Platform(invite_review, validate_policy, helpful_policy, select_policy, expected_rating, policy)
            else:
                print('Variable Policy not represented')
                sys.exit()
            new_review = Platform_x.gen_position_to_know()
            num_reviews = []
            qualities = []
            fitnesses = []
            ratings = []
            for t in tqdm(range(T)):
                Platform_x.game_step(Homunculus)
                num_reviews.append(len(Platform_x.total_reviews))
                qualities.append(Platform_x.sample_quality)
                fitnesses.append(Platform_x.sample_fitness)
                ratings.append(Platform_x.sample_rating)
            fitness_df[policy] = fitnesses
            rating_df[policy] = ratings
            quality_df[policy] = qualities
        fitness_df['No. Reviews'] = rating_df['No. Reviews'] = quality_df['No. Reviews'] = num_reviews 
        return fitness_df, rating_df, quality_df, validate_policy

    ## Make plot for a particular experiment on a particular metric and save df to file.
    def make_line_plot(metric_type, variable, validate_policy):
    
        ## Loading appropriate dataframe.
        if metric_type == 'Quality':
            metric_df = quality_df
        elif metric_type == 'Fitness':
            metric_df = fitness_df
        elif metric_type == 'Rating':
            metric_df = rating_df 
        else:
            print('Unexpected metric_type for analysis')
            sys.exit()
        
        ## Saving metric dataframe to csv and setting up plot.
        metric_df.to_csv(os.path.join('Results', 'line_plot', 'line_plot_%s_%s_%s_DF.csv'%(variable, validate_policy, metric_type)), index=False)
        metric_df.drop('No. Reviews', axis=1, inplace=True)
        metric_df.plot() 
        plt.title('Sample %s'%(metric_type))
        plt.xlabel('Iteration')
        plt.ylabel('%s Value'%(metric_type))
        plt.ylim(-1, 1)
            
        ## Showing and saving plot.
        #file_plot = os.path.join('Results', 'line_plot', 'line_plot_%s_%s_%s.png'%(variable, validate_policy, metric_type))
        #plt.savefig(file_plot)
        plt.show()
        return
    

    ## Make plot for a particular experiment on a particular metric and save df to file.
    def make_box_plot(metric_type, variable, validate_policy):
    
        ## Loading appropriate dataframe.
        if metric_type == 'Quality':
            metric_df = box_quality_df
        elif metric_type == 'Fitness':
            metric_df = box_fitness_df
        else:
            print('Unexpected metric_type for analysis')
            sys.exit()
        
        ## Saving metric dataframe to csv and setting up plot.
        metric_df.to_csv(os.path.join('Results', 'box_plot', 'box_plot_%s_%s_%s_DF.csv'%(variable, validate_policy, metric_type)), index=False)
        boxplot = metric_df.boxplot(grid=False)  

        plt.title('Sample %s'%(metric_type))
        plt.ylabel('%s Value'%(metric_type))
        plt.ylim(-1, 1)

        ## Showing and saving plot.
        file_plot = os.path.join('Results', 'box_plot', 'box_plot_%s_%s_%s.png'%(variable, validate_policy, metric_type))
        plt.savefig(file_plot)
        plt.show()
        return
    
    ## Selecting and analysing the metrics
    Homunculus = EAA.Person_Type("standard")
    
    ## Line plot analysis
    if analysis_type == 'line plots':
        
        ## Validate Policy must be specified
        validate_policy = 'Only Validated'
    
        ## Choose variable for analysis 
        #variable = 'Helpful Policy'
        variable = 'Select Policy'
        #variable = 'Sample Policy'
        
        ## Produce analysis and line plots
        fitness_df, rating_df, quality_df, validate_policy = get_results(variable, validate_policy)
        metrics = ['Quality', 'Fitness']
        for metric_type in metrics:
            make_line_plot(metric_type, variable, validate_policy)
    
    ## Box plot analysis
    elif analysis_type == 'box plots':
        
        ## Validate Policy must be specified in ['Only Validated', 'None']
        validate_policy = 'Only Validated'
        """
        ## Set Helpful policy for analysis 
        variable = 'Helpful Policy'
        box_quality_df = pd.DataFrame(columns=['No Feedback', 'Positive', 'Both'])
        box_fitness_df = pd.DataFrame(columns=['No Feedback', 'Positive', 'Both'])
        """
        ## Set Select policy for analysis 
        variable = 'Select Policy'
        box_quality_df = pd.DataFrame(columns=['Random', 'Most Helpful', 'Most Recent', 'Best Quality'])
        box_fitness_df = pd.DataFrame(columns=['Random', 'Most Helpful', 'Most Recent', 'Best Quality'])
        """
        ## Set Sample policy for analysis 
        variable = 'Sample Policy'
        box_quality_df = pd.DataFrame(columns=[2, 5, 10, 20])
        box_fitness_df = pd.DataFrame(columns=[2, 5, 10, 20])
        """
        for seed in tqdm(range(1,50)):
            np.random.seed(seed)
            random.seed(seed)
            initial_state_np = np.random.get_state()
            initial_state_py = random.getstate() 
            fitness_df, rating_df, quality_df, validate_policy = get_results(variable, validate_policy)
            fitness_df.drop('No. Reviews', axis=1, inplace=True)
            quality_df.drop('No. Reviews', axis=1, inplace=True)
            box_fitness_df = pd.concat([box_fitness_df, fitness_df.tail(1)], ignore_index=True)
            box_quality_df = pd.concat([box_quality_df, quality_df.tail(1)], ignore_index=True)
                      
        metrics = ['Quality', 'Fitness']
        for metric_type in metrics:
            make_box_plot(metric_type, variable, validate_policy)
    else:
        print('analysis type not represented')
        sys.exit()
    return

## Takes 'line plots' or 'box plots' as input.
run_experiments('line plots', initial_state_np, initial_state_py)
