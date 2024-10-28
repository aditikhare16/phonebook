from flask import Flask, render_template, request, redirect, url_for, flash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

# MongoDB configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/phonebook_db"
mongo = PyMongo(app)
contacts = mongo.db.contacts

# Config for file uploads
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home route - view all contacts
@app.route('/')
def index():
    all_contacts = contacts.find().sort("name", 1)
    return render_template('index.html', contacts=all_contacts)

# Add contact
@app.route('/add', methods=['POST'])
def add_contact():
    name = request.form.get('name')
    number = request.form.get('number')
    email = request.form.get('email')
    is_favorite = 'favorite' in request.form

    # Handle file upload for profile photo
    profile_photo = request.files.get('profile_photo')
    profile_photo_path = ''

    if profile_photo and allowed_file(profile_photo.filename):
        filename = secure_filename(profile_photo.filename)
        profile_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        profile_photo.save(profile_photo_path)  # Save the uploaded file

    # Insert contact into MongoDB
    if name and number:
        contacts.insert_one({
            'name': name,
            'number': number,
            'email': email,
            'profile_photo': profile_photo_path,  # Save the file path in DB
            'is_favorite': is_favorite
        })
        flash('Contact Added Successfully!')
    else:
        flash('Name and Number are required!')

    return redirect(url_for('index'))

# Delete contact
@app.route('/delete/<id>')
def delete_contact(id):
    contacts.delete_one({'_id': ObjectId(id)})
    flash('Contact Deleted Successfully!')
    return redirect(url_for('index'))

# Update contact
@app.route('/update/<id>', methods=['GET', 'POST'])
def update_contact(id):
    contact = contacts.find_one({"_id": ObjectId(id)})

    if request.method == 'POST':
        updated_contact = {
            "name": request.form['name'],
            "number": request.form['number'],
            "email": request.form['email'],
            "is_favorite": 'favorite' in request.form  # Handle the favorite checkbox
        }

        # Handle updating the profile photo
        profile_photo = request.files.get('profile_photo')
        if profile_photo and allowed_file(profile_photo.filename):
            filename = secure_filename(profile_photo.filename)
            profile_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_photo.save(profile_photo_path)
            updated_contact["profile_photo"] = profile_photo_path

        contacts.update_one({"_id": ObjectId(id)}, {"$set": updated_contact})
        flash('Contact Updated Successfully!')
        return redirect(url_for('index'))

    return render_template('update.html', contact=contact)

# Search contact
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    search_results = contacts.find({"name": {"$regex": query, "$options": "i"}})
    return render_template('index.html', contacts=search_results)

# Mark as favorite
@app.route('/favorites')
def favorites():
    favorite_contacts = contacts.find({"is_favorite": True}).sort("name", 1)
    return render_template('index.html', contacts=favorite_contacts)

if __name__ == '__main__':
    app.run(debug=True)
