import os

import streamlit as st
import requests
from dotenv import load_dotenv


# .env 설정 불러오기
load_dotenv()
api_url = os.getenv("API_URL")

st.title('얼굴 매칭 테스트')

source_image_file = st.file_uploader("증명사진 이미지 업로드", type=['jpg', 'jpeg', 'png'])
target_image_file = st.file_uploader("단체사진 이미지 업로드", type=['jpg', 'jpeg', 'png'])

if st.button("시작"):
    if source_image_file and target_image_file:
        files = {
            "source_image": source_image_file,
            "target_image": target_image_file,
        }
        try:
            response = requests.post(f"{api_url}/process-images/", files=files, timeout=10)
            if response.status_code == 200:
                st.success("이미지 처리가 완료되었습니다!")
                st.image(response.content, caption='결과 이미지', use_column_width=True)
            else:
                st.error(f"에러가 발생했습니다: {response.text}")
        except requests.RequestException as e:
            st.error(f"서버에 연결할 수 없습니다: {e}")
    else:
        st.error("모든 필수 필드를 입력해주세요.")
