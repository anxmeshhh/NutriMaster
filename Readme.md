# NutriMaster
NutriMaster is a Flask-based web application for tracking nutrition and fitness goals. Users can log food intake via image analysis (using Google Gemini API) or manual entry, calculate BMI, set personalized goals, and visualize daily/weekly progress with interactive charts.
Features

User Authentication: Secure sign-up/login with password hashing.
Food Logging:
Upload food images for nutritional analysis (calories, protein, carbs, fats, vitamins, minerals).
Manual food entry with detailed nutritional data.


BMI Calculation: Compute and store BMI based on height and weight.
Goal Setting: Define daily calorie and protein targets (bulk/lean goals).
Progress Tracking: View daily food logs and historical data with macronutrient breakdowns.
Visual Analytics: Interactive charts for calorie/protein progress and weekly trends.
Responsive Design: Clean, user-friendly interface with Bootstrap styling.

Technologies

Backend: Flask, SQLite
Frontend: HTML, Bootstrap, Chart.js, Flatpickr
API: Google Gemini API for image-based nutritional analysis
Dependencies: Python 3.8+, Werkzeug, python-dotenv, google-generativeai

Prerequisites

Python 3.8 or higher
Git
Google Gemini API key (obtain from Google AI Studio)

Installation

Clone the Repository:
git clone https://github.com/your-username/nutrimaster.git
cd nutrimaster


Create a Virtual Environment:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Install Dependencies:
pip install -r requirements.txt


Set Up Environment Variables:

Create a .env file in the project root:GEMINI_API_KEY=your_gemini_api_key





Running the Application

Initialize the Database:

The app automatically creates database.db on first run.


Start the Flask Server:
python app.py


Access the App:

Open http://localhost:5000 in your browser.



Usage

Sign Up/Login: Create an account or log in to access the dashboard.
Set BMI and Goals: Enter height/weight for BMI and set calorie/protein goals.
Log Food:
Upload a food image for automatic nutritional analysis.
Or manually enter food details (name, calories, macros, etc.).


View Progress:
Dashboard: See today’s food logs, macronutrient breakdown, and goal progress via charts.
History: Select a date to view past logs and weekly trends.


Update Goals: Adjust calorie/protein targets as needed.

Project Structure
nutrimaster/
├── static/
│   ├── css/
│   ├── js/
│   └── uploads/            # Stores uploaded food images
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── history.html
│   └── ...                # Other HTML templates
├── app.py                 # Main Flask application
├── database.db            # SQLite database
├── update_db.py           # Script to update image paths
├── .env                   # Environment variables
├── requirements.txt       # Python dependencies
└── README.md

Database Schema

users: Stores user ID, username, and hashed password.
bmi: Stores user ID, height, weight, and calculated BMI.
goals: Stores user ID, goal type (bulk/lean), daily calories, and protein.
food_logs: Stores food log ID, user ID, date, food name, nutritional data, and image path.

API Integration

Google Gemini API: Analyzes food images to extract nutritional data (calories, protein, carbs, fats, vitamins, minerals).
Ensure a valid API key is set in .env.

Troubleshooting

Images Not Displaying:
Verify static/uploads/ exists and contains images.
Check image_path in food_logs table (should be static/uploads/filename.jpg).
Ensure template image URLs use {{ url_for('static', filename=log['image_path'].replace('static/', '')) }}.


API Errors:
Confirm Gemini API key is valid and quota is not exceeded.


Database Issues:
Run python app.py to initialize the database if database.db is missing.



Future Enhancements

Meal categorization (breakfast, lunch, etc.).
Water intake tracking.
Exercise logging for calorie expenditure.
Dietary recommendations via Gemini API.
Exportable progress reports (PDF/CSV).

Contributing
Contributions are welcome! Please:

Fork the repository.
Create a feature branch (git checkout -b feature-name).
Commit changes (git commit -m "Add feature").
Push to the branch (git push origin feature-name).
Open a pull request.

License
This project is licensed under the MIT License. See the LICENSE file for details.
