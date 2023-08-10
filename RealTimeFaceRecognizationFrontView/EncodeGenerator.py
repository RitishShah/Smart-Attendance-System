import cv2
import face_recognition
import pickle
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://realtimefaceattendancesystem-default-rtdb.firebaseio.com/",
    "storageBucket": "realtimefaceattendancesystem.appspot.com"
})

# Importing students images into a list.
folderPath = "Images"
modePathList = os.listdir(folderPath)
imgList = []
studentIds = []
imgType = []

for path in modePathList:
    imgList.append(cv2.imread(os.path.join(folderPath, path)))  # storing exact path of each image of Modes
    studentIds.append(os.path.splitext(path)[0])  # storing exact ids of student images.
    # print(os.path.splitext(path)[0])

    imgType.append(os.path.splitext(path)[1])

    fileName = f'{folderPath}/{path}'
    bucket = storage.bucket()
    blob = bucket.blob(fileName)
    blob.upload_from_filename(fileName)

print(studentIds)
print(imgList)

def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # converting bgr to rgb
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)

    return encodeList

print("Encoding Started...")
encodeListKnown = findEncodings(imgList)
encodeListKnownWithIds = [encodeListKnown, studentIds, imgType]
print(encodeListKnown)
print("Encoding Ended")

file = open("EncodeFile.p", 'wb')  # Here, we create a file called EncodeFile.p with wb permission.
pickle.dump(encodeListKnownWithIds, file)  # In file, we dump the encodedImages with their Ids.
file.close()  # Close that file.
print("File Saved")

print(imgType)
