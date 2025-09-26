from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import uvicorn

app = FastAPI(title="Student Monitoring API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class StudentBase(BaseModel):
    FIO: str
    Group_id: int
    Curs_id: int
    Science_id: int


class StudentResponse(StudentBase):
    ID: int
    Group_name: Optional[str] = None
    Curs_name: Optional[str] = None
    Science_name: Optional[str] = None


class GroupResponse(BaseModel):
    ID: int
    Group_name: str


class ScienceResponse(BaseModel):
    ID: int
    Science_name: str


class StatisticsResponse(BaseModel):
    total_students: int
    students_by_group: dict
    students_by_science: dict


def get_db_connection():
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            dbname='ShumovDdb',
            user='postgres',
            password='1234',
            client_encoding='UTF8'
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")


@app.get("/api/students")
async def get_students(group_id: Optional[int] = None, science_id: Optional[int] = None):  # Было group_id: Optional[int]
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = '''
                SELECT 
                    s.id, 
                    s.fio, 
                    g.group_name, 
                    c.curs_name,   
                    sc.science_name,
                    s.group_id,
                    s.curs_id,
                    s.science_id
                FROM students s
                LEFT JOIN groups g ON s.group_id = g.id
                LEFT JOIN curs c ON s.curs_id = c.id
                LEFT JOIN science sc ON s.science_id = sc.id
                WHERE 1=1
            '''
            params = []

            if group_id is not None:
                query += " AND s.group_id = %s"
                params.append(group_id)

            if science_id is not None:
                query += " AND s.science_id = %s"
                params.append(science_id)

            query += " ORDER BY s.id"

            print(f"DEBUG: Executing query with group_id={group_id}, science_id={science_id}")  # Отладка
            cursor.execute(query, params)
            students = cursor.fetchall()
            return [dict(student) for student in students]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        conn.close()


@app.post("/api/students", response_model=dict)
async def create_student(student: StudentBase):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO Students (FIO, Group_id, Curs_id, Science_id) VALUES (%s, %s, %s, %s) RETURNING ID",
                (student.FIO, student.Group_id, student.Curs_id, student.Science_id)
            )
            student_id = cursor.fetchone()[0]
            conn.commit()
            return {"message": "Student created successfully", "id": student_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating student: {str(e)}")
    finally:
        conn.close()


@app.delete("/api/students/{student_id}")
async def delete_student(student_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM Students WHERE id = %s", (student_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Student not found")
            conn.commit()
            return {"message": "Student deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting student: {str(e)}")
    finally:
        conn.close()


@app.get("/api/statistics", response_model=StatisticsResponse)
async def get_statistics():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT COUNT(ID) as total FROM Students")
            total_students = cursor.fetchone()['total']

            cursor.execute('''
                SELECT g.Group_name, COUNT(s.ID) as count 
                FROM Groups g 
                LEFT JOIN Students s ON g.ID = s.Group_id 
                GROUP BY g.ID, g.Group_name
            ''')
            students_by_group = {row['group_name']: row['count'] for row in cursor.fetchall()}

            cursor.execute('''
                SELECT sc.Science_name, COUNT(s.ID) as count 
                FROM Science sc 
                LEFT JOIN Students s ON sc.ID = s.Science_id 
                GROUP BY sc.ID, sc.Science_name
            ''')
            students_by_science = {row['science_name']: row['count'] for row in cursor.fetchall()}

            return {
                "total_students": total_students,
                "students_by_group": students_by_group,
                "students_by_science": students_by_science
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")
    finally:
        conn.close()


@app.get("/api/groups")
async def get_groups():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT ID, Group_name FROM groups ORDER BY Group_name")
            groups = cursor.fetchall()
            return [dict(group) for group in groups]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching groups: {str(e)}")
    finally:
        conn.close()


@app.get("/api/sciences")
async def get_sciences():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT ID, Science_name FROM science ORDER BY Science_name")
            sciences = cursor.fetchall()
            return [dict(science) for science in sciences]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sciences: {str(e)}")
    finally:
        conn.close()


def run_api():
    uvicorn.run(app, host="localhost", port=8000)


if __name__ == "__main__":
    run_api()
