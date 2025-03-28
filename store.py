import openai
import smtplib
from flask import Flask, request, jsonify
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Debugging: Print environment variables (for testing; remove in production)
print("OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))
print("SENDER_EMAIL:", os.getenv("SENDER_EMAIL"))

# Ensure required environment variables are set
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("Error: OPENAI_API_KEY is missing. Make sure it's set in the environment variables.")
if not os.getenv("SENDER_EMAIL") or not os.getenv("SENDER_PASSWORD"):
    raise ValueError("Error: Email credentials are missing. Set SENDER_EMAIL and SENDER_PASSWORD.")

# Initialize Flask app
app = Flask(__name__)

# Set OpenAI API Key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_fitness_plan(user_data):
    """Generates a personalized fitness plan using OpenAI GPT-4o-mini."""
    prompt = f"""
    Create a highly detailed 7-day fitness and diet plan for a user based on the following details:

    - **Email:** {user_data['email']}
    - **Fitness Goal:** {user_data['fitness_goal']}
    - **Where do you train:** {user_data['training_location']}
    - **Available Equipment (if any):** {user_data['equipment'] or 'None'}
    - **Current Weight:** {user_data['weight']} kg
    - **Fitness Level:** {user_data['fitness_level']}
    - **Diet Level:** {user_data['diet_level']}
    - **Height:** {user_data['height']} cm
    - **Age:** {user_data['age']}
    - **Average Hours of Sleep:** {user_data['sleep_hours']} hours
    - **How many times do you train per week:** {user_data['training_frequency']}
    - **Additional Information:** {user_data['additional_info'] or 'None'}

    - **Fitness Plan Format:**
      1. Daily workout plan (including exercise names, sets, reps, and rest time)
      2. Daily diet plan (meals with calorie & macronutrient breakdown)
      3. Any special tips or adjustments based on fitness level, equipment, and diet level.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional fitness coach and nutritionist."},
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
    msg["From"] = os.getenv("SENDER_EMAIL")
    msg["To"] = recipient_email
    msg["Subject"] = "Your Personalized AI Fitness Plan"
    msg.attach(MIMEText(fitness_plan, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(os.getenv("SENDER_EMAIL"), os.getenv("SENDER_PASSWORD"))
        server.sendmail(os.getenv("SENDER_EMAIL"), recipient_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@app.route("/generate_plan", methods=["POST"])
def generate_plan_route():
    """Handles POST request: generates a fitness plan and sends it via email."""
    data = request.json

    # Validate required fields
    required_fields = [
        "email", "fitness_goal", "training_location", "weight", "fitness_level",
        "diet_level", "height", "age", "sleep_hours", "training_frequency"
    ]
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"{field} is required"}), 400

    # Set optional fields to None if missing
    data.setdefault("equipment", None)
    data.setdefault("additional_info", None)

    # Generate the fitness plan
    fitness_plan = generate_fitness_plan(data)
    if not fitness_plan:
        return jsonify({"error": "Failed to generate fitness plan"}), 500

    # Send email with the fitness plan
    if send_email(data["email"], fitness_plan):
        return jsonify({"message": "Plan generated and sent successfully!"})
    else:
        return jsonify({"error": "Failed to send email"}), 500

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Welcome to the Shopify & OpenAI API!"})

