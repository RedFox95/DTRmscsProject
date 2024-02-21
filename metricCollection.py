import sched
import time
import psutil
from flask import Flask

# Function to collect and print metrics
def collect_metrics():
    # CPU Information
    print("CPU Core Count (Physical):", psutil.cpu_count(logical=False))
    print("CPU Core Count (Logical):", psutil.cpu_count(logical=True))
    print("CPU Current Frequency:", psutil.cpu_freq().current, "MHz")
    print("System Uptime:", round(psutil.boot_time()), "seconds")

    # Memory Information
    memory = psutil.virtual_memory()
    print("Total Memory:", memory.total)
    print("Available Memory:", memory.available)

    # Disk Information
    disk = psutil.disk_usage('/')
    print("Total Disk:", disk.total)
    print("Used Disk:", disk.used)
    print("Free Disk:", disk.free)
    print("Disk Usage Percentage:", disk.percent, "%")

    # Process Information
    for proc in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent', 'memory_percent', 'cpu_times']):
        print(proc.info)

# Scheduler setup
scheduler = sched.scheduler(time.time, time.sleep)

# Function to be scheduled
def scheduled_task(sc):
    collect_metrics()  # Call the metric collection function
    sc.enter(30, 1, scheduled_task, (sc,))  # Schedule the next call

# Schedule the first task
scheduler.enter(30, 1, scheduled_task, (scheduler,))

# Start the scheduler
scheduler.run()
