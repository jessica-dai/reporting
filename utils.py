import numpy as np
import pandas as pd

"""
    actual_reports: df of all reports. each row is an individual report; 
    columns include the features that define groups 

    all_groups_dict: list of all groups (as dictionaries) to test for. all_groups_dict[i] gives the ith group, e.g. `{feature1: value1, feature2: value2, ...}`

    base_groups: base rates, i.e. Pr[G] in terms of all loan applicants, all vaccine recipients, etc.
"""

def _get_group_idx(group, db):
    """
    group: a dictionary of features and values that define a group e.g. `{feature1: value1, feature2: value2, ...}`
    db: the databse to look up
    """
    cdb = db.copy(deep=True)
    for key in group.keys(): 
        cdb = cdb.loc[(cdb[key] == group[key])]
    return cdb.index

def get_flagged_groups(reports, group_dicts, base_rates, BETA=1.5):
    """
    Returns indices of groups that are flagged as having significantly higher reporting rates than the base rates (rather than as frozensets. )
    """
    report_rates = np.array([len(_get_group_idx(group, reports)) for group in group_dicts])/len(reports)
    all_ratios = report_rates / base_rates
    flag_groups = np.where((all_ratios > BETA))[0]
    return flag_groups

def get_group_report_rate(reports, group):
    return len(_get_group_idx(group, reports))/len(reports)

def get_rows_where(group, data, keys):
    idx = _get_group_idx(group, data)
    group_df = data.iloc[idx]
    for key in keys:
        group_df = group_df[group_df[key] == keys[key]]
    return group_df

def compute_logwealth(mug, beta, mug0, verbose=False):
    """
    Compute expected log-wealth. Expects scalar inputs.
    """
    betamug0 = beta*mug0
    lambda_opt = np.clip((mug - betamug0)/(betamug0*(1 - mug0)), 0, 1)
    if lambda_opt == 1:
        if verbose:
            print('lambda_opt = 1')
        return lambda_opt, mug*np.log(1 + 1/(1 - betamug0)) + np.log(1 - betamug0)
    elif lambda_opt == 0:
        if verbose:
            print('lambda_opt = 0')
        return lambda_opt, 0
    else:
        if verbose:
            print('lambda_opt =', lambda_opt)
        return lambda_opt, mug*np.log((1/betamug0 - 1)*mug - (1-beta)*mug0) + (1-mug)*np.log((1 - mug) - (1-beta)*mug0) - np.log(1 - mug0)