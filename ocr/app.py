import easyocr
import numpy as np
import cv2
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

app = FastAPI()

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'], gpu=True)  

@app.post("/extract/")
async def extract_text(image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)  
        result = reader.readtext(img, detail=0)  

        text = ''.join(result).replace(' ', '').strip()
        extracted_text = text if text.isdigit() and len(text) == 3 and int(text) > 99 else None  

        return JSONResponse(content={"text": extracted_text}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
