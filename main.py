'''
Starts a Twitter Clone Webpage.
'''

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3
import re
import uvicorn
from markupsafe import Markup, escape

app = FastAPI()
templates = Jinja2Templates(directory='templates')

def detect_url(text):
    escaped = escape(text)
    linked = re.sub(
        r'(https?://\S+)',
        r'<a href="\1">\1</a>',
        str(escaped)
    )
    return Markup(linked)

templates.env.filters['detect_url'] = detect_url
app.mount("/static", StaticFiles(directory="static"), name="static")

try:
    _con = sqlite3.connect('twitter_clone.db')
    _con.execute('ALTER TABLE users ADD COLUMN description TEXT')
    _con.commit()
    _con.close()
except sqlite3.OperationalError:
    pass

try:
    _con = sqlite3.connect('twitter_clone.db')
    _con.execute('ALTER TABLE messages ADD COLUMN reply_to_id INTEGER')
    _con.commit()
    _con.close()
except sqlite3.OperationalError:
    pass

def check_credentials(request: Request):
    '''
    returns username is user is logged in.
    if not logged in, return None.
    "morally" the same as True for loggedin and False for logged out
    '''
    ## Q: HOW TO remember if we are logged in or not.
    ## A: cookies
    query_username = request.query_params.get('username')
    query_password = request.query_params.get('password')
    print('query_username=', query_username)
    print('query_password=', query_password)

    cookie_username = request.cookies.get('username')
    cookie_password = request.cookies.get('password')
    print('cookie_username=', cookie_username)
    print('cookie_password=', cookie_password)

    username = cookie_username
    password = cookie_password

    con = sqlite3.connect('twitter_clone.db')
    cur = con.cursor()
    cur.execute('SELECT username FROM users WHERE username = ? AND password = ?', (username, password))
    row = cur.fetchone()
    con.close()

    if row:
        print(f"logged in as {row[0]}")
        return row[0]
        
    else:
        print('not logged in')
        return None

@app.get('/', response_class=HTMLResponse)
async def index(request: Request):

    # showing only 50 messages 
    try:
        page = max(0, int(request.query_params.get('page', 0)))
    except ValueError:
        page = 0
    page_size = 50
    offset = page * page_size

    con = sqlite3.connect('twitter_clone.db')
    cur = con.cursor()

    cur.execute('''
        SELECT users.username, users.age, messages.message, messages.created_at, messages.id, messages.reply_to_id
        FROM messages
        JOIN users ON messages.sender_id = users.id
        WHERE messages.reply_to_id IS NULL
        ORDER BY messages.created_at DESC
        LIMIT ? OFFSET ?
    ''', (page_size, offset))
    top_rows = cur.fetchall()

    top_ids = [row[4] for row in top_rows]
    if top_ids:
        placeholders = ','.join('?' * len(top_ids))
        cur.execute(f'''
            SELECT users.username, users.age, messages.message, messages.created_at, messages.id, messages.reply_to_id
            FROM messages
            JOIN users ON messages.sender_id = users.id
            WHERE messages.reply_to_id IN ({placeholders})
            ORDER BY messages.created_at ASC
        ''', top_ids)
        reply_rows = cur.fetchall()
    else:
        reply_rows = []

    cur.execute('SELECT COUNT(*) FROM messages WHERE reply_to_id IS NULL')
    total_top_level = cur.fetchone()[0]
    num_pages = (total_top_level + page_size - 1) // page_size
    con.close()

    replies_by_parent = {}
    for row in reply_rows:
        replies_by_parent.setdefault(row[5], []).append({
            "username": row[0],
            "age": row[1],
            "message": row[2],
            "created_at": row[3],
            "id": row[4],
            "reply_to_id": row[5],
            "replies": [],
        })

    messages = []
    for row in top_rows:
        msg = {
            "username": row[0],
            "age": row[1],
            "message": row[2],
            "created_at": row[3],
            "id": row[4],
            "reply_to_id": row[5],
            "replies": replies_by_parent.get(row[4], []),
        }
        messages.append(msg)

    has_prev = page > 0
    has_next = (offset + page_size) < total_top_level

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "is_logged_in": check_credentials(request),
            "username": check_credentials(request),
            "messages": messages,
            "not_found": request.query_params.get('not_found'),
            "page": page,
            "has_prev": has_prev,
            "has_next": has_next,
            "num_pages": num_pages,
        }
    )

@app.get('/messages.json')
async def messages_json():
    con = sqlite3.connect('twitter_clone.db')
    cur = con.cursor()
    cur.execute('''
        SELECT users.username, users.age, messages.message, messages.created_at, messages.id
        FROM messages
        JOIN users ON messages.sender_id = users.id
        ORDER BY messages.created_at DESC
    ''')
    rows = cur.fetchall()
    con.close()
    return [
        {"id": r[4], "username": r[0], "age": r[1], "message": r[2], "created_at": r[3]}
        for r in rows
    ]

@app.get('/logout', response_class=HTMLResponse)
async def logout(request: Request):
    response = templates.TemplateResponse(
        request=request,
        name='logout.html',
    )
    response.delete_cookie(key='username')
    response.delete_cookie(key='password')
    return response

@app.get('/login', response_class=HTMLResponse)
async def login(request: Request): # can't write doctests for async functions
    submitted_username = request.query_params.get('username')
    submitted_password = request.query_params.get('password')

    error = None
    if submitted_username is not None or submitted_password is not None:
        con = sqlite3.connect('twitter_clone.db')
        cur = con.cursor()
        cur.execute('SELECT username FROM users WHERE username = ?', (submitted_username,))
        user_row = cur.fetchone()
        if not user_row:
            error = 'This username does not match our records.'
        else:
            cur.execute('SELECT username FROM users WHERE username = ? AND password = ?', (submitted_username, submitted_password))
            if not cur.fetchone():
                error = 'Password is incorrect.'
            else:
                con.close()
                response = RedirectResponse(url='/')
                response.set_cookie(key='username', value=submitted_username)
                response.set_cookie(key='password', value=submitted_password)
                return response
        con.close()

    response = templates.TemplateResponse(
        request=request,
        name='login.html',
        context={
            'is_logged_in': check_credentials(request),
            'username': check_credentials(request),
            'error': error,
        }
    )
    response.set_cookie(key='username', value=submitted_username)
    response.set_cookie(key='password', value=submitted_password)
    return response

@app.get('/create_message', response_class=HTMLResponse)
async def create_message(request: Request):
    username = check_credentials(request)
    submitted_message = request.query_params.get('message')

    if username and submitted_message is not None:
        reply_to_id = request.query_params.get('reply_to_id')
        con = sqlite3.connect('twitter_clone.db')
        cur = con.cursor()
        cur.execute('SELECT id FROM users WHERE username = ?', (username,))
        row = cur.fetchone()
        if row:
            cur.execute(
                'INSERT INTO messages (sender_id, message, reply_to_id) VALUES (?, ?, ?)',
                (row[0], submitted_message, reply_to_id if reply_to_id else None)
            )
            con.commit()
        con.close()
        return RedirectResponse(url='/')

    return templates.TemplateResponse(
        request=request,
        name='create_message.html',
        context={
            'is_logged_in': username,
            'username': username,
        }
    )

@app.get('/delete_message', response_class=HTMLResponse)
async def delete_message(request: Request):
    username = check_credentials(request)
    message_id = request.query_params.get('id')

    if username and message_id:
        con = sqlite3.connect('twitter_clone.db')
        cur = con.cursor()
        cur.execute('''
            DELETE FROM messages
            WHERE id = ?
            AND sender_id = (SELECT id FROM users WHERE username = ?)
        ''', (message_id, username))
        con.commit()
        con.close()

    return RedirectResponse(url=f'/user/{username}')

@app.get('/create_user', response_class=HTMLResponse)
async def create_user(request: Request):
    submitted_username = request.query_params.get('username')
    submitted_password = request.query_params.get('password')
    submitted_password2 = request.query_params.get('password2')

    error = None
    if submitted_username is not None:
        if submitted_password != submitted_password2:
            error = 'Passwords do not match.'
        else:
            try:
                con = sqlite3.connect('twitter_clone.db')
                cur = con.cursor()
                cur.execute('INSERT INTO users (username, password) VALUES (?, ?)', (submitted_username, submitted_password))
                con.commit()
                con.close()
                response = RedirectResponse(url='/')
                response.set_cookie(key='username', value=submitted_username)
                response.set_cookie(key='password', value=submitted_password)
                return response
            except sqlite3.IntegrityError:
                error = 'An account with that username already exists.'

    return templates.TemplateResponse(
        request=request,
        name='create_user.html',
        context={
            'is_logged_in': check_credentials(request),
            'username': check_credentials(request),
            'error': error,
        }
    )

@app.get('/change_password', response_class=HTMLResponse)
async def change_password(request: Request):
    username = check_credentials(request)
    if not username:
        return RedirectResponse(url='/login')

    old_password = request.query_params.get('old_password')
    new_password = request.query_params.get('new_password')
    new_password2 = request.query_params.get('new_password2')

    cookie_password = request.cookies.get('password')

    if old_password != cookie_password:
        return RedirectResponse(url=f'/user/{username}?password_error=Current+password+is+incorrect.')
    if not new_password or new_password != new_password2:
        return RedirectResponse(url=f'/user/{username}?password_error=New+passwords+do+not+match.')

    con = sqlite3.connect('twitter_clone.db')
    cur = con.cursor()
    cur.execute('UPDATE users SET password = ? WHERE username = ?', (new_password, username))
    con.commit()
    con.close()

    response = RedirectResponse(url=f'/user/{username}?password_success=1')
    response.set_cookie(key='password', value=new_password)
    return response

@app.get('/search', response_class=HTMLResponse)
async def search(request: Request):
    query = request.query_params.get('username')
    if not query:
        return RedirectResponse(url='/')

    con = sqlite3.connect('twitter_clone.db')
    cur = con.cursor()
    cur.execute('SELECT username FROM users WHERE username = ?', (query,))
    row = cur.fetchone()
    con.close()

    if row:
        return RedirectResponse(url=f'/user/{row[0]}')
    return RedirectResponse(url=f'/?not_found={query}')

@app.get('/user/{profile_username}', response_class=HTMLResponse)
async def user_profile(request: Request, profile_username: str):
    username = check_credentials(request)
    submitted_description = request.query_params.get('description')

    con = sqlite3.connect('twitter_clone.db')
    cur = con.cursor()

    if submitted_description is not None and username == profile_username:
        cur.execute('UPDATE users SET description = ? WHERE username = ?', (submitted_description, username))
        con.commit()

    cur.execute('SELECT id, username, age, description FROM users WHERE username = ?', (profile_username,))
    user_row = cur.fetchone()

    if not user_row:
        con.close()
        return RedirectResponse(url='/')

    cur.execute('''
        SELECT messages.message, messages.created_at, messages.id
        FROM messages
        WHERE messages.sender_id = ?
        ORDER BY messages.created_at DESC
    ''', (user_row[0],))
    rows = cur.fetchall()
    con.close()

    messages = [{"message": r[0], "created_at": r[1], "id": r[2]} for r in rows]

    return templates.TemplateResponse(
        request=request,
        name='user.html',
        context={
            'is_logged_in': username,
            'username': username,
            'profile_username': user_row[1],
            'profile_age': user_row[2],
            'profile_description': user_row[3],
            'messages': messages,
            'is_owner': username == user_row[1],
            'password_error': request.query_params.get('password_error'),
            'password_success': request.query_params.get('password_success'),
        }
    )

@app.get('/delete_user', response_class=HTMLResponse)
async def delete_user(request: Request):
    username = check_credentials(request)

    if username:
        con = sqlite3.connect('twitter_clone.db')
        cur = con.cursor()
        cur.execute('DELETE FROM messages WHERE sender_id = (SELECT id FROM users WHERE username = ?)', (username,))
        cur.execute('DELETE FROM users WHERE username = ?', (username,))
        con.commit()
        con.close()
        response = RedirectResponse(url='/')
        response.delete_cookie(key='username')
        response.delete_cookie(key='password')
        return response

    return RedirectResponse(url='/')

if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)

