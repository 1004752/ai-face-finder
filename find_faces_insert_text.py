import face_recognition
import os
import openai
import requests
import base64
import io
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv


# .env 설정 불러오기
load_dotenv()
openai.api_key = os.environ["OPENAI_API_KEY"]
client = openai.OpenAI()

app_path = os.getenv('APP_PATH')

def load_image_and_encode(file_path):
    """이미지를 로드하고 얼굴 인코딩을 반환합니다. 얼굴을 찾지 못한 경우 None을 반환합니다."""
    image = face_recognition.load_image_file(file_path)
    face_encodings = face_recognition.face_encodings(image)
    if face_encodings:
        return image, face_encodings[0]  # 첫 번째 얼굴 인코딩 반환
    else:
        return image, None  # 얼굴 인코딩이 없는 경우 None 반환


def match_opensource(source_image_path, target_image_path, source_encodings, font_path):
    target_image = face_recognition.load_image_file(target_image_path)
    face_locations = face_recognition.face_locations(target_image)

    pil_image = Image.open(target_image_path)
    draw = ImageDraw.Draw(pil_image)
    font = ImageFont.truetype(font_path, 70)

    for index, face_location in enumerate(face_locations):
        # 얼굴 인코딩 추출 시 얼굴 위치 명시적으로 전달
        _, _, bottom, left = face_location
        current_face_location = [face_location]  # 얼굴 위치를 리스트로 래핑

        # 얼굴 위치를 명시적으로 전달하여 얼굴 인코딩을 추출
        current_face_encodings = face_recognition.face_encodings(target_image, known_face_locations=current_face_location)

        if not current_face_encodings:  # 얼굴 인코딩을 찾지 못한 경우
            continue

        match = face_recognition.compare_faces(known_face_encodings=source_encodings,
                                               face_encoding_to_check=current_face_encodings[0])

        if match[0]:
            # 일치하는 얼굴 발견 시 텍스트 그리기
            text = get_pure_filename(source_image_path)
            draw.text((left, bottom + 10), text, fill="red", font=font)

    pil_image.save(f"{app_path}/find_faces/modified_" + os.path.basename(target_image_path))
    # pil_image.show()


def match_openai(source_image_path, target_image_path, font_path):
    target_image = face_recognition.load_image_file(target_image_path)
    face_locations = face_recognition.face_locations(target_image)

    pil_image = Image.open(target_image_path)
    draw = ImageDraw.Draw(pil_image)
    font = ImageFont.truetype(font_path, 70)

    for index, face_location in enumerate(face_locations):
        # 얼굴 인코딩 추출 시 얼굴 위치 명시적으로 전달
        top, right, bottom, left = face_location
        target_face_image_path = f"{app_path}/find_faces/face_{index}.jpg"

        # 추출한 얼굴 이미지 접근
        face_image = target_image[top:bottom, left:right]
        face_pil_image = Image.fromarray(face_image)
        face_pil_image.save(f"{app_path}/find_faces/face_{index}.jpg")

        image_sources = [source_image_path, target_face_image_path]
        prompt = "첫번째 이미지와 두번째 이미지의 사람이 동일한 사람인지 'YES' 또는 'NO'로만 답해주세요."
        print(f"{get_pure_filename(target_face_image_path)} >> ")
        response_text = process_and_display_images(image_sources, prompt)
        if "YES" in response_text:
            # 일치하는 얼굴 발견 시 텍스트 그리기
            text = get_pure_filename(source_image_path)
            draw.text((left, bottom + 10), text, fill="red", font=font)

    pil_image.save(f"{app_path}/find_faces/modified_" + os.path.basename(target_image_path))
    pil_image.show()


def load_and_encode_images(image_sources):
    encoded_images = []
    pil_images = []
    for source in image_sources:
        if source.startswith('http'):  # URL인 경우
            response = requests.get(source)
            image_data = response.content
        else:  # 파일 경로인 경우
            with open(source, "rb") as image_file:
                image_data = image_file.read()

        pil_images.append(Image.open(io.BytesIO(image_data)))
        encoded_images.append(base64.b64encode(image_data).decode('utf-8'))
    return encoded_images, pil_images


# 이미지 경로 또는 URL과 프롬프트를 처리하는 함수
def process_and_display_images(image_sources, prompt):
    # 이미지 로드, base64 인코딩 및 PIL 이미지 객체 생성
    base64_images, pil_images = load_and_encode_images(image_sources)

    # OpenAI에 요청 보내기
    messages = [
        {
            "role": "user",
            "content": [
                           {"type": "text", "text": prompt}
                       ] + [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}} for base64_image in base64_images]
        }
    ]
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=messages,
        max_tokens=1000
    )
    response_text = response.choices[0].message.content
    display_response(pil_images, response.choices[0].message.content)

    return response_text


# 응답결과와 이미지를 출력하기 위한 함수
def display_response(pil_images, response_text):
    # 이미지 로딩 및 서브플롯 생성
    _, axes = plt.subplots(nrows=1, ncols=len(pil_images), figsize=(5 * len(pil_images), 5))
    if len(pil_images) == 1:  # 하나의 이미지인 경우
        axes = [axes]

    # 이미지들 표시
    for i, img in enumerate(pil_images):
        axes[i].imshow(img)
        axes[i].axis('off')  # 축 정보 숨기기
        axes[i].set_title(f'Image #{i+1}')

    # 전체 플롯 표시
    plt.show()

    print(response_text)


def get_pure_filename(file_path):
    """파일 경로에서 폴더와 확장자를 제외한 순수 파일명을 반환합니다."""
    return os.path.splitext(os.path.basename(file_path))[0]


# 메인 로직
def main(source_image_path, target_image_path):
    # source_image_path = "./phase2/man1.jpeg"
    # target_image_path = "./phase2/all_people_org.jpeg"
    font_path = os.getenv('FONT_PATH')
    font_file_name = os.getenv('FONT_FILE_NAME')
    font_path = f"{font_path}/{font_file_name}"  # 실제 폰트 경로로 수정 필요

    source_encodings = []
    _, source_encoding = load_image_and_encode(source_image_path)
    if source_encoding is not None:  # source_encoding이 None이 아닐 때만 처리
        source_encodings.append(source_encoding)

    # 방법1: 오픈소스 이용
    match_opensource(source_image_path, target_image_path, source_encodings, font_path)

    # 방법2: OpenAI 이용
    # match_openai(source_image_path, target_image_path, font_path)
