from django.shortcuts import render, HttpResponse
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
import os
import traceback
import numpy as np
import cv2 
import imutils
from imutils import contours
from imutils.perspective import four_point_transform
from skimage.filters import threshold_local
import pandas as pd
from PIL import Image
import pytesseract
import base64
from base64 import decodestring 
from django.core.files.storage import default_storage
from rest_framework.decorators import api_view

# Create your views here.
@csrf_exempt
def home(request):
    return HttpResponse("Go to extract_date")

@api_view(['POST',])
def extract_date(request):
    if request.method == 'POST':
        base64_string =request.POST.get("base_64_image_content")
        file_name="image.jpeg"
        fh = open(file_name, "wb")
        fh.write(base64.b64decode(base64_string))
        file_url = default_storage.url(file_name)
        img=cv2.imread(file_url)
        ratio = img.shape[0]/500.0
        print("ratio=",ratio)        
        original_img = img.copy()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) # converting image into grayscale
        blurred = cv2.GaussianBlur(gray, (5,5) ,0)   # blurring and finding edges of the image
        edged = cv2.Canny(gray, 75, 200)
        thresh = cv2.threshold(gray, 225, 255, cv2.THRESH_BINARY_INV)[1] # applying threshold to grayscale image
        (cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # finding contours

        # draw contours on image 
        cv2.drawContours(img, cnts, -1, (240, 0, 159), 3)

        H,W = img.shape[:2]
        for cnt in cnts:
            x,y,w,h = cv2.boundingRect(cnt)
            if cv2.contourArea(cnt) > 100 and (0.7 < w/h < 1.3) and (W/4 < x + w//2 < W*3/4) and (H/4 < y + h//2 < H*3/4):
                break

        # creating mask and performing bitwise-op
        mask = np.zeros(img.shape[:2],np.uint8)
        cv2.drawContours(mask, [cnt],-1, 255, -1)
        dst = cv2.bitwise_and(img, img, mask=mask)
        

        #tesseract from program files
        pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
        

        # fetching text from the image and storing it into a text file
        file_text = pytesseract.image_to_string(dst)
        #print(file_text)
        #import datefinder
        import dateutil.parser as dparser
        l = []
        for i in file_text.splitlines():
            try:
                #matches = list(datefinder.find_dates(i))
                matches=dparser.parse(i,fuzzy=True)
                matches=matches.strftime('%Y-%m-%d')
                l.append(matches)
            except Exception as e:
                pass
                
        if len(l)>0:
            date=l[0]
        else:
            date='null'
        print(date)
        fh.close()
        default_storage.delete(file_name)
        return Response ({'date':date})
