#!/bin/bash
# tests for SQL injection and HTML/XSS injection attacks.
# run bash tests/injection.sh

set -e
URL="http://127.0.0.1:8080"


echo "Test 1: SQL injection in /create_user"
# try to drop the users table by putting sql in the username field.
curl -s -G "$URL/create_user" \
    --data-urlencode "username=hacker'; DROP TABLE users; --" \
    --data-urlencode "password=x" \
    --data-urlencode "password2=x" > /dev/null

# if the table was dropped, the home page would crash because it joins messages to users.
HOME=$(curl -s "$URL/")
if echo "$HOME" | grep -q "Timeline"; then
    echo "PASS: users table was not dropped"
else
    echo "FAIL: home page broken, table might be gone"
    exit 1
fi # stops the if in bash


echo "Test 2: SQL injection in /login"
LOGIN=$(curl -s -G "$URL/login" \
    --data-urlencode "username=' OR '1'='1" \
    --data-urlencode "password=anything")
if echo "$LOGIN" | grep -q "does not match"; then
    echo "PASS: tautology rejected"
else
    echo "FAIL: tautology may have logged in"
    exit 1
fi


echo "Test 3: XSS in messages"
# log in as trummp to post a message 
curl -s -c cookies.txt -G "$URL/login" \
    --data-urlencode "username=Trump" \
    --data-urlencode "password=Trump" > /dev/null

# post a message containing a script tag.
curl -s -b cookies.txt -G "$URL/create_message" \
    --data-urlencode "message=<script>alert(1)</script>" > /dev/null

# the script tag should be escaped on the home page, not rendered as real html.
HOME=$(curl -s "$URL/")
if echo "$HOME" | grep -q "<script>alert(1)</script>"; then
    echo "FAIL: script tag was rendered, XSS is possible"
    exit 1
else
    echo "PASS: script tag was escaped"
fi


echo "Test 4: XSS in user description"
# set trump's description to a script tag.
curl -s -b cookies.txt -G "$URL/user/Trump" \
    --data-urlencode "description=<script>alert(1)</script>" > /dev/null

PROFILE=$(curl -s "$URL/user/Trump")
if echo "$PROFILE" | grep -q "<script>alert(1)</script>"; then
    echo "FAIL: description was rendered as HTML"
    exit 1
else
    echo "PASS: description was escaped"
fi


rm -f cookies.txt
echo ""
echo "All tests passed."
