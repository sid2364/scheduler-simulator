# scheduler-simulator
Simulator for rate monotonic, deadline monotonic, EDF and RR scheduling algorithms

## How to run
```
python3 simulator.py {rm,dm,audsley,edf,rr} task_set_file
```

## Task set file format
Tasks are added with their respective offset 𝑂𝑖, computation time 𝐶𝑖, deadline 𝐷𝑖 and period 𝑇𝑖. Task set filesare simple Comma Separated Value (CSV) files where the line 𝑖 encodes the 𝑂𝑖,𝐶𝑖,𝐷𝑖,𝑇𝑖 of task 𝑖
```text
0,7,41,58
1,4,62,69
4,3,12,80
0,8,24,94
```
