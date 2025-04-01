import os
import requests
import openai
import smtplib
from flask import Flask, request, jsonify
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API Keys from .env
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

# Ensure required environment variables are set
if not OPENAI_API_KEY:
    raise ValueError("Error: OPENAI_API_KEY is missing.")
if not SHOPIFY_API_KEY or not SHOPIFY_STORE_URL:
    raise ValueError("Error: Shopify credentials are missing.")
if not SENDER_EMAIL or not SENDER_PASSWORD:
    raise ValueError("Error: Email credentials are missing.")

# Initialize Flask App
app = Flask(__name__)

# Set OpenAI API Key
openai.api_key = OPENAI_API_KEY

# Shopify Headers
SHOPIFY_HEADERS = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": SHOPIFY_API_KEY
}

@app.route("/products", methods=["GET"])
def get_products():
    url = f"{SHOPIFY_STORE_URL}/admin/api/2023-10/products.json"
    response = requests.get(url, headers=SHOPIFY_HEADERS)
    return jsonify(response.json()) if response.status_code == 200 else jsonify({"error": "Failed to fetch products"}), response.status_code

@app.route("/chat", methods=["POST"])
def chat_with_gpt():
    data = request.json
    user_message = data.get("message", "")
    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    openai_payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": user_message}]
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", 
                             headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                             json=openai_payload)
    return jsonify(response.json()) if response.status_code == 200 else jsonify({"error": "Failed to connect to OpenAI"}), response.status_code

@app.route("/generate_plan", methods=["POST"])
def generate_plan():
    data = request.json
    required_fields = ["email", "fitness_goal", "training_location", "weight", "fitness_level", "diet_level", "height", "age", "sleep_hours", "training_frequency"]
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"{field} is required"}), 400

    data.setdefault("equipment", None)
    data.setdefault("additional_info", None)

    prompt = f"Create a 7-day fitness and diet plan for a user based on: {data}"
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a professional fitness coach."}, {"role": "user", "content": prompt}],
        max_tokens=1500
    )
    fitness_plan = response.choices[0].message["content"]

    msg = MIMEMultipart()
    msg["From"], msg["To"], msg["Subject"] = SENDER_EMAIL, data["email"], "Your AI Fitness Plan"
    msg.attach(MIMEText(fitness_plan, "plain"))
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, data["email"], msg.as_string())
        server.quit()
        return jsonify({"message": "Plan generated and sent successfully!"})
    except Exception as e:
        return jsonify({"error": f"Failed to send email: {e}"}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to the Shopify & OpenAI API!"})

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
