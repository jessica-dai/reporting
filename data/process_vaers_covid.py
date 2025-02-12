# Preprocess the VAERS database.

import sys
import os
import pickle 

import numpy as np
from numpy import nan
import pandas as pd
import matplotlib.pyplot as plt
from itertools import product
import seaborn as sns


from datetime import datetime
from preprocess_utils import get_groups, save_preprocessed

sys.path.append('..')
from utils import _get_group_idx

def inc_get_group_count(group, db, survey=0):
    cdb = db.copy(deep=True)
    for key in group.keys(): 
        cdb = cdb.loc[(cdb[key] == group[key])]  
    return cdb.shape[0]

def inc_get_cat_count(group, db, survey=0):
    cdb = db.copy(deep=True)
    return cdb.shape[0]

###################################################
# Settings 
###################################################



###################################################
# Load data 
###################################################'

## Download Base Data 

HOME_DIR = ""

#Download from data sources
#Child: https://data.cdc.gov/Vaccinations/National-Immunization-Survey-Child-COVID-Module-NI/uny6-e3dx/about_data
#Adult: https://data.cdc.gov/Vaccinations/National-Immunization-Survey-Adult-COVID-Module-NI/udsf-9v7b/about_data

base_child = pd.read_csv(HOME_DIR + "National_Immunization_Survey_Child_COVID_Module__NIS-CCM___COVIDVaxViews__Data___Centers_for_Disease_Control_and_Prevention__cdc.gov_-Archived_20240515.csv")
base_adult = pd.read_csv(HOME_DIR + "/incidents/data_downloads/VAERS_Vaccine/National_Immunization_Survey_Adult_COVID_Module__NIS-ACM___COVIDVaxViews__Data___Centers_for_Disease_Control_and_Prevention__cdc.gov_-Archived_20240515.csv")

##Download Incident Data 

VAERS_path = HOME_DIR + "/Incident/VAERS_Vaccine/Incident/"

df_catalog = dict()

for filename in os.listdir(VAERS_path):
    full_filename = os.path.join(VAERS_path, filename)
    print(filename)
    df_catalog[filename] = {"df": pd.read_csv(full_filename, encoding = "ISO-8859-1", low_memory=False)}

years_included = dict()


#for each year, upload VAERSDATA, VAERSSYMPTOMS, VAERSVAX
for item in df_catalog.keys():
    year = int(item[:4])
    if year in years_included.keys():
        item_name = item[9:-4]
        years_included[year][item_name] = df_catalog[item]
    else:
        item_name = item[9:-4]
        years_included[year] = {item_name: df_catalog[item]}

df_vax_total = pd.DataFrame()
for year in range(1990, 2025):
    #add columns across available feature tables
    df_vax_raw = pd.merge(years_included[year]['VAX']['df'], years_included[year]['DATA']['df'], on="VAERS_ID", how='outer')
    df_vax_raw = pd.merge(df_vax_raw, years_included[year]['SYMPTOMS']['df'], on="VAERS_ID", how='outer')
    #add rows across the years
    df_vax_total = pd.concat([df_vax_total, df_vax_raw])

#save to csv 
df_vax_total.to_csv('total_incident_vaccine.csv', index=False)

###################################################
# Clean data
###################################################

## Base data

#Look at National Adult samples with more than one dose 
fb_adf = base_adult.loc[base_adult["Geography Type"] == "National Estimates"] 
fb_adf = fb_adf.loc[fb_adf["Indicator Category"] == "Vaccinated (>=1 dose)"]
fb_adf["Count"] = ((fb_adf["Estimate (%)"].astype(float)/100)*fb_adf["Sample Size"]).astype(int)

#Take subset of National Adult samples for which we have age values 
fb_adf_age = fb_adf.loc[fb_adf["Group Name"] == "Age"]
fb_adf_age.drop('Indicator Name', axis=1, inplace=True)
fb_adf_age.drop('95% CI (%)', axis=1, inplace=True)
fb_adf_age.drop('Suppression Flag ', axis=1, inplace=True)
fb_adf_age = fb_adf_age.drop_duplicates()

fb_adf_age = fb_adf_age[fb_adf_age['Time Type'] != "Monthly"]

#Take subset of National Adult samples for which we have sex values 
fb_adf_sex = fb_adf.loc[fb_adf["Group Name"] == "Sex"]
fb_adf_sex.drop('Indicator Name', axis=1, inplace=True)
fb_adf_sex.drop('95% CI (%)', axis=1, inplace=True)
fb_adf_sex.drop('Suppression Flag ', axis=1, inplace=True)
fb_adf_sex = fb_adf_sex.drop_duplicates()

fb_adf_sex = fb_adf_sex[fb_adf_sex['Time Type'] != "Monthly"]
fb_adf_sex["Age Range"] = "18+"

#Look at National Child samples with more than one dose 
fb_cdf = base_child.loc[base_child["Geography Type"] == "National Estimates"] 
fb_cdf = fb_cdf.loc[fb_cdf["Indicator Category"] == 'Vaccinated (>=1 dose)']
fb_cdf["Count"] = ((fb_cdf["Estimate (%)"].astype(float)/100)*fb_cdf["Sample Size"]).astype(int)

#Take subset of National Child samples for which we have age values 
fb_cdf_age = fb_cdf.loc[fb_cdf["Group Name"] == 'Age']
fb_cdf_age.drop('Indicator Name', axis=1, inplace=True)
fb_cdf_age.drop('95% CI', axis=1, inplace=True)
fb_cdf_age.drop('Suppression Flag', axis=1, inplace=True)
fb_cdf_age.drop('Age Range', axis=1, inplace=True)
fb_cdf_age = fb_cdf_age.drop_duplicates()

fb_cdf_age = fb_cdf_age[fb_cdf_age['Group Category'] != "6 months-1 year"]
fb_cdf_age = fb_cdf_age[fb_cdf_age['Group Category'] != "2-4 years"]

#Take subset of National Child samples for which we have sex values 
fb_cdf_sex = fb_cdf.loc[fb_cdf["Group Name"] == 'Sex']
fb_cdf_sex.drop('Indicator Name', axis=1, inplace=True)
fb_cdf_sex.drop('95% CI', axis=1, inplace=True)
fb_cdf_sex.drop('Suppression Flag', axis=1, inplace=True)
#fb_cdf_sex.drop('Age Range', axis=1, inplace=True)
fb_cdf_sex = fb_cdf_sex.drop_duplicates()

fb_cdf_sex = fb_cdf_sex[fb_cdf_sex['Age Range'] != "6 months-17 years"]
fb_cdf_sex = fb_cdf_sex[fb_cdf_sex['Age Range'] != "5-17 years"]

#Combine for Adult and Child samples 
base_df_sex = pd.concat([fb_cdf_sex, fb_adf_sex])
base_df_age = pd.concat([fb_cdf_age, fb_adf_age])

#Format base data for combined Adult and Child samples
base_df_sex.replace(['Female', 'Male'], ['F', 'M'], inplace=True)
base_df_sex.replace(['12-17 years', '5-11 years', '6 months-4 years'], ['12-17', '5-11', '0-4'], inplace=True)
base_df_age.replace(['6 months � 4 years', '12 � 15 years', '16 � 17 years', '5 � 11 years', '18 – 29 years', '30 – 39 years', '40 – 49 years', '50 – 64 years', '65 – 74 years', '75+ years'], ['0-4', '12-17', '12-17', '5-11', '18-29', '30-39', '40-49', '50-64', '65-74', '75+'], inplace=True)

#Save to csv 
base_df_age.to_csv("base_covid_age.csv")
base_df_sex.to_csv("base_covid_sex_age.csv")


## Incident data 

#starting from uploaded file of concatenated incidents across years 
df_vax_total = pd.read_csv('total_incident_vaccine.csv')

df_vax = pd.DataFrame()

# Z_i, Treatment
df_vax["Treatment"] = df_vax_total["VAX_TYPE"]

# N, Count_treated

# Metadata
meta = list()
features = list()
incidents = list()

for index, row in df_vax_total.iterrows():
    meta_dict = dict()
    meta_dict["full_vax_name"] = row["VAX_NAME"]
    meta_dict["date_logged"] = row["RECVDATE"]
    meta_dict["incident_id"] = row["VAERS_ID"]
    meta.append(meta_dict)

# X_i, Features
    features_dict = dict()
    features_dict["vax_manufacturer"] = row["VAX_MANU"]
    features_dict["vax_lot"] = row["VAX_LOT"]
    features_dict["dose"] = row["VAX_DOSE_SERIES"]

    features_dict["state"] = row["STATE"]
    features_dict["age"] = row["AGE_YRS"] #Not that this is a continuous variable, counting months (eg. 1.26 is a valid age)
    features_dict["gender"] = row["SEX"]

    features_dict["med_history"] = row["HISTORY"]
    features_dict["prior_vax"] = row["PRIOR_VAX"]
    features.append(features_dict)

# Y_i
    ind_dict = dict()
    ind_dict["symptoms_text"] = row["SYMPTOM_TEXT"]
    ind_dict["died_flag"] = row["DIED"]

    s_dict = dict()
    for i in range(1,6):
        s_idx = "S%d"%i
        s_query = "SYMPTOM%d"%i
        s_dict[s_idx] = row[s_query]

    ind_dict["symptoms"] = s_dict
    incidents.append(ind_dict)


df_vax['Metadata'] = meta
df_vax['Features'] = features
df_vax['Incidents'] = incidents

#  t
df_vax["Report Date"] = df_vax_total['RECVDATE']

# Save to csv 
df_vax.to_csv('clean_total_incident_vaccine.csv', index=False)


###################################################
# Set up reports df  - covid, myo
###################################################

df_icounts = pd.read_csv("clean_total_incident_vaccine.csv")
df_icounts_covid = df_icounts.loc[df_icounts["Treatment"] == "COVID19"] 
df_icounts_covid.to_csv("clean_total_incident_covid.csv")

df_icovid = pd.DataFrame()

age_col = list()
gen_col = list()
rep_col = list()
sympt_col = list()
myo_col = list()

for index, row in df_icounts_covid.iterrows():
    #print(type(row["Features"]))
    f_dict = eval(row["Features"])
    s_dict = eval(row["Incidents"])
    age_col.append(f_dict["age"])
    gen_col.append(f_dict["gender"])
    rep_col.append(row["Report Date"])
    sympt_col.append(s_dict['symptoms'])
    myo_flag = "N"
    for s in list(s_dict['symptoms'].values()):
        if s is not nan:
            if "myocarditis" in s.lower():
                #print(s) #myocarditis
                myo_flag = "Y"
    
    myo_col.append(myo_flag)

    #break

df_icovid["Age"] = age_col
df_icovid["Gender"] = gen_col
df_icovid["Report Date"] = rep_col
df_icovid["Symptoms"] = sympt_col
df_icovid["Myo_flag"] = myo_col

df_icovid.loc[df_icovid["Myo_flag"] == "Y"].to_csv("_covid_myocarditis_flag_Y.csv")

isex_bukets = df_icovid["Gender"].unique()

#bins_1 = pd.IntervalIndex.from_tuples([(-1, 18), (18, 50), (50, 65), (65, 200)])
bins_2 = pd.IntervalIndex.from_tuples([(-1, 4), (4, 11), (11, 17), (17, 29), (29, 39), (39, 49), (49, 64), (64, 74),(74, 200)]) # 0-12, 13-17, 18-24, 25-35, 36-49, ++ 
x = pd.cut(df_icovid["Age"], bins_2)
#labels_1 =["0-17", "18-49", "50-64", "65+"]
labels_2 =["0-4", "5-11", "12-17", "18-29", "30-39", "40-49", "50-64", "65-74", "75+"]
x = x.cat.rename_categories(labels_2)
df_icovid["Age"] = x.astype('str')

df_icovid = df_icovid.rename(columns={"age": "Age", "Gender": "Sex"})

#Drop NaN
df_icovid = df_icovid.replace('nan', "U") #mark unknown 

df_icovid.loc[df_icovid["Myo_flag"] == "Y"].to_csv('myocard_exact_vaccine_reports_10yr_Y.csv', index=False) 

actual_reports = df_icovid.loc[df_icovid["Myo_flag"] == "Y"]

###################################################
# Set up groups
###################################################

#NOTE: Set up groups wrt incident database! 

dem_cols = ["Age", "Sex"]

df_icovid['Age'].unique()
df_icovid['Sex'].unique()

# iterate through possible groups 
sex, age = [df_icovid[col].unique().tolist() for col in dem_cols]
groups_product = list(product(sex, age))
all_groups_dict = [{dem_cols[i]: group[i] for i in range(len(dem_cols))} for group in groups_product]

# set up groups disctionary
for col in dem_cols:
    for val in df_icovid[col].unique():
        all_groups_dict.append({col: val})

#save to pickle file 
with open('vaccine_groups_10yr.pkl', 'wb') as handle:
    pickle.dump(all_groups_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

###################################################
# Get base rates
###################################################

df_bcovid_age = pd.read_csv("base_covid_age.csv")
df_bcovid_age_sex = pd.read_csv("base_covid_sex_age.csv")

with open('vaccine_groups_10yr.pkl', 'rb') as f:
    # Load the pickled object
    all_groups_dict = pickle.load(f)

cdb_as = df_bcovid_age_sex.copy(deep=True)
cdb_a = df_bcovid_age.copy(deep=True)

total_age_count = cdb_a["Count"].sum()
total_age_sex_count = cdb_as["Count"].sum()
res = dict()

for item in all_groups_dict:
    ikeys = item.keys()
    if ("Age" in ikeys) and (len(ikeys)<=1):
        #Age only
        print(item)
        cdb = cdb_a.loc[(cdb_a["Group Category"] == item["Age"])]
        cat_age_count = cdb["Count"].sum()
        res[str(item)] = cat_age_count/total_age_count

    if ("Sex" in ikeys) and (len(ikeys)<=1):
        #Sex only 
        print(item)
        cdb = cdb_as.loc[(cdb_as["Group Category"] == item["Sex"])]
        cat_sex_count = cdb["Count"].sum()
        res[str(item)] = cat_sex_count/total_age_sex_count

    if ("Sex" in ikeys) and (len(ikeys)>1):
        #Sex, Age
        #base rate is age base rate x gender base rate 
        cdb1 = cdb_a.loc[(cdb_a["Group Category"] == item["Age"])]
        cdb2 = cdb_as.loc[(cdb_as["Group Category"] == item["Sex"])]
        cat_sex_count = cdb1["Count"].sum()
        sex_base = cat_sex_count/total_age_sex_count
        cat_age_count = cdb2["Count"].sum()
        age_base = cat_age_count/total_age_count
        res[str(item)] = sex_base*age_base

#save base rates 
with open('vaccine_base_rates_10yr.pkl', 'wb') as handle:
    pickle.dump(np.array(list(res.values())), handle, protocol=pickle.HIGHEST_PROTOCOL)

###################################################
# Get ground truth flagged groups 
###################################################

base_rates = list()
report_features = pd.read_csv('myocard_exact_vaccine_reports_10yr_Y.csv') #('myocarditis_exact_vaccine_reports_10yr_Y.csv') 

BETA = 1.1
flagged_groups = {}
for group in all_groups_dict:
    base_group_rate = res[str(group)] 
    report_group_rate = inc_get_group_count(group, report_features) / inc_get_cat_count(group, report_features) 
    base_rates.append(base_group_rate)
    if report_group_rate >= BETA*base_group_rate and base_group_rate > 0.01:
        flagged_groups[frozenset(group.items())] = (report_group_rate/base_group_rate)
        
base_groups = np.array(base_rates)

###################################################
# Save everything
###################################################
save_path = 'vaers/vaers__'
save_preprocessed(actual_reports, all_groups_dict, base_groups, save_path)

