import tkinter as tk
from tkinter import messagebox
import os, sys
import cv2
import dlib
import face_recognition
import numpy as np
import math
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from datetime import datetime
import pandas as pd

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://realtimefaceattendancesystem-default-rtdb.firebaseio.com/",
    "storageBucket": "realtimefaceattendancesystem.appspot.com"
})

def start_attendance():
    # Get the entered values from the input fields

    teacher_name = name_entry.get()
    authentication_code = code_entry.get()
    class_name = class_entry.get()
    subject_name = subject_entry.get()
    timer_minutes = timer_entry.get()
    timer_seconds = int(timer_minutes) * 60  # Convert minutes to seconds

    # Check if any field is empty
    if not teacher_name or not authentication_code or not class_name or not timer_minutes or not subject_name:
        messagebox.showerror("Error", "Please fill in all the fields.")
        return

    # Check if timer is integer or not.
    isInt = str(timer_minutes).isdigit()
    if isInt != True:
        messagebox.showerror("Error", "Time should be integer value")
        return

    id = authentication_code
    teacherInfo = db.reference(f'Teachers/{id}').get()
    if not teacherInfo:
        messagebox.showerror("Error", "Code is not valid")
        return

    if teacherInfo['name'] != teacher_name:
        messagebox.showerror("Error", "Teacher name is not matched")
        return

    if teacherInfo['class'] != class_name:
        messagebox.showerror("Error", "Class is not associated to the code provided")
        return

    if teacherInfo['subject'] != subject_name:
        messagebox.showerror("Error", "Subject is not associated to the code provided")
        return

    if timer_minutes == '0':
        messagebox.showerror("Error", "Time should be greater than 0 minutes")
        return


    # Start the timer for the specified duration
    print(f"Attendance started for {timer_minutes} minutes")

    # Remove window
    window.destroy()

    classStudentsId = []

    def downloadExcelSheet():
        # import pandas as pd

        def download_attendance():
            # Retrieve attendance data from the database or any other source
            # Replace this step with your actual data retrieval logic
            attendance_data = []

            for id in classStudentsId:
                studentInfo = db.reference(f'Students/{id}').get()
                name = studentInfo['name']
                major = studentInfo['major']
                dateTime = datetime.now()
                date = dateTime.date().strftime('%Y-%m-%d')
                time = dateTime.time().strftime('%H:%M:%S')
                attendance = studentInfo[f'{teacher_name}_class_attendance']

                info = {'Name': name, 'Major': major, 'Attendance': attendance, 'date': date, 'time': time}
                attendance_data.append(info)


            # Create a DataFrame using the attendance data
            df = pd.DataFrame(attendance_data)

            # Create an Excel writer using pandas
            writer = pd.ExcelWriter(f'{teacher_name}_{class_name}_{subject_name}_attendance.xlsx', engine='xlsxwriter')
            df.to_excel(writer, index=False, sheet_name='Attendance')
            writer.close()

            # Show a success message
            message_label.config(text="Attendance downloaded successfully!")
            window.destroy()

        # Create a Tkinter window
        window = tk.Tk()
        window.title("Attendance System")
        window.geometry("200x100")

        # Create a button to trigger the attendance download
        download_button = tk.Button(window, text="Download Attendance", command=download_attendance)
        download_button.pack(pady=10)

        # Create a label to display download status/messages
        message_label = tk.Label(window, text="")
        message_label.pack()

        # Start the Tkinter event loop
        window.mainloop()

    class FaceRecognition:
        face_locations = []
        face_encodings = []
        face_names = []
        known_face_encodings = []
        known_face_names = []
        process_current_frame = True
        studentIds = []
        studentBranch = []
        markStudentsAttendanceDefault = []

        def __init__(self):
            self.encode_faces()

        def encode_faces(self):
            for image in os.listdir('Images'):
                face_image = face_recognition.load_image_file(f'Images/{image}')
                face_encoding = face_recognition.face_encodings(face_image)[0]

                self.studentIds.append(os.path.splitext(image)[0])  # storing exact ids of student images.)
                self.known_face_encodings.append(face_encoding)  # storing encodings of all faces in local storage.

            # storing name of all students
            for studentId in self.studentIds:
                studentInfo = db.reference(f'Students/{studentId}').get()
                self.known_face_names.append(studentInfo['name'])
                self.studentBranch.append(studentInfo['major'])


            print(self.known_face_names)

        def run_recognition(self):
            video_capture = cv2.VideoCapture(0)
            video_capture.set(3, 1780)
            video_capture.set(4, 1280)

            # In case, webcam does not work then it will throw an error.
            if not video_capture.isOpened():
                sys.exit('Video Source is not found...')

            timer = datetime.now().timestamp() + timer_seconds
            print(datetime.now().timestamp())
            print(timer_seconds)
            counter = 0

            # while datetime.now().timestamp() < timer:
            while counter < timer_seconds:
                # ret will tell if the frames are processed or not.
                # frame are the actual frames itself.
                ret, frame = video_capture.read()

                # Inorder to save process cycles.
                if self.process_current_frame:
                    # re-sizing the frame to 1/4th to save process time.
                    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                    # This syntax convert rbg to rgb.
                    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

                    # find all faces in the current frame
                    self.face_locations = face_recognition.face_locations(rgb_small_frame)
                    # finding all face encodings present in webcam
                    self.face_encodings = face_recognition.face_encodings(rgb_small_frame, self.face_locations)

                    self.face_names = []
                    # taking each encoding of images captures from webcam against all encodings present in array.
                    for face_encoding in self.face_encodings:
                        # getting values of images from local storage in terms of true/false
                        matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)

                        name = 'Unknown'
                        branch = 'Unknown'

                        face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                        best_match_idx = np.argmin(
                            face_distances)  # It will find the min dist idx from face_distances array

                        if matches[best_match_idx]:
                            # print(self.studentIds[best_match_idx])
                            name = self.known_face_names[best_match_idx]
                            branch = self.studentBranch[best_match_idx]

                            id = self.studentIds[best_match_idx]
                            studentInfo = db.reference(f'Students/{id}').get()

                            if studentInfo['exit_time'] == "" and studentInfo['major'] == class_name and \
                                    studentInfo[teacher_name + '_class_attendanceMarked'] == False:

                                ref = db.reference(f'Students/{id}')
                                classStudentsId.append(id)
                                print(studentInfo)
                                studentInfo[teacher_name + '_class_attendanceMarked'] = True
                                self.markStudentsAttendanceDefault.append(id)
                                ref.child(teacher_name + '_class_attendanceMarked').set(
                                    studentInfo[teacher_name + '_class_attendanceMarked'])
                                studentInfo[teacher_name + '_class_attendance'] += 1
                                ref.child(teacher_name + '_class_attendance').set(studentInfo[teacher_name + '_class_attendance'])

                        self.face_names.append(f'{name} ({branch})')

                self.process_current_frame = not self.process_current_frame

                # Display annotations
                for (top, right, bottom, left), name in zip(self.face_locations, self.face_names):
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4

                    # It will create rectangle over faces in webcam
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                    cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)

                cv2.imshow('Face Recognition', frame)

                # Hit 'q' on the keyboard to quit!
                if cv2.waitKey(1) == ord('q'):
                    break

                # print(timer - datetime.now().timestamp())
                counter += 1

            # Release handle to the webcam
            video_capture.release()
            cv2.destroyAllWindows()

            # After Attendance Timer get over, Mark that Teacher's class attendance as false.
            # As, if next class is also taken by same teacher.
            for id in self.markStudentsAttendanceDefault:
                studentInfo = db.reference(f'Students/{id}').get()
                ref = db.reference(f'Students/{id}')
                print('Users are unmarked')
                studentInfo[teacher_name+'_class_attendanceMarked'] = False
                ref.child(teacher_name+'_class_attendanceMarked').set(studentInfo[teacher_name+'_class_attendanceMarked'])

            # Download Excel sheet of attendance
            downloadExcelSheet()

    #  __name__ is dunder name whose value = __main__
    if __name__ == '__main__':
        fr = FaceRecognition()
        fr.run_recognition()


# Create the main window
window = tk.Tk()
window.title("Teacher Attendance")
window.geometry("500x250")

# Create and place the labels and input fields
name_label = tk.Label(window, text="Name:")
name_label.pack()
name_entry = tk.Entry(window)
name_entry.pack()

code_label = tk.Label(window, text="Code:")
code_label.pack()
code_entry = tk.Entry(window, show="*")
code_entry.pack()

class_label = tk.Label(window, text="Class:")
class_label.pack()
class_entry = tk.Entry(window)
class_entry.pack()

subject_label = tk.Label(window, text="Subject:")
subject_label.pack()
subject_entry = tk.Entry(window)
subject_entry.pack()

timer_label = tk.Label(window, text="Timer (minutes):")
timer_label.pack()
timer_entry = tk.Entry(window)
timer_entry.pack()

# Create the start button
start_button = tk.Button(window, text="Start Attendance", command=start_attendance)
start_button.pack()

# Start the Tkinter event loop
window.mainloop()