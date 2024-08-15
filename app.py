from flask import Flask, render_template, request, redirect
import cloudinary
import cloudinary.uploader
import requests
from PIL import Image, ImageEnhance
import os
import json
import io

app = Flask(__name__)

# إعداد Cloudinary
cloudinary.config(
    cloud_name='dl2xpanl2',  # استبدل بالقيمة الخاصة بك
    api_key='475655655261754',  # استبدل بالقيمة الخاصة بك
    api_secret='5A325nu-ZbcLhjeQT10-R8voP_s'  # استبدل بالقيمة الخاصة بك
)

REMOVE_BG_API_KEY = 'nCNkwVB1NRraJuYjHwohjmVk'  # API الخاص بـ remove.bg

TRANSLATIONS_FOLDER = 'translations'

def load_translation(language):
    translation_file = os.path.join(TRANSLATIONS_FOLDER, f'{language}.json')
    if os.path.exists(translation_file):
        with open(translation_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def remove_bg(image_data):
    response = requests.post(
        'https://api.remove.bg/v1.0/removebg',
        files={'image_file': image_data},
        data={'size': 'auto'},
        headers={'X-Api-Key': REMOVE_BG_API_KEY}
    )
    if response.status_code == 200:
        return Image.open(io.BytesIO(response.content))
    else:
        raise Exception(f"Error removing background: {response.status_code}, {response.text}")

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

    # معالجة الصورة محليًا
    img = Image.open(file)
    
    # إزالة البيانات الوصفية
    data = list(img.getdata())
    img_without_metadata = Image.new(img.mode, img.size)
    img_without_metadata.putdata(data)

    # إزالة الخلفية إذا كان المستخدم يريد ذلك
    if request.form.get('remove_bg'):
        img_without_metadata = remove_bg(file)

    # تغيير DPI إذا تم تحديده
    dpi = int(request.form.get('dpi', 72))
    
    # تغيير العرض والارتفاع
    width = int(request.form.get('width', img.width))
    height = int(request.form.get('height', img.height))
    img_without_metadata = img_without_metadata.resize((width, height), Image.ANTIALIAS)
    
    # تحسين جودة الصورة
    enhancer = ImageEnhance.Sharpness(img_without_metadata)
    img_without_metadata = enhancer.enhance(2.0)  # زيادة الحدة
    enhancer = ImageEnhance.Contrast(img_without_metadata)
    img_without_metadata = enhancer.enhance(1.5)  # زيادة التباين
    
    # حفظ الصورة في الذاكرة المؤقتة
    image_io = io.BytesIO()
    img_without_metadata.save(image_io, format='PNG', dpi=(dpi, dpi))
    image_io.seek(0)
    
    # رفع الصورة إلى Cloudinary
    upload_result = cloudinary.uploader.upload(image_io, public_id=request.form.get('new_name', os.path.splitext(file.filename)[0]))

    # استخراج رابط الصورة المعالجة
    processed_image_url = upload_result['secure_url']

    language = request.args.get('lang', 'en')
    translation = load_translation(language)
    
    return render_template('result.html', 
                           translation=translation, 
                           new_name=request.form.get('new_name', os.path.splitext(file.filename)[0]), 
                           width=upload_result['width'], 
                           height=upload_result['height'], 
                           dpi=dpi, 
                           file_format=upload_result['format'], 
                           filename=processed_image_url)

if __name__ == '__main__':
    if not os.path.exists(TRANSLATIONS_FOLDER):
        os.makedirs(TRANSLATIONS_FOLDER)
    app.run(host='0.0.0.0', port=8080)
