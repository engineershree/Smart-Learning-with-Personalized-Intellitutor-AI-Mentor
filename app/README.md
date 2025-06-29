# AI Learning Platform

This is an educational platform that allows students to learn various subjects with personalized AI tutors. The platform includes features for progress tracking, teacher information, course management, and more.

## Features

- Dashboard with progress tracking and course information
- Personalized AI tutor for each subject
- Video lessons with YouTube integration
- Note-taking capabilities
- Learning resources and reference materials
- User profiles with achievements

## Subjects Covered

- Math
- Science
- Programming
- Language Arts

## Getting Started

### Prerequisites

- Python 3.7+
- pip (Python package manager)

### Installation

1. Clone the repository or extract the project files
2. Navigate to the project directory

```bash
cd app
```

3. Create a virtual environment (optional but recommended)

```bash
python -m venv venv
```

4. Activate the virtual environment

On Windows:
```bash
venv\Scripts\activate
```

On macOS/Linux:
```bash
source venv/bin/activate
```

5. Install the required dependencies

```bash
pip install -r requirements.txt
```

### Running the Application

Run the application using the run.py script:

```bash
python run.py
```

The application will be available at [http://localhost:3000](http://localhost:3000)

### Login Information

Use these credentials to log in:

- Username: `student1` - Password: `password123`
- Username: `student2` - Password: `password123`
- Username: `student3` - Password: `password123`
- Username: `student4` - Password: `password123`
- Username: `student5` - Password: `password123`
- Username: `admin` - Password: `admin123`

## Usage

1. Log in using the provided credentials
2. Navigate to the dashboard to see your progress
3. Select a subject to start a learning session
4. Interact with the AI tutor using the chat interface
5. Watch video lessons on the subject
6. Take notes during your learning session
7. Explore additional resources to enhance your learning

## Project Structure

- `simple_app.py` - Main Flask application file
- `dashboard.py` - Dashboard and session template definitions
- `requirements.txt` - Dependencies required for the project
- `run.py` - Script to run the application

## Future Enhancements

- Integration with real AI models for more intelligent responses
- Real database backend for persistent data storage
- Progress assessment and quizzes
- Voice interaction with the AI tutor
- Mobile app support
- Integration with learning management systems 