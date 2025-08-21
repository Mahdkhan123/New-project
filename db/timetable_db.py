import tkinter.messagebox as messagebox
import sqlite3
import os

# Ensure working directory is DB folder
os.chdir(os.path.dirname(__file__))

# New: use separate DB files per shift
_DB_FILES = {
    "Morning": os.path.join(os.path.dirname(__file__), 'timetable_morning.db'),
    "Evening": os.path.join(os.path.dirname(__file__), 'timetable_evening.db')
}
_conns = {}

# Move/create table helper before connection creation so it can be invoked immediately
def _create_tables_on_conn(conn_local):
    c = conn_local.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            class_section_id INTEGER NOT NULL,
            semester TEXT NOT NULL,
            shift TEXT NOT NULL,
            FOREIGN KEY (teacher_id) REFERENCES teachers (id),
            FOREIGN KEY (course_id) REFERENCES courses (id),
            FOREIGN KEY (room_id) REFERENCES rooms (id),
            FOREIGN KEY (class_section_id) REFERENCES class_sections (id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT NOT NULL,
            indicators TEXT,
            teacher_id INTEGER NOT NULL, 
            FOREIGN KEY (teacher_id) REFERENCES teachers (id),
            UNIQUE(name, code, teacher_id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name INTEGER NOT NULL UNIQUE 
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS class_sections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            semester TEXT NOT NULL,
            shift TEXT NOT NULL,
            UNIQUE(name, semester, shift)   
        )
    ''')
    conn_local.commit()

def _ensure_conn(shift):
    if shift not in _DB_FILES:
        shift = "Morning"
    if shift not in _conns:
        path = _DB_FILES[shift]
        conn_local = sqlite3.connect(path, check_same_thread=False)
        conn_local.execute('PRAGMA foreign_keys = ON')
        # Ensure schema exists immediately for this DB
        _create_tables_on_conn(conn_local)
        _conns[shift] = conn_local
    return _conns[shift]

# Backwards-compatible default conn (Morning)
conn = _ensure_conn("Morning")

def get_conn_for_shift(shift):
    """
    Returns the database connection for the given shift.
    Defaults to 'Morning' if shift is not recognized.
    """
    return _ensure_conn(shift)

def fetch_id_from_name(table, name, **kwargs):
    cur = None
    try:
        # determine shift for operations that require a specific DB
        shift = kwargs.get("shift", "Morning")
        conn_local = get_conn_for_shift(shift)
        cur = conn_local.cursor()

        if table == "rooms":
            try:
                room_name_val = int(name)
                if room_name_val <= 0:
                    raise ValueError
                query = "SELECT id FROM rooms WHERE name = ?"
                params = (room_name_val,)
            except ValueError:
                messagebox.showerror("Invalid Room", "Room must be a positive integer.")
                return None
        elif table == "teachers":
            query = "SELECT id FROM teachers WHERE name = ?"
            params = (name,)
        elif table == "courses":
            teacher_id = kwargs.get("teacher_id")
            code = kwargs.get("code")
            indicators = kwargs.get("indicators", "") 
            if not teacher_id or not code:
                messagebox.showerror("Missing Data", "Teacher ID and Course Code are required for courses.")
                return None
            query = "SELECT id FROM courses WHERE name = ? AND teacher_id = ? AND code = ?"
            params = (name, teacher_id, code)
        elif table == "class_sections":
            semester_text = kwargs.get("semester")
            shift_text = kwargs.get("shift", shift)
            if semester_text is None or not shift_text:
                messagebox.showerror("Missing Data", "Semester (as text) and Shift are required for class sections.")
                return None
            query = "SELECT id FROM class_sections WHERE name = ? AND semester = ? AND shift = ?"
            params = (name, semester_text, shift_text)
        else:
            messagebox.showerror("Error", f"Unknown table: {table}")
            return None

        cur.execute(query, params)
        result = cur.fetchone()

        if result:
            return result[0]
        else:
            # Insert the record into the DB for the given shift (conn_local)
            if table == "teachers":
                cur.execute("INSERT INTO teachers (name) VALUES (?)", (name,))
            elif table == "courses":
                cur.execute("INSERT INTO courses (name, teacher_id, code, indicators) VALUES (?, ?, ?, ?)", 
                            (name, teacher_id, code, indicators))
            elif table == "rooms":
                cur.execute("INSERT INTO rooms (name) VALUES (?)", (int(name),))
            elif table == "class_sections":
                cur.execute("INSERT INTO class_sections (name, semester, shift) VALUES (?, ?, ?)", 
                            (name, semester_text, shift_text))
            
            conn_local.commit()
            return cur.lastrowid

    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Failed to fetch or create ID in {table} for '{name}': {e}")
        return None
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred in fetch_id_from_name for {table} '{name}': {e}")
        return None

def load_timetable(shift, semester_label=None):
    cur = get_conn_for_shift(shift).cursor()
    
    query = '''
        SELECT 
            t.id AS entry_id,
            t.teacher_id,
            teachers.name AS teacher_name, 
            t.course_id,
            courses.name AS course_name,
            courses.code AS course_code,
            courses.indicators AS course_indicators,
            t.room_id,
            rooms.name AS room_name, 
            t.class_section_id,
            class_sections.name AS class_section_name, 
            t.semester,
            t.shift
        FROM timetable t
        JOIN teachers ON t.teacher_id = teachers.id
        JOIN courses ON t.course_id = courses.id
        JOIN rooms ON t.room_id = rooms.id
        JOIN class_sections ON t.class_section_id = class_sections.id
        WHERE t.shift = ? 
    '''
    params_list = [shift]
    
    if semester_label:
        query += ' AND t.semester = ?'
        params_list.append(semester_label)
    
    cur.execute(query, tuple(params_list))
    
    columns = [
        'entry_id', 'teacher_id', 'teacher_name', 
        'course_id', 'course_name', 'course_code', 'course_indicators',
        'room_id', 'room_name', 
        'class_section_id', 'class_section_name', 
        'semester', 'shift'
    ]
    
    return [dict(zip(columns, row)) for row in cur.fetchall()]

def load_timetable_for_ga(shift):
    cur = get_conn_for_shift(shift).cursor()
    query = """
        SELECT 
            tt.teacher_id, tt.course_id, tt.room_id, tt.class_section_id, 
            tt.semester,
            tt.shift,
            c.name as course_name, c.code as course_code, c.indicators as course_indicators,
            r.name as room_name,
            t.name as teacher_name,
            cs.name as class_section_name
        FROM timetable tt
        JOIN courses c ON tt.course_id = c.id
        JOIN rooms r ON tt.room_id = r.id
        JOIN teachers t ON tt.teacher_id = t.id
        JOIN class_sections cs ON tt.class_section_id = cs.id
        WHERE tt.shift = ? 
    """
    params = [shift]
    
    cur.execute(query, tuple(params))
    
    columns = [
        'teacher_id', 'course_id', 'room_id', 'class_section_id', 
        'semester', 'shift', 
        'course_name', 'course_code', 'course_indicators', 
        'room_name', 'teacher_name', 'class_section_name'
    ]
    results = [dict(zip(columns, row)) for row in cur.fetchall()]
    print(f"Loaded {len(results)} entries for GA for shift: {shift}")
    return results

def delete_timetable_entry_from_db(entry_id, shift=None):
    try:
        conn_local = get_conn_for_shift(shift or "Morning")
        cur = conn_local.cursor()
        cur.execute("DELETE FROM timetable WHERE id = ?", (entry_id,))
        conn_local.commit()
        return cur.rowcount > 0
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", f"Failed to delete entry from database: {e}")
        return False

def get_all_class_sections():
    """
    Return combined list of (semester, name, shift) from both DBs.
    """
    combined = []
    for s in _DB_FILES.keys():
        cur = get_conn_for_shift(s).cursor()
        cur.execute("SELECT DISTINCT semester, name, shift FROM class_sections")
        combined.extend(cur.fetchall())
    return combined

def get_all_course_entries():
    """
    Return combined list of (semester, class_section_name, shift, code, course_name)
    joined from timetable->courses->class_sections across both DBs.
    """
    combined = []
    query = ("SELECT cs.semester, cs.name, cs.shift, c.code, c.name FROM courses c "
             "JOIN timetable t ON t.course_id = c.id "
             "JOIN class_sections cs ON t.class_section_id = cs.id")
    for s in _DB_FILES.keys():
        cur = get_conn_for_shift(s).cursor()
        try:
            cur.execute(query)
            combined.extend(cur.fetchall())
        except Exception:
            # ignore empty or missing joins
            pass
    return combined

def close_db():
    for c in list(_conns.values()):
        try:
            c.close()
        except:
            pass
    _conns.clear()
    # reset default
    global conn
    conn = _ensure_conn("Morning")