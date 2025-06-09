from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
from datetime import date, timedelta
import mimetypes

app = Flask(__name__)
app.secret_key = 'your_secure_random_key_12345'  # Replace with a secure random key in production
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max upload size
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def init_db():
    """Initialize the database with all required tables."""
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS bmi (
        user_id INTEGER,
        height REAL,
        weight REAL,
        bmi REAL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS goals (
        user_id INTEGER,
        goal_type TEXT,
        daily_calories INTEGER,
        daily_protein INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS food_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        food_name TEXT,
        calories INTEGER,
        protein REAL,
        carbs REAL,
        fats REAL,
        vitamins TEXT,
        minerals TEXT,
        image_path TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    c.execute('CREATE INDEX IF NOT EXISTS idx_food_logs_user_date ON food_logs (user_id, date)')
    conn.commit()
    conn.close()

def get_db():
    """Return a database connection with row factory."""
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def analyze_food_image(image_path):
    """Analyze food image using Gemini API and return detailed nutritional data."""
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')  # Replace with 'gemini-1.5-pro' if needed
        with open(image_path, 'rb') as img_file:
            img_data = img_file.read()
        mime_type, _ = mimetypes.guess_type(image_path)
        if mime_type not in ['image/jpeg', 'image/png']:
            raise ValueError("Unsupported image format. Use JPEG or PNG.")
        prompt = """Analyze this food image and return a JSON object with detailed nutritional breakdown in point format:
        - food_name: string (name of the food)
        - calories: integer (estimated total calories)
        - protein: float (grams of protein)
        - carbs: float (grams of carbohydrates)
        - fats: float (grams of fats)
        - vitamins: string (list of vitamins, e.g., 'Vitamin C, Vitamin A')
        - minerals: string (list of minerals, e.g., 'Iron, Potassium')
        Example: {"food_name": "Healthy Lunch Bowl", "calories": 450, "protein": 20.0, "carbs": 25.0, "fats": 30.0, "vitamins": "Vitamin C, Vitamin A", "minerals": "Iron, Potassium"}
        Ensure the response is valid JSON without markdown or extra text."""
        response = model.generate_content([prompt, {'mime_type': mime_type, 'data': img_data}])
        print("Raw Gemini API response:", response.text)
        if not response.text:
            raise ValueError("Empty response from Gemini API")
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith('```'):
            response_text = response_text[3:-3].strip()
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print("JSON decode error:", str(e))
            raise ValueError(f"Invalid JSON response from Gemini: {response_text}")
    except Exception as e:
        print("Error in analyze_food_image:", str(e))
        raise Exception(f"Image analysis failed: {str(e)}")

def validate_analysis(analysis):
    """Validate the nutritional analysis data."""
    required_keys = ['food_name', 'calories', 'protein', 'carbs', 'fats', 'vitamins', 'minerals']
    return all(key in analysis for key in required_keys) and all(isinstance(analysis[key], (int, float, str)) for key in required_keys)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('signup.html')
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            flash('Sign-up successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists.', 'error')
        finally:
            conn.close()
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('login.html')
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            conn = get_db()
            c = conn.cursor()
            c.execute('SELECT * FROM bmi WHERE user_id = ?', (session['user_id'],))
            bmi_exists = c.fetchone()
            c.execute('SELECT * FROM goals WHERE user_id = ?', (session['user_id'],))
            goal_exists = c.fetchone()
            conn.close()
            if bmi_exists and goal_exists:
                return redirect(url_for('dashboard'))
            return redirect(url_for('bmi'))
        flash('Invalid credentials.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/bmi', methods=['GET', 'POST'])
def bmi():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM bmi WHERE user_id = ?', (session['user_id'],))
    if c.fetchone():
        conn.close()
        return redirect(url_for('goal'))
    conn.close()
    if request.method == 'POST':
        try:
            height = float(request.form['height']) / 100  # Convert cm to meters
            weight = float(request.form['weight'])
            if height <= 0 or weight <= 0:
                raise ValueError("Height and weight must be positive.")
            bmi = weight / (height ** 2)
            conn = get_db()
            c = conn.cursor()
            c.execute('INSERT INTO bmi (user_id, height, weight, bmi) VALUES (?, ?, ?, ?)',
                      (session['user_id'], height, weight, bmi))
            conn.commit()
            conn.close()
            return redirect(url_for('goal'))
        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'error')
    return render_template('bmi.html')

@app.route('/goal', methods=['GET', 'POST'])
def goal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM goals WHERE user_id = ?', (session['user_id'],))
    if c.fetchone():
        conn.close()
        return redirect(url_for('dashboard'))
    conn.close()
    if request.method == 'POST':
        goal_type = request.form['goal']
        if goal_type not in ['bulk', 'lean']:
            flash('Invalid goal selected.', 'error')
            return render_template('goal.html')
        daily_calories = int(request.form.get('daily_calories', 2500 if goal_type == 'bulk' else 1800))
        daily_protein = int(request.form.get('daily_protein', 150 if goal_type == 'bulk' else 100))
        try:
            if daily_calories <= 0 or daily_protein <= 0:
                raise ValueError("Calories and protein must be positive.")
        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'error')
            return render_template('goal.html')
        conn = get_db()
        c = conn.cursor()
        c.execute('INSERT INTO goals (user_id, goal_type, daily_calories, daily_protein) VALUES (?, ?, ?, ?)',
                  (session['user_id'], goal_type, daily_calories, daily_protein))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('goal.html')

@app.route('/update_goal', methods=['GET', 'POST'])
def update_goal():
    """Handle GET and POST requests for updating user goals."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    if request.method == 'POST':
        goal_type = request.form.get('goal')
        try:
            daily_calories = int(request.form['daily_calories'])
            daily_protein = int(request.form['daily_protein'])
            if daily_calories <= 0 or daily_protein <= 0:
                raise ValueError("Calories and protein must be positive.")
        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'error')
            return render_template('update_goal.html')
        c.execute('UPDATE goals SET goal_type = ?, daily_calories = ?, daily_protein = ? WHERE user_id = ?',
                  (goal_type, daily_calories, daily_protein, session['user_id']))
        conn.commit()
        flash('Goal updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    # Fetch current goal for pre-population in the form
    c.execute('SELECT goal_type, daily_calories, daily_protein FROM goals WHERE user_id = ?', (session['user_id'],))
    current_goal = c.fetchone()
    conn.close()
    return render_template('update_goal.html', current_goal=current_goal)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM goals WHERE user_id = ?', (session['user_id'],))
    goal = c.fetchone()
    today = date.today().isoformat()
    c.execute('SELECT * FROM food_logs WHERE user_id = ? AND date = ?', (session['user_id'], today))
    food_logs = c.fetchall()
    total_calories = sum(log['calories'] for log in food_logs)
    total_protein = sum(log['protein'] for log in food_logs)
    total_carbs = sum(log['carbs'] for log in food_logs)
    total_fats = sum(log['fats'] for log in food_logs)
    conn.close()
    if request.method == 'POST':
        if 'food_image' in request.files and request.files['food_image'].filename:
            image = request.files['food_image']
            if not image.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                flash('Unsupported image format. Use JPEG or PNG.', 'error')
                return redirect(url_for('dashboard'))
            # Normalize the filename with forward slashes and lowercase 'uploads'
            filename = os.path.join('static', 'uploads', image.filename).replace('\\', '/')
            image_path = filename  # Store the normalized path
            try:
                # Ensure the directory exists
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                # Save the image and verify
                image.save(filename)
                if not os.path.exists(filename):
                    flash('Failed to save image. Check directory permissions.', 'error')
                    return redirect(url_for('dashboard'))
                print(f"Image saved at: {filename}")  # Debug print
                try:
                    analysis = analyze_food_image(filename)
                    if not validate_analysis(analysis):
                        raise ValueError('Invalid analysis data')
                except Exception as e:
                    flash(f'Error analyzing image: {str(e)}. Using default values.', 'error')
                    analysis = {
                        'food_name': 'Unknown Food',
                        'calories': 0,
                        'protein': 0,
                        'carbs': 0,
                        'fats': 0,
                        'vitamins': '',
                        'minerals': ''
                    }
                food_name = analysis.get('food_name', 'Unknown')
                calories = int(analysis.get('calories', 0))
                protein = float(analysis.get('protein', 0))
                carbs = float(analysis.get('carbs', 0))
                fats = float(analysis.get('fats', 0))
                vitamins = analysis.get('vitamins', '')
                minerals = analysis.get('minerals', '')
            except Exception as e:
                flash(f'Error processing image: {str(e)}', 'error')
                return redirect(url_for('dashboard'))
        elif 'food_name' in request.form:
            food_name = request.form['food_name'].strip()
            try:
                calories = int(request.form['calories'])
                protein = float(request.form['protein'])
                carbs = float(request.form['carbs'])
                fats = float(request.form['fats'])
                if calories < 0 or protein < 0 or carbs < 0 or fats < 0:
                    raise ValueError("Values cannot be negative.")
                vitamins = request.form.get('vitamins', '')
                minerals = request.form.get('minerals', '')
                image_path = None
            except ValueError as e:
                flash(f'Invalid manual input: {str(e)}', 'error')
                return redirect(url_for('dashboard'))
        else:
            flash('Please upload an image or enter food details.', 'error')
            return redirect(url_for('dashboard'))
        conn = get_db()
        c = conn.cursor()
        c.execute('INSERT INTO food_logs (user_id, date, food_name, calories, protein, carbs, fats, vitamins, minerals, image_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                  (session['user_id'], today, food_name, calories, protein, carbs, fats, vitamins, minerals, image_path))
        conn.commit()
        conn.close()
        flash('Food logged successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('dashboard.html', goal=goal, food_logs=food_logs, total_calories=total_calories,
                          total_protein=total_protein, total_carbs=total_carbs, total_fats=total_fats)

@app.route('/history', methods=['GET', 'POST'])
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    selected_date = request.form.get('selected_date', date.today().isoformat())
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM food_logs WHERE user_id = ? AND date = ?', (session['user_id'], selected_date))
    food_logs = c.fetchall()
    total_calories = sum(log['calories'] for log in food_logs)
    total_protein = sum(log['protein'] for log in food_logs)
    total_carbs = sum(log['carbs'] for log in food_logs)
    total_fats = sum(log['fats'] for log in food_logs)
    trend_data = []
    for i in range(6, -1, -1):
        day = (date.today() - timedelta(days=i)).isoformat()
        c.execute('SELECT SUM(calories) as calories, SUM(protein) as protein FROM food_logs WHERE user_id = ? AND date = ?',
                  (session['user_id'], day))
        row = c.fetchone()
        trend_data.append({
            'date': day,
            'calories': row['calories'] or 0,
            'protein': row['protein'] or 0
        })
    conn.close()
    return render_template('history.html', food_logs=food_logs, selected_date=selected_date,
                          total_calories=total_calories, total_protein=total_protein,
                          total_carbs=total_carbs, total_fats=total_fats, trend_data=trend_data)

@app.route('/dashboard_data')
def dashboard_data():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute('SELECT * FROM food_logs WHERE user_id = ? AND date = ?', (session['user_id'], today))
    food_logs = c.fetchall()
    c.execute('SELECT daily_calories, daily_protein FROM goals WHERE user_id = ?', (session['user_id'],))
    goal = c.fetchone()
    total_calories = sum(log['calories'] for log in food_logs)
    total_protein = sum(log['protein'] for log in food_logs)
    total_carbs = sum(log['carbs'] for log in food_logs)
    total_fats = sum(log['fats'] for log in food_logs)
    conn.close()
    return jsonify({
        'total_calories': total_calories,
        'total_protein': total_protein,
        'total_carbs': total_carbs,
        'total_fats': total_fats,
        'daily_calories': goal['daily_calories'],
        'daily_protein': goal['daily_protein']
    })

@app.route('/test_image')
def test_image():
    """Test route to verify image serving."""
    image_path = 'static/uploads/dosa-recipe.jpg'
    if os.path.exists(image_path):
        return f'<img src="{url_for("static", filename="uploads/dosa-recipe.jpg")}" alt="Test Image" style="max-width: 200px;">'
    else:
        return "Image not found."

if __name__ == '__main__':
    os.makedirs('static/uploads', exist_ok=True)
    init_db()
    app.run(debug=True)