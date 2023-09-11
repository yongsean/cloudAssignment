
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
    return render_template('SearchCompany.html', number=1)

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
        
@app.route("/displayJobFind", methods=['POST','GET'])
def displayAllJobs():
    # Get all the jobs from the database
    select_sql = "SELECT * FROM job"
    cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql)
        jobs = cursor.fetchall()

        if not jobs:
            return "No jobs found"

        # Create a list of job objects
        job_objects = []
        for job in jobs:
            job_id = job[0]
            publish_date = job[1]
            job_type = job[2]
            job_position = job[3]
            job_desc = job[4]
            job_requirement = job[5]
            job_location = job[6]
            salary = job[7]
            num_of_opening = job[8]
            company_id = job[9]
            industry_id = job[10]

            # Get the company name from the database
            select_company_sql = "SELECT name FROM company WHERE companyId = %s"
            cursor.execute(select_company_sql, (company_id,))
            company_name = cursor.fetchone()[0]

            # Get the industry name from the database
            select_industry_sql = "SELECT name FROM industry WHERE industryId = %s"
            cursor.execute(select_industry_sql, (industry_id,))
            industry_name = cursor.fetchone()[0]

            job_object = {
                "job_id": job_id,
                "publish_date": publish_date,
                "job_type": job_type,
                "job_position": job_position,
                "job_desc": job_desc,
                "job_requirement": job_requirement,
                "job_location": job_location,
                "salary": salary,
                "num_of_opening": num_of_opening,
                "company_name": company_name,
                "industry_name": industry_name
            }

            job_objects.append(job_object)

    except Exception as e:
        return str(e)

    finally:
        cursor.close()
        db_conn.close()
        return render_template('SearchCompany.html', jobs=job_objects)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)