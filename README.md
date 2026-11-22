# Study Management

A web application that helps students organise their studies: subjects, notes, tasks, a weekly timetable, and a progress dashboard. Built with Django and MySQL.

## Features
- User registration, login and logout (each student sees only their own data)
- Subjects with code and weekly target study hours
- Notes for each subject
- Tasks with due date, description and status (Pending, In Progress, Completed)
- Weekly timetable
- Dashboard with task progress, overdue tasks, today's schedule and planned study hours vs target

## Tech Stack
- Backend: Python, Django
- Database: MySQL
- Frontend: HTML, CSS, JavaScript

## Setup
1. Clone the repo and open the folder
2. Create and activate a virtual environment
3. `pip install -r requirements.txt`
4. Create a MySQL database named `studydb`
5. Set the database password: `$env:DB_PASSWORD="your-password"` (PowerShell)
6. `python manage.py migrate`
7. `python manage.py runserver`
8. Open http://127.0.0.1:8000