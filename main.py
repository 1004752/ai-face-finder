from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
import uvicorn
import shutil
import os
from .find_faces_insert_text import match_opensource, match_openai

app = FastAPI()

app_path = os.getenv('APP_PATH')


@app.post("/process-images/")
async def create_upload_files(
        source_image: UploadFile = File(...),
        target_image: UploadFile = File(...),
        processing_method: str = Form(...)
):
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
        if processing_method == "1.오픈소스":
            # 오픈소스 라이브러리를 사용한 얼굴 매칭 처리
            match_opensource(source_image_path, target_image_path)
        elif processing_method == "2.OpenAI":
            # OpenAI API를 사용한 얼굴 매칭 처리
            match_openai(source_image_path, target_image_path)
        else:
            raise HTTPException(status_code=400, detail="Invalid processing method")

        modified_image_path = f"{app_path}/find_faces/modified_" + os.path.basename(target_image_path)
        return FileResponse(modified_image_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {e}")
    finally:
        # 이 부분에서 임시 폴더와 그 내용을 삭제합니다.
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
