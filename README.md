## Fairness and Performance Testing via Incidents

This is the code and data for reproducing the experiments described in the paper "From Individual Experience to Collective Evidence: A Reporting-Based Framework for Identifying Systemic Harms."

To reproduce the paper results exactly, the shell scripts (`run_covid.sh` and `run_hmda.sh`) can be run directly (depending on your local environment, you may need to install packages from `requirements.txt` within the shell script). The `results` directory contains results from running those two shell scripts. The notebooks `plotting-covid.ipynb` and `plotting-hmda.ipynb` contain code for plotting and interpreting results. 

Other files: 
* `data` directory: contains preprocessed files, preprocessing code, as well as references to where to download the raw data files (at the time this paper was written in fall 2024).
* `results` directory: 
* `algorithms.py`: main code for algorithms. Includes an implementation of Wald's SPRT, though we found this performed poorly in practice and excluded it from the paper. 
* `run_experiment.py`: script for running _one_ dataset at _one_ $\beta$ for a fixed number of trials.  
* `load_data.py` and `utils.py`: helper files for (almost) all of the above. 

Questions about algorithm code and the HMDA dataset can be sent to Jessica (jessicadai@berkeley.edu); questions about the COVID vaccine dataset can be sent to Deb (rajiinio@berkeley.edu). 