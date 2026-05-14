"""
tests for sql injection and html/xss injection attacks.
start the server first (python main.py), then run: python tests/injection.py
"""

import requests

URL = "http://127.0.0.1:8080"


print("Test 1: SQL injection in /create_user")
# try to drop the users table by putting sql in the username field
requests.get(f"{URL}/create_user", params={
    "username": "hacker'; DROP TABLE users; --",
    "password": "x",
    "password2": "x",
})

# if the table was dropped, the home page would crash because it joins messages to users.
home = requests.get(f"{URL}/").text
if "Timeline" in home:
    print("PASS: users table was not dropped")
else:
    print("FAIL: home page broken, table might be gone")
    exit(1)


print("Test 2: SQL injection in /login")
# if injection worked, this would log us in as someone.
login = requests.get(f"{URL}/login", params={
    "username": "' OR '1'='1",
    "password": "anything",
}).text
if "does not match" in login:
    print("PASS: tautology rejected")
else:
    print("FAIL: tautology may have logged in")
    exit(1)


print("Test 3: XSS in messages")
# log in as trump using a session so cookies are kept between requests.
session = requests.Session()
session.get(f"{URL}/login", params={"username": "Trump", "password": "Trump"})

# post a message containing a script tag.
session.get(f"{URL}/create_message", params={
    "message": "<script>alert(1)</script>",
})

# the script tag should be escaped on the home page, not rendered as real html.
home = requests.get(f"{URL}/").text
if "<script>alert(1)</script>" in home:
    print("FAIL: script tag was rendered, XSS is possible")
    exit(1)
else:
    print("PASS: script tag was escaped")


print("Test 4: XSS in user description")
# set trump's description to a script tag.
session.get(f"{URL}/user/Trump", params={
    "description": "<script>alert(1)</script>",
})

profile = requests.get(f"{URL}/user/Trump").text
if "<script>alert(1)</script>" in profile:
    print("FAIL: description was rendered as HTML")
    exit(1)
else:
    print("PASS: description was escaped")


print()
print("All tests passed.")
