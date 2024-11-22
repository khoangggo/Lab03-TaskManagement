from datetime import datetime
import psycopg2
from psycopg2.extras import DictCursor

class Database:
    def __init__(self,password, host='localhost', database='project-management', user='postgres'):
        self.conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
        self.create_tables()
    
    def create_tables(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS Users (
                    UserID SERIAL PRIMARY KEY,
                    Name VARCHAR(100) NOT NULL,
                    Email VARCHAR(100) UNIQUE NOT NULL,
                    Role VARCHAR(50) NOT NULL,
                    Password VARCHAR(100) NOT NULL
                );

                CREATE TABLE IF NOT EXISTS Projects (
                    ProjectID SERIAL PRIMARY KEY,
                    ProjectName VARCHAR(100) NOT NULL,
                    Description TEXT,
                    StartDate DATE NOT NULL,
                    EndDate DATE NOT NULL
                );

                CREATE TABLE IF NOT EXISTS Tasks (
                    TaskID SERIAL PRIMARY KEY,
                    ProjectID INTEGER REFERENCES Projects(ProjectID),
                    TaskName VARCHAR(200) NOT NULL,
                    AssignedTo INTEGER REFERENCES Users(UserID),
                    Status VARCHAR(50) NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ProjectMembers (
                    ProjectID INTEGER REFERENCES Projects(ProjectID),
                    UserID INTEGER REFERENCES Users(UserID),
                    PRIMARY KEY (ProjectID, UserID)
                );
            """)
            self.conn.commit()

    def get_user(self, email, password):
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM Users WHERE Email = %s AND Password = %s", 
                       (email, password))
            return cur.fetchone()

    def create_user(self, name, email, role, password):
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO Users (Name, Email, Role, Password) VALUES (%s, %s, %s, %s) RETURNING UserID",
                (name, email, role, password)
            )
            self.conn.commit()
            return cur.fetchone()[0]
        
    def update_user(self, user_id, name, email, role):
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE Users SET Name = %s, Email = %s, Role = %s WHERE UserID = %s",
                (name, email, role, user_id)
            )
            self.conn.commit()

    def delete_user(self, user_id):
        try:
            with self.conn.cursor() as cur:
                cur.execute("DELETE FROM Users WHERE UserID = %s", (user_id,))
                self.conn.commit()  
        except psycopg2.errors.ForeignKeyViolation:
            self.conn.rollback()  
            print('Cannot delete the user because they have associated tasks.')
            raise
        except Exception as e:
            self.conn.rollback() 
            print(f'An unexpected error occurred: {str(e)}')
            raise

         

    def get_user_by_id(self, user_id):
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM Users WHERE UserID = %s", (user_id,))
            return cur.fetchone()

    def get_all_projects(self):
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM Projects")
            return cur.fetchall()

    def create_project(self, name, description, start_date, end_date):
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO Projects (ProjectName, Description, StartDate, EndDate) VALUES (%s, %s, %s, %s) RETURNING ProjectID",
                (name, description, start_date, end_date)
            )
            self.conn.commit()
            return cur.fetchone()[0]

    def update_project(self, project_id, name, description, start_date, end_date):
        with self.conn.cursor() as cur:
            cur.execute(
                """UPDATE Projects 
                   SET ProjectName = %s, Description = %s, StartDate = %s, EndDate = %s 
                   WHERE ProjectID = %s""",
                (name, description, start_date, end_date, project_id)
            )
            self.conn.commit()

    def delete_project(self, project_id):
        try:
            with self.conn.cursor() as cur:

                cur.execute("DELETE FROM Projects WHERE ProjectID = %s", (project_id,))
                self.conn.commit() 
        except psycopg2.errors.ForeignKeyViolation:
            self.conn.rollback()  
            print("Cannot delete the project because it has associated tasks.")
            raise  
        except Exception as e:
            self.conn.rollback() 
          
            print(f"An error occurred while deleting the project: {str(e)}")
            raise 

    # Task operations
    def get_active_tasks(self):
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT t.*, p.ProjectName, u.Name as AssigneeName 
                FROM Tasks t
                JOIN Projects p ON t.ProjectID = p.ProjectID
                JOIN Users u ON t.AssignedTo = u.UserID
                WHERE t.Status != 'Completed'
            """)
            return cur.fetchall()

    def create_task(self, project_id, task_name, assigned_to, status):
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO Tasks (ProjectID, TaskName, AssignedTo, Status) VALUES (%s, %s, %s, %s) RETURNING TaskID",
                (project_id, task_name, assigned_to, status)
            )
            self.conn.commit()
            return cur.fetchone()[0]

    def update_task(self,project_id, task_id, task_name, assigned_to, status):
        with self.conn.cursor() as cur:
            cur.execute(
                """UPDATE Tasks 
                   SET ProjectID = %s, TaskName = %s, AssignedTo = %s, Status = %s 
                   WHERE TaskID = %s""",
                (project_id,task_name, assigned_to, status, task_id)
            )
            self.conn.commit()

    def get_project(self, project_id):
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM Projects WHERE ProjectID = %s", (project_id,))
            return cur.fetchone()

    def get_all_users(self):
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM Users")
            return cur.fetchall()

    def get_task(self, task_id):
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT t.*, p.ProjectName, u.Name as AssigneeName 
                FROM Tasks t
                JOIN Projects p ON t.ProjectID = p.ProjectID
                JOIN Users u ON t.AssignedTo = u.UserID
                WHERE t.TaskID = %s
            """, (task_id,))
            return cur.fetchone()

    def delete_task(self, task_id):
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM Tasks WHERE TaskID = %s", (task_id,))
            self.conn.commit()

    def get_project_members(self, project_id):
        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT u.* FROM Users u
                JOIN ProjectMembers pm ON u.UserID = pm.UserID
                WHERE pm.ProjectID = %s
            """, (project_id,))
            return cur.fetchall()

    def add_project_member(self, project_id, user_id):
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO ProjectMembers (ProjectID, UserID) VALUES (%s, %s)",
                (project_id, user_id)
            )
            self.conn.commit()

    def remove_project_member(self, project_id, user_id):
        with self.conn.cursor() as cur:
            cur.execute(
                "DELETE FROM ProjectMembers WHERE ProjectID = %s AND UserID = %s",
                (project_id, user_id)
            )
            self.conn.commit()

