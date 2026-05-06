"""
Starts a hello world webserver.
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
# from dbm import sqlite3
import uvicorn

def check_credentials(request: Request):
    """

    """

    username = request.query_params.get("username")
    password = request.query_params.get("password")
    print('username = ', username)
    print('password = ', password)
     # FIXME: this should connect to the db

    if username.lower() == 'trump' and password == 12345:
        return 'Trump'
    else: 
        return False



app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    is_logged_in = check_credentials(request)

    # con = sqlite3.connect("twitter_clone.db")
    # cur = con.cursor()
    # sql = """
    # SELECT username FROM useres WHERE id = 3
    # """

    # cur.execute(sql)
    # for row in cur.fetchall():
    #     username = row[0]

    username = "temp"
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "is_logged_in": check_credentials(request),
            "username": username,
        }
    )



@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "is_logged_in": check_credentials(request)
        }
    )

@app.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="logout.html",
        context={
            "is_logged_in": check_credentials(request)
        }
    )


if __name__ == "__main__":
    uvicorn.run('main:app', host='127.0.0.1', port=8000, reload=True)