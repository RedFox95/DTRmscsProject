import Database

def test_database_init():
    db = Database.Database("test1.db")
    cursor = db.getCursor()
    # check for the tables 
    cursor.execute("pragma table_info(SystemMetrics);")
    assert cursor.fetchall() != []
    cursor.execute("pragma table_info(PrunedSystemMetrics);")
    assert cursor.fetchall() != []
    cursor.execute("pragma table_info(Processes);")
    assert cursor.fetchall() != []
    cursor.execute("pragma table_info(ProcessMetrics);")
    assert cursor.fetchall() != []

def test_add_system_metrics():
    db = Database.Database("test2.db")
    cursor = db.getCursor()

    db.addSystemMetrics(1.111, 2.222, 3.333)
    cursor.execute("select * from SystemMetrics where cpuUsage=1.111 and memoryUsage=2.222 and diskUsage=3.333;")
    result = cursor.fetchall()
    assert result != []

def test_add_process_metrics():
    db = Database.Database("test3.db")
    cursor = db.getCursor()    

    pid = 123
    name = "myProcess"
    executionTime = 123.456
    cpuUsage = 1.111
    memoryUsage = 2.222

    # make sure pid is not already in the tables
    cursor.execute("select * from Processes where pid={id};".format(id=pid))
    assert cursor.fetchall() == []
    cursor.execute("select * from ProcessMetrics where pid={id};".format(id=pid))
    assert cursor.fetchall() == []

    # add the metrics
    db.addProcessMetrics(pid, name, executionTime, cpuUsage, memoryUsage)

    # check the tables for the correct entries
    cursor.execute("select * from Processes where pid={id} and name='{pName}' and executionTime={eTime};".format(id=pid, pName=name, eTime=executionTime))
    assert cursor.fetchall() != []
    cursor.execute("select * from ProcessMetrics where pid={id} and cpuUsage={cUsage} and memoryUsage={mUsage};".format(id=pid, cUsage=cpuUsage, mUsage=memoryUsage))
    assert cursor.fetchall() != []

    # add another set of metrics 
    executionTime2 = 456.789
    cpuUsage2 = 3.333
    memoryUsage2 = 4.444
    db.addProcessMetrics(pid, name, executionTime2, cpuUsage2, memoryUsage2)

    # check there is still one entry in Processes 
    cursor.execute("select * from Processes where pid={id} and name='{pName}';".format(id=pid, pName=name))
    assert len(cursor.fetchall()) == 1

    # check that the execution time was updated 
    cursor.execute("select executionTime from Processes where pid={id} and name='{pName}';".format(id=pid, pName=name))
    assert (executionTime2,) in cursor.fetchall()

    # check that a new entry was added to ProcessMetrics
    cursor.execute("select * from ProcessMetrics where pid={id};".format(id=pid))
    assert len(cursor.fetchall()) == 2

    # check that an entry with the correct data is there
    cursor.execute("select * from ProcessMetrics where pid={id} and cpuUsage={cUsage} and memoryUsage={mUsage};".format(id=pid, cUsage=cpuUsage, mUsage=memoryUsage))
    assert cursor.fetchall() != []

# TODO test adding bad values
    
# TODO test prune
