
from flask import redirect
import mimetypes
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from botocore.exceptions import ClientError
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)
app.secret_key = 'cc'

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

@app.route("/addCompanyReg", methods=['POST'])
def addCompanyRegistration():
    try:
        # Create a cursor
        cursor = db_conn.cursor()
        
        # Execute the SELECT COUNT(*) query to get the total row count
        select_sql = "SELECT COUNT(*) as total FROM company"      
        cursor.execute(select_sql)
        result = cursor.fetchone()
        
        cursor.close()

        company_id = int(result[0]) + 1
        company_name = request.form['company_name']
        company_image_file = request.files['company_image_file']
        about_company = request.form['about_company']
        company_phone = request.form['company_phone']
        company_address = request.form['company_address']
        company_email = request.form['company_email']
        password = request.form['password']

        insert_sql = "INSERT INTO company VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        cursor = db_conn.cursor()

        if company_image_file.filename == "":
            return "Please select a file"
        
        try:
                cursor.execute(insert_sql, (company_id, password, company_name, about_company, company_address, company_email, company_phone, "pending",))
                db_conn.commit()
                
                # Uplaod image file in S3 #
                comp_image_file_name_in_s3 = "comp-id-" + str(company_id) + "_image_file"
                s3 = boto3.resource('s3')

                try:
                    print("Data inserted in MySQL RDS... uploading image to S3...")
                    s3.Bucket(custombucket).put_object(Key=comp_image_file_name_in_s3, Body=company_image_file)
                    bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
                    s3_location = (bucket_location['LocationConstraint'])

                    if s3_location is None:
                        s3_location = ''
                    else:
                        s3_location = '-' + s3_location

                    object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                        s3_location,
                        custombucket,
                        comp_image_file_name_in_s3)

                except Exception as e:
                    return str(e)
        
        finally:
            cursor.close()
            print("Company registration request submitted...")
            return render_template('home.html')
    
    except Exception as e:
        print(str(e))
        print("failed get count...")
        return render_template('home.html')

@app.route("/verifyLogin", methods=['POST', 'GET'])
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
            session['loggedInStudent'] = user[0]
            return render_template('studentHome.html', studentId=user[0], studentName=user[1], IC=user[2], mobileNumber=user[3], gender=user[4], address=user[5], email=user[6], level=user[7], programme=user[8], supervisor=user[9], cohort=user[10])
        else:
            # User not found, login failed
            return render_template('LoginStudent.html', msg="Access Denied: Invalid Email or Ic Number")

@app.route('/student_home', methods=['GET', 'POST'])
def student_home():
    id = session['loggedInStudent']

    select_sql = "SELECT * FROM student WHERE studentId = %s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql, (id))
        student = cursor.fetchone()

        if not student:
            return "No such student exist."

    except Exception as e:
        return str(e)

    return render_template('studentHome.html', studentId=student[0],
                           studentName=student[1],
                           IC=student[2],
                           mobileNumber=student[3],
                           gender=student[4],
                           address=student[5],
                           email=student[6],
                           level=student[7],
                           programme=student[8],
                           supervisor=student[9],
                           cohort=student[10])

# Navigation to Edit Student Page
@app.route('/edit_student', methods=['GET', 'POST'])
def edit_student():
    id = session['loggedInStudent']

    select_sql = "SELECT * FROM student WHERE studentId = %s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql, (id))
        student = cursor.fetchone()

        if not student:
            return "No such student exist."

    except Exception as e:
        return str(e)

    pendingRequestCount = check_pending_requests(id)

    return render_template('EditStudentProfile.html', studentId=student[0],
                           studentName=student[1],
                           IC=student[2],
                           mobileNumber=student[3],
                           gender=student[4],
                           address=student[5],
                           email=student[6],
                           level=student[7],
                           programme=student[8],
                           supervisor=student[9],
                           cohort=student[10],
                           pendingRequestCount=pendingRequestCount)

# CHECK REQUEST EDIT PENDING


def check_pending_requests(id):
    pending_request_sql = "SELECT COUNT(*) FROM request WHERE studentId = %s AND status = %s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(pending_request_sql, (id, 'pending'))
        foundRecords = cursor.fetchall()

        if not foundRecords:
            return 0

        return foundRecords[0][0]

    except Exception as e:
        return str(e)

# Update student profile (Function)


@app.route('/update_student', methods=['GET', 'POST'])
def update_student():
    id = session['loggedInStudent']

    select_sql = "SELECT * FROM student WHERE studentId = %s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql, (id))
        student = cursor.fetchone()

        if not student:
            return "No such student exist."

    except Exception as e:
        return str(e)

    # Get the newly updated input fields
    newStudentName = request.form['studentName']
    newGender = request.form['gender']
    newMobileNumber = request.form['mobileNumber']
    newAddress = request.form['address']

    # Compare with the old fields
    # Student name
    if student[1] != newStudentName:
        # Insert into request table
        insert_sql = "INSERT INTO request (attribute, `change`, status, reason, studentId) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(insert_sql, ('studentName', newStudentName,
                                    'pending', None, session['loggedInStudent']))
        db_conn.commit()

    # Gender
    if student[4] != newGender:
        # Insert into request table
        insert_sql = "INSERT INTO request (attribute, `change`, status, reason, studentId) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(insert_sql, ('gender', newGender, 'pending',
                                    None, session['loggedInStudent']))
        db_conn.commit()

    # Mobile number
    if student[3] != newMobileNumber:
        # Insert into request table
        insert_sql = "INSERT INTO request (attribute, `change`, status, reason, studentId) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(insert_sql, ('mobileNumber', newMobileNumber,
                                    'pending', None, session['loggedInStudent']))
        db_conn.commit()

    # Address
    if student[5] != newAddress:
        # Insert into request table
        insert_sql = "INSERT INTO request (attribute, `change`, status, reason, studentId) VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(insert_sql, ('address', newAddress,
                                    'pending', None, session['loggedInStudent']))
        db_conn.commit()

    return redirect('/edit_student')

# Navigate to Upload Resume Page


@app.route('/upload_resume', methods=['GET', 'POST'])
def upload_resume():
    id = session['loggedInStudent']

    select_sql = "SELECT * FROM student WHERE studentId = %s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql, (id))
        student = cursor.fetchone()

        if not student:
            return "No such student exist."

    except Exception as e:
        return str(e)

    return render_template('UploadResume.html', studentId=student[0],
                           studentName=student[1],
                           IC=student[2],
                           mobileNumber=student[3],
                           gender=student[4],
                           address=student[5],
                           email=student[6],
                           level=student[7],
                           programme=student[8],
                           supervisor=student[9],
                           cohort=student[10],)

# Upload Resume into S3


@app.route('/uploadResume', methods=['GET', 'POST'])
def uploadResume():
    id = session['loggedInStudent']

    select_sql = "SELECT * FROM student WHERE studentId = %s"
    cursor = db_conn.cursor()
    stud_resume_file_name_in_s3 = id + "_resume"
    student_resume_file = request.files['resume']

    s3 = boto3.resource('s3')

    try:
        cursor.execute(select_sql, (id))
        student = cursor.fetchone()
        db_conn.commit()

        print("Data inserted in MySQL RDS... uploading resume to S3...")

        # Set the content type to 'application/pdf' when uploading to S3
        s3.Object(custombucket, stud_resume_file_name_in_s3).put(
            Body=student_resume_file,
            ContentType='application/pdf'
        )

        bucket_location = boto3.client(
            's3').get_bucket_location(Bucket=custombucket)
        s3_location = (bucket_location['LocationConstraint'])

        if s3_location is None:
            s3_location = ''
        else:
            s3_location = '-' + s3_location

    except Exception as e:
        return str(e)

    print("Resume uploaded complete.")
    return render_template('UploadResumeOutput.html', studentName=student[1], id=session['loggedInStudent'])


# Download resume from S3 (based on Student Id)
@app.route('/viewResume', methods=['GET', 'POST'])
def view_resume():
    # Retrieve student's ID
    student_id = session.get('loggedInStudent')
    if not student_id:
        return "Student not logged in."

    # Construct the S3 object key
    object_key = f"{student_id}_resume"

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3')

    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': custombucket,
                'Key': object_key,
                'ResponseContentDisposition': 'inline',
            },
            ExpiresIn=3600  # Set the expiration time (in seconds) as needed
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            # If the resume does not exist, return a page with a message
            return render_template('no_resume_found.html')
        else:
            return str(e)

    # Redirect the user to the URL of the PDF file
    return redirect(response)


# Navigate to Student View Report
@app.route('/view_progress_report', methods=['GET', 'POST'])
def view_progress_report():
    return render_template('StudentViewReport.html')

# Navigate to Student Registration

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
                    qualification_level=job[4]
                    job_requirement = job[6]
                    job_location = job[7]
                    salary = job[8]
                    company_id=job[10]
                    company_name = job[12]  # Extracted from the JOINed column


                     # Generate the S3 image URL using custombucket and customregion
                    company_image_file_name_in_s3 = "comp-id-"+str(company_id)+"_image_file"
                    s3 = boto3.client('s3', region_name=customregion)
                    bucket_name = custombucket

                    response = s3.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': bucket_name, 'Key': company_image_file_name_in_s3},
                        ExpiresIn=1000  # Adjust the expiration time as needed
                    )
                    job_object = {
                        "job_id": job_id,
                        "publish_date": publish_date,
                        "job_type": job_type,
                        "job_position": job_position,
                        "qualification_level": qualification_level,
                        "job_requirement": job_requirement,
                        "job_location": job_location,
                        "salary": salary,
                        "company_name": company_name,
                        "company_id": company_id,
                        "image_url": response
                    }

                    job_objects.append(job_object)

        return render_template('SearchCompany.html', jobs=job_objects)

    except Exception as e:
        # Log the exception for debugging
        print(f"Error: {str(e)}")
        return "An error occurred while fetching job data."


@app.route("/displayJobDetails", methods=['POST', 'GET'])
def display_job_details():
    if request.method == 'POST':
        # Get the selected job_id from the form
        selected_job_id = request.form.get('transfer-id')


        select_sql = """
        SELECT j.*, c.name AS company_name, i.name AS industry_name, c.email AS company_email, c.phone AS company_phone
        FROM job j
        LEFT JOIN company c ON j.company = c.companyId
        LEFT JOIN industry i on j.industry = i.industryId
        WHERE jobId =%s
        """
        cursor = db_conn.cursor()
        try:
            cursor.execute(select_sql, (selected_job_id,))
            job = cursor.fetchone()

            if not job:
                return "No such job exists."
        except Exception as e:
            return str(e)

        # Initialize job_objects as an empty list
        job_objects = []

        # Append job details to job_objects
        job_id = job[0]
        publish_date = job[1]
        job_type = job[2]
        job_position = job[3]
        qualification_level = job[4]
        job_description=job[5]
        job_requirement = job[6]
        job_location = job[7]
        salary = job[8]
        num_of_operate = job[9]
        company_id = job[10]
        company_name = job[12]  # Extracted from the JOINed column
        industry_name = job[13]
        company_email =job[14]
        company_phone =job[15]

        # Generate the S3 image URL using custombucket and customregion
        company_image_file_name_in_s3 = "comp-id-" + str(company_id) + "_image_file"
        s3 = boto3.client('s3', region_name=customregion)
        bucket_name = custombucket

        response = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': company_image_file_name_in_s3},
            ExpiresIn=1000  # Adjust the expiration time as needed
        )

        job_object = {
            "job_id": job_id,
            "publish_date": publish_date,
            "job_type": job_type,
            "job_position": job_position,
            "qualification_level": qualification_level,
            "job_description":job_description,
            "job_requirement": job_requirement,
            "job_location": job_location,
            "salary": salary,
            "company_name": company_name,
            "company_id": company_id,
            "num_of_operate": num_of_operate,
            "industry_name": industry_name,
            "company_email": company_email,
            "company_phone": company_phone,
            "image_url": response
        }

        job_objects.append(job_object)
        return render_template('JobDetail.html', jobs=job_objects)

    return render_template('SearchCompany.html', jobs=job_objects)

@app.template_filter('replace_and_keep_hyphen')
def replace_and_keep_hyphen(s):
    return s.replace('-', '<br>-')


@app.route('/downloadStudF04', methods=['GET'])
def download_StudF04():
    # Construct the S3 object key
    object_key = f"forms/FOCS_StudF04.docx"

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3')

    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': custombucket,
                'Key': object_key,
                'ResponseContentDisposition': 'inline',
            },
            ExpiresIn=3600  # Set the expiration time (in seconds) as needed
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            # If the resume does not exist, return a page with a message
            return render_template('no_resume_found.html')
        else:
            return str(e)

    # Redirect the user to the URL of the PDF file
    return redirect(response)


# DOWNLOAD FOCS_StudF05.docx
@app.route('/downloadStudF05', methods=['GET'])
def download_StudF05():
    # Construct the S3 object key
    object_key = f"forms/FOCS_StudF05.docx"

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3')

    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': custombucket,
                'Key': object_key,
                'ResponseContentDisposition': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            },
            ExpiresIn=3600  # Set the expiration time (in seconds) as needed
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            # If the resume does not exist, return a page with a message
            return render_template('no_resume_found.html')
        else:
            return str(e)

    # Redirect the user to the URL of the PDF file
    return redirect(response)
            

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)