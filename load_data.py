
import pickle
import os.path
import pandas as pd

def get_data(dataname = 'covid'):

    if dataname == 'covid':

        return _get_covid()
    
    if dataname == 'hmda' or dataname == 'hmda_all-denials':
        
        return _get_hmda(reports='all')

    if dataname == 'hmda_hdti-denials':
        
        return _get_hmda(reports='hdti')

    if dataname == 'hmda_corr':
        
        return _get_hmda(reports='corr')

    if dataname == 'hmda_anticorr':
        
        return _get_hmda(reports='anticorr')

    return "Dataset name not found - try `covid` or `hmda`"

def _get_covid():
    if not os.path.exists('data_processed/vaers/covid__reports.csv'):
        print("Data not found - please run the preprocessing scripts in data_processed/process_covid.py first.")
        return
    
    reports = pd.read_csv('data_processed/vaers/covid__reports.csv')
    group_dicts = pickle.load(open('data_processed/vaers/covid__groups.pkl', 'rb'))
    base_rates = pickle.load(open('data_processed/vaers/covid__base_groups.pkl', 'rb'))

    return reports, group_dicts, base_rates

def _get_hmda(reports='all'):

    if not os.path.exists('data_processed/hmda/hmda__denials.csv'):
        print("Data not found - please run the preprocessing scripts in data_processed/process_hmda.py first.")
        return 
    
    all_denials = pd.read_csv('data_processed/hmda/hmda__denials.csv')
    group_dicts = pickle.load(open('data_processed/hmda/hmda__groups.pkl', 'rb'))
    base_rates = pickle.load(open('data_processed/hmda/hmda__base_rates.pkl', 'rb'))

    if reports == 'all':
        reports = all_denials
    elif reports == 'hdti':
        reports = all_denials[all_denials['dti'] == 'healthy']
    elif reports == 'corr':
        dti_to_report_rates = {
            'struggling': 0.1,
            'unmanageable': 0.3,
            'manageable': 0.5,
            'healthy': 0.9
        }

        reports = _get_corr_reports(dti_to_report_rates, all_denials)
    elif reports == 'anticorr':
        dti_to_report_rates = {
            'struggling': 0.9,
            'unmanageable': 0.7,
            'manageable': 0.5,
            'healthy': 0.1
        }

        reports = _get_corr_reports(dti_to_report_rates, all_denials)

    return reports, group_dicts, base_rates

def _get_corr_reports(dti_report_rates, all_denials):
    g = all_denials.groupby('dti')

    reports = pd.DataFrame(columns=['race', 'sex', 'age', 'dti'])

    for dti in dti_report_rates:
        dti_sampled = g.get_group(dti).sample(frac=dti_report_rates[dti], random_state=0)
        reports = pd.concat([reports, dti_sampled[['race', 'sex', 'age', 'dti']]], ignore_index=True)

    return reports.sample(frac=1, random_state=0) 
