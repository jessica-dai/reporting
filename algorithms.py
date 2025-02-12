import numpy as np
from utils import *


"""
    incident_db: df of all reports. each row is an individual report; 
    columns include the features that define groups 

    all_groups_dict: list of all groups (as dictionaries) to test for. all_groups_dict[i] gives the ith group, e.g. `{feature1: value1, feature2: value2, ...}`

    group_base_rates: base rates, i.e. Pr[G] in terms of all loan applicants, all vaccine recipients, etc.
"""

def run_test(incident_db, all_groups, base_rates, \
                 ALPHA=0.05, BETA=1.5, max_iter=20000, method='eval', asymptotic=False): 
    if method == 'eval':
        test = GenericTest(all_groups, base_rates, ALPHA)
    elif method == 'sprt':
        test = SPRTest(all_groups, base_rates, ALPHA)
    elif method == 'lil':
        test = LILTest(all_groups, base_rates, ALPHA, asymptotic=asymptotic)
    return test.run(incident_db, max_iter=max_iter, ALPHA=ALPHA, BETA=BETA)

##############################################
####### algs written for a single beta #######
##############################################

class GenericTest:
    """
    The base class `GenericTest` implements Bonferroni.
    Other methods are subclasses of `GenericTest` and may implement their own update and selection steps.
    """
    def __init__(self, all_groups, base_rates, ALPHA = 0.05, return_single=False):

        self.G = len(all_groups)
        self.base_rates = base_rates
        self.all_groups = all_groups
        self.alpha = ALPHA
        self.thresh = np.log(self.G/ALPHA)
        self.return_single = return_single
    
    def run(self, incident_db, max_iter=20000, lmbd='ons', BETA=1, ALPHA=None):
        """
        Main algorithm for running test with reports `incident_db`. 
        """

        self.omega_g = np.zeros(self.G)
        self.lambda_g = np.zeros(self.G) # np.ones(self.G)*0.5
        self.lambda_counter = np.zeros(self.G)  # sum of second moments for ONS, group counts for agrapa
        self.lambdavar_counter = np.zeros(self.G) # for agrapa, sum (X_i - muhat_i)^2

        rejected_groups = []
        rejected_times = []

        rejected_invalid = {}
        
        self.t = 1
        while self.t < min(max_iter, len(incident_db)):
            self._one_step_update(incident_db, BETA, lmbd) # this updates self.t
            # check if any group passes
            if np.any(self.omega_g > self.thresh - np.log(self.G)):
                    rejected_inds = np.where(self.omega_g > np.log(1/self.alpha))[0]
                    for ind in rejected_inds:
                        # only add if not already in rejected_nulls
                        if ind not in rejected_invalid.keys():
                            rejected_invalid[ind] = self.t
            if np.any(self.omega_g > self.thresh):
                if self.return_single:
                    return self.t, np.argmax(self.omega_g)
                else:
                    rejected_inds = np.where(self.omega_g > self.thresh)[0]
                    for ind in rejected_inds:
                        # only add if not already in rejected_nulls
                        if ind not in rejected_groups:
                            rejected_groups.append(ind)
                            rejected_times.append(self.t)

        invalid_t = [rejected_invalid[g] for g in rejected_groups]

        results = pd.DataFrame({'group': rejected_groups, 't': rejected_times, 't-inv': invalid_t})
        return results
    
    def _one_step_update(self, incident_db, BETA, lmbd):
        """
        Updates omegas & lambdas. 
        Updates t.
        """
        mu_0 = BETA * self.base_rates
        # current report 
        curr_report = incident_db.iloc[self.t-1]
        row_flags = np.array([np.product([curr_report[k] == group[k] for k in group]) for group in self.all_groups])
        g_t = row_flags - mu_0
        # positive capital process
        dot = self._update_omega(g_t)
        self._update_lambda(g_t, dot, lmbd, BETA)
        self.t += 1
   
    def _update_omega(self, g_t):
        dot = g_t*self.lambda_g
        self.omega_g += np.log(1 + dot)
        return dot
    
    def _update_lambda(self, g_t, dot, lmbd, BETA):

        if lmbd == 'ons':
            grad = g_t/(1 + dot)
            self.lambda_counter += grad **2
            const = 2/(2 - np.log(3))
            zterm = grad/(1 + self.lambda_counter)
            self.lambda_g = np.clip(const*zterm + self.lambda_g, 0, 1)

        elif lmbd == 'agrapa':
            self.lambda_counter += g_t + self.base_rates*BETA
            muhat_g = self.lambda_counter / self.t 
            diff_g = muhat_g - self.base_rates*BETA
            if self.t > 1:
                var_g = self.lambda_counter/(self.t-1) - 2 * self.lambda_counter*muhat_g/(self.t-1) + np.square(muhat_g)*self.t/(self.t-1)
                self.lambda_g = np.maximum(np.zeros(self.G), diff_g/(0.00000001 + var_g + np.square(diff_g)))
            self.lambda_g = np.clip(self.lambda_g, 0, 1/(self.base_rates*BETA))

class SPRTest(GenericTest):
    def __init__(self, all_groups, base_rates, ALPHA = 0.05, return_single=False):
        super().__init__(all_groups, base_rates, ALPHA, return_single)
        # note that self.lambda_counter will be group counts

    def _one_step_update(self, incident_db, BETA, lmbd=None):
        """
        Updates counts (per group test statistics)
        Updates t.
        """
        mu = BETA * self.base_rates
        eps = 0.05
        # current report 
        curr_report = incident_db.iloc[self.t-1]
        row_flags = np.array([np.product([curr_report[k] == group[k] for k in group]) for group in self.all_groups])
        # test statistic for SPRT is as follows 
        self.lambda_counter += row_flags
        self.omega_g = self.lambda_counter*np.log(1 + eps) + (self.t - self.lambda_counter)*(np.log(np.maximum(0.01, (1 - (1+eps)*mu))) - np.log(1 - mu))
        self.t += 1

class LILTest(GenericTest):

    def __init__(self, all_groups, base_rates, ALPHA = 0.05, return_single=False, asymptotic=False):
        super().__init__(all_groups, base_rates, ALPHA, return_single)
        self.asymp = asymptotic

    def _one_step_update(self, incident_db, BETA, lmbd=None):

        mu = BETA * self.base_rates
        # current report 
        curr_report = incident_db.iloc[self.t-1]
        row_flags = np.array([np.product([curr_report[k] == group[k] for k in group]) for group in self.all_groups])
        # test statistic is count vs. a group-specific threshold
        self.omega_g += row_flags
        thresh_factor = np.sqrt(np.minimum(mu, 1)*np.maximum((1-mu), 0)) if self.asymp else 0.5
        thresh = (self.t)*mu + thresh_factor*np.sqrt(2.07*(self.t)*np.log((2+np.log2(self.t))**2/self.alpha))
        self.thresh = 20000 if (self.t < 25 and self.asymp) else thresh
        self.t += 1