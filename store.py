import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API Keys from .env
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Flask App
app = Flask(__name__)

# Shopify Headers
SHOPIFY_HEADERS = {
    "Content-Type": "application/json",
    "X-Shopify-Access-Token": SHOPIFY_API_KEY
}

# ✅ Shopify: Fetch Products
@app.route("/products", methods=["GET"])
def get_products():
    url = f"{SHOPIFY_STORE_URL}/admin/api/2023-10/products.json"
    response = requests.get(url, headers=SHOPIFY_HEADERS)

    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to fetch products"}), response.status_code

# ✅ OpenAI: Generate a Response
@app.route("/chat", methods=["POST"])
def chat_with_gpt():
    data = request.json
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    openai_url = "https://api.openai.com/v1/chat/completions"
    openai_headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    openai_payload = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": user_message}]
    }

    response = requests.post(openai_url, headers=openai_headers, json=openai_payload)

    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to connect to OpenAI"}), response.status_code

# ✅ Home Route
@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to the Shopify & OpenAI API!"})

# Run App
if __name__ == "__main__":
    app.run(debug=True)
