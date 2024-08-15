from flask import Flask, render_template, request, redirect
import cloudinary
import cloudinary.uploader
import os
import json

app = Flask(__name__)

# إعداد Cloudinary
cloudinary.config(
    cloud_name='dl2xpanl2',  # استبدل بالقيمة الخاصة بك
    api_key='475655655261754',  # استبدل بالقيمة الخاصة بك
    api_secret='5A325nu-ZbcLhjeQT10-R8voP_s'  # استبدل بالقيمة الخاصة بك
)

TRANSLATIONS_FOLDER = 'translations'

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

    # احصل على اسم الصورة الجديد من المستخدم
    new_image_name = request.form.get('new_name', os.path.splitext(file.filename)[0])

    # رفع الصورة إلى Cloudinary
    upload_result = cloudinary.uploader.upload(file, public_id=new_image_name)

    # استخراج رابط الصورة المعالجة
    processed_image_url = upload_result['secure_url']

    language = request.args.get('lang', 'en')
    translation = load_translation(language)
    
    return render_template('result.html', 
                           translation=translation, 
                           new_name=new_image_name, 
                           width=upload_result['width'], 
                           height=upload_result['height'], 
                           dpi='Original',  # Cloudinary لا يقوم بتغيير DPI
                           file_format=upload_result['format'],  # صيغة الصورة
                           filename=processed_image_url)

@app.route('/download_file/<filename>')
def download_file(filename):
    # في هذا السيناريو، يتم تقديم رابط مباشر لتنزيل الصورة من Cloudinary
    return redirect(filename)

if __name__ == '__main__':
    if not os.path.exists(TRANSLATIONS_FOLDER):
        os.makedirs(TRANSLATIONS_FOLDER)
    app.run(host='0.0.0.0', port=8080)
