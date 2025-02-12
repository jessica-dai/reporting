import pandas as pd

################################
# clean_data.py from Markup code
################################

def clean_location(row):
    
    '''
    Standardizes census tract and county codes into one column.
    Choosing tract or county for records where they are missing one piece of info
    '''
    
        
    census_tract = row['census_tract']
    county = row['county_code']
    null = ['00-00', 'ii-ii']
        
    ### If there's tract info but no county, return tract
    if census_tract not in null and county in null:
        return census_tract
        
    ### If there's no tract info but there's county info, return county
    elif census_tract in null and county not in null:
        return county
        
    ### When tract and county are not null, return tract
    elif census_tract not in null and county not in null:
        return census_tract
        
    ### When tract and county are both null, return '-----'
    elif census_tract in null and county in null:
        return '-----'
        
        
        
def clean_race_ethnicity(row):
    
    '''
    Standardizing and merging race and ethnicity columns into one consistent column
    '''
    
    try:
        race = row['applicant_race_1']
        ethnicity = row['applicant_ethnicity_1']
    
    ### this is intended for co-applicants
    except KeyError:
        race = row['co_applicant_race_1']
        ethnicity = row['co_applicant_ethnicity_1']
    

    
    latinx = ['1', '11', '12', '13', '14']
    asian = ['2', '21', '22', '23', '24', '25', '26', '27']
    pac_islander = ['4', '41', '42', '43', '44']
    black = ['3']
    white = ['5']
    native = ['1']
    ethnicity_na = ['2', '3', '4', '000']
    race_na = ['6', '7', '-1', '000']
    
    ### Used for co-applicants
    ethnicity_nocoapp = ['5']
    race_nocoapp = ['8']
    
    
    ### Latinx
    if ethnicity in latinx:
        return '6'
    ### Black
    elif ethnicity not in latinx and race in black:
        return '3'
    ### Asian
    elif ethnicity not in latinx and race in asian:
        return '2'
    ### Pacific Islander
    elif ethnicity not in latinx and race in pac_islander:
        return '4'
    ### Native
    elif ethnicity not in latinx and race in native:
        return '1'
    ### White
    elif ethnicity not in latinx and race in white:
        return '5'
    # Race NA
    elif ethnicity in ethnicity_na and race in race_na:
        return '7'
        
    ### No Co-Applicants: Where both are no co-applicants OR where just one is no co-applicant
    elif (ethnicity in ethnicity_nocoapp and race in race_nocoapp) or (race in race_nocoapp and ethnicity in ethnicity_na) or (ethnicity in ethnicity_nocoapp and race in race_na): 
        return '8'
        
def find_same_race(row):
    '''
    Looking at an applicant's and co-applicant's race to determine to same or different race
    '''
    
    app_race_ethnicity = row['app_race_ethnicity']
    coapp_race_ethnicity = row['coapp_race_ethnicity']
    
    race_yes = ['1', '2', '3', '4', '5', '6']
    race_na = ['7']
    no_coapp = ['8']
    
    
    ### Same Race: Where App's race is not 7 and co-app's is not 8 and race is the same for both
    if app_race_ethnicity not in race_na and coapp_race_ethnicity not in no_coapp and app_race_ethnicity == coapp_race_ethnicity:
        return '1'
        
    ### Different Race:
    elif app_race_ethnicity not in race_na and coapp_race_ethnicity not in race_na + no_coapp and app_race_ethnicity != coapp_race_ethnicity:
        return '2'
    
    ### Race NA
    elif (app_race_ethnicity in race_na and coapp_race_ethnicity in race_na) or (app_race_ethnicity in race_yes and coapp_race_ethnicity in race_na) or (app_race_ethnicity in race_na and coapp_race_ethnicity in race_yes):
        return '3'
        
    ### No Co-Applicant
    elif coapp_race_ethnicity in no_coapp:
        return '4'
        
        
def clean_credit_model(row):
    
    '''
    Standardizing credit model column
    '''
    
    equifax = ['1']
    experian = ['2']
    transunion = ['3', '4']
    vantage = ['5', '6']
    more_than_one = ['7']
    other_model = ['8']
    credit_na = ['9', '1111']
    
    credit_model = row['applicant_credit_score_type']
    
    
    if credit_model in equifax:
        return '1'
    elif credit_model in experian:
        return '2'
    elif credit_model in transunion:
        return '3'
    elif credit_model in vantage:
        return '4'
    elif credit_model in more_than_one:
        return '5'
    elif credit_model in other_model:
        return '6'
    elif credit_model in credit_na:
        return '7'
        
        
def find_coapplicants(row):
    
    '''
    Looking for co applicants within five columns
    '''
    
    ### Co-Applicants
    coapp_race = ['1', '2', '3', '4', '5', '6']
    coapp_sex = ['1', '2']
    coapp_age = ['<25', '25-34', '35-44', '45-54', '55-64', '65-74', '>74']
    coapp_credit = ['1', '2', '3', '4', '5', '6', '7', '8']

    ### NA Co-Applicants
    na_coapp_race = ['7']
    na_coapp_sex = ['3', '4', '6']    
    na_coapp_age = ['8888']
    na_coapp_credit = ['9', '1111']
    
    ### No Co-Applicants
    nocoapp_race = ['8']
    nocoapp_sex = ['5']
    nocoapp_age = ['9999']
    nocoapp_credit = ['10']
    
    
    ### Co-Applicants Rows
    co_race = row['coapp_race_ethnicity']
    co_sex = row['co_applicant_sex']
    co_age = row['co_applicant_age']
    co_credit = row['co_applicant_credit_score_type']
    
    
    # CO APPLICANTS: 1
    ### Records where Race is known and the other fields are not "no co-applicant" 
    ### race = y AND sex != n AND age != n AND credit != n (6003752 records)
    if co_race in coapp_race and co_sex not in nocoapp_sex and co_age not in nocoapp_age and co_credit not in nocoapp_credit:
        return '1'
    
    ### Records where Sex is known and the other fields are not "no co-applicant"
    ### race != n AND sex = y AND age != n AND credit != n (438837 records)
    elif co_race not in nocoapp_race and co_sex in coapp_sex and co_age not in nocoapp_age and co_credit not in nocoapp_credit:
        return '1'
    
    ### Records where Age is known and the other fields are not "no co-applicant"
    ### race != n AND sex != n AND age = y AND credit != n (643528 records)
    elif co_race not in nocoapp_race and co_sex not in nocoapp_sex and co_age in coapp_age and co_credit not in nocoapp_credit:
        return '1'
    
    ### Records where Credit is known and the other fields are not "no co-applicant"
    ### race != n AND sex != n AND age != n AND credit = y (99 records)
    elif co_race not in nocoapp_race and co_sex not in nocoapp_sex and co_age not in nocoapp_age and co_credit in coapp_credit:
        return '1'
        
    ### Where race and sex have info, but age or credit are "no co-applicant"
    # race = y AND sex = y AND (age = n or credit = N) (20324 records)
    elif (co_race in coapp_race and co_sex in coapp_sex) and (co_age in nocoapp_age or co_credit in nocoapp_credit):
        return '1'
    
    ### Where race or sex have info and the other is NA, but age or credit are "no co-applicant"
    # ((r = na and sex = y) or (r = y and sex = na)) and (age = no or credit = no) (497 records)
    elif ((co_race in na_coapp_race and co_sex in coapp_sex) or (co_race in coapp_race and co_sex in na_coapp_sex)) and\
    (co_age in nocoapp_age or co_credit in nocoapp_credit):
        return '1'
    
    # NO CO APPLICANTS: 2
    
    ### Where race is no and the rest are not "yes"
    #race = no AND sex != y AND age != y AND credit != y (9136951 records)
    elif co_race in nocoapp_race and co_sex not in coapp_sex and co_age not in coapp_age and co_credit not in coapp_credit:
        return '2'
    
    ### Where sex is no and the rest are not "yes"
    #race != y AND sex = n AND age != y AND credit != y (1234 records)
    elif co_race not in coapp_race and co_sex in nocoapp_sex and co_age not in coapp_age and co_credit not in coapp_credit:
        return '2'
    
    ### Where age is no and the rest are not "yes"
    #race != y AND sex != y AND age = n AND credit != y (131133 records)
    elif co_race not in coapp_race and co_sex not in coapp_sex and co_age in nocoapp_age and co_credit not in coapp_credit:
        return '2'
    
    ### Where credit is no and the rest are not "yes"    
    #race != y AND sex != y AND age != y AND credit = n (44 records)
    elif co_race not in coapp_race and co_sex not in coapp_sex and co_age not in coapp_age and co_credit in nocoapp_credit:
        return '2'
    
    ### NA CO-APPLICANTS:
    
    ### Where all columns are not applicable
    #race = na AND sex = na AND age = na AND credit = na (1143149 records)
    elif co_race in na_coapp_race and co_sex in na_coapp_sex and co_age in na_coapp_age and co_credit in na_coapp_credit:
        return '3'
        
    ### Where race and sex, or at least one of them are no, and age or credit are yes
    # ((race = n and sex = n) or (race = n and sex = na) or (race = na and sex = n))and (age = y or credit = y) (20450 records)
    elif ((co_race in nocoapp_race and co_sex in nocoapp_sex) or (co_race in nocoapp_race and co_sex in na_coapp_sex) or\
    (co_race in na_coapp_race and co_sex in nocoapp_sex)) and (co_age in coapp_age or co_credit in coapp_credit):
        return '3'
    
    ### Where race and sex contradict each other
    # (race = y and sex = n) or (race = n and sex = y) (3450 records)
    elif (co_race in coapp_race and co_sex in nocoapp_sex) or (co_race in nocoapp_race and co_sex in coapp_sex):
        return '3'
    
    ### Where race and sex are not applicable and age and credit contradict each other
    # (race = na and sex = na) and ((age = y and credit = n) or (age = n and credit = y)) (1093 records)
    elif (co_race in na_coapp_race and co_sex in na_coapp_sex) and ((co_age in coapp_age and co_credit in nocoapp_credit) or\
    (co_age in nocoapp_age and co_credit in coapp_credit)):
        return '3'
        
        
def clean_outcomes(row):
    
    '''
    Standardize outcomes, grouping the ambiguous outcomes together
    '''
    
    outcome = row['action_taken']
    other_outcomes = ['2', '4', '5', '7', '8']
    
    ### Loans
    if outcome == '1':
        return '1'
    
    ### Denials
    elif outcome == '3':
        return '3'
    
    ### Othercomes
    elif outcome in other_outcomes:
        return '4'
    
    ### Purchase loans
    elif outcome == '6':
        return '6'
        
def find_aus_patterns(df):
    
    
    '''
    Looking for the patterns within the five aus columns
    Answering questions: How many times was the same aus used or were different ones used
    '''
    
    
    df_container = []
    
    for index_num in df.index:
        
        ### take a single row
        single_row_df = df.loc[[index_num]].copy()
        
        ### convert to series
        row = pd.Series(single_row_df.values[0])
        ### Count the values in that series
        
        valuescount_df = pd.DataFrame(row.value_counts(dropna = False))
        num_unqiue_values = valuescount_df.index.nunique(dropna = False)
        
        try:
            number_nulls = valuescount_df[(valuescount_df.index.isnull())].values[0][0]
        except IndexError:
            number_nulls = 0
            
        single_row_df['number_of_values'] = num_unqiue_values
        single_row_df['number_of_nulls'] = number_nulls
        df_container.append(single_row_df)
    
    df = pd.concat(df_container)
    
    return df
    
def clean_aus(row):
    
    '''
    Created a standardized column for AUS
    '''
    
    
    aus1 = row['aus_1']
    unique_values = row['number_of_values']
    nulls = row['number_of_nulls']
    
    ### Only AUS was used
    if aus1 != '1111' and unique_values == 2 and nulls == 4:
        return '1'
    
    ### Same AUS used multiple times
    elif (unique_values == 2 and (nulls > 0 and nulls < 4)) or (unique_values == 1 and nulls == 0):
        return '2' 
    
    ### Different AUS used
    elif (unique_values >= 2 and nulls == 0) or (unique_values >= 3 and nulls <= 3):
        return '3'
        
    ## Exempt  
    elif aus1 == '1111':
        return '4'
    
        
        
################################
# categorize_data.py from Markup code
################################
    


def setup_dti_cat(row):
    
    '''
    Setup dti categories based on lenders and CFPB approach to them
    '''
    
    dti = row['debt_to_income_ratio']
    
    healthy = ['<20%', '20%-<30%', '30%-<36%', ]
    manageable = ['36', '37', '38', '39', '40', '41', '42',]
    unmanageable = ['43', '44', '45', '46', '47', '48', '49']
    struggling = ['50%-60%', '>60%']
    
    if dti in healthy:
        return '1'
    elif dti in manageable:
        return '2'
    elif dti in unmanageable:
        return '3'
    elif dti in struggling:
        return '4'
        
    elif dti == 'Exempt':
        return '5'
    elif dti == 'null':
        return '6'
        
        
def categorize_cltv(row):
    
    '''
    Use CLTV to create a downpayment flag
    
    '''
    
    cltv = row['cltv_ratio']
    
    if cltv <= 80:
        return '1'
    elif cltv > 80:
        return '2'
        
    else:
        return '3'
        
        
        
def calculate_prop_zscore(row):
    
    '''
    Calculate property z scores 
    Mean and standard deviation are based on ratio below 10
    '''
    
    
    ### This numbers come from 1_property_value_analysis Jupyter Notebook
    standard_deviation = 0.907
    mean = 1.475
    
    prop_value_ratio = row['property_value_ratio']
    
    z_score = ((prop_value_ratio - mean)/standard_deviation)
    
    return z_score
        
def categorize_property_value_ratio(row):
    
    '''
    Creating categories based on z-scores
    '''
    
    prop_value_ratio = row['property_value_ratio']  
    

    ### More than one negative standard deviation
    if prop_value_ratio >= 0.009 and prop_value_ratio <= 0.567:
        return '1'
    
    ### Between negative one standatd deviation and zero
    elif prop_value_ratio >= 0.568 and prop_value_ratio <= 1.474:
        return '2'
        
    ### Between zero and one standard deviation       
    elif prop_value_ratio >= 1.475 and prop_value_ratio <= 2.381:
        return '3'
    
    ### Between one standard deviation and two standard deviations
    elif prop_value_ratio >= 2.382 and prop_value_ratio <= 3.288:
        return '4'
    
    ### Greater than two standard deviations but less than 10 for the property value ratio
    elif prop_value_ratio >= 3.289 and prop_value_ratio < 10:
        return '5'
    
    ### Greater than 10 property value ratio
    elif prop_value_ratio >= 10:
        return '6'
        
    else:
        return '7'

        

def categorize_age(row):
    
    '''
    Creating categories for applicant's age
    '''
    
    age = row['applicant_age']
    
    if age == '<25':
        return '1'
        
    elif age == '25-34':
        return '2'
        
    elif age == '35-44':
        return '3'
        
    elif age == '45-54':
        return '4'
        
    elif age == '55-64':
        return '5'
        
    elif age == '65-74':
        return '6'
        
    elif age == '>74':
        return '7'
        
    elif age == '8888' or age == '9999':
        return '8'
    
    
def categorize_sex(row):
    
    '''
    Categorizing applicant's sex
    '''
    
    sex = row['applicant_sex']
    
    
    if sex == '1':
        return '1'
        
    elif sex == '2':
        return '2'
    
    elif sex == '3' or sex == '4':
        return '3'
        
    elif sex == '6':
        return '6'
        
        
def categorize_underwriter(row):
    
    '''
    Categorizing underwriter to see which main underwriter the lender is using 
    '''
    
    
    aus_cat = row['aus_cat']
    aus1 = row['aus_1']
    
    one_aus = ['1', '2']
    
    
    ### Desktop Underwriter
    if aus_cat in one_aus and aus1 == '1':
        return '1'
    ### Loan Prospector
    elif aus_cat in one_aus and aus1 == '2':
        return '2'
    ### Technology Open to Approved Lenders
    elif aus_cat in one_aus and aus1 == '3':
        return '3'
    ### Guaranteed Underwirting System
    elif aus_cat in one_aus and aus1 == '4':
        return '4'
    ### Other
    elif aus_cat in one_aus and aus1 == '5':
        return '5'
    ### No main AUS
    elif aus_cat == '3':
        return '6'
        
    ### Not Applicable or Exempt
    elif aus1 == '6' or aus1 == '1111':
        return '7'
    
    
def categorize_loan_term(row):
    
    '''
    Categorize loan term into more or less than 30 years or exactly 30 years
    '''
    
    loan_term = row['em_loan_term']
    
    ### 30 year mortgage
    if loan_term == 360:
        return '1'
    ### less than 30
    elif loan_term < 360:
        return '2'
    ### More than 30
    elif loan_term > 360:
        return '3'
    ### Exempts and NAs
    else:
        return '4'
        
        
def categorize_lmi(row):
    
    '''
    Categorize low-to-moderate income neighborhoods
    '''
    
    tract_msa_ratio = row['tract_msa_ratio']
    
    ### Low 
    if tract_msa_ratio > 0 and tract_msa_ratio < 50:
        return '1'
    ### Moderate
    elif tract_msa_ratio >= 50 and tract_msa_ratio < 80:
        return '2'
    ### Middle
    elif tract_msa_ratio >= 80 and tract_msa_ratio < 120:
        return '3'
    ### Upper
    elif tract_msa_ratio >= 120:
        return '4'
    ### None
    elif tract_msa_ratio == 0:
        return '5'
    
    
    
    
    