
from flask import Flask, render_template, request, redirect, url_for
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'

@app.route('/')
def index():
    return render_template('home.html', number=1)

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route('/register_company')
def register_company():
    return render_template('RegisterCompany.html')

@app.route('/login_company')
def login_company():
    return render_template('LoginCompany.html')

@app.route('/login_student')
def login_student():
    return render_template('LoginStudent.html')

@app.route('/student_HomePage')
def student_HomePage():
    return render_template('StudentHomePage.html')
#Navigate to registration student
@app.route('/register_student')
def register_student():
    return render_template("RegisterStudent.html")

#Register a student
@app.route("/addstud", methods=['POST'])
def add_student():
    try:
        level = request.form['level']
        cohort = request.form['cohort']
        programme = request.form['programme']
        student_id = request.form['studentId']
        email = request.form['email']
        name = request.form['name']
        ic = request.form['ic']
        mobile = request.form['mobile']
        gender = request.form['gender']
        address = request.form['address']

        insert_sql = "INSERT INTO student (studentId, studentName, IC, mobileNumber, gender, address, email, level, programme, cohort) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor = db_conn.cursor()

        cursor.execute(insert_sql, (student_id, name, ic, mobile,
                                    gender, address, email, level, programme, cohort))
        db_conn.commit()

    except Exception as e:
        db_conn.rollback()

    finally:
        cursor.close()

    # Redirect back to the registration page with a success message
    return render_template("home.html")

@app.route("/about", methods=['POST'])
def about():
    return render_template('www.tarc.edu.my')


@app.route("/verifyLogin", methods=['POST','GET'])
def verifyLogin():
    if request.method == 'POST':
        StudentIc = request.form['StudentIc']
        Email = request.form['Email']

        # Query the database to check if the email and IC number match a record
        cursor = db_conn.cursor()
        query = "SELECT * FROM student WHERE IC = %s AND email = %s"
        cursor.execute(query, (StudentIc, Email))
        user = cursor.fetchone()
        cursor.close()

        if user:
            # User found in the database, login successful
            # Redirect to the student home page
            return render_template('StudentHomePage.html')
        else:
            # User not found, login failed
            return render_template('LoginStudent.html',msg="Access Denied: Invalid Email or Ic Number")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)