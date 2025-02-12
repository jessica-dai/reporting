import pandas as pd 
import numpy as np

from process_hmda_utils import (clean_location, clean_race_ethnicity, find_same_race, clean_credit_model, 
                              find_coapplicants, clean_outcomes, find_aus_patterns, clean_aus,
                              setup_dti_cat, categorize_cltv, categorize_property_value_ratio, 
                                   calculate_prop_zscore, categorize_age, categorize_sex, 
                                   categorize_underwriter, categorize_loan_term, categorize_lmi)

CLEAN1_FILENAME = ''
CLEAN2_FILENAME = ''
LENDER_DEF_FILENAME= '' # '../../data/supplemental_hmda_data/cleaned/lender_definitions_em210513.csv' 
COUNTIES_FILENAME = '' # '../../data/census_data/county_to_metro_crosswalk/clean/all_counties_210804.csv'
COUNTIES_PROPVAL_FILENAME = '' # '../../data/census_data/property_values/ACSDT5Y2019.B25077_data_with_overlays_2021-06-23T115616.csv'
CENSUS_RACE_FILENAME = '' # '../../data/census_data/racial_ethnic_demographics/clean/tract_race_pct2019_210204.csv'

###############################################################################
# 1_clean_data.ipynb from https://github.com/the-markup/investigation-redlining
###############################################################################

def markup_clean_data():
    # ### 1. Import HMDA data
    # - Data can be download from the CFPB site: [2019 LAR dataset](https://ffiec.cfpb.gov/data-publication/snapshot-national-loan-level-dataset/2019)
    # - The date the file was downloaded was appended to the raw file name.
    # - 99 Columns
    # - 17,545,457 records
    # - [Data Dictionary](https://ffiec.cfpb.gov/documentation/2019/lar-data-fields/)

    # --
    hmda19_df = pd.read_csv('../../data/hmda_lar/raw_data/2019_lar.txt', sep="|")

    # ### 2. Clean Data
    # 
    # 
    # #### Dropping columns I don't need (21 in total) to make the data easier to work with:
    # 
    # ##### The following columns were added by the CFPB, not using them. 
    #     - derived_loan_product_type
    #     - derived_dwelling_category
    #     -

    # ### 1. Import HMDA data
    # - Data can be download from the CFPB site: [2019 LAR dataset](https://ffiec.cfpb.gov/data-publication/snapshot-national-loan-level-dataset/2019)
    # - The date the file was downloaded was appended to the raw file name.
    # - 99 Columns
    # - 17,545,457 records
    # - [Data Dictionary](https://ffiec.cfpb.gov/documentation/2019/lar-data-fields/)

    # --
    hmda19_df = pd.read_csv('../../data/hmda_lar/raw_data/2019_lar.txt', sep="|")

    # ### 2. Clean Data
    # 
    # 
    # #### Dropping columns I don't need (21 in total) to make the data easier to work with:
    # 
    # ##### The following columns were added by the CFPB, not using them. 
    #     - derived_loan_product_type
    #     - derived_dwelling_category
    #     - derived_ethnicity
    #     - derived_race
    #     - derived_sex
    # ##### Focusing on the applicant's first ethnicity
    #     - applicant_ethnicity-2
    #     - applicant_ethnicity-3
    #     - applicant_ethnicity-4
    #     - applicant_ethnicity-5
    # ##### Focusing on the co-applicant's first ethnicity. Don't need these columns to find co-applicants.
    #     - co-applicant_ethnicity-2
    #     - co-applicant_ethnicity-3
    #     - co-applicant_ethnicity-4
    #     - co-applicant_ethnicity-5
    # ##### Focusing on the applicant's first race
    #     - applicant_race-2
    #     - applicant_race-3
    #     - applicant_race-4
    #     - applicant_race-5
    # ##### Focusing on the co-applicant's first race. Don't need these columns to find co-applicants.
    #     - co-applicant_race-2 
    #     - co-applicant_race-3 
    #     - co-applicant_race-4 
    #     - co-applicant_race-5
    #     
    # #### Using 78 columns instead of 99

    # --
    remove_cols = ['derived_loan_product_type', 'derived_dwelling_category', 'derived_ethnicity', 
                'derived_race', 'derived_sex', 
                'applicant_ethnicity_2','applicant_ethnicity_3', 'applicant_ethnicity_4', 'applicant_ethnicity_5',
                'co_applicant_ethnicity_2', 'co_applicant_ethnicity_3', 'co_applicant_ethnicity_4', 
                'co_applicant_ethnicity_5', 
                'applicant_race_2','applicant_race_3', 'applicant_race_4', 'applicant_race_5', 
                'co_applicant_race_2', 'co_applicant_race_3', 'co_applicant_race_4', 
                'co_applicant_race_5']

    new_headers = []
    for column in hmda19_df.columns:
        if column not in remove_cols:
            new_headers.append(column)
            

    # -- [markdown]
    # #### Create smaller subset of HMDA data
    # - Deleting the orginal HMDA df to clear memory

    # --
    hmda19_df2 = hmda19_df[new_headers].copy()
    del hmda19_df

    hmda19_df2.info()

    # --
    hmda19_df2_backup = hmda19_df2.copy(deep=True)

    # -- [markdown]
    # ### 2. Clean Location

    # --
    ### Group all unique combinations of county codes and census tract
    location_df = pd.DataFrame(hmda19_df2.groupby(by = ['county_code', 'census_tract'], dropna = False).size()).\
                reset_index().rename(columns = {0: 'count'})

    ### Replacing the Nulls with other text so that the function works, Keeping the Nulls seperate from the "NAs"
    location_df = location_df.replace(to_replace = 'Na', value = 'ii-ii')
    location_df = location_df.fillna('00-00')

    # --
    ### Number of unique combinations of county and census
    print("Number of unique combinations of county and census:", len(location_df))

    ### Records where county code or census tract are Na
    print("Records where county code or census tract are Na", ((location_df['county_code'] == 'ii-ii') | (location_df['census_tract'] == 'ii-ii')).values.sum())
    ### Records where county or census tract are NULL
    print("Records where county or census tract are NULL", ((location_df['county_code'] == '00-00') | (location_df['census_tract'] == '00-00')).values.sum())

    # --
    ### Running clean_location function to ensure every record has county code
    location_df['location_code'] = location_df.apply(clean_location, axis = 1) # this line was ok 
    ### Split location column for state and county fips codes
    # NOTE: convert the location code to a string before indexing! 
    location_df['state_fips'] = location_df['location_code'].astype(str).str[0:2]
    location_df['county_fips'] = location_df['location_code'].astype(str).str[2:5]

    ## these lines replaced the following old code: 
    # location_df['state_fips'] = location_df['location_code'].str[0:2]
    # location_df['county_fips'] = location_df['location_code'].str[2:5]

    ### Number of records with no county code and census tract information
    nulls_df = location_df[(location_df['state_fips'] == '--') & (location_df['county_fips'] == '---')]
    print('Number of records with location nulls: ' + str(nulls_df['count'].sum())) # this number is consistent ! 
    ### Remove columns that are no longer needed
    location_df2 = location_df.drop(columns = ['count', 'location_code'], axis = 1)

    # --
    ### Replace two dashes and three dashes data points with NaN 
    location_df2 = location_df2.replace(to_replace = '--', value = np.nan)
    location_df2 = location_df2.replace(to_replace = '---', value = np.nan)

    ### Replace '00-00' and 'ii-ii' with the orginal data points to join back to the orginal HMDA data
    location_df2 = location_df2.replace(to_replace = '00-00', value = np.nan)
    location_df2 = location_df2.replace(to_replace = 'ii-ii', value = 'Na')

    # --
    hmda19_df2 = pd.merge(hmda19_df2, location_df2, how = 'left', on = ['county_code', 'census_tract'])

    # --
    nulls_records = (hmda19_df2['county_fips'].isnull() & hmda19_df2['state_fips'].isnull()).values.sum()

    ### This number matches the one from above (IT MATCHES!)
    print('Null Records that don\'t have fips data: ' + str((nulls_records)))

    # -- [markdown]
    # ### 3. Clean Race and Ethnicity
    # - 1: Native American
    # - 2: Asian
    # - 3: Black
    # - 4: Pacific Islander
    # - 5: White
    # - 6: Latino
    # - 7: Race NA

    # --
    ### Group race and ethnicity for all unique combinations
    main_race_eth = pd.DataFrame(hmda19_df2.groupby(by = ['applicant_race_1', 'applicant_ethnicity_1'],
                                dropna = False).size()).reset_index().rename(columns = {0: 'count'})

    ### Replace NAs with 000 for cleaning purposes
    main_race_eth = main_race_eth.fillna('000')
    print(len(main_race_eth))

    # --
    # need to convert floats to ints to stirngs for compatibility
    main_race_eth['applicant_ethnicity_1'] = main_race_eth['applicant_ethnicity_1'].astype(int).astype(str)
    main_race_eth['applicant_race_1'] = main_race_eth['applicant_race_1'].astype(int).astype(str) 

    # --
    ### Apply clean_race_ethnicity function for the r/e dataframe
    main_race_eth['app_race_ethnicity'] = main_race_eth.apply(clean_race_ethnicity, axis = 1)

    ### Replace 000 with NaN to join back with HMDA data
    # NOTE don't do this, fill HMDA with '000'
    # main_race_eth = main_race_eth.replace(to_replace = '000', value = np.nan)
    ### Drop Count Column
    main_race_eth = main_race_eth.drop(columns = ['count'], axis = 1)

    # --
    # NOTE need to fill nans correctly for the merge
    hmda19_df2['applicant_ethnicity_1'] = hmda19_df2['applicant_ethnicity_1'].fillna('000')
    hmda19_df2['applicant_race_1'] = hmda19_df2['applicant_race_1'].fillna('000')
    hmda19_df2['applicant_ethnicity_1'] = hmda19_df2['applicant_ethnicity_1'].astype(int).astype(str)
    hmda19_df2['applicant_race_1'] = hmda19_df2['applicant_race_1'].astype(int).astype(str)

    # --
    hmda19_df2 = pd.merge(hmda19_df2, main_race_eth, how = 'left', on = ['applicant_race_1', 'applicant_ethnicity_1'])

    hmda19_df2['app_race_ethnicity'].value_counts(dropna = False)

    # -- [markdown]
    # ### 4. Clean Co Race and Ethnicity
    # - 1: Native American
    # - 2: Asian
    # - 3: Black
    # - 4: Pacific Islander
    # - 5: White
    # - 6: Latino
    # - 7: Race NA
    # - 8: No Coapp

    # --
    coapp_race_ethnicity = pd.DataFrame(hmda19_df2.groupby(by = ['co_applicant_race_1', 'co_applicant_ethnicity_1'],
                                        dropna = False).size()).reset_index().rename(columns = {0: 'count'})

    coapp_race_ethnicity = coapp_race_ethnicity.fillna('000')
    coapp_race_ethnicity.head(1)

    # --
    # NOTE same deal as above
    coapp_race_ethnicity['co_applicant_race_1'] = coapp_race_ethnicity['co_applicant_race_1'].astype(int).astype(str)
    coapp_race_ethnicity['co_applicant_ethnicity_1'] = coapp_race_ethnicity['co_applicant_ethnicity_1'].astype(int).astype(str)

    # --
    ### Using clean_race_ethnicity function for the coapp r/e dataframe, it has a no co-app flag
    coapp_race_ethnicity['coapp_race_ethnicity'] = coapp_race_ethnicity.apply(clean_race_ethnicity, axis = 1)

    # --
    coapp_race_ethnicity = coapp_race_ethnicity.drop(columns = ['count'], axis = 1)
    # coapp_race_ethnicity = coapp_race_ethnicity.replace(to_replace = '000', value = np.nan)

    # --
    # NOTE need to fill nans correctly for the merge
    hmda19_df2['co_applicant_ethnicity_1'] = hmda19_df2['co_applicant_ethnicity_1'].fillna('000')
    hmda19_df2['co_applicant_race_1'] = hmda19_df2['co_applicant_race_1'].fillna('000')
    hmda19_df2['co_applicant_ethnicity_1'] = hmda19_df2['co_applicant_ethnicity_1'].astype(int).astype(str)
    hmda19_df2['co_applicant_race_1'] = hmda19_df2['co_applicant_race_1'].astype(int).astype(str)

    # --

    hmda19_df2 = pd.merge(hmda19_df2, coapp_race_ethnicity, how = 'left', 
                        on = ['co_applicant_race_1', 'co_applicant_ethnicity_1'])

    # hmda19_df2['coapp_race_ethnicity'].value_counts(dropna = False)

    # -- [markdown]
    # ### 6. Same or Different Race for Co-Applicant
    # - 1: Same
    # - 2: Difference
    # - 3: Not Applicable

    # --
    ### group all instances of main applicants and co-applicants races and ethnicities
    coapp_same_race = pd.DataFrame(hmda19_df2.groupby(by = ['app_race_ethnicity', 'coapp_race_ethnicity'],
                                dropna = False).size()).reset_index().rename(columns = {0: 'count'})

    # --
    coapp_same_race = coapp_same_race.fillna('000')
    coapp_same_race['app_race_ethnicity'] = coapp_same_race['app_race_ethnicity'].astype(int).astype(str)
    coapp_same_race['coapp_race_ethnicity'] = coapp_same_race['coapp_race_ethnicity'].astype(int).astype(str)
    # coapp_same_race.apply(find_same_race, axis = 1).unique()

    # --
    ### Find records where applicant and co-applicant are the same
    coapp_same_race['coapp_same_race'] = coapp_same_race.apply(find_same_race, axis = 1)

    coapp_same_race = coapp_same_race.drop(columns = ['count'], axis = 1)

    # --

    hmda19_df2 = pd.merge(hmda19_df2, coapp_same_race, how = 'left', 
                        on = ['app_race_ethnicity', 'coapp_race_ethnicity'])

    # hmda19_df2['coapp_same_race'].value_counts(dropna = False)

    # -- [markdown]
    # ### 7. Clean Credit Models
    # - 1: Equifax
    # - 2: Experian
    # - 3: TransUnion
    # - 4: Vantage
    # - 5: More than one
    # - 6: Other Model
    # - 7: Credit Na

    # --
    credit_models = pd.DataFrame(hmda19_df2.groupby(by = ['applicant_credit_score_type'],
                    dropna = False).size()).reset_index().rename(columns = {0: 'count'})
    # --
    credit_models['applicant_credit_score_type'] = credit_models['applicant_credit_score_type'].astype(int).astype(str)

    # --
    ### Using function to standardize credit model
    credit_models['app_credit_model'] = credit_models.apply(clean_credit_model, axis = 1)

    credit_models = credit_models.drop(columns = ['count'], axis = 1)

    # --
    hmda19_df2['applicant_credit_score_type'] = hmda19_df2['applicant_credit_score_type'].astype(int).astype(str)

    # --

    hmda19_df2 = pd.merge(hmda19_df2, credit_models, how = 'left', on = ['applicant_credit_score_type'])

    # hmda19_df2['app_credit_model'].value_counts(dropna = False)

    # -- [markdown]
    # ### 8. Find Co-Applicants
    # 
    # - 9999 in age means [no co-applicant](https://s3.amazonaws.com/cfpb-hmda-public/prod/help/2018-public-LAR-code-sheet.pdf)
    # - 8888 in age means no applicable

    # --
    coapp_cols = ['coapp_race_ethnicity', 'co_applicant_sex', 'co_applicant_age', 'co_applicant_credit_score_type']

    coapp_comb_df = pd.DataFrame(hmda19_df2.groupby(by = coapp_cols, dropna = False).size()).reset_index().rename(\
                    columns = {0: 'count'})

    # -- [markdown]
    # #### Co-Applicants
    # 
    # - 1: Co-Applicants
    # - 2: No co-applicants
    # - 3: Not Applicable

    # --
    for col in coapp_cols:
        coapp_comb_df[col] = coapp_comb_df[col].fillna('000')
        coapp_comb_df[col] = coapp_comb_df[col].astype(str)

    # --
    ### Run function to find co-applicants
    coapp_comb_df['co_applicant'] = coapp_comb_df.apply(find_coapplicants, axis = 1)
    coapp_comb_df = coapp_comb_df.drop(columns = ['count'], axis = 1)

    # --
    for col in coapp_cols:
        hmda19_df2[col] = hmda19_df2[col].fillna('000')
        hmda19_df2[col] = hmda19_df2[col].astype(str)

    # --

    hmda19_df2 = pd.merge(hmda19_df2, coapp_comb_df, how = 'left', on = coapp_cols)

    # hmda19_df2['co_applicant'].value_counts(dropna = False)

    # -- [markdown]
    # ### 9. Standardize Outcomes
    # - 1: Loan originated
    # - 2: Application approved but not accepted
    # - 3: Application denied
    # - 4: Application withdrawn by applicant
    # - 5: File closed for incompleteness
    # - 6: Purchased loan
    # - 7: Preapproval request denied
    # - 8: Preapproval request approved but not accepted

    # --
    action_taken = pd.DataFrame(hmda19_df2['action_taken'].value_counts(dropna = False)).reset_index()

    # .\
    #                rename(columns = {'index': 'action_taken', 'action_taken': 'count'})

    # -- [markdown]
    # #### Outcomes:
    # - 1: Loans
    # - 3: Denials
    # - 4: Other Outcomes
    # - 6: Purchase loans

    # --
    action_taken['action_taken'] = action_taken['action_taken'].astype(str)

    # --
    ### Clean Outcomes
    action_taken['loan_outcome'] = action_taken.apply(clean_outcomes, axis = 1)

    action_taken = action_taken.drop(columns = ['count'], axis = 1)

    # --
    hmda19_df2['action_taken']= hmda19_df2['action_taken'].astype(str)

    # --
    hmda19_df2 = pd.merge(hmda19_df2, action_taken, how = 'left', on = ['action_taken'])

    # hmda19_df2['loan_outcome'].value_counts(dropna = False)

    # -- [markdown]
    # ### 10. Standardize Automated Underwriting System

    # --
    aus = ['aus_1', 'aus_2', 'aus_3', 'aus_4', 'aus_5']

    ### Group all unique combinations of AUS together to find all the patterns
    aus_df = pd.DataFrame(hmda19_df2.groupby(by = aus, dropna = False).size()).\
            reset_index().rename(columns = {0: 'count'})
    aus_df = aus_df.drop(columns = ['count'], axis = 1)

    # -- [markdown]
    # #### Aus Cat
    # - 1: One AUS was used
    # - 2: Same AUS was used mulitple times
    # - 3: Different AUS was used 
    # - 4: Exempt

    # --
    ### Calculate unique values and nulls
    aus_df = find_aus_patterns(aus_df)

    # --
    ### Categorize AUS
    aus_df['aus_cat'] = aus_df.apply(clean_aus, axis = 1)

    # --
    aus_df = aus_df.drop(columns = ['number_of_values', 'number_of_nulls'], axis = 1)

    # --
    hmda19_df2 = pd.merge(hmda19_df2, aus_df, how = 'left', on = aus)
    hmda19_df2['aus_cat'].value_counts(dropna = False)

    # -- [markdown]
    # ### Write out new csv

    # --
    hmda19_df2.to_csv(CLEAN1_FILENAME, index = False)


###############################################################################
# 2_categorize_data.ipynb from https://github.com/the-markup/investigation-redlining
###############################################################################

def markup_categorize_data(clean1_filename = CLEAN1_FILENAME, clean2_filename = CLEAN2_FILENAME):
    # -- [markdown]
    # ### 1. Import Cleaned Data
    # - Rows: 17,545,457
    # - Columns: 87

    # --
    hmda19_df = pd.read_csv(clean1_filename, dtype = str)

    # -- [markdown]
    # ### 2. Join with Lender Info

    # --
    lender_def = pd.read_csv(LENDER_DEF_FILENAME, 
                            dtype = str)

    # --
    lender_def2 = lender_def[['lei', 'lar_count', 'assets', 'lender_def', 'con_apps']].copy()

    # --
    hmda19_df = pd.merge(hmda19_df, lender_def2, how = 'left', on = ['lei'])

    # -- [markdown]
    # Every record in HMDA data has a lender match. There are no missing values after the join. 

    # --
    hmda19_df = hmda19_df.dropna(axis=0, subset=['lar_count'])

    # -- [markdown]
    # #### Lender Definition
    # Only 30,000 records, less than one percent,  in overall HMDA data come from no definitions for lenders.
    # - 1: Banks
    # - 2: Credit Union
    # - 3: Independent Mortgage Companies
    # - 4: No definition 

    # --

    # -- [markdown]
    # ### 3. Adding Metro Definitions

    # --
    counties_df = pd.read_csv(COUNTIES_FILENAME,
                            dtype = str)

    # --
    counties_df2 = counties_df[['fips_state_code', 'fips_county_code', 'metro_code', 'metro_type_def',
                                'metro_percentile']].copy()

    counties_df2 = counties_df2.rename(columns = {'fips_state_code': 'state_fips', 
                                                'fips_county_code': 'county_fips'})

    # -- [markdown]
    # #### Metro Percentile Definitions
    # Majority of applications come from metros in the 80th percentile or larger ones.
    # 
    # - 111: Micro
    # - 000: No Metro
    # - 99: 99th percentile
    # - 9: 90th percentile

    # --
    hmda19_df = pd.merge(hmda19_df, counties_df2, how = 'left', on = ['state_fips', 'county_fips'])

    hmda19_df['metro_percentile'].value_counts(dropna = False, normalize = True) * 100

    # -- [markdown]
    # ### 4. Add Property Value by County

    # --
    prop_values_df = pd.read_csv(COUNTIES_PROPVAL_FILENAME, dtype = str)

    # -- [markdown]
    # #### First pass at cleaning median property value data

    # --
    prop_values_df2 = prop_values_df[(prop_values_df['GEO_ID'] != 'id')]

    prop_values_df3 = prop_values_df2.rename(columns = {'B25077_001E': 'median_value', 
                                                        'B25077_001M': 'median_value_moe'})

    prop_values_df3['state_fips'] = prop_values_df3['GEO_ID'].str[9:11]
    prop_values_df3['county_fips'] = prop_values_df3['GEO_ID'].str[11:]

    prop_values_df4 = prop_values_df3[['state_fips', 'county_fips', 'median_value']].copy()

    # -- [markdown]
    # #### Convert property value to numeric
    # - No property value for these two counties

    # --
    prop_values_df4[(prop_values_df4['median_value'] == '-')]

    # --
    prop_values_df4.loc[(prop_values_df4['median_value'] != '-'), 'median_prop_value'] = prop_values_df4['median_value']
    prop_values_df4.loc[(prop_values_df4['median_value'] == '-'), 'median_prop_value'] = np.nan
    prop_values_df4['median_prop_value'] = pd.to_numeric(prop_values_df4['median_prop_value'])

    prop_values_df4[(prop_values_df4['median_prop_value'].isnull())]

    # --
    hmda19_df = pd.merge(hmda19_df, prop_values_df4, how = 'left', on = ['state_fips', 'county_fips'])

    # --
    hmda19_df.loc[(hmda19_df['property_value'] != 'Exempt'), 'prop_value'] = hmda19_df['property_value']

    hmda19_df.loc[(hmda19_df['property_value'] == 'Exempt'), 'prop_value'] = np.nan

    hmda19_df['prop_value'] = pd.to_numeric(hmda19_df['prop_value'])

    # -- [markdown]
    # ### 5. Add Race and Ethnicity Demographic per Census Tract

    # --
    race_df = pd.read_csv(CENSUS_RACE_FILENAME,
                        dtype = str)

    # --
    race_df['white_pct'] = pd.to_numeric(race_df['white_pct'])

    race_df['census_tract'] = race_df['state'] + race_df['county'] + race_df['tract']

    race_df2 = race_df[['census_tract', 'total_estimate', 'white_pct', 'black_pct', 'native_pct', 'latino_pct', 
                        'asian_pct', 'pacislander_pct', 'othercb_pct', 'asiancb_pct']].copy()

    race_df2.sample(2, random_state = 303)

    # -- [markdown]
    # #### Create White Gradiant

    # --
    race_df2.loc[(race_df2['white_pct'] > 75), 'diverse_def'] = '1'

    race_df2.loc[(race_df2['white_pct'] <= 75) & (race_df2['white_pct'] > 50), 'diverse_def'] = '2'

    race_df2.loc[(race_df2['white_pct'] <= 50) & (race_df2['white_pct'] > 25), 'diverse_def'] = '3'

    race_df2.loc[(race_df2['white_pct'] <= 25), 'diverse_def'] = '4'

    race_df2.loc[(race_df2['white_pct'].isnull()), 'diverse_def'] = '5'

    # race_df2['diverse_def'].value_counts(dropna = False)

    # -- [markdown]
    # - 0: No census data there
    # - NaN: Records that don't find a match in the census data

    # --
    hmda19_df = pd.merge(hmda19_df, race_df2, how = 'left', on = ['census_tract'])

    # -- [markdown]
    # Convert the NaN to 0's

    # --
    hmda19_df.loc[(hmda19_df['diverse_def'].isnull()), 'diverse_def'] = '0'

    # hmda19_df['diverse_def'].value_counts(dropna = False)

    # -- [markdown]
    # ### 7. Clean Debt-to-Income Ratio

    # --
    dti_df = pd.DataFrame(hmda19_df['debt_to_income_ratio'].value_counts(dropna = False)).reset_index()
    # .\
    #          rename(columns = {'index': 'debt_to_income_ratio', 'debt_to_income_ratio': 'count'})

    ### Convert the nulls for cleaning purposes
    dti_df = dti_df.fillna('null')

    # --
    ### Running function to organize debt-to-income ratio
    dti_df['dti_cat'] = dti_df.apply(setup_dti_cat, axis = 1)


    # --
    ### Drop count column and replace the null values back to NaN
    dti_df2 = dti_df.drop(columns = ['count'], axis = 1)
    dti_df2 = dti_df2.replace('null', np.nan)

    # --
    hmda19_df = pd.merge(hmda19_df, dti_df2, how = 'left', on = ['debt_to_income_ratio'])

    # hmda19_df['dti_cat'].value_counts(dropna = False, normalize = True) * 100

    # -- [markdown]
    # ### 8. Combine Loan-to-Value Ratio

    # --
    cltv_df = pd.DataFrame(hmda19_df['combined_loan_to_value_ratio'].value_counts(dropna = False)).reset_index()
    # .\
    #           rename(columns = {'index': 'combined_loan_to_value_ratio', 'combined_loan_to_value_ratio': 'count'})

    ### Convert cltv to numeric
    cltv_df.loc[(cltv_df['combined_loan_to_value_ratio'] != 'Exempt'), 'cltv_ratio'] =\
                cltv_df['combined_loan_to_value_ratio']

    cltv_df['cltv_ratio'] = pd.to_numeric(cltv_df['cltv_ratio'])

    # -- [markdown]
    # #### Downpayment Flag
    # - 1: 20 percent or more downpayment
    # - 2: Less than 20 percent
    # - 3: Nulls

    # --
    cltv_df['downpayment_flag'] = cltv_df.apply(categorize_cltv, axis = 1)
    cltv_df2 = cltv_df.drop(columns = ['count', 'cltv_ratio'], axis = 1)


    hmda19_df = pd.merge(hmda19_df, cltv_df2, how = 'left', on = ['combined_loan_to_value_ratio'])
    # hmda19_df['downpayment_flag'].value_counts(dropna = False)

    # -- [markdown]
    # ### 9. Property Value Ratio Z-Score
    # 
    # Property value ratios are more normally distributed than raw property values. Because there's they are normally distributed below the 10th ratio, I will use the z-scores and place them into buckets based on those z-scores.

    # --
    property_value_df = pd.DataFrame(hmda19_df.groupby(by = ['state_fips', 'county_fips', 'property_value',
                        'prop_value', 'median_prop_value'], dropna = False).size()).reset_index()
    # .\
    #                      rename(columns = {0: 'count'})

    # --
    property_value_df['property_value_ratio'] = property_value_df['prop_value'].\
                                                div(property_value_df['median_prop_value']).round(3)

    property_value_df['prop_zscore'] = property_value_df.apply(calculate_prop_zscore, axis = 1).round(3)

    property_value_df['prop_value_cat'] = property_value_df.apply(categorize_property_value_ratio, axis = 1)

    # --
    property_value_df2 = property_value_df[['state_fips', 'county_fips', 'property_value',
                                            'median_prop_value', 'property_value_ratio', 'prop_zscore',
                                            'prop_value_cat']].copy()

    # --
    hmda19_df = pd.merge(hmda19_df, property_value_df2, how = 'left', on = ['state_fips', 'county_fips',
                        'property_value', 'median_prop_value'])

    # -- [markdown]
    # ### 10. Applicant Age
    # 
    # - [9999](https://s3.amazonaws.com/cfpb-hmda-public/prod/help/2018-public-LAR-code-sheet.pdf): No Co-applicant
    # - 8888: Not Applicable

    # --
    age_df = pd.DataFrame(hmda19_df['applicant_age'].value_counts(dropna = False)).reset_index()

    # .\
    #          rename(columns = {'index': 'applicant_age', 'applicant_age': 'count'})

    # --
    age_df['applicant_age_cat'] = age_df.apply(categorize_age, axis = 1)

    age_df = age_df.drop(columns = ['count'], axis = 1)

    # -- [markdown]
    # #### Age Categories
    # - 1: Less than 25
    # - 2: 25 through 34
    # - 3: 35 through 44
    # - 4: 45 through 54
    # - 5: 55 through 64
    # - 6: 65 through 74
    # - 7: Greater than 74
    # - 8: Not Applicable

    # --
    hmda19_df = pd.merge(hmda19_df, age_df, how = 'left', on = ['applicant_age'])

    # hmda19_df['applicant_age_cat'].value_counts(dropna = False)

    # -- [markdown]
    # ### 11. Income and Loan Amount Log

    # --
    hmda19_df['income'] = pd.to_numeric(hmda19_df['income'])
    hmda19_df['loan_amount'] = pd.to_numeric(hmda19_df['loan_amount'])

    hmda19_df['income_log'] = np.log(hmda19_df['income'])
    hmda19_df['loan_log'] = np.log(hmda19_df['loan_amount'])

    # -- [markdown]
    # ### 12. Applicant Sex
    # - 1: Male
    # - 2: Female
    # - 3: Information not provided
    # - 4: Not Applicable
    # - 5: No Co-Applicable
    # - 6: Marked Both

    # --
    sex_df = pd.DataFrame(hmda19_df['applicant_sex'].value_counts(dropna = False)).reset_index()

    # .\
    #          rename(columns = {'index': 'applicant_sex', 'applicant_sex': 'count'})

    # --
    sex_df = sex_df.drop(columns = ['count'], axis = 1)

    sex_df['applicant_sex_cat'] = sex_df.apply(categorize_sex, axis = 1)

    # -- [markdown]
    # #### New applicant sex categories
    # - 1: Male
    # - 2: Female
    # - 3: Not applicable
    # - 4: Makred both sexes

    # --
    hmda19_df = pd.merge(hmda19_df, sex_df, how = 'left', on = ['applicant_sex'])

    # hmda19_df['applicant_sex_cat'].value_counts(dropna = False)

    # -- [markdown]
    # ### 13. Automated Underwiting systems
    # - 1: Only one AUS was used
    # - 2: Same AUS was multiple times
    # - 3: Different AUS were used
    # - 4: Exempt

    # --
    hmda19_df['aus_cat'].value_counts(dropna = False)

    # --
    underwriter_df = pd.DataFrame(hmda19_df.groupby(by = ['aus_1', 'aus_cat']).size()).reset_index().\
                    rename(columns = {0: 'count'})

    underwriter_df['main_aus'] = underwriter_df.apply(categorize_underwriter, axis = 1)

    underwriter_df = underwriter_df.drop(columns = ['count'], axis = 1)

    # -- [markdown]
    # #### Main Aus
    # - 1: Desktop Underwriter
    # - 2: Loan Prospector
    # - 3: Technology Open to Approved Lenders
    # - 4: Guaranteed Underwriting System
    # - 5: Other
    # - 6: No main Aus
    # - 7: Not Applicable

    # --
    hmda19_df = pd.merge(hmda19_df, underwriter_df, how = 'left', on = ['aus_1', 'aus_cat'])

    # hmda19_df['main_aus'].value_counts(dropna = False)

    # -- [markdown]
    # ### 14. Loan Term

    # --
    loanterm_df = pd.DataFrame(hmda19_df['loan_term'].value_counts(dropna = False)).reset_index()
    # .\
    #               rename(columns = {'index': 'loan_term', 'loan_term': 'count'})

    loanterm_df.loc[(loanterm_df['loan_term'] != 'Exempt'), 'em_loan_term'] = loanterm_df['loan_term']

    loanterm_df['em_loan_term'] = pd.to_numeric(loanterm_df['em_loan_term'])

    # --
    loanterm_df['mortgage_term'] = loanterm_df.apply(categorize_loan_term, axis = 1)

    loanterm_df = loanterm_df.drop(columns = ['count', 'em_loan_term'])

    # -- [markdown]
    # #### Mortgage Term
    # - 1: 30 year mortgage
    # - 2: Less than 30 years
    # - 3: More than 30 years
    # - 4: Not applicable

    # --
    hmda19_df = pd.merge(hmda19_df, loanterm_df, how = 'left', on = ['loan_term'])

    # hmda19_df['mortgage_term'].value_counts(dropna = False)

    # -- [markdown]
    # ### 15. Tract MSA Income Percentage

    # --
    tractmsa_income_df = pd.DataFrame(hmda19_df['tract_to_msa_income_percentage'].value_counts(dropna = False)).\
                        reset_index()

    # .rename(columns = {'index': 'tract_to_msa_income_percentage', 
    #                                                      'tract_to_msa_income_percentage': 'count'})

    tractmsa_income_df['tract_msa_ratio'] = pd.to_numeric(tractmsa_income_df['tract_to_msa_income_percentage'])

    # --
    tractmsa_income_df['lmi_def'] = tractmsa_income_df.apply(categorize_lmi, axis = 1)

    tractmsa_income_df = tractmsa_income_df.drop(columns = ['count', 'tract_msa_ratio'], axis = 1)

    # -- [markdown]
    # #### LMI Definition
    # - 1: Low
    # - 2: Moderate
    # - 3: Middle
    # - 4: Upper
    # - 5: None

    # --
    hmda19_df = pd.merge(hmda19_df, tractmsa_income_df, how = 'left', on = ['tract_to_msa_income_percentage'])

    # hmda19_df['lmi_def'].value_counts(dropna = False)

    # -- [markdown]
    # ### 16. Filter: 
    # 
    # #### For Conventional and FHA loans that first-lien, one-to-four unit, site built unites for home purchase where the applicant is going to live in that property

    # --
    one_to_four = ['1', '2', '3', '4']

    hmda19_df2 = hmda19_df[((hmda19_df['loan_type'] == '1') | (hmda19_df['loan_type'] == '2'))\
                        & (hmda19_df['occupancy_type'] == '1') &\
                            (hmda19_df['total_units'].isin(one_to_four)) &\
                            (hmda19_df['loan_purpose'] == '1') &\
                            (hmda19_df['action_taken'] != '6') &\
                            (hmda19_df['construction_method'] == '1') &\
                            (hmda19_df['lien_status'] == '1') &\
                            (hmda19_df['business_or_commercial_purpose'] != '1')].copy()

    print('len hmda19_df: ' + str(len(hmda19_df)))
    print('len hmda19_df2: ' + str(len(hmda19_df2)))

    # -- [markdown]
    # ### 17. Write new dataframe to CSV

    # --
    hmda19_df2.to_csv(clean2_filename, index = False)


