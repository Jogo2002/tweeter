"""
adds ~150 random messages to the existing twitter_clone.db.
"""

import sqlite3
import random

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
]

con = sqlite3.connect("twitter_clone.db")
cur = con.cursor()

cur.execute("SELECT id FROM users")
user_ids = [row[0] for row in cur.fetchall()]

if not user_ids:
    print("No users in the database. Run db_create.py first.")
else:
    for _ in range(150):
        sender_id = random.choice(user_ids)
        message = random.choice(SAMPLE_MESSAGES)
        cur.execute(
            "INSERT INTO messages (sender_id, message) VALUES (?, ?)",
            (sender_id, message),
        )
    con.commit()
    print("Inserted 150 messages.")

con.close()
