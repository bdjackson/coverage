#!/usr/bin/env python
# =============================================================================

import sys
import os.path
import optparse
import time

import random

import numpy as np

import ROOT
import rootlogon
import metaroot

# =============================================================================
def plot_coverage_probability(s_max, n_trials):
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    random.seed(time.time())
    for s in xrange(s_max):
        prob = 0.
        for t in xrange(n_trials):
            # N = random.
            # l,u = interval_generator()
            pass

# =============================================================================
def main():
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    plot_coverage_probability(10, 1000)

# =============================================================================
if __name__ == '__main__':
    main()
