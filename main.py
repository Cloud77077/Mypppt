from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import json
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# In-memory storage for numbers (will reset if server restarts)
numbers_list = []

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/get_balance")
async def get_balance(api_key: str = Form(...)):
    try:
        url = "https://otpdoctor.in/stubs/handler_api.php"
        params = {"action": "getBalance", "api_key": api_key}
        response = requests.get(url, params=params, timeout=30)
        return {"status": "success", "balance": response.text.strip()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/load_services")
async def load_services(api_key: str = Form(...), country: str = Form("in")):
    try:
        url = "https://otpdoctor.in/stubs/handler_api.php"
        params = {"action": "getServices", "api_key": api_key, "country": country}
        response = requests.get(url, params=params, timeout=30)
        return {"status": "success", "services": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/get_number")
async def get_number(api_key: str = Form(...), service: str = Form(...)):
    try:
        url = "https://otpdoctor.in/stubs/handler_api.php"
        params = {"action": "getNumber", "api_key": api_key, "service": service}
        response = requests.get(url, params=params, timeout=30)
        return {"status": "success", "response": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
