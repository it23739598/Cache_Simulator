Cache Memory Hierarchy Simulator & Plotting Scripts[1][2][3]

## Project overview
This repository contains a configurable cache and memory hierarchy simulator written in Python, along with MATLAB scripts used to generate publication-quality plots for an Advanced Computer Organization & Architecture assignment on cache performance analysis. The work explores how cache size, block size, associativity, and replacement policy affect hit ratio and average memory access time (AMAT) in single-level and multi-level cache designs.[2][3][1]

## Features
- Parameterized cache model supporting multiple replacement policies: LRU, FIFO, Random, and LFU.[2]
- Support for sweeps over cache size, block size, and associativity, with per-cache and overall statistics such as hits, misses, hit ratio, miss ratio, AMAT, and total access time.[2]
- Multi-level cache hierarchy modeling with configurable hit times and main memory access latency.[1][2]
- CSV export of simulation results for downstream analysis and plotting.[2]
- MATLAB plotting script to generate AMAT comparison, hit ratio comparison, associativity effect, and replacement policy comparison figures using actual simulation outputs.[3][1]

## Repository structure
- `assingment.py`: Core cache & memory hierarchy simulator, including cache line and cache classes, hierarchy management, trace generators, and experiment helpers for running configurations and exporting CSVs.[2]
- `ACOA_plots.m`: MATLAB script that loads simulation outputs and produces plots for AMAT vs configuration, L1 hit ratio, associativity effects, and replacement policy comparisons, saving them as PNG files.[3]
- `ACOA_FinalReport.pdf`: Report documenting theoretical background, experiment design, simulation methodology, result analysis, and conclusions on cache performance optimization.[1]

## Requirements
- Python 3.x with standard library modules (`math`, `random`, `time`, `csv`, `typing`).[2]
- MATLAB (R2013b or later recommended for `readtable`) for running the plotting script.[3]

## How to run simulations
1. Prepare or modify a memory access trace using the trace generator utilities or your own trace inside `assingment.py`.[2]
2. Define one or more cache configurations (e.g., 1-level direct-mapped, 4-way set-associative, 2-level hierarchy) by instantiating `Cache` objects and passing them to `run_simulation`.[2]
3. Run the Python script to execute the simulation, print per-level statistics, and write CSV files (e.g., for configuration sweeps and policy comparisons).[2]
4. Ensure that the generated CSV files (such as `policy_comparison.csv` and associativity/configuration result files) are stored in the same directory as the MATLAB script if you intend to plot them.[3][2]

## How to generate plots
1. Run the Python simulations and confirm that the required CSV files with hit ratios and AMAT values have been generated.[2]
2. Open `ACOA_plots.m` in MATLAB and adjust any file names or hard-coded values if your CSV naming differs.[3]
3. Execute `ACOA_plots.m` to generate and save:  
   - `amat_comparison_plot_actual.png`  
   - `hit_ratio_comparison_plot_actual.png`  
   - `associativity_effect_plot_actual.png`  
   - `replacement_policy_comparison.png`[3]

## Academic context and usage
The simulator and plots were developed for a 2nd-year Advanced Computer Organization & Architecture course project titled “Performance Analysis and Design Strategies for Cache Memory Systems: A Simulation Approach.” The code is suitable as a learning tool or baseline for further research on cache hierarchy design, replacement policies, and performance tuning in modern processors.[1][3][2]

[1](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/69354439/ceee6757-6fc6-4cbe-970f-42a504296c71/ACOA_FinalReport.pdf)
[2](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/69354439/fc632048-91ba-4e2a-9242-cf047e89a0b1/assingment.py)
[3](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/69354439/3be5c052-835b-4ff9-a7f0-5298cfaad13d/ACOA_plots.m)
