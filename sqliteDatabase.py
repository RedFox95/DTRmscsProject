import sqlite3

# Connect to the SQLite database
connection = sqlite3.connect("test.db")
cursor = connection.cursor()

# Create a table
cursor.execute("CREATE TABLE IF NOT EXISTS example (id INTEGER, name TEXT, age INTEGER)")

# Insert data
cursor.execute("INSERT INTO example VALUES (2, 'alice', 20)")
cursor.execute("INSERT INTO example VALUES (1, 'bob', 20)")
cursor.execute("INSERT INTO example VALUES (1, 'eve', 20)")

# Commit the transaction
connection.commit()

# Query the data
cursor.execute("SELECT * FROM example")
rows = cursor.fetchall()

# Process and print the results
for row in rows:
    print(row)

# Close the cursor and connection
cursor.close()
connection.close()
