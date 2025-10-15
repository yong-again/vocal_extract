"""
애플리케이션 설정
"""
from pathlib import Path


class Config:
    """애플리케이션 설정 클래스"""

    # 디렉토리 설정
    OUTPUT_DIR = Path("./output")
    TEMP_DIR = Path("./temp")

    # Demucs 모델 설정
    DEMUCS_MODEL = 'htdemucs'  # htdemucs, htdemucs_ft, htdemucs_6s

    # GPU 설정
    USE_GPU = True  # M1 Mac의 경우 MPS 사용

    # Flask 서버 설정
    HOST = '0.0.0.0'
    PORT = 8888
    DEBUG = True

    @classmethod
    def init_directories(cls):
        """필요한 디렉토리 생성"""
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        cls.TEMP_DIR.mkdir(exist_ok=True)
        print(f"✓ 출력 폴더: {cls.OUTPUT_DIR}")
        print(f"✓ 임시 폴더: {cls.TEMP_DIR}")