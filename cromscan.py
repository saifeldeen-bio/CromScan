import matplotlib.pyplot as plt
import pandas as pd
import os
import sys
import numpy as np
import argparse
import subprocess
import matplotlib.patches as mpatches
####################################### parser ########################################
class CustomArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(f'Error: {message}')
        self.print_help()
        sys.exit(2)
parser = argparse.ArgumentParser(description="CromScan v1.0.0 is a performance profiling tool for Cromwell WDL workflows that generates execution "
                                "statistics and visual reports for workflow timelines, CPU efficiency, memory usage, and resource utilization.")
parser.add_argument("-l", "--log", type=str, required=True, help="Path to Cromwell log File")
parser.add_argument("-o", "--outDir", type=str, required=True, help="Path to outputs directory")
args = parser.parse_args()
try:
    os.mkdir(os.path.expanduser(args.outDir))
except:
    print(f"OutDir exists: {args.outDir}")

logFile = os.path.expanduser({args.log})
command = f"grep 'Starting' {logFile}" 
StartTimes=subprocess.run(command, shell=True,capture_output=True, text=True)
print(StartTimes.stdout)
TasksStarts = list()
for line in StartTimes.stdout.splitlines():
    try:
        StartHour = int(line.split()[1].split(":")[0]) * 60
        StartMin = int(line.split()[1].split(":")[1])
        StartSec = int(line.split()[1].split(":")[2].split(",")[0]) / 60
        StartTotal = StartHour + StartMin + StartSec
        if len(line.split()) == 7:
            Task = line.split()[-1].split(".")[1]
            TasksStarts.append({"Task":Task,"StartTime":StartTotal})
        else:
            tasks = line.split()[6:]
            for task in tasks:
                Task = task.split(".")[1]
                Task = Task.removesuffix(",")
                TasksStarts.append({"Task":Task,"StartTime":StartTotal})
    except:
        continue
TasksStarts = pd.DataFrame(TasksStarts)

command = f"grep 'Done' {logFile}" 
EndTimes=subprocess.run(command, shell=True,capture_output=True, text=True)

TasksEnds = list()
for line in EndTimes.stdout.splitlines():
    try:
        EndHour = int(line.split()[1].split(":")[0]) * 60
        EndMin = int(line.split()[1].split(":")[1])
        EndSec = int(line.split()[1].split(":")[2].split(",")[0]) / 60
        EndTotal = EndHour + EndMin + EndSec
        Task = line.split()[4].split(".")[1].split(":")[0]
        TasksEnds.append({"Task":Task,"EndTime":EndTotal})
    except:
        continue
TasksEnds = pd.DataFrame(TasksEnds)

command = f"grep 'job id' {logFile}" 
tasksids=subprocess.run(command, shell=True,capture_output=True, text=True)

TasksIDs = list()
for line in tasksids.stdout.splitlines():
    try:
        Task = line.split()[4].split(".")[1].split(":")[0]
        JobID = line.split()[-1]
        TasksIDs.append({"Task":Task,"JobID":JobID})
    except:
        continue
TasksIDs = pd.DataFrame(TasksIDs)
TasksData = pd.merge(TasksStarts, TasksEnds, on='Task', how='outer').merge(TasksIDs, on='Task', how='outer')
TasksData["Duration"] = TasksData["EndTime"] - TasksData["StartTime"]

#################################### Get CPUs and Mem information ################################################
JobsData = list()
for JobId in TasksData["JobID"]:
    command=f"sacct -j {JobId} --format=JobID,JobName,Elapsed,CPUTime,MaxRSS,ReqCPUS,ReqMem,State --units=G"
    JobData = subprocess.run(command, shell=True,capture_output=True, text=True)
    ReqCPUS = eval(JobData.stdout.splitlines()[2].split()[4])
    ReqMem = eval(JobData.stdout.splitlines()[2].split()[5].removesuffix("G"))
    MaxRSS = eval(JobData.stdout.splitlines()[3].split()[4].removesuffix("G"))
    if "-" in JobData.stdout.splitlines()[3].split()[3]:
        CpuTimeD = int(JobData.stdout.splitlines()[3].split()[3].split("-")[0]) * 24 * 60 * 60
        CpuTimeH = int(JobData.stdout.splitlines()[3].split()[3].split(":")[0].split("-")[1]) * 60 * 60
        CpuTimeM = int(JobData.stdout.splitlines()[3].split()[3].split(":")[1]) * 60
        CpuTimeS = int(JobData.stdout.splitlines()[3].split()[3].split(":")[2])
        CpuTime = CpuTimeD + CpuTimeH + CpuTimeM + CpuTimeS
    else:
        CpuTimeH = int(JobData.stdout.splitlines()[3].split()[3].split(":")[0]) * 60 * 60
        CpuTimeM = int(JobData.stdout.splitlines()[3].split()[3].split(":")[1]) * 60
        CpuTimeS = int(JobData.stdout.splitlines()[3].split()[3].split(":")[2])
        CpuTime = CpuTimeH + CpuTimeM + CpuTimeS

    if "-" in JobData.stdout.splitlines()[1].split()[2]:
        ElapsedD = int(JobData.stdout.splitlines()[3].split()[2].split("-")[0]) * 24 * 60 * 60
        ElapsedH = int(JobData.stdout.splitlines()[3].split()[2].split(":")[0].split("-")[1]) * 60 * 60
        ElapsedM = int(JobData.stdout.splitlines()[3].split()[2].split(":")[1]) * 60
        ElapsedS = int(JobData.stdout.splitlines()[3].split()[2].split(":")[2])
        Elapsed = ElapsedD + ElapsedH + ElapsedM + ElapsedS
    else:
        ElapsedH = int(JobData.stdout.splitlines()[3].split()[2].split(":")[0]) * 60 * 60
        ElapsedM = int(JobData.stdout.splitlines()[3].split()[2].split(":")[1]) * 60
        ElapsedS = int(JobData.stdout.splitlines()[3].split()[2].split(":")[2])
        Elapsed = ElapsedH + ElapsedM + ElapsedS
    try:
        CpuEff = (CpuTime / (Elapsed*ReqCPUS)) * 100
        MemEff = (MaxRSS/ReqMem) * 100
    except:
        CpuEff = 0
        MemEff = 0
    JobsData.append({"JobID": JobId, "ReqCPUsGB":ReqCPUS, "ReqMemGB":ReqMem, "MaxRSSGB":MaxRSS, "CpuTimeSec":CpuTime, "ElapsedSec":Elapsed, "CpuEff%":CpuEff, "MemEff%":MemEff})
JobsData = pd.DataFrame(JobsData)
TasksData = pd.merge(TasksData, JobsData, on='JobID', how='outer')
TasksData["TempCol"] = TasksData["StartTime"].astype(int)
TasksData["Flow"] = np.where(TasksData["TempCol"].duplicated(keep=False), "Parallel", "Sequential")
TasksData = TasksData.drop(columns=["TempCol"])
TasksData["CpuEff"] = np.where(TasksData["CpuEff%"] >= 70, "Good", np.where((TasksData["CpuEff%"] >= 30) & (TasksData["CpuEff%"] < 70), "Moderate", "Poor"))
TasksData["MemEff"] = np.where(TasksData["MemEff%"] > 70, f"> 70% of Requested", np.where((TasksData["MemEff%"] >= 30) & (TasksData["MemEff%"] <= 70), f"30-70% of Requested", f"< 30% of Requested"))
Offset = min(TasksData["StartTime"])
TasksData["StartTimeOffsit"] = TasksData["StartTime"] - Offset
TasksData["EndTimeOffsit"] = TasksData["EndTime"] - Offset
TasksDataSorted = TasksData.sort_values(by="StartTime")
TasksDataSorted.to_csv(os.path.expanduser(f"{args.outDir}/Performance.csv"), index=False)
walltime = round((max(TasksData["EndTime"]) - min(TasksData["StartTime"])) / 60, ndigits=2)
########################################################### Visualizations #############################################################################################################################
#--Workflow Gantt Chart
FlowcolorMap = {"Parallel":"#1baf7a", "Sequential": "#2a78d6"}
legenHandles = [
    mpatches.Patch(color=color, label = category)
    for category,color in FlowcolorMap.items()
]
TasksDataSorted["FlowColor"] = TasksDataSorted["Flow"].map(FlowcolorMap)
fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.barh(TasksDataSorted["Task"], TasksDataSorted["Duration"],left=TasksDataSorted["StartTimeOffsit"],color=TasksDataSorted["FlowColor"])
ax.bar_label(bars, labels=round(TasksDataSorted["Duration"], ndigits=2).astype(str) + " m",padding=5, fontsize=5)
ax.set_xlabel("Minutes from Workflow Start")
ax.legend(handles=legenHandles,fontsize=10, loc="lower right", frameon=True, shadow=True)
ax.set_title(f"Workflow Gantt Chart: (Walltime= {walltime} h)")
plt.tight_layout()
plt.savefig(os.path.expanduser(f"{args.outDir}/Workflow_Gantt_Chart.png"), dpi=300)
plt.close()

#--Memory usage Chart
MemcolorMap = {f"< 30% of Requested":"#2a78d6", f"30-70% of Requested": "#eda100", f"> 70% of Requested":"#e34948"}
legenHandles = [
    mpatches.Patch(color=color, label = category)
    for category,color in MemcolorMap.items()
]
TasksDataSorted["MemColor"] = TasksDataSorted["MemEff"].map(MemcolorMap)
fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.barh(TasksDataSorted["Task"], TasksDataSorted["MaxRSSGB"],color=TasksDataSorted["MemColor"])
ax.bar_label(bars, labels=TasksDataSorted["MaxRSSGB"].astype(str) + " GB" + " ("+ round(TasksDataSorted["MemEff%"], ndigits=2).astype(str) + "%)",padding=5, fontsize=5)
ax.set_xlabel("Memory (GB)")
ax.legend(handles=legenHandles,fontsize=10, loc="lower right", frameon=True, shadow=True)
ax.set_title("Memory Used vs Requested")
ax.set_xlim(0, max(TasksDataSorted["ReqMemGB"]))
plt.tight_layout()
plt.savefig(os.path.expanduser(f"{args.outDir}/Memory_Usage_Chart.png"), dpi=300)
plt.close()

#--CPU eff
CpucolorMap = {f"Good":"#1baf7a", f"Moderate": "#eda100", "Poor":"#e34948"}
legenHandles = [
    mpatches.Patch(color=color, label = category)
    for category,color in CpucolorMap.items()
]
TasksDataSorted["CpuColor"] = TasksDataSorted["CpuEff"].map(CpucolorMap)
fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.barh(TasksDataSorted["Task"], TasksDataSorted["CpuEff%"],color=TasksDataSorted["CpuColor"])
ax.bar_label(bars, labels=round(TasksDataSorted["CpuEff%"], ndigits=2).astype(str) + "%",padding=5, fontsize=5)
ax.set_xlabel("CPU Efficiency (%)")
ax.legend(handles=legenHandles,fontsize=10, loc="lower right", frameon=True, shadow=True)
ax.set_title("CPU Efficiency per Task")
ax.set_xlim(0, 100)
plt.tight_layout()
plt.savefig(os.path.expanduser(f"{args.outDir}/CPU_Efficiency.png"), dpi=300)
plt.close()
