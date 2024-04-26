import Database
import datetime
import bcrypt

def test_database_init():
    db = Database.Database("testDbInit.db")
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
    # check for the admin user
    cursor.execute("select * from Users where username='admin' and password='$2b$12$NUtvo5eIyaEIHQPewvkQYuZHDbK6lM/j/uSFbfd1uqo/moj2mE4H6' and role='Admin';")
    assert len(cursor.fetchall()) == 1

def test_add_system_metrics():
    db = Database.Database("testAddSysMet.db")
    cursor = db.getCursor()

    db.addSystemMetrics(1.111, 2.222, 3.333)
    cursor.execute("select * from SystemMetrics where cpuUsage=1.111 and memoryUsage=2.222 and diskUsage=3.333;")
    result = cursor.fetchall()
    assert result != []

def test_add_process_metrics():
    db = Database.Database("testAddProcMet.db")
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

def test_prune_system_metrics():
    db = Database.Database("testPruneSysMet.db")
    cursor = db.getCursor()

    # fill the SystemMetrics table with some metrics
    db.addSystemMetrics(1.1, 2.2, 3.3)
    db.addSystemMetrics(2.2, 3.3, 4.4)
    db.addSystemMetrics(3.3, 4.4, 5.5)
    db.addSystemMetrics(4.4, 5.5, 6.6)
    db.addSystemMetrics(5.5, 6.6, 7.7)

    db.pruneSystemMetrics()

    # check that there are no entries in the SystemMetrics table anymore
    cursor.execute("select * from SystemMetrics;")
    assert cursor.fetchall() == []

    # check that there is one entry in the PrunedSystemMetrics
    cursor.execute("select * from PrunedSystemMetrics;")
    assert len(cursor.fetchall()) == 1

    # check that the values are correct in this entry
    cursor.execute("select cpuUsageAverage, memoryUsageAverage, diskUsageAverage from PrunedSystemMetrics;")
    results = cursor.fetchall()
    assert results[0][0] == 3.3
    assert results[0][1] == 4.4
    assert results[0][2] == 5.499999999999999 # NTS: should be 5.5 but python math says it's this

def test_prune_process_metrics():
    db = Database.Database("testPruneProcMet.db")
    cursor = db.getCursor()

    # add process metrics for pid 0 (current time)
    db.addProcessMetrics(0, "proc0", 1.1, 2.2, 3.3)
    db.addProcessMetrics(0, "proc0", 4.4, 5.5, 6.6)
    db.addProcessMetrics(0, "proc0", 7.7, 8.8, 9.9)

    # add process metrics manually for pid 1 (past time)
    cursor.execute("insert into Processes values (1, 'proc1', 10.1);")
    randomPastDate1 = datetime.datetime(2023, 1, 1)
    randomPastDate2 = datetime.datetime(2023, 2, 1)
    randomPastDate3 = datetime.datetime(2023, 3, 1)
    epochTime = datetime.datetime(1970, 1, 1)
    cursor.execute("insert into ProcessMetrics values (1, {time}, 11.1, 12.1);".format(time=(randomPastDate1 - epochTime).total_seconds()))
    cursor.execute("insert into ProcessMetrics values (1, {time}, 14.1, 15.1);".format(time=(randomPastDate2 - epochTime).total_seconds()))
    cursor.execute("insert into ProcessMetrics values (1, {time}, 17.1, 18.1);".format(time=(randomPastDate3 - epochTime).total_seconds()))

    db.pruneProcessMetrics()

    # ensure pid 0 is still there
    cursor.execute("select * from Processes where pid=0;")
    assert len(cursor.fetchall()) == 1
    cursor.execute("select * from ProcessMetrics where pid=0;")
    assert len(cursor.fetchall()) == 3

    # ensure all pid 1 entries are gone from both tables
    cursor.execute("select * from Processes where pid=1;")
    assert cursor.fetchall() == []
    cursor.execute("select * from ProcessMetrics where pid=1;")
    assert cursor.fetchall() == []

def test_add_and_delete_user():
    db = Database.Database("testAddDeleteUser.db")
    cursor = db.getCursor()

    # add the user and check if they are there
    db.addUser("testUsername", "testPassword", "testRole")
    cursor.execute("select * from Users where username='testUsername' and password='testPassword' and role='testRole';")
    assert len(cursor.fetchall()) == 1

    # delete the user and check that they're not there
    db.deleteUser("testUsername")
    cursor.execute("select * from Users where username='testUsername' and password='testPassword' and role='testRole';")
    assert len(cursor.fetchall()) == 0

def test_update_user_role():
    db = Database.Database("testUpdateUserRole.db")
    cursor = db.getCursor()

    # add a new user and check that their role updated
    db.addUser("testUsername", "testPassword", "testRole")
    cursor.execute("select * from Users where username='testUsername' and password='testPassword' and role='testRole';")
    db.updateUserRole("testUsername", "testNewRole")
    cursor.execute("select * from Users where username='testUsername' and password='testPassword' and role='testNewRole';")
    assert len(cursor.fetchall()) == 1

    # delete the test user
    db.deleteUser("testUsername")
    cursor.execute("select * from Users where username='testUsername' and password='testPassword' and role='testNewRole';")
    assert len(cursor.fetchall()) == 0

def test_password_checking():
    db = Database.Database("testPasswordChecking.db")
    cursor = db.getCursor()

    # add the user and check if they are there
    hashed_password = bcrypt.hashpw('testPassword'.encode(), bcrypt.gensalt())
    db.addUser('testUsername', hashed_password, 'testRole')
    selectQuery = "select * from Users where username='testUsername' and role='testRole';"
    cursor.execute(selectQuery)
    assert len(cursor.fetchall()) == 1

    # correct password
    assert db.isValidLogon("testUsername", "testPassword")

    # incorrect password
    assert not db.isValidLogon("testUsername", "bad")

    # incorrect username
    assert not db.isValidLogon("bad", "testPassword")

    # incorrect username and password
    assert not db.isValidLogon("bad1", "bad2")
