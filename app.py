from flask import Flask, render_template, request, session, url_for, redirect, flash
import tensorflow as tf
import pymysql
import time
import cv2
import datetime
import numpy as np
import pandas as pd
import os
from werkzeug.utils import secure_filename

import matplotlib.pyplot as plt
from tensorflow.keras.preprocessing import image
import ast

#import imutils
UPLOAD_FOLDER = 'static/Currency/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'random string'


##################################################load modelfunction##########################################
def predict_image(imgname, from_test_dir):
    test_image = image.load_img(imgname, target_size = (224, 224))

    # plt.imshow(test_image)
    # plt.show()

    test_image = np.asarray(test_image)
    test_image = np.expand_dims(test_image, axis=0)
    interpreter.set_tensor(input_details[0]['index'], test_image.astype('float32'))
    interpreter.invoke()
    result = interpreter.get_tensor(output_details[0]['index'])


    result_dict = dict()
    for key in list(final_labels.keys()):
        result_dict[final_labels[key]] = result[0][key]
    sorted_results = {k: v for k, v in sorted(result_dict.items(), key=lambda item: item[1], reverse=True)}

    if not from_test_dir:
        print('=' * 50)
        for label in sorted_results.keys():
            print("{}: {}%".format(label, sorted_results[label] * 100))

    final_result = dict()
    final_result[list(sorted_results.keys())[0]] = sorted_results[list(sorted_results.keys())[0]] * 100

    return final_result

def verify_test_dir():
    path = 'test-images'
    folders = os.listdir(path)

    correct_preds = 0
    file_count = 0
    for fold in folders:
        files = os.listdir(path + '\\' + fold)
        for filename in files:
            final_string = fold
            prediction = predict_image(path + '\\{}\\'.format(fold) + filename, True)
            if list(prediction.keys())[0] == final_string:
                print("{}\{}: Correct Prediction".format(fold, filename), prediction)
                correct_preds += 1
            else:
                print("{}\{}: INCORRECT PREDICTION".format(fold, filename), prediction)
            file_count += 1

    print(correct_preds, file_count)


interpreter = tf.lite.Interpreter(model_path="Model_training/new_convert_to_lite.tflite")
interpreter.allocate_tensors()

# Get input and output tensor details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

f = open("Model_training/vgg16_watermark_class_indices.txt", "r")
labels = f.read()
labels = ast.literal_eval(labels)
final_labels = {v: k for k, v in labels.items()}


##################################################load modelfunction##########################################
##################################################database connection##########################################

def dbConnection():
    try:
        connection = pymysql.connect(host="localhost", user="root", password="root", database="fakecurrency")
        return connection
    except:
        print("Something went wrong in database Connection")


def dbClose():
    try:
        dbConnection().close()
    except:
        print("Something went wrong in Close DB Connection")

##################################################database connection##########################################


@app.route('/pred', methods=["GET","POST"])
def audio():
    print("Printing Hi before post method")
    if request.method == "POST":
        f2= request.files['file']
        print("File is uploaded")
        print(f2)
        filename_secure = secure_filename(f2.filename)
        print("### filename_secure ###")
        print(filename_secure)
        f2.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_secure))
        print("print saved") 
        filename1 =os.path.join(app.config['UPLOAD_FOLDER'], filename_secure)
        print(filename1)
        
        final_result = predict_image(filename1, False)
        print("Final Result: ", final_result)
        
        result = []
        result_probability = []
        for key,val in final_result.items():
            
            if key == "yes_watermark":
                a = "Currency is Real"
                result.append(a)
                result_probability.append(val)
            else:
                a = "Currency is Fake"
                result.append(a)
                result_probability.append(val)
            
        
        
        return render_template("pred.html",result_probability=result_probability[0],result=result[0],filename1=filename1) 
    return render_template("pred.html")

@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/logout')
def logout():
    session.pop('user')
    session.pop('userid')
    return redirect(url_for('login'))


@app.route('/', methods=["GET","POST"])
def login():
    msg = ''
    if request.method == "POST":
        try:
            session.pop('user',None)
            username = request.form.get("email")
            password = request.form.get("pass")
            con = dbConnection()
            cursor = con.cursor()
            cursor.execute('SELECT * FROM userdetails WHERE email = %s AND pass = %s', (username, password))
            result = cursor.fetchone()
            if result:
                session['user'] = result[1]
                session['userid'] = result[0]
                return redirect(url_for('index'))
            else:
                return render_template('login.html')
        except:
            print("Exception occured at login")
            return render_template('login.html') 
        finally:
            dbClose()
    #return redirect(url_for('index'))
    return render_template('login.html')       

@app.route('/register', methods=["GET","POST"])
def register():
    if request.method == "POST":
        try:
            fname = request.form.get("fname")
            lname = request.form.get("lname")
            email = request.form.get("email")
           
            password = request.form.get("pass")
            print(fname,lname,email,password)
            
            con = dbConnection()
            cursor = con.cursor()
            sql = "INSERT INTO userdetails (fname, lname,email, pass) VALUES (%s, %s, %s, %s)"
            val = (fname, lname,email, password)
            print("printing hi after query")
            cursor.execute(sql, val)
            con.commit()
            return render_template('login.html')
        except:
            print("Exception occured at register")
            return render_template('register.html')
        finally:
            dbClose()
    return render_template('register.html') 

# @app.route('/home')
# def home():
#     if 'user' in session:
#         return render_template('home.html', user=session['user'])
#     return redirect(url_for('index'))

@app.route('/about')
def about():
    # if 'user' in session:
    # return render_template('about.html', user=session['user'])
    return render_template('about.html')

@app.route('/contact')
def contact():
    # if 'user' in session:
    # return render_template('contact.html', user=session['user'])
    return render_template('contact.html')


if __name__ == '__main__':
    app.run(debug=True)
    # app.run('0.0.0.0')
