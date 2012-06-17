#!/usr/bin/env python
# =============================================================================

import sys
import os.path
import optparse
import time

import array
import math
import numpy as np

import ROOT
import rootlogon
import metaroot

# =============================================================================
template_num_trials = 10000
poisson_template_spacing = 0.1
# poisson_template_spacing = 0.01
poisson_templates = {}
cumulative_poisson_templates = {}

# =============================================================================
def generate_poisson_templates(s):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # print 'generating poisson template for s: %s' % s
    if not s in poisson_templates:
        trials = np.random.poisson(s, template_num_trials)
        trials.sort()

        # construct bin probabilities
        poisson_templates[s] = [0]*(trials[-1]+1)
        for tr in trials:
            poisson_templates[s][tr] += 1./template_num_trials

        # construct cumulative probabilities
        cumulative_poisson_templates[s] = [0.]*len(poisson_templates[s])
        for i in xrange(len(cumulative_poisson_templates[s])):
            # print poisson_templates[s]
            for j in xrange(0, i+1):
                cumulative_poisson_templates[s][i] += poisson_templates[s][j]

# -----------------------------------------------------------------------------
def get_poisson_prob(test_stat, mean):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # prob = mean^test_stat * exp(-mean)/(test_stat!)
    prob = mean**test_stat * math.exp(-mean)/(math.factorial(test_stat))
    return prob

# -----------------------------------------------------------------------------
def get_cumulative_prob(test_stat, mean):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # prob = mean^test_stat * exp(-mean)/(test_stat!)
    cum_prob = 0.
    for i in xrange(test_stat+1):
        cum_prob += get_poisson_prob(i, mean)
    return cum_prob

# -----------------------------------------------------------------------------
def find_test_bin(t, points_per_bin):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    tb = int(t*points_per_bin)
    return tb

# -----------------------------------------------------------------------------
# def root_n_interval(t, sample_points):
def root_n_interval(t, points_per_bin):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    width = math.sqrt(t)
    return (t - width, t+width)

# -----------------------------------------------------------------------------
def central_interval(t, points_per_bin):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    test_bin = find_test_bin(t, points_per_bin)

    l = -1
    u = -1

    # search for upper bound
    i = -1
    while u == -1:
        i += 1
        # test_paramer = i*poisson_template_spacing
        test_paramer = i
        # test_prob = get_poisson_prob(t, test_paramer)

        cumulative_prob = get_cumulative_prob(i, t)

        # if cumulative_prob > 0.16:
        if cumulative_prob < 0.84:
            u = test_paramer

        u += 1

    # search for lower bound
    i = -1
    while l == -1:
        i += 1
        # test_paramer = i*poisson_template_spacing
        test_paramer = i
        # test_prob = get_poisson_prob(t, test_paramer)

        cumulative_prob = get_cumulative_prob(i, t)

        if cumulative_prob < 0.16:
            l = test_paramer

        l += 1

    return (l, u)

# -----------------------------------------------------------------------------
def feldman_cousins_interval(t):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    return 1

# -----------------------------------------------------------------------------
def mode_centered_interval(t):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    return 1

# -----------------------------------------------------------------------------
def plot_coverage_probability(s_max, points_per_bin, n_trials):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    interval_generators = { 'central':central_interval
                          , 'root(n)':root_n_interval
                          # , 'feldman-cousins':feldman_cousins_interval
                          # , 'mode':mode_centered_interval
                          }

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    num_points = s_max*points_per_bin + 1
    sample_points = range(num_points)
    sample_points = [float(x)/points_per_bin for x in sample_points]
    print 'sample_points: %s' % sample_points
    print 'points_per_bin: %s' % points_per_bin

    l_profile = {}
    u_profile = {}
    prob = {}

    for ig in interval_generators:
        l_profile[ig] = [0.]*num_points
        u_profile[ig] = [0.]*num_points
        prob[ig]      = [0.]*num_points

    for s_itr, s in enumerate(sample_points):
        # print '------------------------------------------------------'
        # if not s == 4: continue
        for i in xrange(n_trials):
            t = np.random.poisson(s)
            for ig in prob:
                this_gen = interval_generators[ig]
                l,u = this_gen(t, points_per_bin)
                print '------------------------------------------------------'
                print 's; %s - t: %s - l: %s - u: %s' % (s,t,l,u)
                l_profile[ig][s_itr] += float(l)/n_trials
                u_profile[ig][s_itr] += float(u)/n_trials
                if s >= l and s <= u:
                    prob[ig][s_itr] += 1./n_trials

    draw_probabilities(prob, sample_points)
    draw_profiles(l_profile, u_profile, sample_points)

# -----------------------------------------------------------------------------
def draw_probabilities(coverage_prob, sample_points):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    num_points = len(sample_points)
    c = ROOT.TCanvas('prob')
    frame = ROOT.TH2F( 'dummy_frame_prob'
                     , 'coverage probability ; Poisson parameter ; Coverage probability'
                     , 1, 0, sample_points[-1]
                     , 1, 0, 1.05
                     )
    frame.Draw()
    line = ROOT.TLine(0, 0.68, num_points, 0.68)
    line.SetLineStyle(ROOT.kDashed)
    line.Draw('L')

    g_coverage_prob = [line]
    labels = ['68% reference']
    for i, key in enumerate(coverage_prob):
        print 'drawing coverage probability for %s' % key
        labels.append(key)
        g_coverage_prob.append( ROOT.TGraph( num_points
                                           , array.array('d', sample_points)
                                           , array.array('d', coverage_prob[key])
                                           )
                              )
        g_coverage_prob[-1].SetLineWidth(2)
        g_coverage_prob[-1].SetLineColor(i+2)
        g_coverage_prob[-1].Draw('LSAME')

    leg = metaroot.hist.make_legend( g_coverage_prob
                                   , labels
                                   , ['L']*len(labels)
                                   , x1 = 0.6
                                   , x2 = 0.8
                                   , y1 = 0.2
                                   , y2 = 0.5
                                   )
    leg.Draw()
    c.Print('coverage_prob.png')

# -----------------------------------------------------------------------------
def draw_profiles(l_profile, u_profile, sample_points):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    num_points = len(sample_points)

    ref_line = ROOT.TLine(0, 0, sample_points[-1], sample_points[-1])
    ref_line.SetLineStyle(ROOT.kDashed)
    ref_line.SetLineColor(2)

    for i, key in enumerate(l_profile):
        print 'drawing profiles for %s' % key
        print '\tpoints (%d): %s'    % (len(sample_points) , sample_points)
        print '\tl profile (%d): %s' % (len(l_profile[key]), l_profile[key])
        print '\tu profile (%d): %s' % (len(u_profile[key]), u_profile[key])
        c = ROOT.TCanvas('profiles_%s' % key)
        frame = ROOT.TH2F( 'dummy_frame_profile'
                         , 'average profiles for %s ; Observed range ; Poisson parameter' % key
                         , 1, 0, sample_points[-1]+0.5
                         , 1, 0, 2*sample_points[-1]
                         )
        frame.Draw()
        ref_line.Draw('LSAME')

        g_l_profile = ROOT.TGraph( num_points
                                 , array.array('d', sample_points)
                                 , array.array('d', l_profile[key])
                                 )
        g_u_profile = ROOT.TGraph( num_points
                                 , array.array('d', sample_points)
                                 , array.array('d', u_profile[key])
                                 )
        g_l_profile.SetLineWidth(2)
        g_u_profile.SetLineWidth(2)

        g_l_profile.SetLineColor(3)
        g_u_profile.SetLineColor(4)

        g_l_profile.Draw('LSAME')
        g_u_profile.Draw('LSAME')

        leg = metaroot.hist.make_legend( [ref_line, g_u_profile, g_l_profile]
                                       , ['45^{o} reference', 'upper', 'lower']
                                       , ['L']*3
                                       , x1 = 0.2
                                       , x2 = 0.4
                                       , y1 = 0.7
                                       , y2 = 0.9
                                       )
        leg.Draw()

        c.Print('profiles_%s.png' % key)

# =============================================================================
def main():
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # plot_coverage_probability(20, 10, 1000)
    # plot_coverage_probability(10, 10, 1000)
    # plot_coverage_probability(3, 10, 1000)
    plot_coverage_probability(5, 2, 100)

# =============================================================================
if __name__ == '__main__':
    main()
