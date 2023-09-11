@app.route("/displayJobFind", methods=['POST','GET'])
def displayAllJobs():
    # Get user inputs from the form
    search_company = request.form.get("search-company")
    search_title = request.form.get("search-title")
    search_state = request.form.get("search-state")
    search_allowance = request.form.get("search-allowance")

    # Initialize parameters and SQL parts
    params = {}
    conditions = []

    # Build the filter condition based on user inputs
    if search_company:
        conditions.append("company.name LIKE %(company_name)s")
        params["company_name"] = f"%{search_company}%"
    if search_title:
        conditions.append("job.job_position LIKE %(job_position)s")
        params["job_position"] = f"%{search_title}%"
    if search_state != "All":
        conditions.append("job.job_location = %(job_location)s")
        params["job_location"] = search_state
    if search_allowance != "All":
        conditions.append("job.salary <= %(salary)s")
        params["salary"] = int(search_allowance)

    # Construct the SQL query with the filter conditions
    select_sql = """
        SELECT job.*, company.name AS company_name, industry.name AS industry_name
        FROM job
        INNER JOIN company ON job.company_id = company.companyId
        INNER JOIN industry ON job.industry_id = industry.industryId
        WHERE 1 = 1
    """

    if conditions:
        select_sql += " AND " + " AND ".join(conditions)

    cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql, params)
        jobs = cursor.fetchall()

        if not jobs:
            return "No jobs found"

        # Create a list of job objects
        job_objects = []
        for job in jobs:
            # Fetch job details
            job_id = job[0]
            publish_date = job[1]
            job_type = job[2]
            job_position = job[3]
            job_desc = job[4]
            job_requirement = job[5]
            job_location = job[6]
            salary = job[7]
            num_of_opening = job[8]
            company_name = job[11]
            industry_name = job[12]

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

        return render_template('SearchCompany.html', jobs=job_objects)

    except Exception as e:
        return str(e)

    finally:
        cursor.close()
        db_conn.close()
