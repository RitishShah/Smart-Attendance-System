import os
import pickle
import numpy as np
import cv2
import face_recognition
import cvzone
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from datetime import datetime, time

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://realtimefaceattendancesystem-default-rtdb.firebaseio.com/",
    "storageBucket": "realtimefaceattendancesystem.appspot.com"
})

bucket = storage.bucket()

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(3, 680)
cap.set(4, 480)

imgBackground = cv2.imread("Resources/background.png")

# Importing the Modes images into a list.
folderModePath = "Resources/Modes"
modePathList = os.listdir(folderModePath)
imgModeList = []

for path in modePathList:
    imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))  # storing exact path of each image of Modes

# Load the encoded files.
print("Loading Encoded Files")
file = open('EncodeFile.p', 'rb')  # Loading the Encoded Images with rb permission.
encodeListKnownWithIds = pickle.load(file)  # Using pickle, we load the encoded files.
file.close()  # Closing the file.
encodeListKnown, studentIds, imgType = encodeListKnownWithIds  # Get values for (encodeListKnown, studentIds, imgType).
# print(studentIds)
print("Encoded Files Loaded")

modeType = 0  # get mode from Modes Folder
imgTypeIdx = -1  # get idx of image from Images Folder
counter = 0  # to run counter in 1 sec to fetch user details from db.
id = -1  # get student id matched from live image
imgStudent = []

while True:
    success, img = cap.read()

    imgSmall = cv2.resize(img, (0, 0), None, 0.25, 0.25)  # Resizing the img to its 1/4th size.
    imgSmall = cv2.cvtColor(imgSmall, cv2.COLOR_BGR2RGB)  # converting bgr to rbg as face_recognition uses rgb.

    faceCurrFrame = face_recognition.face_locations(imgSmall)  # Gives diff locations of our live image.
    encodeCurrFrame = face_recognition.face_encodings(imgSmall, faceCurrFrame)  # Gives encodings of diff locations.

    imgBackground[162:162+480, 55:55+640] = img  # Here, we set webcam inside the background image.
    imgBackground[44:44+633, 808:808+414] = imgModeList[modeType]  # Here, we set modes inside the background image.

    if faceCurrFrame:

        # zip allows to iterate over both arrays at same time.
        for encodeFace, faceLoc in zip(encodeCurrFrame, faceCurrFrame):
            # It compares live image with the encoded images present in image Folder
            # And present in form of boolean value array associated to each image in image Folder
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            # It finds the face distance of live image with images present in image Folder.
            # Lower the distance, Better the face match.
            # And present in form of float value array associated to each image in image Folder.
            faceDist = face_recognition.face_distance(encodeListKnown, encodeFace)

            print("Matches", matches)
            print("FaceDist", faceDist)

            matchIndex = np.argmin(faceDist)  # Finds the min. value index from faceDist array.

            print(matchIndex)

            if matches[matchIndex]:
                print("Face Detected Successfully")
                print(studentIds[matchIndex])
                # If we find match, then we'll put rectangle box around face.
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1*4, x2*4, y2*4, x1*4  # since, we reduce the size of image above.
                bbox = 55+x1, 162+y1, x2-x1, y2-y1  # Set values for boundary box of rectangle.
                imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)

                id = studentIds[matchIndex]  # Matched student Id
                imgTypeIdx = matchIndex  # Matched student idx of image

                if counter == 0:
                    counter = 1
                    # Initially, mode is 0 which shows active in web cam, When user matched then changed it to mode-2's idx
                    modeType = 1

            else:
                modeType = 4
                imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

        #  counter should run at least once
        if counter != 0:

            #  When counter runs for one time then change it's mode
            if counter == 1:
                # get the data
                studentInfo = db.reference(f'Students/{id}').get()
                print(studentInfo)
                # get image from storage
                blob = bucket.get_blob(f'Images/{id}{imgType[imgTypeIdx]}')
                print(f'Images/{id}{imgType[imgTypeIdx]}')

                # convert buffer into 1-d array
                array = np.frombuffer(blob.download_as_string(), np.uint8)
                # convert image color from bgra to bgr
                imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)

                # converting string format of datetime into object format.
                # dateTimeObject = datetime.strptime(studentInfo['last_attendance_time'],
                #                                   "%Y-%m-%d %H:%M:%S")
                #
                # secondsElapsed = (datetime.now() - dateTimeObject).total_seconds()
                # print(secondsElapsed)

                entryTime = time(8, 0)
                exitTime = time(23, 30)

                if entryTime <= datetime.now().time() <= exitTime:
                    # Update data of attendance, whenever we place live image over webcam
                    ref = db.reference(f'Students/{id}')
                    print('Entry Time is noted')
                    ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    ref.child('exit_time').set("")

                else:
                    modeType = 3
                    counter = 0
                    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

            if modeType != 3:

                if 20 < counter <= 30:
                    modeType = 2
                    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                if counter <= 20:
                    # Inorder to set name at center, calculate offset for starting pos. of name.
                    (w, h), _ = cv2.getTextSize(studentInfo['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                    offset = (414 - w)//2  # // -> Floor Division

                    # show name
                    cv2.putText(imgBackground, str(studentInfo['name']), (808+offset, 445),
                                cv2.FONT_HERSHEY_COMPLEX,1,(50, 50, 50), 1)

                    # Show major
                    cv2.putText(imgBackground, str(studentInfo['major']), (1006, 550),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 225, 225), 1)

                    # Show id
                    cv2.putText(imgBackground, str(id), (1006, 493),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 225, 225), 1)

                    # Show current course
                    cv2.putText(imgBackground, str(studentInfo['year']), (1025, 625),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)

                    # show starting year
                    cv2.putText(imgBackground, str(studentInfo['starting_year']), (1125, 625),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)

                    cv2.putText(imgBackground, str(studentInfo['standing']), (910, 625),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)

                    # put the image of student on mode 2
                    imgBackground[175:175+216, 909:909+216] = imgStudent


                if counter > 30:
                    modeType = 3
                    studentInfo = []
                    imgStudent = []
                    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

                counter+= 1

    else:
        modeType = 0
        counter = 0

    # Hit 'q' on the keyboard to quit!
    if cv2.waitKey(1) == ord('q'):
        break

    # cv2.imshow("Webcam", img)
    cv2.imshow("Face Attendance", imgBackground)  # It will show webcam image.
    cv2.waitKey(1)
