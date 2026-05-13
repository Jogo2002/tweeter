"""
populates the existing twitter_clone.db with 200 users and 200 messages each (40,000 total).
"""

import sqlite3
import random

NUM_USERS = 200
MESSAGES_PER_USER = 200

SAMPLE_MESSAGES = [
    "Just had coffee, feeling great.",
    "Anyone watching the game tonight?",
    "Why is python so good?",
    "Reading a book about SQL.",
    "Twitter clone is fun to build.",
    "Good morning everyone!",
    "Cannot believe it's already Friday.",
    "New blog post coming soon.",
    "Working on a new project.",
    "Pizza for dinner again.",
    "Long day, but a good one.",
    "Anyone got recommendations for a movie?",
    "Learning new things every day.",
    "Coding is the best.",
    "Tired but happy.",
    "It's been a busy week.",
    "Hello world!",
    "Trying to get to 10000 steps today.",
    "Just deployed my first website!",
    "Coffee is the answer to everything.",
    "I miss summer.",
    "Anyone else find SQL fun?",
    "Just finished my homework.",
    "Studying for finals.",
    "Visit https://example.com for more info.",
    "Izbicki is the best professor!",
]

con = sqlite3.connect("twitter_clone.db", timeout=10.0)
cur = con.cursor()

# step 1: create 200 bot users (skip any that already exist).
user_rows = []
for i in range(1, NUM_USERS + 1):
    username = f"bot{i:03d}"
    password = f"pw{i:03d}"
    age = random.randint(18, 70)
    user_rows.append((username, password, age))

cur.executemany(
    "INSERT OR IGNORE INTO users (username, password, age) VALUES (?, ?, ?)",
    user_rows,
)

# step 2: look up the ids of all bot users.
cur.execute("SELECT id FROM users WHERE username LIKE 'bot%'")
bot_ids = [row[0] for row in cur.fetchall()]
print(f"Found {len(bot_ids)} bot users to post messages from.")

# step 3: build 200 messages per bot user and insert them all in one batch.
message_rows = []
for user_id in bot_ids:
    for _ in range(MESSAGES_PER_USER):
        message_rows.append((user_id, random.choice(SAMPLE_MESSAGES)))

print(f"Inserting {len(message_rows)} messages...")
cur.executemany(
    "INSERT INTO messages (sender_id, message) VALUES (?, ?)",
    message_rows,
)

con.commit()
con.close()
print("Done.")