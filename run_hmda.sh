echo "hello"

for beta in 1.8
do
    echo "Running experiments for beta=$beta"
    for dataset in hmda_all-denials hmda_corr hmda_anticorr # hmda_hdti-denials 
    do
        echo "Running experiments for dataset=$dataset"
        python run_experiment.py --DATASET=$dataset --BETA=$beta --N_TRIALS=100 
    done
done
