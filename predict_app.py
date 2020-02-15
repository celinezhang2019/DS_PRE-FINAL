import base64
import numpy as np
import io
from PIL import Image
import keras
from keras import backend as K
from keras.models import Sequential
from keras.models import load_model
from keras.preprocessing.image import ImageDataGenerator
from keras.preprocessing.image import img_to_array
from flask import request
from flask import jsonify
from flask import Flask
from keras import applications

import os
import uuid
import shutil
import zipfile
from flask import render_template

# celine add according to: https://blog.csdn.net/qq_36213248/article/details/90049915
import tensorflow as tf
global graph,model
graph = tf.get_default_graph()


app = Flask(__name__)

BASE_DIR = "/Users/zxt/Desktop/pic/testzip1" #os.path.dirname(os.path.abspath(__file__))


# 遍历文件夹
def walkFile(file):
    for root, dirs, files in os.walk(file):

        # root 表示当前正在访问的文件夹路径
        # dirs 表示该文件夹下的子目录名list
        # files 表示该文件夹下的文件list

        # 遍历文件
        for f in files:
            filePath = os.path.join(root, f)
            if(filePath.endswith('.png')):
                print(filePath)

def unzip_file(zip_src, dst_dir):
    """
    解压zip文件
    :param zip_src: zip文件的全路径
    :param dst_dir: 要解压到的目的文件夹
    :return:
    """
    r = zipfile.is_zipfile(zip_src)
    if r:
        fz = zipfile.ZipFile(zip_src, "r")
        for file in fz.namelist():
            fz.extract(file, dst_dir)
    else:
        return "请上传zip类型压缩文件"

def get_model():
    global model
    #model = load_model('VGG16_cats_and_dogs.h5')
    #model = load_model('model_vgg.h5')
    model = load_model('model_vgg2.h5')
    print(" * Model loaded!")

def preprocess_image(image, target_size):
    if image.mode != "RGB":
        image = image.convert("RGB")
    image = image.resize(target_size)
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)

    return image

print(" * Loading Keras model...")
get_model()

@app.route("/dictionary", methods=["POST"])
def dictionary():
    message = request.get_json(force=True)
    prediction_id = message['prediction_id']
    print("#prediction_id=" + prediction_id)
    
    #print("#walkFile")
    #walkFile(BASE_DIR + '/' + prediction_id)
    
    response = {
        'prediction': []
    }
    
    prediction_id_direction = BASE_DIR + '/' + prediction_id #遍历解压文件所在目录
    for root, dirs, files in os.walk(prediction_id_direction):
        for f in files:
            filePath = os.path.join(root, f)
            print("#filePath=" + filePath)
            print(filePath.count('__MACOSX'))
            if (os.path.exists(filePath)):
                if((filePath.endswith('.jpg') or filePath.endswith('.jpeg') or filePath.endswith('.png')) and filePath.count('__MACOSX')==0):
                    image = Image.open(filePath)
                    processed_image = preprocess_image(image, target_size=(224, 224))

                    with graph.as_default():
                        prediction = model.predict(processed_image).tolist()
                       
                    prediction_item = {
                        'fileName': f,
                        'dog': prediction[0][1],
                        'cat': prediction[0][0]
                    }
                    
                    #http://osask.cn/front/ask/view/4047678
                    response['prediction'].append(prediction_item)
                    
    print("#response")
    print(response)
    return jsonify(response)


@app.route("/predict", methods=["POST"])
def predict():
    message = request.get_json(force=True)
    encoded = message['image']
    decoded = base64.b64decode(encoded)
    image = Image.open(io.BytesIO(decoded))
    processed_image = preprocess_image(image, target_size=(224, 224))
    
    with graph.as_default():
        prediction = model.predict(processed_image).tolist()

    response = {
        'prediction': [{
            'dog': prediction[0][1],
            'cat': prediction[0][0]
        },
        {
            'dog': prediction[0][1],
            'cat': prediction[0][0]
        }]
    }
    return jsonify(response)


# https://www.cnblogs.com/believepd/p/10339394.html
@app.route("/upload", methods=["POST"])
def upload():
    #if request.method == "GET":
    #    return render_template("upload.html")
    obj = request.files.get("file")
    print(obj)  # <FileStorage: "test.zip" ("application/x-zip-compressed")>
    print("filename:" + obj.filename)  # test.zip
    print(obj.stream)  # <tempfile.SpooledTemporaryFile object at 0x0000000004135160>
    # 检查上传文件的后缀名是否为zip
    ret_list = obj.filename.rsplit(".", maxsplit=1)
    if len(ret_list) != 2:
        return "请上传zip类型压缩文件"
    if ret_list[1] != "zip":
        return "请上传zip类型压缩文件"

    # 方式一：直接保存文件
    # obj.save(os.path.join(BASE_DIR, obj.filename))
    
    # 方式三：先保存压缩文件到本地，再对其进行解压，然后删除压缩文件
    file_path = os.path.join(BASE_DIR, obj.filename)  # 上传的文件保存到的路径
    obj.save(file_path)
    target_dictionary = str(uuid.uuid4())
    print("target_dictionary=" + target_dictionary)
    target_path = os.path.join(BASE_DIR, target_dictionary)  # 解压后的文件保存到的路径
    ret = unzip_file(file_path, target_path)
    #os.remove(file_path)  # 删除文件
    if ret:
        return ret
    
    response = {
        'result': '[' + obj.filename + ']文件上传成功，可以点击Predict按钮 开始预测',
        'prediction_id': target_dictionary
    }
    return jsonify(response)