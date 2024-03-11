import streamlit as st
import requests
from dotenv import load_dotenv
import os

# .env 설정 불러오기
load_dotenv()
api_url = os.getenv("API_URL")

st.title('얼굴 매칭 테스트')

# 처리 방법 선택 콤보박스
processing_method = st.selectbox(
    "처리 방법을 선택하세요:",
    ("1.오픈소스", "2.OpenAI")
)

# 파일 업로더
source_image_file = st.file_uploader("증명사진 이미지 업로드", type=['jpg', 'jpeg', 'png'])
target_image_file = st.file_uploader("단체사진 이미지 업로드", type=['jpg', 'jpeg', 'png'])

if st.button("시작"):
    if source_image_file and target_image_file:
        # 파일의 내용을 읽어서 전송 데이터에 포함시킵니다.
        files = {
            "source_image": (source_image_file.name, source_image_file.getvalue(), 'image/jpeg'),
            "target_image": (target_image_file.name, target_image_file.getvalue(), 'image/jpeg'),
        }
        # 선택된 처리 방법을 파라미터로 추가합니다.
        data = {"processing_method": processing_method}
        try:
            response = requests.post(f"{api_url}/process-images/", files=files, data=data, timeout=60*5)
            if response.status_code == 200:
                st.success("이미지 처리가 완료되었습니다!")
                # 결과 이미지를 사용자에게 보여줍니다.
                st.image(response.content, caption='결과 이미지', use_column_width=True)
            else:
                st.error(f"에러가 발생했습니다: {response.text}")
        except requests.RequestException as e:
            st.error(f"서버에 연결할 수 없습니다: {e}")
    else:
        st.error("모든 필수 필드를 입력해주세요.")
