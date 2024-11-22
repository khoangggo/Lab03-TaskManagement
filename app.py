from psycopg2 import errors
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import Database
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

db = None

@app.route('/')
@app.route('/connect', methods=['GET', 'POST'])
def connect_db():
    global db
    if request.method == 'POST':
        try:
            # Ví dụ: Kết nối với database với mật khẩu từ form
            db = Database(password=request.form['password'])
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Connection error: {str(e)}")
            return redirect(url_for('connect_db'))
    return render_template('connect.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if db is None:
        flash("Please connect to database first")
        return redirect(url_for('connect_db'))

    if request.method == 'POST':
        user = db.get_user(request.form['email'], request.form['password'])
        if user:
            session['user_id'] = user['userid']
            session['user_name'] = user['name']
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    projects = db.get_all_projects()
    active_tasks = db.get_active_tasks()
    return render_template('dashboard.html', 
                         projects=projects, 
                         tasks=active_tasks)

# Additional routes for CRUD operations
@app.route('/projects/new', methods=['GET', 'POST'])
def new_project():
    if request.method == 'POST':
        db.create_project(
            request.form['name'],
            request.form['description'],
            request.form['start_date'],
            request.form['end_date']
        )
        return redirect(url_for('dashboard'))
    return render_template('project_form.html',is_edit=False)

@app.route('/tasks/new', methods=['GET', 'POST'])
def new_task():
    if request.method == 'POST':
        db.create_task(
            request.form['project_id'],
            request.form['task_name'],
            request.form['assigned_to'],
            'New'
        )
        return redirect(url_for('dashboard'))
    projects = db.get_all_projects()
    users = db.get_all_users()
    return render_template('task_form.html', projects=projects,users = users,is_edit=False)

@app.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
def edit_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        db.update_project(
            project_id,
            request.form['name'],
            request.form['description'],
            request.form['start_date'],
            request.form['end_date']
        )
        return redirect(url_for('dashboard'))
    
    project = db.get_project(project_id)
    return render_template('project_form.html', project=project,is_edit=True)

@app.route('/projects/<int:project_id>/delete', methods=['POST'])
def delete_project(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        
        db.delete_project(project_id)
        flash('Project deleted successfully.', 'success')
    except psycopg2.errors.ForeignKeyViolation:
        db.conn.rollback() 
        flash('Cannot delete the project because it has associated tasks.', 'danger')
    except Exception as e:
        db.conn.rollback() 
        flash(f'An unexpected error occurred: {str(e)}', 'danger')
    
    # Quay lại trang dashboard sau khi xử lý
    return redirect(url_for('dashboard'))

@app.route('/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
def edit_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        db.update_task(
            request.form['project_id'],
            task_id,
            request.form['task_name'],
            request.form['assigned_to'],
            request.form['status']
        )
        return redirect(url_for('dashboard'))
    
    task = db.get_task(task_id)
    projects = db.get_all_projects()
    users = db.get_all_users()
    return render_template('task_form.html', task=task, projects=projects, users=users,is_edit=True)

@app.route('/tasks/<int:task_id>/delete', methods=['POST'])
def delete_task(task_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db.delete_task(task_id)
    return redirect(url_for('dashboard'))

@app.route('/projects/<int:project_id>/members', methods=['GET', 'POST'])
def project_members(project_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        user_id = request.form['user_id']
        action = request.form['action']
        
        if action == 'add':
            db.add_project_member(project_id, user_id)
        elif action == 'remove':
            db.remove_project_member(project_id, user_id)
            
        return redirect(url_for('project_members', project_id=project_id))
    
    project = db.get_project(project_id)
    members = db.get_project_members(project_id)
    all_users = db.get_all_users()
    return render_template('project_members.html', 
                         project=project, 
                         members=members, 
                         users=all_users)

@app.route('/users')
def users():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    all_users = db.get_all_users()
    return render_template('users.html', users=all_users)

@app.route('/users/new', methods=['GET', 'POST'])
def new_user():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        role = request.form['role']
        password = request.form['password']
        db.create_user(name, email, role, password)
        return redirect(url_for('users'))
    
    return render_template('user_form.html', is_edit=False)

@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        role = request.form['role']
        # Update user data, assuming `update_user` exists in `db`
        db.update_user(user_id, name, email, role)
        return redirect(url_for('users'))
    
    user = db.get_user_by_id(user_id)  # Create this function in the `Database` class
    return render_template('user_form.html', user=user, is_edit=True)

@app.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        
        db.delete_user(user_id)  
        flash('User deleted successfully.', 'success')
    except psycopg2.errors.ForeignKeyViolation:
        db.conn.rollback() 
        flash('Cannot delete the user because it has associated tasks.', 'danger')
    except Exception as e:
        db.conn.rollback() 
        flash(f'An unexpected error occurred: {str(e)}', 'danger')
    
    return redirect(url_for('users'))
    
   

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)