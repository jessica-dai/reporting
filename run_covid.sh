echo "hello - covid"

for beta in 1.01 1.5 2.0 2.5 3.0
do
    echo "Running experiments for beta=$beta"
    python run_experiment.py --DATASET=covid --BETA=$beta --N_TRIALS=100
done
