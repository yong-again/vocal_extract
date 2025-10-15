"""
YouTube 음원 분리 웹 애플리케이션 (모듈화 버전)

메인 실행 파일
"""
from flask import Flask

from config import Config
from downloader import YouTubeDownloader
from separator import AudioSeparator
from routes import init_routes


def create_app():
    """Flask 애플리케이션 생성 및 설정"""

    # Flask 앱 생성
    app = Flask(__name__)

    # 설정 초기화
    print("\n" + "=" * 50)
    print("🎵 YouTube 음원 분리 웹앱 (Demucs)")
    print("=" * 50 + "\n")

    Config.init_directories()

    # 다운로더 초기화
    downloader = YouTubeDownloader(Config.TEMP_DIR)

    # 음원 분리기 초기화
    separator = AudioSeparator(
        model_name=Config.DEMUCS_MODEL,
        output_dir=Config.OUTPUT_DIR,
        use_gpu=Config.USE_GPU
    )

    # 라우트 등록
    init_routes(app, downloader, separator)

    return app


if __name__ == '__main__':
    app = create_app()

    # 접속 정보 출력
    print("\n" + "=" * 50)
    print(f"모델: {Config.DEMUCS_MODEL}")
    print(f"브라우저에서 http://127.0.0.1:{Config.PORT} 접속")
    print("=" * 50 + "\n")

    # 서버 실행
    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )