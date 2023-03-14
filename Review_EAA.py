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
from scipy.special import binom
import sys
from tqdm import tqdm

## Using rnd_seed from Review_parameters.py
np.random.seed(rnd_seed)
random.seed(rnd_seed)

## Save the initial state of the random number generator
initial_state_np = np.random.get_state()
initial_state_py = random.getstate()

########### FUNCTIONS #############


class Platform:

    ## Setup platform and product parameters 
    def __init__(self, invite_review, validate_policy, helpful_policy, select_policy, expected_rating, sample_size):   
        self.invite_review = invite_review ## Time as a proportion of the expected time required to sufficiently test use: [0,1].
        self.validate_policy = validate_policy ## Possible values: ['Only Validated', 'None']
        self.helpful_policy = helpful_policy ## Possible values: ['No Feedback', 'Positive', 'Both']
        self.select_policy = select_policy ## Possible values: ['Random', 'Most Helpful', 'Most Recent', 'Best Quality']
        self.expected_rating = expected_rating ## Ground truth value (i.e. from Which? website review): binary (0,1)
        self.total_reviews = []
        self.sample_quality = 'None'
        self.sample_fitness = 'None'
        self.sample_rating = 'None'
        self.M = sample_size
        
    def gen_position_to_know(self):
        author_pos = np.random.uniform(0,1)
        if self.validate_policy == 'Only Validated':
            validated = True
            interact_time = (np.random.uniform(self.invite_review, 1) + author_pos) / 2
        elif self.validate_policy == 'None':
            validated = False
            interact_time = (np.random.uniform(0,1) + author_pos) / 2
            author_pos = 0 ##The author will not have any review history.
        else:
            print('Validation Policy not represented.')
            sys.exit()
        feat_use = max(np.random.uniform(0,1), author_pos)
        new_review = Position_To_Know(len(self.total_reviews), interact_time, feat_use, validated, self.helpful_policy, author_pos)
        new_review.calc_Q_arg()
        new_review.calc_rating(self.expected_rating)
        self.total_reviews.append(new_review)
        return new_review
    
    def game_step(self, agent_type):
        selected_reviews = self.update_sample_attributes(agent_type)
        if np.random.uniform(0,1) <= mu:
            new_review = self.gen_position_to_know()
        else:
            agent_type.helpful_review(selected_reviews, self.helpful_policy)
        #self.calc_mean_rating()
    
    def get_review_order(self):
        assert self.select_policy in ['Random', 'Most Helpful', 'Most Recent', 'Best Quality']
        if self.select_policy == 'Most Helpful':
            self.total_reviews.sort(key=attrgetter('review_pos'), reverse=True)
        elif self.select_policy == 'Best Quality':
            self.total_reviews.sort(key=attrgetter('Q_arg'), reverse=True)
        num_total = len(self.total_reviews)
        if num_total <= self.M:
            selected_reviews = self.total_reviews                
        elif self.select_policy == 'Random':
            selected_reviews = random.sample(self.total_reviews, self.M) 
        elif self.select_policy in ['Most Helpful', 'Best Quality']:
            selected_reviews = self.total_reviews[:self.M]
        elif self.select_policy == 'Most Recent':
            selected_reviews = self.total_reviews[-self.M:]
        else:
            print("Input Select Policy not represented in above conditionals.")
            sys.exit()
        return selected_reviews
        
    def update_sample_attributes(self, agent_type):
        selected_reviews = self.get_review_order()
        num_selected = len(selected_reviews)
        assert num_selected > 0
        self.sample_quality = 0
        self.sample_fitness = 0
        self.sample_rating = 0
        for review in selected_reviews:
            if num_selected == 1:
                review.calc_zeta_arg([])
            else:
                #alt_reviews = selected_reviews.copy() ## Updated to below in accordance with paper
                #alt_reviews.remove(review) ## Updated to below in accordance with paper
                #review.calc_zeta_arg(alt_reviews) ## Updated to below in accordance with paper
                review.calc_zeta_arg(selected_reviews)
            review.calc_G_arg(selected_reviews)
            review.calc_Pi_arg()
            self.sample_quality += review.Q_arg
            self.sample_fitness += review.Pi_arg * review.rating
            self.sample_rating += review.rating
        self.sample_fitness /= num_selected
        self.sample_quality /= num_selected
        self.sample_rating /= num_selected 
        return selected_reviews
    
    """
    ## Calculates the mean rating over all available reviews.
    def calc_mean_rating(self):
        sum_rating = 0
        for review in self.total_reviews:
            sum_rating += review.rating
        self.mean_rating = sum_rating / len(self.total_reviews)
    """


## Defining the agent. Only one option at present so purely homogenous and uninteresting.
class Person_Type:
    
    ## Initial setup
    def __init__(self, id_type):        
        self.id_type = id_type ## Possible values: ["standard"]
        self.args = []
        
    ## NEEDS REWRITING IN LINE WITH PAPER. Progressing the game such that an agent selects reviews to be rated as helpful. 
    def helpful_review(self, selected_reviews, helpful_policy):  
        assert helpful_policy in ['No Feedback', 'Positive', 'Both']    
        for review in selected_reviews: 
            if review.Pi_arg > 0:
                if np.random.uniform(0,1) <= review.Pi_arg:
                    if helpful_policy in ['Positive', 'Both']:
                        review.review_pos += 1
                        review.review_net += 1
            else:
                if np.random.uniform(0,1) <= abs(review.Pi_arg):
                    if helpful_policy == 'Both':
                        review.review_neg += 1
                        review.review_net -= 1
            assert review.review_net == review.review_pos - review.review_neg
    
    
class Position_To_Know:
    
    ## Initial setup
    def __init__(self, idx, interaction_time, feature_use, validated, helpful_policy, author_pos):        
        self.idx = idx
        self.cq1 = 'None'
        self.interaction_time = interaction_time #CQ1 normalised scale value: [0, 1]
        self.feature_use = feature_use #CQ1 normalised scale value: [0, 1]
        self.cq2 = 'None'
        self.validated = validated #CQ2 binary value: (0,1)
        self.review_pos = 0 #CQ2 integer: [0, inf]
        self.review_neg = 0 #CQ2 integer: [0, inf]
        self.review_net = 0 #CQ2 integer: [0, inf]
        self.author_pos = author_pos #CQ2 value: [0,1]
        self.Q_arg = 'None' #Function of CQ1 and CQ2 for determining rating of review and reader trust.
        self.G_arg = 'None' #Function of support force, and zeta_arg (the support balance).
        self.rho_arg = 'None' #The proportion of net positive votes over the number of votes over the review set.
        self.zeta_arg = 'None' #Function of support balance, weighing the quality of the supporters vs attackers.
        self.rating = 'None' #CQ3 binary value: (0,1)
        self.Pi_arg = 'None' #Overall fitness of the review: [-1, 1]
    
    ## Calculates the rating of the review based on the quality of the argument Q_arg
    def calc_rating(self, expected_rating):
        assert self.Q_arg != 'None'
        if np.random.uniform(-1,1) <= (1 + self.Q_arg) / 2:
            self.rating = expected_rating #assuming rating: (-1, 1)
        else:
            self.rating = -expected_rating
    
    ## Calculates overall fitness of the argument.
    def calc_Pi_arg(self):
        self.Pi_arg = (self.G_arg + self.Q_arg) / 2
        #print("review net help:", self.review_net)
    
    ## Calculates Q_arg, the quality of the argument as a function of its critical questions.
    def calc_Q_arg(self):
        self.cq1_reliability()
        self.cq2_reliability()
        self.Q_arg = self.cq1 + self.cq2 - 1
        if abs(self.Q_arg) > 1:
            print('Magnitude of Q_arg > 1')
            sys.exit()
    
    ## CQ1: Is a in position to know whether A is true (false)?
    def cq1_reliability(self):
        self.cq1 = (self.interaction_time + self.feature_use) / 2
    
    ## CQ2: Is a an honest (trustworthy, reliable) source?
    ## Note that this formula has been slightly altered based on the associated paper and the
    ## commented formula is the old version.
    def cq2_reliability(self):
        #self.cq2 = (self.author_pos + (1 - D*(1 - self.validated))) / 2
        self.cq2 = (self.author_pos + (1 - D*(2 - self.validated))) / 2
    
    ## Calculates G_arg (the interaction force of the argument) as a function of its support force
    ## (as determined by its helpfulness votes), and zeta_arg (the balance of supporters vs attackers encountered).
    def calc_G_arg(self, reviews):
        self.calc_rho_arg(reviews)
        self.G_arg = (self.zeta_arg + self.rho_arg) / 2
    
    ## Calculates the proportion of the net helpful votes over the total votes over the set of reviews. 
    def calc_rho_arg(self, reviews):
        num_reviews = len(reviews)
        if num_reviews == 0:
            total_helpful = 0
            self.rho_arg = 0
        else:
            max_votes = max((instance.review_pos + instance.review_pos) for instance in reviews)
            for review in reviews:
                assert review.rating in (-1,1)
                if max_votes > 0:
                    self.rho_arg = review.review_net / max_votes
                else:
                    self.rho_arg = 0
        
    ## Calculates zeta_arg, the balance of supporters vs attackers for the argument. Supporters (resp. attackers)
    ## are simply considered to share the same conclusion (resp. rebut each other's conclusion).
    ## Note that this formula has been slightly altered based on the associated paper and the
    ## commented part pertains to the old version. 
    def calc_zeta_arg(self, selected_reviews):
        alt_reviews = selected_reviews.copy() ## Added in accordance with paper
        if len(alt_reviews) > 0:
            alt_reviews.remove(self) ## Added in accordance with paper
        num_reviews = len(alt_reviews)
        if num_reviews == 0:
            self.zeta_arg = 0
        else:
            interaction_sum = 0   
            for alt in alt_reviews: 
                #alt.calc_rho_arg(alt_reviews) ## Updated to below in accordance with paper
                alt.calc_rho_arg(selected_reviews)
                interaction_sum += alt.rating * (alt.Q_arg + alt.rho_arg) / 2
            self.zeta_arg = self.rating * interaction_sum / num_reviews
  