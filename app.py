from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
from PIL import Image
from Core import Apprenant, send_email
import base64
import werkzeug as wz
import bcrypt
from Mentor import mentor_page

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a secure key


def check_user(file, email, password):
    try:
        # Read the CSV file into a DataFrame
        df = pd.read_csv(file, names=['nom', 'prénom', 'email', 'password'], encoding='latin1')
        
        # Filter the DataFrame to find the user by email
        user = df[df['email'] == email]
        
        if not user.empty:
            # Get the stored hashed password
            stored_hashed_password = user.iloc[0]['password']
            
            # Verify the input password against the stored hashed password
            if bcrypt.checkpw(password.encode('utf-8'), stored_hashed_password.encode('utf-8')):
                # Set session variables if authentication is successful
                session['username'] = user.iloc[0]['nom']
                session['email'] = user.iloc[0]['email']
                session['FirstName'] = user.iloc[0]['prénom']
                return True
        
        # Return False if no match found or password verification fails
        return False

    except FileNotFoundError:
        flash("User file not found.")
        return False
    except UnicodeDecodeError:
        flash("Encoding error in the user file.")
        return False


# Homepage
@app.route('/')
def index():
    return render_template('Log_in.html')


# Login route
@app.route('/login', methods=['POST'])
def login():
    password ='chafik'
    print(bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))
    email = request.form['Email']
    password = request.form['password']
    if check_user('Mentor1.csv', email, password):
        session['user_type'] = 'mentor'
        return redirect(url_for('mentor'))
    elif check_user('Student1.csv', email, password):
        session['user_type'] = 'student'
        return redirect(url_for('student'))
    else:
        flash("Invalid credentials")
        render_template('Log_in.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        firstname = request.form['firstname']
        email = request.form['email']
        password = request.form['password']

        # cheking if the user already exists in the database
        if  email in pd.read_csv('Student1.csv', sep=',').to_dict(orient='records'):
            flash("User already exists.")
            return redirect(url_for('sign_up'))
        else:

            # 2. Hash the password for security 
            # (e.g., using werkzeug.security's generate_password_hash method)
            password=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            #save user in student database
            with open('Student1.csv', 'a') as file:
                file.write(f"{username},{firstname},{email},{password}\n")

            #we'll just display a decorated message to the user
            return flash("User created successfully. Please login to continue.")
            #THIS IS A BUTTON TO REDIRECT TO THE LOGIN PAGE

    return render_template('sign_up.html')






# Mentor page
@app.route('/mentor')
def mentor():
    if 'user_type' in session and session['user_type'] == 'mentor':
        username = session.get('username')
        email=session.get('email')
        table_data = mentor_page(email) # Load mentor data
        return render_template('mentor.html', username=username, table_data=table_data)
    return redirect(url_for('index'))

# Student page
@app.route('/student')
def student(parcours=""):

    if 'user_type' in session and session['user_type'] == 'student':
        username = session.get('username')
        mentors=pd.read_csv('Mentor1.csv', sep=',').to_dict(orient='records')
        mentors_Data=pd.read_csv('BD_PROF.csv').to_dict(orient='records')
        
        
        return render_template('student.html', username=username,mentors=mentors,parcours=parcours,mentors_Data=mentors_Data)
    return redirect(url_for('index'))




# IN THIS FUNCTION WE WILL USE THE STUDENT CLASS TO GENERATE THE RECOMMENDATION 
# IT TAKE THE GRADES OF THE STUDENT FROM THE STUDENT INTERFACE AS INPUT AND RETURN THE RECOMMENDATION
@app.route('/sudent/recommendation', methods=['POST','GET'])
def submit_recommendation():
    username = session.get('username')
    #subject list 
    subjects = [
        "mathématique", "physique", "mécanique", "informatique",
        "sciencedentreprise", "sciencehumaine", "adpl", "lbd", "langues"
        ]

    # List of interests
    interests = [
        "Finance", "Informatique", "Management", "Mécanique", 
        "Physique", "technologie", "Electronique", "Energie"
    ]

    # List of stage1A fields
    stages = [f"stage1A_{interest}" for interest in interests]

    # Combine all fields
    fields = [f"note_{subject}" for subject in subjects] + \
            [f"centre_d_interet_{interest}" for interest in interests] + \
            stages

    # Retrieve all grades using request.form.get
    grades = [request.form.get(field) for field in fields]

    for i in range(len(grades)):
        grades[i]=float(grades[i])

    lignes = pd.read_csv('Student1.csv', sep=',')    

    for i in range(len(lignes)):
        if lignes.loc[i][0]==username:
            elements=[lignes.loc[i]['username'], lignes.loc[i]['first_name'], lignes.loc[i]['email'], lignes.loc[i]['password']]
    elements
    A=Apprenant(elements[0],elements[1],elements[2],elements[3])
    
    # Generate recommendation using Core.py function rc 
    parcours=A.rc(grades)

    return student(parcours)



# Route to submit a mentoring request


@app.route('/student/mentoring', methods=['POST','GET'])
def submit_request():
    sujet = request.form.get("sujet")
    date = request.form.get("date")
    creneau = request.form.get("creneau")
    mentor = request.form.get('mentor')
    FirstName=session.get('FirstName')
    username = session.get('username')
    mail=session.get('email')
    # Log the mentoring request in a file or database (for demonstration, a simple file log is used)
    new_request = {
        'First_name':FirstName,
        'username':username,
        'Email':mail,
        'Subject':sujet,
        'date':date,
        'time':creneau,
        'mentor':mentor
    }

    # Load existing requests from CSV (if exists)
    try:
        df = pd.read_csv("mentoring_request1.csv", sep=',')
    except FileNotFoundError:
        df = pd.DataFrame(columns=['First_name', 'username', 'Email', 'Subject', 'date', 'time', 'mentor'])

    # Append the new request to the DataFrame
    df = df._append(new_request, ignore_index=True)

    # Save the updated DataFrame to CSV
    df.to_csv("mentoring_request1.csv", index=False, sep=',')
    return student(parcours="")




@app.route('/student_account')

def student_account():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect(url_for('index'))

    username = session.get('username')

    try:
        df = pd.read_csv("mentoring_request1.csv", sep=',')
        requests = df[df['username'] == username].to_dict('records')
        return render_template('student_account.html', requests=requests)
    except FileNotFoundError:
        flash("Request file not found.")
        return render_template('student.html') 


# Route for mentor actions on requests (accept/deny)
@app.route('/handle_request', methods=['POST'])
def handle_request():
    # Check user authorization
    if 'user_type' not in session or session['user_type'] != 'mentor':
        flash("Unauthorized access.")
        return redirect(url_for('index'))

    # Get form data
    action = request.form.get('action')
    email = request.form.get('email')
    filename = "mentoring_request1.csv"
    print(action, email)

    # Load the CSV file
    df = pd.read_csv(filename)

        # Locate the request by email
    request_row = df[df['Email'] == email]

        # Extract requester information
    requester_name = request_row.iloc[0]['First_name']
    meeting_subject = request_row.iloc[0]['Subject']
    meeting_date = request_row.iloc[0]['date']
    meeting_time = request_row.iloc[0]['time']

        # Remove the request from the CSV
    df = df[df['Email'] != email]
    df.to_csv(filename, index=False)

        # Compose email
    if action == 'accept':
            subject = "Mentoring Request Accepted!"
            body = f"""
            Dear {requester_name},

            Your mentoring request for {meeting_subject} scheduled on {meeting_date} at {meeting_time} has been Accepted by {session.get('username')}.
            Please contact them to schedule a meeting.

            Sincerely,
            The Pro-Path Team
            """
            flash(f"Request for {email} has been accepted.")
    elif action == 'deny':
            subject = "Mentoring Request Denied"
            body = f"""
            Dear {requester_name},
            We regret to inform you that your mentoring request for "{meeting_subject}" scheduled on {meeting_date}at{meeting_time}has been  Denied at this time.  

            We encourage you to explore other mentoring opportunities and remain committed to supporting your growth in the future.  

            Sincerely,  
            The Pro-Path Team  
            """
            flash(f"Request for {email} has been denied.")
    else:
            flash("Invalid action.")
            return redirect(url_for('mentor'))

        # Send email
    send_email(email, subject, body)
    return redirect(url_for('mentor'))



# Logout route

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
