'''
Starts a Twitter Clone Webpage.
'''

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import sqlite3
import uvicorn

app = FastAPI()
templates = Jinja2Templates(directory='templates')
app.mount("/static", StaticFiles(directory="static"), name="static")

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
    # Extract username from database
    con = sqlite3.connect('twitter_clone.db')
    cur = con.cursor()

    sql = """
    SELECT users.username, users.age, messages.message, messages.created_at
    FROM messages
    JOIN users ON messages.sender_id = users.id
    ORDER BY messages.created_at DESC;
    """

    cur.execute(sql)
    rows = cur.fetchall()
    messages = []

    for row in rows:
        messages.append({
            "username": row[0],
            "age": row[1],
            "message": row[2],
            "created_at": row[3]
        })

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "is_logged_in": check_credentials(request),
            "username": check_credentials(request),
            "messages": messages
        }
    )
    con.close()

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
                response = RedirectResponse(url='/', status_code=302)
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
    return templates.TemplateResponse(
        request=request,
        name='create_message.html',
        context={
            'is_logged_in': check_credentials(request),
            "username": check_credentials(request),
        }
    )

@app.get('/create_user', response_class=HTMLResponse)
async def create_user(request: Request):
    return templates.TemplateResponse(
        request=request,
        name='create_user.html',
        context={
            'is_logged_in': check_credentials(request),
            "username": check_credentials(request),
        }
    )


if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=True)

