"""
Flask 라우트 정의
"""
from flask import render_template_string, request, jsonify, send_from_directory
import traceback

from config import Config
from downloader import YouTubeDownloader
from separator import AudioSeparator
from templates import HTML_TEMPLATE
from utils import convert_to_wav, load_audio_with_pydub, cleanup_temp_files
from logger import get_logger

logger = get_logger('routes')


def init_routes(app, downloader: YouTubeDownloader, separator: AudioSeparator):
    """
    Flask 라우트 초기화

    Args:
        app: Flask 애플리케이션
        downloader: YouTube 다운로더 인스턴스
        separator: 음원 분리기 인스턴스
    """

    @app.route('/')
    def index():
        """메인 페이지"""
        logger.info("메인 페이지 접속")
        return render_template_string(HTML_TEMPLATE)

    @app.route('/favicon.ico')
    def favicon():
        """favicon 제공"""
        return '''
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
            <text y="80" font-size="80">🎵</text>
        </svg>
        ''', 200, {'Content-Type': 'image/svg+xml'}

    @app.route('/audio/<path:filename>')
    def serve_audio(filename):
        """오디오 파일 서빙"""
        logger.info(f"오디오 파일 요청: {filename}")
        return send_from_directory(Config.OUTPUT_DIR, filename)

    @app.route('/separate', methods=['POST'])
    def separate_audio():
        """음원 분리 API"""
        try:
            data = request.json
            youtube_url = data.get('url')

            if not youtube_url:
                logger.warning("URL이 제공되지 않음")
                return jsonify({'error': 'URL이 제공되지 않았습니다.'}), 400

            logger.info(f"="*50)
            logger.info(f"처리 시작: {youtube_url}")
            logger.info(f"="*50)

            # 1. YouTube 다운로드
            logger.info("1️⃣ YouTube 다운로드 시작")
            audio_file, title = downloader.download_audio(youtube_url)

            # 2. mp4를 wav로 변환
            logger.info("2️⃣ 오디오 파일 변환 시작")
            wav_file = convert_to_wav(
                audio_file,
                str(Config.TEMP_DIR / "temp_audio.wav")
            )

            # 3. 오디오 로드
            logger.info("3️⃣ 오디오 파일 로드 시작")
            wav, sr = load_audio_with_pydub(wav_file)

            # 4. 음원 분리
            logger.info("4️⃣ 음원 분리 시작")
            result = separator.separate(wav, sr, title)

            # 5. 임시 파일 정리
            cleanup_temp_files(wav_file)

            logger.info("="*50)
            logger.info("✅ 모든 작업 완료!")
            logger.info("="*50)

            return jsonify({
                'success': True,
                **result
            })

        except Exception as e:
            logger.error(f"음원 분리 처리 중 오류: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500