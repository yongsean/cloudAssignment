
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
    

# Function to create a database connection context
def get_db_connection():
    customhost = 'database-1.cdsilkd4knvu.us-east-1.rds.amazonaws.com'
    customuser = 'aws_user'
    custompass = 'Bait3273'
    customdb = 'employee'

    return connections.Connection(
        host=customhost,
        port=3306,
        user=customuser,
        password=custompass,
        db=customdb
    )

@app.route("/displayJobFind", methods=['POST', 'GET'])
def displayAllJobs():
    # Get filter values from the form
    search_company = request.form.get('search-company', '')
    search_title = request.form.get('search-title', '')
    search_state = request.form.get('search-state', 'All')
    search_allowance = request.form.get('search-allowance', '1800')

    # Construct the base SQL query with a JOIN between the job and company tables
    select_sql = """
        SELECT j.*, c.name AS company_name
        FROM job j
        LEFT JOIN company c ON j.company = c.companyId
        WHERE 1
    """

    # Add filter conditions based on form inputs
    if search_company:
        select_sql += f" AND c.name LIKE '%{search_company}%'"

    if search_title:
        select_sql += f" AND j.jobPosition LIKE '%{search_title}%'"

    if search_state != 'All':
        select_sql += f" AND j.jobLocation LIKE '%{search_state}%'"

    if search_allowance:
        select_sql += f" AND j.salary <= {search_allowance}"

    # Add the condition to check the company's status
    select_sql += " AND c.status = 'activated'"

    try:
        with get_db_connection() as db_conn:
            with db_conn.cursor() as cursor:
                cursor.execute(select_sql)
                jobs = cursor.fetchall()

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
                    company_name = job[11]  # Extracted from the JOINed column

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
                    }

                    job_objects.append(job_object)

        return render_template('SearchCompany.html', jobs=job_objects)

    except Exception as e:
        return str(e)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)