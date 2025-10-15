"""
YouTube 음원 분리 웹 애플리케이션 (모듈화 버전)

메인 실행 파일
"""
from flask import Flask

from config import Config
from downloader import YouTubeDownloader
from separator import AudioSeparator
from routes import init_routes
from logger import setup_logger, get_logger


def create_app():
    """Flask 애플리케이션 생성 및 설정"""

    # 설정 초기화
    Config.init_directories()

    # 로거 초기화
    logger = setup_logger('youtube-separator', Config.LOG_DIR)

    logger.info("="*50)
    logger.info("🎵 YouTube 음원 분리 웹앱 (Demucs)")
    logger.info("="*50)

    # Flask 앱 생성
    app = Flask(__name__)
    logger.info("Flask 애플리케이션 생성")

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
    logger.info("라우트 등록 완료")

    return app


if __name__ == '__main__':
    app = create_app()
    logger = get_logger()

    # 접속 정보 출력
    logger.info("="*50)
    logger.info(f"모델: {Config.DEMUCS_MODEL}")
    logger.info(f"로그 디렉토리: {Config.LOG_DIR}")
    logger.info(f"브라우저에서 http://127.0.0.1:{Config.PORT} 접속")
    logger.info("="*50)

    # 서버 실행
    logger.info("Flask 서버 시작")
    app.run(
        debug=Config.DEBUG,
        host=Config.HOST,
        port=Config.PORT
    )