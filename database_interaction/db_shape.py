import sqlite3

con = sqlite3.connect("twitter_clone.db")
cur = con.cursor()

sql = """
SELECT
    (SELECT COUNT(*) FROM users)    AS user_count,
    (SELECT COUNT(*) FROM messages) AS message_count;
"""

cur.execute(sql)
user_count, message_count = cur.fetchone()
print("users:   ", user_count)
print("messages:", message_count)

con.close()
