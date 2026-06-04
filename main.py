from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import base64

app = FastAPI()
templates = Jinja2Templates(directory="templates")

numbers_history = []

def get_rebtel_data(phone):
    try:
        clean = phone.replace("+", "").replace(" ", "").strip()
        if clean.startswith("91") and len(clean) > 10:
            clean = clean[2:]

        url = f"https://www.rebtel.com/en/recharge/india/products?msisdn=+91{clean}"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=20000)
            page.wait_for_timeout(4000)

            screenshot = page.screenshot()
            screenshot_base64 = base64.b64encode(screenshot).decode('utf-8')
            content = page.content()
            browser.close()

        soup = BeautifulSoup(content, "html.parser")
        text = soup.get_text().lower()

        if "jio" in text:
            operator = "Jio"
        elif "airtel" in text:
            operator = "Airtel"
        elif "bsnl" in text:
            operator = "BSNL"
        elif "vi" in text or "vodafone" in text or "idea" in text:
            operator = "Vi"
        else:
            operator = "Unknown"

        return {"operator": operator, "screenshot": screenshot_base64}
    except:
        return {"operator": "Unknown", "screenshot": None}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Fixed: Using list() to avoid "unhashable type: 'dict'" error
    return templates.TemplateResponse("index.html", {
        "request": request,
        "numbers": list(numbers_history)
    })

@app.post("/load_services")
async def load_services(api_key: str = Form(...), country: str = Form("in")):
    try:
        url = "https://otpdoctor.in/stubs/handler_api.php"
        params = {"action": "getServices", "api_key": api_key, "country": country}
        response = requests.get(url, params=params, timeout=30)
        return {"status": "success", "data": response.text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/get_number")
async def get_number(api_key: str = Form(...), service: str = Form(...)):
    try:
        url = "https://otpdoctor.in/stubs/handler_api.php"
        params = {"action": "getNumber", "api_key": api_key, "service": service}
        response = requests.get(url, params=params, timeout=30).text.strip()

        if response.startswith("ACCESS_NUMBER"):
            parts = response.split(":")
            phone = parts[2]
            rebtel = get_rebtel_data(phone)

            number_data = {
                "phone": phone,
                "service": service,
                "activation_id": parts[1],
                "operator": rebtel["operator"],
                "screenshot": rebtel["screenshot"],
                "status": "Waiting",
                "otp": None,
                "created_at": datetime.now(),
                "cancel_time": datetime.now() + timedelta(minutes=1),
                "auto_cancel_time": datetime.now() + timedelta(minutes=5)
            }
            numbers_history.append(number_data)
            return {"status": "success", "number": number_data}
        else:
            return {"status": "error", "message": response}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/check_otp")
async def check_otp(activation_id: str = Form(...)):
    return {"status": "success", "message": "OTP checking will be improved"}

@app.post("/cancel_number")
async def cancel_number(activation_id: str = Form(...)):
    return {"status": "success", "message": "Cancel will be improved"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
