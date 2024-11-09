# Real-Time Uniprocessor - Scheduler Simulator
A simulator for scheduling algorithms commonly used in real-time operating systems, including:

1. Rate Monotonic (RM)
2. Deadline Monotonic (DM)
3. Earliest-Deadline First (EDF)
4. Round Robin (RR)
5. Audsley’s Algorithm

The simulator assesses task schedulability based on attributes like offset, computation time, deadline, and period.

## How to Run
```bash
python3 simulator.py {rm|dm|audsley|edf|rr} <task_set_file|task_set_directory> [options]
```

### Parameters
_Algorithm_: Choose one of `rm`, `dm`, `audsley`, `edf`, or `rr`.

_Task Set_: Provide a path to either a single task set file or a directory of task set files for batch processing.

_Options_:
- -v or --verbose: Enable detailed output, showing the full schedule if a simulation is run.
- -f or --force_simulation: Force full simulation even if shortcuts (like utilization checks) are available.

### Task Set File Format
Each task is represented by four parameters:
O: Offset
C: Computation time
D: Deadline
T: Period

Tasks are added with their respective offset 𝑂𝑖, computation time 𝐶𝑖, deadline 𝐷𝑖 and period 𝑇𝑖. Task set files are simple Comma Separated Value (CSV) files where the line 𝑖 encodes the 𝑂𝑖,𝐶𝑖,𝐷𝑖,𝑇𝑖 of task 𝑖.
```text
0,7,41,58
1,4,62,69
4,3,12,80
0,8,24,94
```

## Project Structure
- simulator.py: Main entry point to run the simulations.
- algorithms.py: Contains the classes for each scheduling algorithm.
- entities.py: Defines core data structures like TaskSet and Task.
- helpers.py: Utility functions for feasibility checks, utilization, and other calculations.
- plotters.py: Functions to visualize results and performance of different algorithms.

### Example
To run the simulator with Deadline Monotonic scheduling on a specific task set file:

```bash
python3 main.py dm path/to/task_set.csv -v
```
### Additional Features
_Batch Processing_: If a directory of task set files is provided, the simulator will process all files in parallel and generate aggregate statistics.

_Visualization_: The plotters.py module includes methods to visualize success rates and feasibility ratios for different algorithms, especially useful when comparing performance across multiple task sets.