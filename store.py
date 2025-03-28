import openai
import smtplib
from flask import Flask, request, jsonify
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Securely get API keys and email credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

# Validate environment variables
if not OPENAI_API_KEY:
    raise ValueError("Error: Missing OPENAI_API_KEY in .env file.")
if not SENDER_EMAIL or not SENDER_PASSWORD:
    raise ValueError("Error: Missing email credentials in .env file.")

# Initialize Flask app
app = Flask(__name__)

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

def generate_fitness_plan(user_data):
    """Generates a personalized fitness and diet plan using OpenAI."""
    prompt = f"""
    Create a highly detailed 7-day fitness and diet plan based on:
    - Email: {user_data['email']}
    - Goal: {user_data['fitness_goal']}
    - Training Location: {user_data['training_location']}
    - Equipment: {user_data['equipment'] or 'None'}
    - Weight: {user_data['weight']} kg
    - Height: {user_data['height']} cm
    - Age: {user_data['age']}
    - Fitness Level: {user_data['fitness_level']}
    - Diet Level: {user_data['diet_level']}
    - Sleep Hours: {user_data['sleep_hours']}
    - Training Frequency: {user_data['training_frequency']}
    - Additional Info: {user_data['additional_info'] or 'None'}

    **Plan Format**:
    1. Daily workout (exercise, sets, reps, rest time)
    2. Daily diet (meals with calories/macronutrient breakdown)
    3. Special tips based on fitness level, diet, and available equipment.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional fitness coach."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500
        )
        return response.choices[0].message["content"]
    except Exception as e:
        print(f"OpenAI API Error: {e}")
        return None

def send_email(recipient_email, fitness_plan):
    """Sends the generated fitness plan via email."""
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient_email
    msg["Subject"] = "Your AI-Generated Fitness Plan"

    msg.attach(MIMEText(fitness_plan, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@app.route("/generate_plan", methods=["POST"])
def generate_plan():
    """Handles POST request, generates a fitness plan, and sends it via email."""
    data = request.json

    required_fields = [
        "email", "fitness_goal", "training_location", "weight", "fitness_level",
        "diet_level", "height", "age", "sleep_hours", "training_frequency"
    ]
    
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"{field} is required"}), 400

    data.setdefault("equipment", None)
    data.setdefault("additional_info", None)

    fitness_plan = generate_fitness_plan(data)
    if not fitness_plan:
        return jsonify({"error": "Failed to generate fitness plan"}), 500

    if send_email(data["email"], fitness_plan):
        return jsonify({"message": "Plan generated and sent successfully!"})
    else:
        return jsonify({"error": "Failed to send email"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
