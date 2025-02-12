import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pickle 
import argparse 

from algorithms import *
from load_data import get_data

"""
general set of all runs to do
"""
all_algorithms = \
[
    { 'name': 'eval', 'params': {'method': 'eval'}},
    # { 'name': 'sprt', 'params': {'method': 'sprt'}},
    { 'name': 'lilt', 'params': {'method': 'lil', 'asymptotic': False}},
    { 'name': 'lila', 'params': {'method': 'lil', 'asymptotic': True}}
] 

def run_one_trial(reports, group_dicts, base_rates, alphas=[0.1], beta=1.5, algorithms=None, trial=0, max_iter=40000):
    """
    ADD DOCSTRING
    """
    np.random.seed(max_iter*trial)
    trial_inds = np.random.permutation(reports.shape[0])

    algorithms = all_algorithms if algorithms is None else algorithms

    result_df = pd.DataFrame(columns=['trial', 'alpha', 'alg'])
    for alpha in alphas:
        print("--alpha=", alpha)

        for alg in algorithms:
            alg['params']['ALPHA'] = alpha
            alg['params']['BETA'] = beta
            results = run_test(reports.iloc[trial_inds], group_dicts, base_rates, **alg['params'], max_iter=max_iter)
            results['trial'] = trial
            results['alpha'] = alpha
            results['alg'] = alg['name']
            result_df = pd.concat([result_df, results], ignore_index=True)
    
    return result_df

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--N_TRIALS', type=int, default=10)
    parser.add_argument('--BETA', type=float, default=1.5)
    parser.add_argument('--DATASET', type=str, default='folktables')
    parser.add_argument('--ALPHAS', type=str, default='0.1')

    args = parser.parse_args()

    reports, group_dicts, base_rates = get_data(args.DATASET)

    N_TRIALS = args.N_TRIALS
    BETA = args.BETA
    if args.ALPHAS == 'all':
        ALPHAS = np.linspace(0.01, 0.1, 10)
    elif args.ALPHAS == 'all_0.2':
        ALPHAS = np.linspace(0.01, 0.2, 20)
    else: 
        ALPHAS = np.array([float(args.ALPHAS)])


    main_result_df = pd.DataFrame(columns=['trial', 'alpha', 'alg'])
    for trial in np.arange(N_TRIALS):
        print(" ======== trial = ", trial) 
        main_result_df = pd.concat([main_result_df, run_one_trial(reports, group_dicts, base_rates, alphas = ALPHAS, beta = BETA, trial=trial)], ignore_index=True)

    filename = 'results/' + str(args.DATASET) + '_ntrials=' + str(N_TRIALS) + '_' + 'beta=' + str(BETA) + '_alphas=' + str(args.ALPHAS) + '.csv'
    main_result_df.to_csv(filename, index=False)