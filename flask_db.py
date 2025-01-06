from flask import Flask, request, jsonify, render_template, redirect, url_for
import google.generativeai as genai
from PIL import Image
import pytesseract
from pymongo import MongoClient
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)

genai.configure(api_key="AIzaSyD0nd00vnh2sZLPVprzTDxe0Pi6IxwkrP4")
model = genai.GenerativeModel("gemini-1.5-flash")

MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client["data"]  
collection = db["text"]  

@app.route("/", methods=["GET"])
def index():
    return render_template("upload.html")  

@app.route("/upload", methods=["POST"])
def upload_images():
    try:
        if "images" not in request.files:
            return jsonify({"error": "No images provided"}), 400

        uploaded_images = request.files.getlist("images")
        if len(uploaded_images) not in [1, 2]:
            return jsonify({"error": "Please upload one or two images"}), 400

        images = []
        for img_file in uploaded_images:
            img = Image.open(img_file)
            images.append(img)

        if len(images) == 1:
            image = images[0]
            text = pytesseract.image_to_string(image)
            response = model.generate_content(
                [
                    "Extract the company name, name, profession, email address, address, phone number, and website. "
                    "Provide the output in JSON format. Don't provide the unwanted string, Provide only json.",
                    text,
                ]
            )
        else:
            text1 = pytesseract.image_to_string(images[0])
            text2 = pytesseract.image_to_string(images[1])
            response = model.generate_content(
                [
                    "Combine the information from the following images. Extract the company name, name, profession, "
                    "email address, address, phone number, and website. Provide the output in JSON format. "
                    "Don't provide the unwanted string, Provide only json.",
                    text1,
                    text2,
                ]
            )

        js = response.text.strip().replace("```json", "").replace("```", "")
        data = json.loads(js)
        collection.insert_one(data)
        return redirect(url_for("search_record"))
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse the response. Ensure the model output is in JSON format."}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/search", methods=["GET", "POST"])
def search_record():
    if request.method == "POST":
        try:
            search_query = request.form.get("search_query", "").strip()
            if not search_query:
                return jsonify({"error": "Please provide a keyword to search"}), 400

            query = {"$or": [
                {key: {"$regex": search_query, "$options": "i"}}
                for key in ["company_name", "name", "profession", "email", "address", "phone_number", "website"]
            ]}
            results = collection.find(query, {"_id": 0})  # Exclude MongoDB's internal _id field
            results_list = list(results)

            if not results_list:
                return render_template("results.html", data=None)  # Render "no results" message

            return render_template("results.html", data=results_list)  # Render matching records
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return render_template("search.html")


if __name__ == "__main__":
    app.run(debug=True)
