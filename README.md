# Online Examination System

## Project Overview
The Online Examination System is a web-based application developed using Python Flask and MySQL. It allows administrators to create and manage examinations, while students can register, log in, attend exams, and view their results.

## Features

### Admin
- Admin login and logout
- Admin dashboard
- Create examinations
- Generate unique exam codes
- Add and manage questions
- Publish examinations
- View available examinations
- View student results
- View individual result details

### Student
- Student registration and login
- Student dashboard
- Join examinations using exam codes
- Attend timed examinations
- Navigate between questions
- Submit examinations
- Automatic result calculation
- View examination results

## Technologies Used
- Python
- Flask
- MySQL
- HTML
- CSS
- JavaScript

## Project Structure

```text
Online-Examination-System/
│
├── app.py
├── database.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── templates/
│
└── static/
```

## Installation and Setup

1. Clone the repository:

```bash
git clone https://github.com/BERYL-SURYA/Online-Examination-System.git
```

2. Navigate to the project folder:

```bash
cd Online-Examination-System
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Create a MySQL database named `online_exam` and configure the required tables.

5. Create a `.env` file in the project folder and configure:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=online_exam
SECRET_KEY=your_secret_key
```

6. Run the application:

```bash
python app.py
```

7. Open your browser and visit:

```text
http://127.0.0.1:5000
```

## Security
- Database credentials are stored in environment variables.
- The `.env` file is excluded from Git using `.gitignore`.
- Never upload passwords or secret keys to GitHub.

## Author
Beryl Surya
