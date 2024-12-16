import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect("your_database.db")

# Open the output file
with open("output.sql", "w") as f:
    for line in conn.iterdump():
        f.write(f"{line}\n")

# Close the connection
conn.close()

print("Database exported to output.sql")

