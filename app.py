from flask import Flask, request, jsonify, render_template
import whisper
from pymongo import MongoClient
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# =========================
# LOAD WHISPER MODEL
# =========================

print("Loading Whisper model...")

model = whisper.load_model("tiny")

print("Model loaded")

# =========================
# MONGODB CONNECTION
# =========================

MONGO_URI = "mongodb+srv://suma:Sumah123@cluster0.2oqefut.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(MONGO_URI)

db = client["speech_to_text_db"]

users_collection = db["users"]

transcription_collection = db["transcriptions"]

print("MongoDB Connected")

# =========================
# HOME
# =========================

@app.route("/")
def home():

    return render_template("index.html")

# =========================
# REGISTER
# =========================

@app.route("/register", methods=["POST"])
def register():

    try:

        data = request.get_json()

        email = data["email"]

        password = data["password"]

        # CHECK EXISTING USER

        existing_user = users_collection.find_one({
            "email": email
        })

        if existing_user:

            return jsonify({
                "message": "User already exists"
            })

        # HASH PASSWORD

        hashed_password = generate_password_hash(password)

        # SAVE USER

        users_collection.insert_one({

            "email": email,

            "password": hashed_password

        })

        return jsonify({
            "message": "Registration successful"
        })

    except Exception as e:

        print(e)

        return jsonify({
            "message": "Registration failed"
        })

# =========================
# LOGIN
# =========================

@app.route("/login", methods=["POST"])
def login():

    try:

        data = request.get_json()

        email = data["email"]

        password = data["password"]

        user = users_collection.find_one({
            "email": email
        })

        if not user:

            return jsonify({
                "success": False,
                "message": "User not found"
            })

        # CHECK PASSWORD

        if not check_password_hash(
            user["password"],
            password
        ):

            return jsonify({
                "success": False,
                "message": "Incorrect password"
            })

        return jsonify({
            "success": True,
            "message": "Login successful"
        })

    except Exception as e:

        print(e)

        return jsonify({
            "success": False,
            "message": "Login failed"
        })

# =========================
# TRANSCRIBE
# =========================

@app.route("/transcribe", methods=["POST"])
def transcribe():

    try:

        print("\n=== NEW REQUEST ===")

        if "audio" not in request.files:

            return jsonify({
                "text": "No audio received"
            })

        email = request.form["email"]

        file = request.files["audio"]

        webm_path = "temp.webm"

        file.save(webm_path)

        print("Saved webm")

        # WHISPER TRANSCRIPTION

        result = model.transcribe(webm_path)

        text = result["text"]

        print("Transcription:", text)

        # SAVE TO DATABASE

        transcription_collection.insert_one({

            "email": email,

            "text": text,

            "created_at": datetime.now()

        })

        return jsonify({
            "text": text
        })

    except Exception as e:

        print("ERROR:", str(e))

        return jsonify({
            "text": "Error occurred"
        })

# =========================
# HISTORY
# =========================

@app.route("/history/<email>")
def history(email):

    try:

        data = transcription_collection.find({

            "email": email

        }).sort("created_at", -1)

        history_list = []

        for item in data:

            history_list.append({

                "text": item["text"],

                "created_at": item["created_at"]

            })

        return jsonify(history_list)

    except Exception as e:

        print(e)

        return jsonify([])

# =========================
# RUN APP
# =========================

if __name__ == "__main__":

    app.run(debug=False)