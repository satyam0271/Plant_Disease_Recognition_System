from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import os
from werkzeug.utils import secure_filename
from model import PlantDiseaseModel, PLANT_CLASSES
from database import init_db, save_prediction, get_recent_predictions
import numpy as np
from remedies import REMEDIES


app = Flask(__name__)
app.secret_key = 'plant_disease_secret_key'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize model and database
model = PlantDiseaseModel()
init_db()


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    recent_predictions = get_recent_predictions()
    return render_template('index.html', recent=recent_predictions)

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join('static/uploads', filename)
        file.save(filepath)
        
        # Make prediction
        predicted_class_idx, confidence = model.predict(filepath)
        predicted_class = PLANT_CLASSES[predicted_class_idx]

        # Get remedy
        remedy = REMEDIES.get(predicted_class, {
            "name": "Unknown",
            "description": "No data available",
            "treatment": ["Consult expert"],
            "prevention": ["General care"]
        })
        
        # Save to database
        confidence = round(confidence * 100, 1)
        save_prediction(filename, predicted_class, float(confidence))
        # print("Saving:", filename, predicted_class, confidence)
        
        return render_template('results.html', 
                             filename=filename,
                             predicted_class=predicted_class,
                             confidence=confidence,
                             class_name=predicted_class.replace('___', ' - '),
                             remedy=remedy,
                             image_path=filepath
                            )
    
    flash('Invalid file type. Please upload image files only.')
    return redirect(url_for('index'))


@app.route('/api/predict', methods=['POST'])
def api_predict():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join('static/uploads', filename)
        file.save(filepath)

        # Prediction
        predicted_class_idx, confidence = model.predict(filepath)
        predicted_class = PLANT_CLASSES[predicted_class_idx]

        confidence = round(confidence * 100, 1)

        # Get remedy
        from remedies import REMEDIES
        remedy = REMEDIES.get(predicted_class, {
            "name": "Unknown",
            "description": "No data available",
            "treatment": ["Consult expert"],
            "prevention": ["General care"]
        })


        return jsonify({
            "class": predicted_class,
            "confidence": float(confidence),
            "remedy": remedy
        })

    return jsonify({"error": "Invalid file type"}), 400

@app.route('/history')
def history():
    recent_predictions = get_recent_predictions(50)
    # print("History data:", recent_predictions)
    return render_template('history.html', recent=recent_predictions)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)