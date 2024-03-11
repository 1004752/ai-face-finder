from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import uvicorn
import shutil
import os
from .find_faces_insert_text import main as process_images  # 이 부분은 실제 구현에 따라 달라질 수 있음

app = FastAPI()

app_path = os.getenv('APP_PATH')


@app.post("/process-images/")
async def create_upload_files(source_image: UploadFile = File(...), target_image: UploadFile = File(...)):
    temp_dir = f"{app_path}/temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    source_image_path = os.path.join(temp_dir, source_image.filename)
    target_image_path = os.path.join(temp_dir, target_image.filename)

    with open(source_image_path, "wb") as buffer:
        shutil.copyfileobj(source_image.file, buffer)
    with open(target_image_path, "wb") as buffer:
        shutil.copyfileobj(target_image.file, buffer)

    try:
        process_images(source_image_path, target_image_path)
        modified_image_path = f"{app_path}/find_faces/modified_" + os.path.basename(target_image_path)
        return FileResponse(modified_image_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {e}")
    finally:
        # 이 부분에서 임시 폴더와 그 내용을 삭제합니다.
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
