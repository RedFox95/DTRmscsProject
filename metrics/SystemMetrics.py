from datetime import timedelta
from collections import deque
import psutil
import time

class SystemMetrics():
    def __init__(self):
        self.cpu_chart_buffer = deque([0] * 61, maxlen=61)
        self.mem_chart_buffer = deque([0] * 61, maxlen=61)

    def get_cpu_info(self):
        freq = psutil.cpu_freq()
        usage = psutil.cpu_percent(interval=1)
        boot_time = psutil.boot_time()
        current_time = time.time()
        uptime_seconds = current_time - boot_time
        uptime = self.format_cpu_time(uptime_seconds)
        self.cpu_chart_buffer.append(usage)

        cpu_data = {
            'speed': freq.current,  # Round to 2 decimal places for GB
            'usage': usage,
            'uptime': uptime,
            'logical': psutil.cpu_count(),
            'physical': psutil.cpu_count(logical=False),
            'y_values': list(self.cpu_chart_buffer)
        }

        return cpu_data

    def get_memory_info(self):
        memory = psutil.virtual_memory()
        total_memory_gb = memory.total / (1024 ** 3)  # Convert bytes to GB
        used_memory_gb = memory.used / (1024 ** 3)  # Convert bytes to GB
        memory_percent = memory.percent  # Percentage of memory used
        self.mem_chart_buffer.append(memory_percent)

        return {
            'total': round(total_memory_gb, 2),  # Round to 2 decimal places for GB
            'used': round(used_memory_gb, 2),
            'percent': memory_percent,
            'y_values': list(self.mem_chart_buffer)
        }

    def get_disk_info(self):
        disks = []
        for partition in psutil.disk_partitions():
            usage = psutil.disk_usage(partition.mountpoint)
            disks.append({
                'device': partition.device,
                'mountpoint': partition.mountpoint,
                'total': round(usage.total / (1024 ** 3), 2),  # Convert to GB
                'used': round(usage.used / (1024 ** 3), 2),  # Convert to GB
                'percent': usage.percent
            })
        return disks

    def get_process_info(self):
        processes = []
        for process in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'cpu_times', 'create_time']):
            try:
                processes.append(process.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return processes[0:10]

    def format_cpu_time(self, t):
        td = timedelta(seconds=t)
        days, remainder = divmod(td.total_seconds(), 86400) # 86400 seconds in a day
        hours, remainder = divmod(remainder, 3600) # 3600 minutes in a day
        minutes, seconds = divmod(remainder, 60)

        cpu_time = ""
        if days > 0:
            cpu_time += f"{round(days)}D, "
        if hours > 0:
            cpu_time += f"{round(hours)}H, "
        if minutes > 0:
            cpu_time += f"{round(minutes)}m, "
        if seconds > 0:
            cpu_time += f"{round(seconds)}s"

        return cpu_time
