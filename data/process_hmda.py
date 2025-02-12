import sys 

import numpy as np
import pandas as pd
import pickle

from process_hmda_markup import markup_categorize_data, markup_clean_data
from preprocess_utils import get_groups, save_preprocessed

sys.path.append('..')
from utils import _get_group_idx

MARKUP_CLEANED_FILENAME = ''


###################################################
# Run scripts from Markup preprocessing 
###################################################

markup_clean_data()
markup_categorize_data(clean2_filename=MARKUP_CLEANED_FILENAME)

all_data = pd.read_csv(MARKUP_CLEANED_FILENAME)

###################################################
# Filter to specific types of loans, reduce columns
#
# If you want to (e.g.) define a reporting model that incorporates additional columns, 
# modify this section to include those columns.
###################################################

# To define groups $G$, we want to keep the following columns. 
# * `app_race_ethnicity` 
# * `applicant_sex_cat`
# * `applicant_age`

# To determine allocations $A$, we want to keep `loan_outcome` column. 

# To define ``worthiness'' $Z$, we use the `dti_cat` (debt-to-income-ratio) column. 

# Finally, we filter by:
# * three lending institutions `lei`
# * positive income 
# * conventional loans
# * either loan made or denied 

# We keep the following columns for now because they could be useful in the future: 
# * `interest_rate` 
# * `combined_loan_to_value_ratio`

all_data['income'] = pd.to_numeric(all_data['income'])

all_data = all_data[(all_data['loan_type'] == 1) & (all_data['income'] > 0) & ((all_data['loan_outcome'] == 1) | (all_data['loan_outcome'] == 3))].copy()

hmda19_df3 = all_data[(all_data['prop_value_cat'] != 7) & (all_data['mortgage_term'] != 4) &\
                        (all_data['dti_cat'] != 6) & (all_data['dti_cat'] != 6) &\
                        (all_data['downpayment_flag'] != '3') & (all_data['lmi_def'] != 5)].copy()
hmda19df3 = hmda19_df3[hmda19_df3['combined_loan_to_value_ratio'] != 'Exempt']
hmda19df3['combined_loan_to_value_ratio'] = pd.to_numeric(hmda19df3['combined_loan_to_value_ratio'])

hmda19_df4 = hmda19df3[(hmda19df3['combined_loan_to_value_ratio'] <= 100)]
keep_cols = ['app_race_ethnicity', 'applicant_sex_cat', 'applicant_age', 'loan_outcome', 'dti_cat', 
            #  'lei', 
             'interest_rate', 'combined_loan_to_value_ratio']
hmda19_df5 = hmda19_df4[keep_cols]
hmda19_df5 = hmda19_df5.rename(columns= {
    'app_race_ethnicity': 'race',
    'applicant_sex_cat': 'sex',
    'dti_cat': 'dti',
    'applicant_age': 'age'
})

del all_data
del hmda19df3
del hmda19_df4

###################################################
# Rename values of demographic & outcome columns 
###################################################

race_map = { # app_race_ethnicity
    1: 'native',
    2: 'asian',
    3: 'black',
    4: 'pac-i',
    5: 'white',
    6: 'latino'
}
sex_map = { # applicant_sex_cat
    1: 'm',
    2: 'f',
    3: 'nb' # both or n/a
}
dti_map = { #dti_cat
    1: 'healthy',
    2: 'manageable',
    3: 'unmanageable',
    4: 'struggling' 
}

outcome_map = {
    1: 'Approved',
    3: 'Denied'
}

hmda19_df5['race'] = hmda19_df5['race'].map(race_map)
hmda19_df5['sex'] = hmda19_df5['sex'].map(sex_map)
hmda19_df5['dti'] = hmda19_df5['dti'].map(dti_map)
hmda19_df5['loan_outcome'] = hmda19_df5['loan_outcome'].map(outcome_map)
hmda19_df5['interest_rate'] = hmda19_df5['interest_rate'].fillna(-1)
hmda19_df5 = hmda19_df5.dropna() # should have 74k 

###################################################
# Set up groups and compute base rates
###################################################
dem_cols = ['sex', 'race', 'age']
dem_vals = [hmda19_df5[col].unique().tolist() + [None] for col in dem_cols]

all_groups_dict = get_groups(dem_vals, dem_cols)

base_group_rate = np.array([len(_get_group_idx(group, hmda19_df5))/len(hmda19_df5) for group in all_groups_dict])

# only keep groups that are sufficiently big overall
nonzero_rate = base_group_rate[base_group_rate > 0.001] 
nonzero_groups = np.array(all_groups_dict)[base_group_rate > 0.001]

###################################################
# Set up reports. Save only denials; can filter further later.
# If you want to allow reports from those who were approved, change the filter here.
###################################################
database = hmda19_df5[hmda19_df5['loan_outcome'] == 'Denied']

###################################################
# Save everything
###################################################
save_path = 'hmda/hmda__'
save_preprocessed(database, nonzero_groups, nonzero_rate, save_path)

group_ys = []
for group in nonzero_groups:
    for key in group.keys():
        database = database[database[key] == group[key]] 
    group_ys.append(len(database[(database['loan_outcome'] == 'Denied') & (database['dti'] == 'healthy')]) / len(database))
pickle.dump(group_ys, open(save_path + 'group_ys.pkl', 'wb'))