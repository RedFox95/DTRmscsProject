import sqlite3
import time
import datetime
import logging 
import bcrypt
import threading

class Database:
    instance = None 
    mutex = threading.Lock()

    def __init__(self, dbName) -> None:
        self.mutex.acquire()
        logging.debug("-> %(dbName)s", {'dbName': dbName})
        if self.instance != None:
            logging.info("Database has already been initialized")
            self.mutex.release()
            return
        # initialize the database
        self.databaseName = dbName # either "systemMetrics.db" or "testx.db" depending on context
        self.connection = sqlite3.connect(self.databaseName)
        self.cursor = self.connection.cursor()

        # setup tables
        self.cursor.execute("create table if not exists SystemMetrics (timestamp real, cpuUsage real, memoryUsage real, diskUsage real)")
        self.cursor.execute("create table if not exists PrunedSystemMetrics (startTimestamp real, endTimestamp real, cpuUsageAverage real, memoryUsageAverage real, diskUsageAverage real)")
        self.cursor.execute("create table if not exists Processes (pid integer, name text, executionTime real)")
        self.cursor.execute("create table if not exists ProcessMetrics (pid integer, timestamp real, cpuUsage real, memoryUsage real)")
        self.cursor.execute("create table if not exists Users (username text primary key, password text, role text)")
        logging.info("Database finished initialization")
        self.instance = self
        self.mutex.release()

        # add default admin user 
        self.cursor.execute("insert into Users values ('admin','$2b$12$NUtvo5eIyaEIHQPewvkQYuZHDbK6lM/j/uSFbfd1uqo/moj2mE4H6', 'Admin');")


    def addSystemMetrics(self, cpuUsage, memoryUsage, diskUsage):
        logging.debug("-> %(cpuUsage)d %(memoryUsage)d %(diskUsage)d", {'cpuUsage': cpuUsage, 'memoryUsage': memoryUsage, 'diskUsage': diskUsage})
        currentTimestamp = time.time()
        insertQuery = "insert into SystemMetrics values ({time}, {cUsage}, {mUsage}, {dUsage})".format(time=currentTimestamp, cUsage=cpuUsage, mUsage=memoryUsage, dUsage=diskUsage)
        self.cursor.execute(insertQuery)
        self.connection.commit()
        logging.debug("<-")

    def addProcessMetrics(self, pid, name, executionTime, cpuUsage, memoryUsage):
        logging.debug("-> %(pid)s %(name)s %(executionTime)d %(cpuUsage)d %(memoryUsage)d", {'pid': pid, 'name': name, 'executionTime': executionTime, 'cpuUsage': cpuUsage, 'memoryUsage': memoryUsage})
        currentTimestamp = time.time()
        # check if pid is in process table, if not then add it
        self.cursor.execute("select * from Processes where pid={id}".format(id=pid))
        if self.cursor.fetchall() == []:
            logging.info("Adding process {p} to the Processes table".format(p=pid))
            # this process is not in the Processes table yet, add it
            insertProcessQuery = "insert into Processes values ({id}, '{pName}', {eTime})".format(id=pid, pName=name, eTime=executionTime)
            self.cursor.execute(insertProcessQuery)
        else:
            logging.info("Process {p} is already in the Processes table, updating execution time".format(p=pid))
            # this process is already in the Processes table, update execution time
            updateProcessQuery = "update Processes set executionTime={eTime} where pid={id}".format(eTime=executionTime, id=pid)
            self.cursor.execute(updateProcessQuery)
        # add the metrics to the ProcessMetrics table no matter what
        insertMetricsQuery = "insert into ProcessMetrics values ({id}, {time}, {cUsage}, {mUsage})".format(id=pid, time=currentTimestamp, cUsage=cpuUsage, mUsage=memoryUsage)
        self.cursor.execute(insertMetricsQuery)
        self.connection.commit()
        logging.debug("<-")

    def addUser(self, username, password, role):
        logging.debug("-> %(username)s ****** %(role)s", {'username': username, 'role': role})
        self.cursor.execute("insert into Users values (?, ?, ?);", (username, password, role))
        self.connection.commit()

    def updateUserRole(self, username, newRole):
        logging.debug("-> %(username)s %(newRole)s", {'username': username, 'newRole': newRole})
        insertQuery = "update Users set role = ? where username = ?;"
        self.cursor.execute(insertQuery, (newRole, username))
        self.connection.commit()
        logging.debug("<-")

    def deleteUser(self, username):
        logging.debug("-> %(username)s", {'username': username})
        deleteQuery = "delete from Users where username='{u}';".format(u=username)
        self.cursor.execute(deleteQuery)
        self.connection.commit()
        logging.debug("<-")

    def isValidLogon(self, username, password):
        logging.debug("-> %(username)s", {'username': username})
        self.cursor.execute("select password from Users where username='{u}';".format(u=username))
        storedPassword = self.cursor.fetchall()
        if storedPassword == []:
            # bad username 
            logging.debug("<- " + str(False))
            return False
        isValid = bcrypt.checkpw(password.encode(), storedPassword[0][0])
        logging.debug("<- " + str(isValid))
        return isValid

    def getUsers(self):
        self.cursor.execute("select username, role from Users")
        return self.cursor.fetchall()

    def getUserRole(self, username):
        self.cursor.execute("select role from Users where username='{u}';".format(u=username))
        return self.cursor.fetchall()

    def get_system_metrics(self):
        self.cursor.execute("select * from SystemMetrics")
        return self.cursor.fetchall()

    def get_system_metrics_date_range(self, start_date, end_date):
        start_time = datetime.datetime.strptime(start_date, '%Y-%m-%d').timestamp()
        end_time = datetime.datetime.strptime(end_date, '%Y-%m-%d').timestamp() + 86399
        self.cursor.execute(f"select * from SystemMetrics where timestamp >= {start_time} and timestamp <= {end_time};")
        return self.cursor.fetchall()

    def get_process(self):
        self.cursor.execute("select * from Processes")
        return self.cursor.fetchall()

    def get_process_by_id(self, ids):
        self.cursor.execute(f"select * from Processes where pid in ({','.join(['?'] * len(ids))})", ids)
        return self.cursor.fetchall()

    def get_process_metrics(self):
        self.cursor.execute("select * from ProcessMetrics")
        return self.cursor.fetchall()

    def get_process_metrics_date_range(self, start_date, end_date):
        start_time = datetime.datetime.strptime(start_date, '%Y-%m-%d').timestamp()
        end_time = datetime.datetime.strptime(end_date, '%Y-%m-%d').timestamp() + 86399
        self.cursor.execute(f"select * from ProcessMetrics where timestamp >= {start_time} and timestamp < {end_time};")
        return self.cursor.fetchall()

    '''
    Prune the system metrics by removing them from the SystemMetrics table and adding the average of the values into the PrunedSystemMetrics table.
    Usage note: this should only be called via the pruneData method and unit tests.
    '''
    def pruneSystemMetrics(self):
        logging.debug("->")
        # get the oldest timestamp
        oldestTimeQuery = "select min(timestamp) from SystemMetrics;"
        self.cursor.execute(oldestTimeQuery)
        # NTS: need to index into it twice since it is returned in this form: [(1.23,)]
        oldestTimestamp = self.cursor.fetchall()[0][0]

        # get the newest timestamp
        newestTimeQuery = "select max(timestamp) from SystemMetrics;"
        self.cursor.execute(newestTimeQuery)
        newestTimestamp = self.cursor.fetchall()[0][0]

        # get all the info between, each in a separate result
        getAllCpuData = "select cpuUsage from SystemMetrics where timestamp>={old} and timestamp<={new};".format(old=oldestTimestamp, new=newestTimestamp)
        self.cursor.execute(getAllCpuData)
        allCpuData = self.cursor.fetchall()

        getAllMemoryData = "select memoryUsage from SystemMetrics where timestamp>={old} and timestamp<={new};".format(old=oldestTimestamp, new=newestTimestamp)
        self.cursor.execute(getAllMemoryData)
        allMemoryData = self.cursor.fetchall()

        getAllDiskData = "select diskUsage from SystemMetrics where timestamp>={old} and timestamp<={new};".format(old=oldestTimestamp, new=newestTimestamp)
        self.cursor.execute(getAllDiskData)
        allDiskData = self.cursor.fetchall()

        # remove from SystemMetrics database
        deleteQuery = "delete from SystemMetrics where timestamp>={old} and timestamp<={new};".format(old=oldestTimestamp, new=newestTimestamp)
        self.cursor.execute(deleteQuery)

        # convert to averages
        cpuAvg = getAverageData(allCpuData)
        memoryAvg = getAverageData(allMemoryData)
        diskAvg = getAverageData(allDiskData)

        # add to PrunedSystemMetrics datasebase
        addPrunedQuery = "insert into PrunedSystemMetrics values ({start}, {end}, {cpu}, {memory}, {disk});".format(start=oldestTimestamp, end=newestTimestamp, cpu=cpuAvg, memory=memoryAvg, disk=diskAvg)
        self.cursor.execute(addPrunedQuery)
        logging.debug("<-")

    '''
    Prunes the process metrics data by removing data for any processes that have not been active for over a week.
    Usage note: this should only be called via the pruneData method and unit tests.
    '''
    def pruneProcessMetrics(self):
        logging.debug("->")
        # get all pids from processes table
        allPidsQuery = "select pid from Processes;"
        self.cursor.execute(allPidsQuery)
        allPids = self.cursor.fetchall()

        # for each process, check the latest timestamp in the ProcessMetrics table
        for pidTuple in allPids:
            pid = pidTuple[0]
            latestTimestampQuery = "select max(timestamp) from ProcessMetrics where pid={id};".format(id=pid)
            self.cursor.execute(latestTimestampQuery)
            latestTimestamp = self.cursor.fetchall()[0][0]
            # if last timestamp >= 1 week ago, delete all records in Processes and ProcessMetrics for this process
            if time.time() - latestTimestamp >= 604800:
                logging.info("Process {p} is old, pruning data".format(p=pid))
                deleteProcessesEntryQuery = "delete from Processes where pid={id};".format(id=pid)
                self.cursor.execute(deleteProcessesEntryQuery)
                deleteProcessMetricsEntryQuery = "delete from ProcessMetrics where pid={id};".format(id=pid)
                self.cursor.execute(deleteProcessMetricsEntryQuery)
        logging.debug("<-")

    '''
    This is the method that should be called to prune all the data at once every 12 hours.
    '''
    def pruneData(self):
        self.pruneSystemMetrics()
        self.pruneProcessMetrics()

    '''
    Returns the cursor for this database. FOR TESTING ONLY.
    Returns None if this is not a testing scenario.
    '''
    def getCursor(self):
        if "test" in self.databaseName:
            return self.cursor

'''
Returns the average of the data.
dataList: list of the data to average in the form returned by sql queries (ex: [(a,), (b,), (c,)])
'''
def getAverageData(dataList):
    sum = 0
    for data in dataList:
        sum += data[0]
    return sum / len(dataList)
