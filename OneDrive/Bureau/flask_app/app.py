from flask import Flask, render_template, request, send_file, redirect, url_for
from PIL import Image
import os
import io
import json

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'static/images'
TRANSLATIONS_FOLDER = 'translations'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

def load_translation(language):
    translation_file = os.path.join(TRANSLATIONS_FOLDER, f'{language}.json')
    if os.path.exists(translation_file):
        with open(translation_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

@app.route('/')
def index():
    language = request.args.get('lang', 'en')
    translation = load_translation(language)
    return render_template('index.html', translation=translation)

@app.route('/process_image', methods=['POST'])
def process_image():
    if 'image' not in request.files:
        return "No file part"
    
    file = request.files['image']
    if file.filename == '':
        return "No selected file"
    
    try:
        img = Image.open(file)
    except Exception as e:
        return f"Error processing image: {str(e)}"

    new_image_name = request.form.get('new_name', os.path.splitext(file.filename)[0])
    width = request.form.get('width', '')
    height = request.form.get('height', '')
    dpi = int(request.form.get('dpi', 72))

    if width and height:
        width = int(width)
        height = int(height)
        img = img.resize((width, height))

    processed_file_path = os.path.join(app.config['PROCESSED_FOLDER'], new_image_name + '.png')
    img.save(processed_file_path, dpi=(dpi, dpi), format='PNG')

    language = request.args.get('lang', 'en')
    translation = load_translation(language)
    
    return render_template('result.html', 
                           translation=translation, 
                           new_name=new_image_name, 
                           width=width if width else 'Original', 
                           height=height if height else 'Original', 
                           dpi=dpi, 
                           file_format='PNG',
                           filename=new_image_name + '.png')

@app.route('/download_file/<filename>')
def download_file(filename):
    file_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
    if not os.path.exists(file_path):
        return "File not found", 404
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if not os.path.exists(PROCESSED_FOLDER):
        os.makedirs(PROCESSED_FOLDER)
    if not os.path.exists(TRANSLATIONS_FOLDER):
        os.makedirs(TRANSLATIONS_FOLDER)
    app.run(debug=True)
