# CromScan

**CromScan** is a lightweight workflow performance profiling and visualization tool for **Cromwell WDL** pipelines running on **SLURM** clusters. It parses Cromwell execution logs together with SLURM accounting records to generate task-level performance metrics and publication-quality visualizations, helping users identify resource bottlenecks and optimize workflow execution.

---

## Features

* Parses Cromwell workflow logs automatically.
* Retrieves execution statistics from SLURM using `sacct`.
* Computes task-level performance metrics (CPU efficiency, Memory Usage, and Parallel vs. sequential task execution)
* Generates high-resolution figures for workflow performance analysis.

---

## Workflow

```
Cromwell Log
        │
        │
        ▼
Extract Task Information
(Start, End, Job IDs)
        │
        ▼
SLURM sacct
(Resource Usage)
        │
        ▼
Performance Metrics
        │
        ▼
Visualization
```

---

## Requirements

* Python 3.10 or newer
* Linux operating system
* Cromwell
* SLURM scheduler
* `sacct` available in your environment

Python packages:

```
pandas
numpy
matplotlib
```

Install dependencies:

```bash
pip install pandas numpy matplotlib
```

---

## Usage

```bash
python CromScan.py \
    -l /path/to/cromwell.log \
    -o /path/to/output_directory
```

### Arguments

| Argument         | Description       | Required |
| ---------------- | ----------------- | -------- |
| `-l`, `--log`    | Cromwell log file | Yes      |
| `-o`, `--outDir` | Output directory  | Yes      |

---

## Output

CromScan generates several performance visualizations.

### 1. Workflow Gantt Chart

Displays the execution timeline of each task relative to the workflow start.

* Task durations
* Workflow wall time
* Parallel and sequential execution

Output:

```
Workflow_Gantt_Chart.png
```

---

### 2. Memory Usage Chart

Compares the maximum memory consumed by each task against the requested memory allocation.
Output:

```
Memory_Usage_Chart.png
```

---

### 3. CPU Efficiency

Shows how efficiently each task utilized its allocated CPUs.

Efficiency categories:
Output:

```
CPU_Efficiency.png
```

---

## Performance Metrics

For each workflow task, CromScan computes:

| Metric            | Description                                     |
| ----------------- | ----------------------------------------------- |
| Start Time        | Task start time extracted from the Cromwell log |
| End Time          | Task completion time                            |
| Duration          | Execution time (minutes)                        |
| Wall Time         | Total workflow runtime                          |
| Requested CPUs    | CPUs requested from SLURM                       |
| Requested Memory  | Memory requested from SLURM                     |
| MaxRSS            | Maximum resident memory used                    |
| CPU Time          | Total CPU time consumed                         |
| Elapsed Time      | Actual runtime reported by SLURM                |
| CPU Efficiency    | CPUTime ÷ (Elapsed × Requested CPUs)            |
| Memory Efficiency | MaxRSS ÷ Requested Memory                       |
| Execution Mode    | Parallel or Sequential                          |

---

## Example

```bash
python CromScan.py \
    -l workflow.log \
    -o Results
```

Generated output:

```
Results/
├── Workflow_Gantt_Chart.png
├── Memory_Usage_Chart.png
├── CPU_Efficiency.png
└── Performance.csv
```

---
