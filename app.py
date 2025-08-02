from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import os
from datetime import datetime
import base64
from fpdf import FPDF
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime
import qrcode
import io
import pdfkit
from flask import make_response
from weasyprint import HTML, CSS
from flask import make_response

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this in production

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# Initialize CSV files if they don't exist
def init_csv_files():
    files = {
        'members.csv': [
            'member_id', 'name', 'address', 'whatsapp', 
            'course', 'joining_date', 'aadhar', 'pin', 
            'wifi', 'status'
        ],
        'admins.csv': ['admin_id', 'username', 'password_hash'],
        'admin_notes.csv': ['member_id', 'note'],
        'notices.csv': ['notice_id', 'notice_text', 'notice_date', 'is_public']
    }
    
    for filename, headers in files.items():
        if not os.path.exists(f'data/{filename}'):
            with open(f'data/{filename}', 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                
                # Create default admin if new file
                # if filename == 'admins.csv':
                #     writer.writerow({
                #         'admin_id': 'ADMIN001',
                #         'username': 'admin',
                #         'password_hash': generate_password_hash('admin123')  # Change this!
                #     })


# Helper functions
def read_csv(filename):
    with open(f'data/{filename}', mode='r') as f:
        return list(csv.DictReader(f))

def write_csv(filename, data, mode='a'):
    with open(f'data/{filename}', mode=mode, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys() if data else [])
        if mode == 'w':
            writer.writeheader()
        writer.writerows(data)

def update_csv_row(filename, key, value, update_data):
    rows = read_csv(filename)
    updated = False
    
    for row in rows:
        if row[key] == value:
            row.update(update_data)
            updated = True
            break
    
    if updated:
        write_csv(filename, rows, mode='w')
    return updated

def generate_member_id():
    members = read_csv('members.csv')
    year = datetime.now().year
    if not members:
        return f'NC{year}-001'
    
    last_id = members[-1]['member_id']
    num = int(last_id.split('-')[1]) + 1
    return f'NC{year}-{num:03d}'

# Routes
@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        members = read_csv('members.csv')
        year = datetime.now().year
        
        # Generate new member ID safely
        if not members:
            new_id = f'NC{year}-001'
        else:
            # Find the highest existing ID number
            max_num = 0
            for member in members:
                try:
                    # Handle both "NC2024-001" and potentially malformed IDs
                    if '-' in member['member_id']:
                        current_num = int(member['member_id'].split('-')[1])
                        max_num = max(max_num, current_num)
                except (ValueError, IndexError):
                    continue
            
            new_id = f'NC{year}-{max_num + 1:03d}'

        # Rest of your form processing...
        new_member = {
            'member_id': new_id,
            'name': request.form.get('name'),
            'address': request.form.get('address'),
            'whatsapp': request.form.get('whatsapp'),
            'course': request.form.get('course'),
            'joining_date': datetime.now().strftime('%Y-%m-%d'),
            'aadhar': request.form.get('aadhar'),
            'pin': request.form.get('pin'),
            'wifi': request.form.get('wifi', 'No'),
            'status': 'Active'
        }

        write_csv('members.csv', [new_member])
        flash(f'Success! New member ID: {new_id}', 'success')
        return redirect(url_for('admin'))

    return render_template('admin_register.html')
@app.route('/admin/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        new_username = request.form.get('new_username')
        
        admins = read_csv('admins.csv')
        admin = next((a for a in admins if a['admin_id'] == session['user_id']), None)
        
        if not admin or not check_password_hash(admin['password_hash'], current_password):
            flash("Current password is incorrect", 'error')
            return redirect(url_for('change_password'))
        
        if new_username and new_username != admin['username']:
            if any(a['username'] == new_username for a in admins if a['admin_id'] != session['user_id']):
                flash("Username already taken", 'error')
                return redirect(url_for('change_password'))
            admin['username'] = new_username
        
        if new_password:
            if new_password != confirm_password:
                flash("New passwords don't match", 'error')
                return redirect(url_for('change_password'))
            admin['password_hash'] = generate_password_hash(new_password)
        
        write_csv('admins.csv', admins, mode='w')
        flash("Credentials updated successfully!", 'success')
        return redirect(url_for('admin'))
    
    return render_template('change_password.html')
@app.route('/admin/register_admin', methods=['GET', 'POST'])
def register_admin():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash("Passwords don't match", 'error')
            return redirect(url_for('register_admin'))

        # Check if username already exists
        admins = read_csv('admins.csv')
        if any(a['username'] == username for a in admins):
            flash("Username already exists", 'error')
            return redirect(url_for('register_admin'))

        # Generate admin ID
        admin_id = f"ADMIN{len(admins) + 1:03d}"

        # Add new admin
        new_admin = {
            'admin_id': admin_id,
            'username': username,
            'password_hash': generate_password_hash(password)
        }

        write_csv('admins.csv', [new_admin])
        flash(f'New admin {username} registered successfully!', 'success')
        return redirect(url_for('admin'))

    return render_template('register_admin.html')
@app.context_processor
def inject_now():
    return {'now': datetime.now()}
@app.route('/')
def index():
    public_notices = [n for n in read_csv('notices.csv') if n['is_public'] == 'True']
    return render_template('index.html', notices=public_notices[-3:])  # Show latest 3

@app.route('/rules')
def rules():
    return render_template('rules.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        login_type = request.form.get('login_type', 'member')  # Default to member login
        
        if login_type == 'admin':
            # Admin login logic
            admins = read_csv('admins.csv')
            admin = next((a for a in admins if a['username'] == username), None)
            
            if admin and check_password_hash(admin['password_hash'], password):
                session['user_id'] = admin['admin_id']
                session['is_admin'] = True
                return redirect(url_for('admin'))
            
            flash('Invalid admin credentials', 'error')
        
        else:
            # Member login logic
            members = read_csv('members.csv')
            member = next((m for m in members if m['member_id'] == username and m['pin'] == password), None)
            
            if member:
                session['user_id'] = member['member_id']
                session['is_admin'] = False
                return redirect(url_for('dashboard'))
            
            flash('Invalid member ID or PIN', 'error')
        
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Handle form submission
        return redirect(url_for('admin'))  # Or wherever you want to redirect after submission
    
    if 'user_id' in session and session.get('is_admin'):
        return redirect(url_for('admin_register'))
    else:
        return render_template('public_register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    member_id = session['user_id']
    members = read_csv('members.csv')
    user = next((m for m in members if m['member_id'] == member_id), None)
    
    if not user:
        session.clear()
        return redirect(url_for('login'))
    
    # Get admin note
    admin_notes = read_csv('admin_notes.csv')
    user_note = next((n['note'] for n in admin_notes if n['member_id'] == member_id), '')
    
    # Get notices
    notices = read_csv('notices.csv')
    
    return render_template('dashboard.html', 
                         user=user, 
                         note=user_note,
                         notices=notices[-5:],  # Show latest 5
                         members=members)

@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    members = read_csv('members.csv')
    notices = read_csv('notices.csv')
    
    # Count WiFi subscriptions (where wifi equals 'Yes' or 'yes')
    wifi_count = sum(1 for member in members if member.get('wifi', '').lower() == 'yes')
    
    return render_template('admin.html', 
                        members=members, 
                        notices=notices,
                        wifi_count=wifi_count)  # Pass the count to template

@app.route('/manage/<member_id>', methods=['GET', 'POST'])
def manage_user(member_id):
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    members = read_csv('members.csv')
    user = next((m for m in members if m['member_id'] == member_id), None)
    
    if not user:
        flash('Member not found', 'error')
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        note = request.form.get('admin_note')
        
        # Update admin note
        admin_notes = read_csv('admin_notes.csv')
        
        # Remove existing note if any
        admin_notes = [n for n in admin_notes if n['member_id'] != member_id]
        
        if note.strip():
            admin_notes.append({'member_id': member_id, 'note': note})
        
        write_csv('admin_notes.csv', admin_notes, mode='w')
        flash('Note updated successfully', 'success')
        return redirect(url_for('admin'))
    
    # Get current note
    admin_notes = read_csv('admin_notes.csv')
    current_note = next((n['note'] for n in admin_notes if n['member_id'] == member_id), '')
    
    return render_template('manage_user.html', user=user, current_note=current_note)

@app.route('/add_notice', methods=['POST'])
def add_notice():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    notice_text = request.form.get('notice_text')
    is_public = 'is_public' in request.form
    
    notices = read_csv('notices.csv')
    notice_id = str(uuid.uuid4())[:8]
    
    notices.append({
        'notice_id': notice_id,
        'notice_text': notice_text,
        'notice_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'is_public': str(is_public)
    })
    
    write_csv('notices.csv', notices, mode='w')
    flash('Notice added successfully', 'success')
    return redirect(url_for('admin'))

@app.route('/download_members')
def download_members():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    
    members = read_csv('members.csv')
    
    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="Nilratran Chatrawas - Member List", ln=1, align='C')
    pdf.cell(200, 10, txt=f"Generated on {datetime.now().strftime('%Y-%m-%d')}", ln=1, align='C')
    pdf.ln(10)
    
    # Table header
    pdf.cell(30, 10, "Member ID", 1)
    pdf.cell(50, 10, "Name", 1)
    pdf.cell(40, 10, "Course", 1)
    pdf.cell(30, 10, "Joining Date", 1)
    pdf.cell(40, 10, "Status", 1)
    pdf.ln()
    
    # Table rows
    for member in members:
        pdf.cell(30, 10, member['member_id'], 1)
        pdf.cell(50, 10, member['name'], 1)
        pdf.cell(40, 10, member['course'], 1)
        pdf.cell(30, 10, member['joining_date'], 1)
        pdf.cell(40, 10, member.get('status', 'Active'), 1)
        pdf.ln()
    
    pdf_output = f"data/members_{datetime.now().strftime('%Y%m%d')}.pdf"
    pdf.output(pdf_output)
    
    return send_file(pdf_output, as_attachment=True)
@app.route('/id_card')
def id_card():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    member_id = session['user_id']
    members = read_csv('members.csv')
    user = next((m for m in members if m['member_id'] == member_id), None)
    
    if not user:
        return redirect(url_for('login'))

    # Generate QR code
    qr_data = f"""
NILRATRAN CHATRAWAS
Student ID: {user['member_id']}
Name: {user['name']}
Course: {user['course']}
Contact: {user['whatsapp']}
Address: {user['address']}
Valid Until: Course Completion
"""
    qr = qrcode.QRCode(version=1, box_size=4, border=1)
    qr.add_data(qr_data.strip())
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR code to bytes
    qr_bytes = io.BytesIO()
    qr_img.save(qr_bytes, format='PNG')
    qr_bytes.seek(0)
    qr_base64 = base64.b64encode(qr_bytes.getvalue()).decode('ascii')

    return render_template('id_card.html', 
                         user=user,
                         qr_code=qr_base64,
                         issue_date=datetime.now().strftime('%Y-%m-%d'))
# @app.route('/download_card')
# def download_card():
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
    
#     member_id = session['user_id']
#     members = read_csv('members.csv')
#     user = next((m for m in members if m['member_id'] == member_id), None)
    
#     if not user:
#         return redirect(url_for('login'))

#     pdf = FPDF('P', 'mm', 'A4')
#     pdf.add_page()
#     pdf.set_margins(15, 15, 15)

#     # --- Background ---
#     pdf.set_fill_color(253, 253, 253)
#     pdf.rect(0, 0, 210, 297, 'F')

#     # --- Header Section (Saffron) ---
#     pdf.set_fill_color(255, 111, 0)
#     pdf.rect(0, 0, 210, 35, 'F')

#     # --- Logo ---
#     pdf.image('static/images/logo.png', x=10, y=5, w=20)

#     # --- Heading: Centered ---
#     pdf.set_font("Arial", 'B', 20)
#     pdf.set_text_color(255, 255, 255)
#     title = "NILRATRAN CHATRAWAS"
#     title_x = 105 - pdf.get_string_width(title) / 2
#     pdf.text(title_x, 15, title)

#     # --- Subheading & Contact ---
#     pdf.set_font("Arial", '', 9)
#     location_lines = [
#         "Student Accommodation Trust",
#         "Siliguri, Darjeeling District, West Bengal - 734001",
#         "Phone: +91-9876543210 | Email: admin@nilratrantrust.org"
#     ]
#     for i, line in enumerate(location_lines):
#         pdf.text(105 - pdf.get_string_width(line)/2, 22 + i*4, line)

#     # --- Card Box ---
#     card_width = 180
#     card_height = 100
#     card_x = (210 - card_width) / 2
#     card_y = 60
#     pdf.set_draw_color(200, 200, 200)
#     pdf.set_fill_color(255, 255, 255)
#     pdf.rect(card_x, card_y, card_width, card_height, 'FD')

#     # Vertical Divider
#     pdf.line(card_x + card_width * 0.6, card_y + 10, card_x + card_width * 0.6, card_y + card_height - 10)

#     # --- Left Column: Details ---
#     pdf.set_text_color(44, 62, 80)
#     x1 = card_x + 10
#     y1 = card_y + 15
#     pdf.set_font("Arial", 'B', 10)
#     pdf.set_xy(x1, y1)
#     pdf.cell(30, 7, "Member ID:", 0, 0)
#     pdf.set_font("Arial", '', 10)
#     pdf.cell(0, 7, user['member_id'], 0, 1)

#     pdf.line(x1, y1 + 8, card_x + card_width * 0.6 - 10, y1 + 8)

#     fields = [
#         ("Name:", user['name']),
#         ("Course:", user['course']),
#         ("Joining Date:", user['joining_date']),
#         ("WhatsApp:", user['whatsapp']),
#     ]
#     for i, (label, value) in enumerate(fields):
#         pdf.set_xy(x1, y1 + 10 + i * 10)
#         pdf.set_font("Arial", 'B', 10)
#         pdf.cell(30, 7, label, 0, 0)
#         pdf.set_font("Arial", '', 10)
#         pdf.cell(0, 7, value, 0, 1)

#     # Address multi-line
#     pdf.set_xy(x1, y1 + 50)
#     pdf.set_font("Arial", 'B', 10)
#     pdf.cell(30, 7, "Address:", 0, 0)
#     pdf.set_font("Arial", '', 8)
#     pdf.multi_cell(card_width * 0.6 - 20, 5, user['address'])

#     # --- QR Code (Improved resolution) ---
#     qr_data = f"""
# NILRATRAN CHATRAWAS
# Student ID: {user['member_id']}
# Name: {user['name']}
# Course: {user['course']}
# Contact: {user['whatsapp']}
# Address: {user['address']}
# Valid Until: Course Completion
# """
#     qr = qrcode.QRCode(version=1, box_size=4, border=1)
#     qr.add_data(qr_data.strip())
#     qr.make(fit=True)
#     qr_img = qr.make_image(fill_color="black", back_color="white")
    
#     qr_bytes = io.BytesIO()
#     qr_img.save(qr_bytes, format='PNG')
#     qr_bytes.seek(0)

#     qr_size = 65
#     qr_x = card_x + card_width * 0.6 + (card_width * 0.4 - qr_size) / 2
#     qr_y = card_y + (card_height - qr_size) / 2
#     pdf.image(qr_bytes, x=qr_x, y=qr_y, w=qr_size)

#     # QR Caption
#     pdf.set_font("Arial", 'I', 8)
#     pdf.set_xy(card_x + card_width * 0.6, card_y + card_height - 15)
#     pdf.cell(card_width * 0.4, 5, "Scan for verification", 0, 1, 'C')

#     # --- Footer Flag ---
#     pdf.set_fill_color(255, 111, 0)  # Orange
#     pdf.rect(0, 265, 210, 10, 'F')
#     pdf.set_fill_color(255, 255, 255)  # White
#     pdf.rect(0, 275, 210, 10, 'F')
#     pdf.set_fill_color(0, 128, 0)  # Green
#     pdf.rect(0, 285, 210, 10, 'F')

#     # --- Centered Footer Message ---
#     pdf.set_text_color(100, 100, 100)
#     pdf.set_font("Arial", 'I', 9)
#     pdf.set_xy(0, 255)
#     pdf.cell(210, 5, "This card is property of Nilratran Chatrawas", 0, 1, 'C')
#     pdf.set_font("Arial", '', 8)
#     pdf.cell(210, 5, "Valid until course completion", 0, 1, 'C')

#     # Signature and Date
#     pdf.set_font("Arial", 'I', 9)
#     pdf.set_xy(card_x + 20, card_y + card_height + 15)
#     pdf.cell(50, 5, "Authorized Signature: ___________________", 0, 0)

#     pdf.set_xy(card_x + card_width - 70, card_y + card_height + 15)
#     pdf.cell(50, 5, f"Issue Date: {datetime.now().strftime('%Y-%m-%d')}", 0, 1, 'R')

#     # Output PDF
#     pdf_output = f"data/id_card_{member_id}.pdf"
#     pdf.output(pdf_output)
#     return send_file(pdf_output, as_attachment=True, download_name=f"NC_ID_{member_id}.pdf")
@app.route('/download_card')
def download_card():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    member_id = session['user_id']
    members = read_csv('members.csv')
    user = next((m for m in members if m['member_id'] == member_id), None)
    
    if not user:
        return redirect(url_for('login'))

    # Generate QR code
    qr_data = f"""NILRATRAN CHATRAWAS
Student ID: {user['member_id']}
Name: {user['name']}
Course: {user['course']}
Contact: {user['whatsapp']}
Address: {user['address']}"""
    
    qr = qrcode.QRCode(version=1, box_size=4, border=1)
    qr.add_data(qr_data.strip())
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    qr_bytes = io.BytesIO()
    qr_img.save(qr_bytes, format='PNG')
    qr_bytes.seek(0)
    qr_base64 = base64.b64encode(qr_bytes.getvalue()).decode('ascii')

    # Get absolute path to static folder
    static_path = os.path.abspath('static')

    html = render_template('id_card_pdf.html',
                         user=user,
                         qr_code=qr_base64,
                         issue_date=datetime.now().strftime('%Y-%m-%d'),
                         static_path=static_path)

    # Generate PDF with proper margins and positioning
    pdf = HTML(string=html, base_url=static_path).write_pdf(
        stylesheets=[CSS(string='''
@page {
            size: A4 portrait;
            margin: 15mm;  /* Remove all margins */
            background-color: white !important;  /* Force white background */
        }
        body {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 0;
            background-color: white !important;  /* Force white background */
        }
        .id-card {
            width: 85mm;
            height: 54mm;
            margin: 0 auto;  /* Center the card */
            border: 1.5px solid black;
            background-color: white;
        }
    ''')]
    )

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=NC_ID_{member_id}.pdf'
    
    return response
@app.route('/wifi')
def wifi():
    
    return render_template('wifi.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)