#!/bin/bash

for i in {1..20}; 
do 
    sbatch ober_complex.sh
    sbatch ober_real.sh
    sbatch ober_real_tf.sh 
done
