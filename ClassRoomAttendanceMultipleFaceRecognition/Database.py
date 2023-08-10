import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://realtimefaceattendancesystem-default-rtdb.firebaseio.com/"
})

ref1 = db.reference('Students')  # Students Database Collection
ref2 = db.reference('Teachers')  # Teachers Database Collection


data1 = {
    "920530":
        {
            "name": "Ritish Shah",
            "major": "ECE",
            "starting_year": 2019,
            "teacher1_class_attendance": 10,
            "teacher1_class_attendanceMarked": False,
            "teacher2_class_attendance": 10,
            "teacher2_class_attendanceMarked": False,
            "year": 4,
            "standing": "B",
            "last_attendance_time": "2023-04-25 00:54:34",
            "exit_time": ""
        },
    "852741":
        {
            "name": "Emily Blunt",
            "major": "CSE",
            "starting_year": 2020,
            "teacher1_class_attendance": 10,
            "teacher1_class_attendanceMarked": False,
            "teacher2_class_attendance": 10,
            "teacher2_class_attendanceMarked": False,
            "year": 3,
            "standing": "G",
            "last_attendance_time": "2023-04-25 00:54:34",
            "exit_time": ""
        },
    "963852":
        {
            "name": "Elon Musk",
            "major": "CSE",
            "starting_year": 2021,
            "teacher1_class_attendance": 10,
            "teacher1_class_attendanceMarked": False,
            "teacher2_class_attendance": 10,
            "teacher2_class_attendanceMarked": False,
            "year": 2,
            "standing": "A",
            "last_attendance_time": "2023-04-25 00:54:34",
            "exit_time": ""
        },
    "893291":
        {
            "name": "Johnny Depp",
            "major": "ECE",
            "starting_year": 2019,
            "teacher1_class_attendance": 10,
            "teacher1_class_attendanceMarked": False,
            "teacher2_class_attendance": 10,
            "teacher2_class_attendanceMarked": False,
            "year": 4,
            "standing": "A",
            "last_attendance_time": "2023-04-25 00:54:34",
            "exit_time": ""
        }
}

data2 = {
    "c1":
        {
            "name": "teacher1",
            "class": "ECE",
            "subject": "ADHOC"
        },
    "c2":
        {
            "name": "teacher1",
            "class": "CSE",
            "subject": "DBMS"
        },
    "c3":
        {
            "name": "teacher2",
            "class": "ECE",
            "subject": "HVPE"
        },
    "c4":
        {
            "name": "teacher2",
            "class": "CSE",
            "subject": "VLSI"
        }
}

# Since data is a json format, so it is treated as dictionary. So, it's unzip by data.items().
for key, value in data1.items():
    ref1.child(key).set(value)

for key, value in data2.items():
    ref2.child(key).set(value)