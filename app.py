from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from myValidation import is_valid_email, presenceCheck
import random
import re

app = Flask(__name__)
app.secret_key = "supersecretkey123"

DB_PATH = "exampleRun.db"

# ============================== Database Class ============================ 
class RunTogetherDB:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    # Create the users table
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                UserID TEXT NOT NULL,
                Email TEXT NOT NULL,
                Password TEXT NOT NULL,
                Username TEXT NOT NULL,
                Proficiency TEXT NOT NULL,
                PreferredPaceLevel TEXT NOT NULL,
                PreferredDistance TEXT NOT NULL,
                Location TEXT NOT NULL,
                Shortlist TEXT
            )
        ''')

        conn.commit()
        conn.close()

    # Get all users, this is important as i need every record to search for things such as logins
    def get_users(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        conn.close()
        return users
    


    # Add a user
    def add_user(self, UserID, Email, Password, Username, Proficiency, PreferredPaceLevel, PreferredDistance, Location):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (
                UserID, Email, Password, Username, Proficiency, 
                PreferredPaceLevel, PreferredDistance, Location
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (UserID, Email, Password, Username, Proficiency, PreferredPaceLevel, PreferredDistance, Location))
        conn.commit()
        conn.close()

    # Update a user by UserID
    def update_user(self, UserID, Email=None, Password=None, Username=None, Proficiency=None, PreferredPaceLevel=None, PreferredDistance=None, Location=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Build dynamic SQL update
        fields = []
        values = []
        if Email: # checks if a value is provided for this field, if nothing is provided i.e no changes are made it skips this if statement
            fields.append("Email = ?"); values.append(Email)  #appends whatever data was given into the 
        if Password: 
            fields.append("Password = ?"); values.append(Password)
        if Username: 
            fields.append("Username = ?"); values.append(Username)
        if Proficiency: 
            fields.append("Proficiency = ?"); values.append(Proficiency)
        if PreferredPaceLevel is not None: 
            fields.append("PreferredPaceLevel = ?"); values.append(PreferredPaceLevel)
        if PreferredDistance: 
            fields.append("PreferredDistance = ?"); values.append(PreferredDistance)
        if Location: 
            fields.append("Location = ?"); values.append(Location)

        if fields:  # checks if the fields list is empty (no changes made)
            sql = f"UPDATE users SET {', '.join(fields)} WHERE UserID = ?" # the fields list becomes a part of the SQL query by joining the list together as a string
            values.append(UserID) # adds userID at the end since this is for the WHERE statement above
            cursor.execute(sql, values) # the SQL Query paired with our values are then executed
            conn.commit()
        conn.close()

    # Delete a user by UserID
    def delete_user(self, UserID):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE UserID = ?", (UserID,))
        conn.commit()
        conn.close()

    # Get one user by UserID
    def get_user(self, UserID):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE UserID = ?", (UserID,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def update_shortlist(self, UserID, shortlist_ids): # takes the current users ID, and the ID to add to the short list
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET Shortlist = ? WHERE UserID = ?", (shortlist_ids, UserID))
        conn.commit()
        conn.close()

    def get_shortlist(self, UserID): # uses the current users ID to search the database and SELECT and return their shortlist
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT Shortlist FROM users WHERE UserID = ?", (UserID,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else ""
        


#############################################CLASS ENDS HERE #######################################################

def is_valid_pace(pace_str):
    #Returns True if pace is in MM:SS format, seconds < 60
    match = re.fullmatch(r'(\d{1,2}):([0-5]\d)', pace_str) #uses regex to ensure data is in the right format
    return bool(match)



# ================= Create DB object ================= #
db = RunTogetherDB()
db.init_db()

# ================= Flask Routes ================= #

@app.route('/')
def index():
    users = db.get_users()
    return render_template('index.html', users=users)

def generate_unique_userid():
    existing_ids = [user[0] for user in db.get_users()]  # extracts all userIDs and appends to a list
    while True:
        userid = f"{random.randint(1000, 9999)}"  # generate 4-digit ID as string
        if userid not in existing_ids: # checks if it already exists in our list of userIDs 
            return userid


@app.route('/add_user', methods=['POST'])
def add_user_route():
    data = request.form #gives you access to form data submitted via POST, access to everything submitted via HTML

    UserID = generate_unique_userid()
    pace = data['PreferredPaceLevel']
    Password = data['Password']
    PasswordConfirm = data['ConfirmPassword']
    Email = data['Email']

    if Password != PasswordConfirm:
        return "Passwords do not match."

    if not is_valid_pace(pace):
        return "Invalid pace! Please use MM:SS format."

    existing_users = db.get_users()
    if any(user[1] == Email for user in existing_users):
        return "An account with this email already exists."

    db.add_user(
        UserID=UserID,
        Email=Email,
        Password=Password,
        Username=data['Username'],
        Proficiency=data['Proficiency'],
        PreferredPaceLevel=pace,  # store as TEXT
        PreferredDistance=data['PreferredDistance'],
        Location=data['Location']
    )
    return redirect(url_for('index'))



@app.route('/login_user', methods=['POST'])
def login_user_route():
    email = request.form['Email'] #request the value in the Email field 
    password = request.form['Password']

    # Check all users in DB
    users = db.get_users()
    for user in users:
        if user[1] == email and user[2] == password:  # Email = user[1], Password = user[2]
            session['user_id'] = user[0] # need this for the shortlist
            session['user_name_to_pass'] = user[3]  # save name to session, to use in the dashboard page
            session['proficiency_to_pass'] = user[4] 
            session['pref_pace_to_pass'] = user[5]  
            session['pref_dist_to_pass'] = user[6]  
            session['location_to_pass'] = user[7]  # these values are passed for my autofill button on the dashboard
            # Login successful
            return redirect(url_for('dashboard'))  
    # Login failed
    return "Login failed! Email or password incorrect."

@app.route('/main')
def dashboard():
    name = session.get('user_name_to_pass')
    proficiency = session.get('proficiency_to_pass')
    pref_pace = session.get('pref_pace_to_pass')
    pref_dist = session.get('pref_dist_to_pass')
    location = session.get('location_to_pass')
    user_id = session.get('user_id')  # ✅ Add this line

    return render_template(
        'dashboard.html',
        name=name,
        proficiency=proficiency,
        pref_pace=pref_pace,
        pref_dist=pref_dist,
        location=location,
        user_id=user_id  # ✅ Pass it to the template
    )



@app.route('/signup')
def signup():
    return render_template('update_user.html')

@app.route('/update_user/<UserID>', methods=['GET', 'POST'])
def update_user_route(UserID):
    if request.method == 'POST':
        data = request.form
        db.update_user(
            UserID,
            Email=data.get('Email'),
            Password=data.get('Password'),
            Username=data.get('Username'),
            Proficiency=data.get('Proficiency'),
            PreferredPaceLevel=float(data.get('PreferredPaceLevel')) if data.get('PreferredPaceLevel') else None,
            PreferredDistance=data.get('PreferredDistance'),
            Location=data.get('Location')
        )
        return redirect(url_for('index'))

    user = db.get_user(UserID)
    return render_template('update_user.html', user=user)

@app.route('/delete_user/<UserID>')
def delete_user_route(UserID):
    db.delete_user(UserID)
    return redirect(url_for('index'))

def pace_to_seconds(pace_str):
    parts = pace_str.split(':')     # split into minutes and seconds
    minutes = int(parts[0])         # convert minutes to integer
    seconds = int(parts[1])         # convert seconds to integer
    total_seconds = minutes * 60 + seconds  # now converted into seconds
    return total_seconds



# ================= search functions ================= #
@app.route('/search_runners', methods=['POST']) # flask responds to the POST method
def search_runners():
    proficiency = request.form['Proficiency']
    pace = request.form['PreferredPaceLevel']
    location = request.form['Location']
    distance = request.form['PreferredDistance']

    # Convert user's pace to seconds
    user_pace = pace_to_seconds(pace)
    lower_pace = user_pace - 30
    upper_pace = user_pace + 30

    conn = sqlite3.connect('exampleRun.db')
    cursor = conn.cursor()

    # Fetch only the exact matches for proficiency, location, and distance
    cursor.execute("""
        SELECT * FROM users
        WHERE Proficiency = ?
          AND Location = ?
          AND PreferredDistance = ?
    """, (proficiency, location, distance))

    all_users = cursor.fetchall()  # here wwe create a list consisting of the users who match the profeciency, location and Preferred distance
    conn.close()

    # Now filter by pace in Python
    results = [] 
    for user in all_users: # uses the list we created, filters thorugh it and checks pace
        db_pace_str = user[5]  # PreferredPaceLevel is at index 5
        db_pace_seconds = pace_to_seconds(db_pace_str)
        if lower_pace <= db_pace_seconds <= upper_pace:
            results.append(user) # if the pace is within range then we add this user to our results list

    print("Filtered results:", results)
    return render_template('search_results.html', users=results)

# short list
@app.route('/add_to_shortlist', methods=['POST'])
def add_to_shortlist():
    user_id = session.get('user_id') # current user
    id_to_add = request.form['user_id'] # id to add

    print(f"Current user ID: {user_id}")
    print(f"ID to add to shortlist: {id_to_add}")

    shortlist_str = db.get_shortlist(user_id) # fetch the current users short list

    # Convert the shortlist string to a list of IDs, or start with an empty list
    ids = []
    if shortlist_str:
        ids = shortlist_str.split(',')

    # Add the new ID only if it's not already in the shortlist
    if id_to_add not in ids:
        ids.append(id_to_add)
        updated_str = ','.join(ids)  # Convert the list back to a comma-separated string
        db.update_shortlist(user_id, updated_str)  # Save the updated shortlist to the database

    return '', 204  # No Content



# ================ short list view page ===============#

@app.route('/shortlist')
def shortlist():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('index'))  # fallback if not logged in

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Step 1: Get shortlist string for current user
    cursor.execute("SELECT Shortlist FROM users WHERE UserID = ?", (user_id,))
    result = cursor.fetchone()

    if not result or not result[0]:
        conn.close()
        return render_template('shortlist.html', runners=[])

    # Step 2: Split shortlist string into list of IDs
    shortlist_ids = result[0].split(',')

    # Step 3: Fetch each runner by ID
    runners = []
    for shortlist_id in shortlist_ids:
        cursor.execute("SELECT * FROM users WHERE UserID = ?", (shortlist_id,))
        runner = cursor.fetchone()
        if runner:
            runners.append(runner)

    conn.close()
    return render_template('shortlist.html', runners=runners)





# ================= Run Flask ================= #
if __name__ == '__main__':
    db.add_user("U001","test@example.com","password123","TestUser","Beginner",6.0,"5K","Manchester") if not db.get_users() else None
    
    app.run(debug=True)
   

