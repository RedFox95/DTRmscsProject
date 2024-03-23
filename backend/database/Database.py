import sqlite3
import time 

class Database:
    def __init__(self, dbName) -> None:
        # initialize the database
        self.databaseName = dbName # either "systemMetrics.db" or "testx.db" depending on context
        self.connection = sqlite3.connect(self.databaseName)
        self.cursor = self.connection.cursor()

        # setup tables
        self.cursor.execute("create table if not exists SystemMetrics (timestamp real, cpuUsage real, memoryUsage real, diskUsage real)")
        self.cursor.execute("create table if not exists PrunedSystemMetrics (startTimestamp real, endTimestamp real, cpuUsageAverage real, memoryUsageAverage real, diskUsageAverage real)")
        self.cursor.execute("create table if not exists Processes (pid integer, name text, executionTime real)")
        self.cursor.execute("create table if not exists ProcessMetrics (pid integer, timestamp real, cpuUsage real, memoryUsage real)")


    def addSystemMetrics(self, cpuUsage, memoryUsage, diskUsage):
        currentTimestamp = time.time()
        insertQuery = "insert into SystemMetrics values ({time}, {cUsage}, {mUsage}, {dUsage})".format(time=currentTimestamp, cUsage=cpuUsage, mUsage=memoryUsage, dUsage=diskUsage)
        print(insertQuery)
        self.cursor.execute(insertQuery)

    def addProcessMetrics(self, pid, name, executionTime, cpuUsage, memoryUsage):
        currentTimestamp = time.time()
        # check if pid is in process table, if not then add it
        self.cursor.execute("select * from Processes where pid={id}".format(id=pid))
        if self.cursor.fetchall() == []:
            # this process is not in the Processes table yet, add it
            insertProcessQuery = "insert into Processes values ({id}, '{pName}', {eTime})".format(id=pid, pName=name, eTime=executionTime)
            print(insertProcessQuery)
            self.cursor.execute(insertProcessQuery)
        else:
            # this process is already in the Processes table, update execution time
            updateProcessQuery = "update Processes set executionTime={eTime} where pid={id}".format(eTime=executionTime, id=pid)
            print(updateProcessQuery)
            self.cursor.execute(updateProcessQuery)
        # add the metrics to the ProcessMetrics table no matter what 
        insertMetricsQuery = "insert into ProcessMetrics values ({id}, {time}, {cUsage}, {mUsage})".format(id=pid, time=currentTimestamp, cUsage=cpuUsage, mUsage=memoryUsage)
        print(insertMetricsQuery)
        self.cursor.execute(insertMetricsQuery)

    def pruneSystemMetrics(self):
        pass

    def pruneProcessMetrics(self):
        pass

    def pruneData():
        # TODO prune data starting from the current time and back x hours?
        # does this happen at the same time for both? could call both other methods from here
        pass

    '''
    Returns the cursor for this database. FOR TESTING ONLY. 
    Returns None if this is not a testing scenario.
    '''
    def getCursor(self):
        if "test" in self.databaseName:
            return self.cursor


