import sqlite3

def store_metrics(timestamp, cpu_usage, memory_usage, disk_usage):
    connection = sqlite3.connect('system_metrics.db')
    cursor = connection.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS SystemMetrics
                      (Timestamp DATETIME PRIMARY KEY, CpuUsage FLOAT, MemoryUsage FLOAT, DiskUsage FLOAT)''')

    cursor.execute('''INSERT INTO SystemMetrics (Timestamp, CpuUsage, MemoryUsage, DiskUsage)
                      VALUES (?, ?, ?, ?)''', (timestamp, cpu_usage, memory_usage, disk_usage))

    connection.commit()
    connection.close()
