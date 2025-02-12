import pickle
from itertools import product


def get_groups(dem_vals, dem_cols):
    """
    :param dem_vals: list of lists of values for each demographic feature
        for example, [['M', 'F'], ['W', 'B', 'H'], ['20s', '30s', '40s']]
    :param dem_cols: list of demographic feature names
        for example, ['Sex', 'Race', 'Age']

    :returns: list of dictionaries, each dictionary is a (fine-grained) group
        for example, [{'Sex': 'M', 'Race': 'W', 'Age': '20s'}, 
                        ...
                      {'Sex': 'M', 'Race': 'W'},
                        ...
                      {'Sex': 'M'}, 
                        ...
                      {'Age': '40s'}]
    """
    for i in range(len(dem_vals)):
        if None not in dem_vals[i]:
            dem_vals[i].append(None) 
    prod = product(*(dem_vals))
    return list(map(lambda x: {k: v for k, v in zip(dem_cols, x) if v is not None}, prod))[:-1]

def save_preprocessed(database, groups_list, base_rates, save_path):
    """
    :param database: pandas dataframe with the reports
    :param groups_list: list of dictionaries, each dictionary is a (fine-grained) group
    :param base_rates: list with the base rates for each group 
        base_rates[i] corresponds to the base rate of groups_list[i]
    :param save_path: path where the preprocessed data will be saved
    """
    with open(save_path + 'groups.pkl', 'wb') as f:
        pickle.dump(groups_list, f)
    with open(save_path + 'base_groups.pkl', 'wb') as f:
        pickle.dump(base_rates, f)
    database.to_csv(save_path + 'reports.csv', index=False)