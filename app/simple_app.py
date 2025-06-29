from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for, send_from_directory
import os
import random
import google.generativeai as genai
# Import our dashboard functionality
from dashboard import setup_dashboard_routes, video_content, teachers, progress_data, session_template

app = Flask(__name__, static_folder='static')
app.secret_key = 'dev-key-simple-app'

# Configure Google Gemini API
genai.configure(api_key='AIzaSyAlzoyskxO0gcsSYO2SqcsZa_VCXXTJcpU')
model = genai.GenerativeModel('gemini-1.5-flash')

# Route to serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

# Sample user data
users = {
    'student1': {'password': 'password123', 'name': 'Student One', 'role': 'student'},
    'student2': {'password': 'password123', 'name': 'Student Two', 'role': 'student'},
    'student3': {'password': 'password123', 'name': 'Student Three', 'role': 'student'},
    'student4': {'password': 'password123', 'name': 'Student Four', 'role': 'student'},
    'student5': {'password': 'password123', 'name': 'Student Five', 'role': 'student'},
    'admin': {'password': 'admin123', 'name': 'Admin User', 'role': 'admin'}
}

# Store subject-specific content
subject_content = {
    'math': {
        'welcome_message': "Hello! I'm your Math tutor. I can help with algebra, calculus, statistics, and more. What would you like to learn today?",
        'videos': video_content['math']
    },
    'science': {
        'welcome_message': "Hello! I'm your Science tutor. I can help with physics, chemistry, biology, and more. What would you like to explore today?",
        'videos': video_content['science']
    },
    'programming': {
        'welcome_message': "Hello! I'm your Programming tutor. I can help with Python, JavaScript, data structures, algorithms, and more. What would you like to code today?",
        'videos': video_content['programming']
    },
    'language': {
        'welcome_message': "Hello! I'm your Language Arts tutor. I can help with writing, grammar, literature analysis, and more. What would you like to work on today?",
        'videos': video_content['language']
    }
}

# Home page template
home_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>AI Learning Platform</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
    <style>
        :root {
            --primary-color: #4568dc;
            --secondary-color: #3f51b5;
            --accent-color: #FF5722;
            --text-color: #333;
            --light-bg: #f4f7fd;
            --card-bg: white;
            --shadow: 0 4px 20px rgba(0,0,0,0.08);
        }
        
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            margin: 0; 
            padding: 0; 
            background-color: var(--light-bg); 
            color: var(--text-color);
        }
        
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
        }
        
        .header { 
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)); 
            color: white; 
            padding: 15px 20px; 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header-logo {
            display: flex;
            align-items: center;
        }
        
        .logo {
            height: 40px;
            margin-right: 10px;
        }
        
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        
        .nav-links a {
            color: white;
            text-decoration: none;
            margin-left: 20px;
            transition: all 0.3s;
        }
        
        .nav-links a:hover {
            opacity: 0.8;
        }
        
        .hero {
            background: url('/static/images/hero-bg.svg') center center / cover no-repeat;
            padding: 80px 20px;
            text-align: center;
            color: white;
            position: relative;
        }
        
        .hero::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(69, 104, 220, 0.8), rgba(63, 81, 181, 0.8));
            z-index: 1;
        }
        
        .hero-content {
            position: relative;
            z-index: 2;
            max-width: 800px;
            margin: 0 auto;
        }
        
        .hero h2 {
            font-size: 36px;
            margin-bottom: 20px;
        }
        
        .hero p {
            font-size: 18px;
            margin-bottom: 30px;
        }
        
        .login-form { 
            max-width: 400px; 
            margin: 50px auto; 
            background: white; 
            padding: 30px; 
            border-radius: 12px; 
            box-shadow: var(--shadow);
            position: relative;
            overflow: hidden;
        }
        
        .login-form h2 {
            margin-top: 0;
            color: var(--primary-color);
            text-align: center;
        }
        
        .button { 
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)); 
            color: white; 
            border: none; 
            padding: 12px 20px; 
            border-radius: 6px; 
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            width: 100%;
            transition: all 0.3s;
        }
        
        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        input[type="text"], input[type="password"] { 
            width: 100%; 
            padding: 12px; 
            margin: 10px 0; 
            border: 1px solid #ddd; 
            border-radius: 6px; 
            box-sizing: border-box;
            font-size: 16px;
        }
        
        .dashboard { 
            display: grid; 
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); 
            gap: 20px; 
            margin-top: 30px; 
        }
        
        .card { 
            background: white; 
            padding: 25px; 
            border-radius: 12px; 
            box-shadow: var(--shadow);
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        }
        
        .card h3 {
            margin-top: 0;
            color: var(--primary-color);
        }
        
        .welcome { 
            margin: 40px 0 30px; 
            font-size: 28px; 
            color: var(--text-color);
            text-align: center;
        }
        
        a { 
            color: var(--primary-color); 
            text-decoration: none; 
        }
        
        a:hover { 
            text-decoration: underline; 
        }
        
        .card-icon {
            position: absolute;
            top: 15px;
            right: 15px;
            font-size: 30px;
            color: var(--primary-color);
            opacity: 0.2;
        }
        
        .decoration-circle {
            position: absolute;
            border-radius: 50%;
            background: var(--primary-color);
            opacity: 0.05;
            z-index: 0;
        }
        
        .circle-1 {
            width: 100px;
            height: 100px;
            top: -30px;
            right: -30px;
        }
        
        .circle-2 {
            width: 60px;
            height: 60px;
            bottom: -20px;
            left: -20px;
        }
        
        .subject-icon {
            width: 60px;
            height: 60px;
            margin-bottom: 15px;
        }
        
        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
            }
            
            .hero h2 {
                font-size: 28px;
            }
            
            .hero p {
                font-size: 16px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-logo">
            <img src="/static/images/logo.svg" alt="AI Learning Platform" class="logo">
            <h1>AI Learning Platform</h1>
        </div>
        
        {% if 'username' in session %}
            <div class="nav-links">
                <a href="/dashboard">Dashboard</a>
                <a href="/profile">Profile</a>
                <a href="/logout">Logout</a>
            </div>
        {% endif %}
    </div>
    
    {% if 'username' not in session %}
        <div class="hero">
            <div class="hero-content">
                <h2>Personalized Learning with AI</h2>
                <p>Experience adaptive learning with our AI-powered platform. Get instant feedback, track your progress, and master new skills at your own pace.</p>
            </div>
        </div>
    {% endif %}
    
    <div class="container">
        {% if 'username' not in session %}
            <div class="login-form">
                <div class="decoration-circle circle-1"></div>
                <div class="decoration-circle circle-2"></div>
                <h2>Login to Your Account</h2>
                {% if error %}
                    <p style="color: red; text-align: center;">{{ error }}</p>
                {% endif %}
                <form method="post" action="/login">
                    <div>
                        <input type="text" name="username" placeholder="Username" required>
                    </div>
                    <div>
                        <input type="password" name="password" placeholder="Password" required>
                    </div>
                    <button type="submit" class="button">Login</button>
                </form>
            </div>
        {% else %}
            <div class="welcome">Welcome to your learning dashboard, {{ session['name'] }}!</div>
            
            <div class="dashboard">
                <div class="card">
                    <div class="decoration-circle circle-1"></div>
                    <div class="decoration-circle circle-2"></div>
                    <i class="fas fa-square-root-alt card-icon"></i>
                    <img src="/static/images/math-icon.svg" alt="Math" class="subject-icon">
                    <h3>Math Learning</h3>
                    <p>Practice algebra, calculus, and statistics with our AI tutor.</p>
                    <a href="/session/math"><button class="button">Start Session</button></a>
                </div>
                
                <div class="card">
                    <div class="decoration-circle circle-1"></div>
                    <div class="decoration-circle circle-2"></div>
                    <i class="fas fa-atom card-icon"></i>
                    <img src="/static/images/science-icon.svg" alt="Science" class="subject-icon">
                    <h3>Science Learning</h3>
                    <p>Explore physics, chemistry, and biology concepts.</p>
                    <a href="/session/science"><button class="button">Start Session</button></a>
                </div>
                
                <div class="card">
                    <div class="decoration-circle circle-1"></div>
                    <div class="decoration-circle circle-2"></div>
                    <i class="fas fa-code card-icon"></i>
                    <img src="/static/images/programming-icon.svg" alt="Programming" class="subject-icon">
                    <h3>Programming</h3>
                    <p>Learn to code with Python, JavaScript, and more.</p>
                    <a href="/session/programming"><button class="button">Start Session</button></a>
                </div>
                
                <div class="card">
                    <div class="decoration-circle circle-1"></div>
                    <div class="decoration-circle circle-2"></div>
                    <i class="fas fa-book card-icon"></i>
                    <img src="/static/images/language-icon.svg" alt="Language" class="subject-icon">
                    <h3>Language Arts</h3>
                    <p>Improve your writing, grammar, and literature analysis.</p>
                    <a href="/session/language"><button class="button">Start Session</button></a>
                </div>
            </div>
        {% endif %}
    </div>
</body>
</html>
'''

# Link up all the routes
@app.route('/')
def home():
    return render_template_string(home_template, error=None)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username in users and users[username]['password'] == password:
        session['username'] = username
        session['name'] = users[username]['name']
        session['role'] = users[username]['role']
        return redirect('/')
    else:
        return render_template_string(home_template, error='Invalid username or password')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/api/chat', methods=['POST'])
def chat():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    user_input = data.get('message', '')
    subject = data.get('subject', '')
    
    if not user_input:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        # Get response from Gemini
        response = model.generate_content(user_input)
        return jsonify({'response': response.text})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': 'Failed to get response from AI model'}), 500

# Setup dashboard routes
setup_dashboard_routes(app)

if __name__ == '__main__':
    # Try with different settings to avoid connection issues
    port = 3000
    print(f"Starting server at http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False) 