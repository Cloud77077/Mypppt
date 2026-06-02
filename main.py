from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import json

app = FastAPI()
templates = Jinja2Templates(directory="templates")

numbers_history = []

def get_operator_rebtel(phone):
    try:
        clean = phone.replace("+", "").replace(" ", "").strip()
        if clean.startswith("91") and len(clean) > 10:
            clean = clean[2:]

        url = f"https://www.rebtel.com/en/recharge/india/products?msisdn=+91{clean}"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=15000)
            page.wait_for_timeout(3000)
            content = page.content()
            browser.close()

        soup = BeautifulSoup(content, "html.parser")
        text = soup.get_text().lower()

        if "jio" in text: return "Jio"
        if "airtel" in text: return "Airtel"
        if "bsnl" in text: return "BSNL"
        if "vi" in text or "vodafone" in text or "idea" in text: return "Vi"
        return "Unknown"
    except:
        return "Error"

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "numbers": numbers_history
    })

@app.post("/get_number")
async def get_number(api_key: str = Form(...), service: str = Form(...)):
    try:
        url = "https://otpdoctor.in/stubs/handler_api.php"
        params = {"action": "getNumber", "api_key": api_key, "service": service}
        response = requests.get(url, params=params, timeout=30).text.strip()

        if response.startswith("ACCESS_NUMBER"):
            parts = response.split(":")
            phone = parts[2]
            operator = get_operator_rebtel(phone)

            number_data = {
                "phone": phone,
                "service": service,
                "activation_id": parts[1],
                "operator": operator,
                "status": "Waiting",
                "otp": None,
                "created_at": datetime.now(),
                "cancel_time": datetime.now() + timedelta(minutes=2),
                "auto_cancel_time": datetime.now() + timedelta(minutes=5)
            }
            numbers_history.append(number_data)
            return {"status": "success", "number": number_data}
        else:
            return {"status": "error", "message": response}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
