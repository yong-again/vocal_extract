from flask import Flask, render_template, request, jsonify
from config import Config as cfg
from downloader import YouTubeDownloader
from separator import AudioSeparator

app = Flask(__name__)

# 설정 로드
cfg.init_directories()

# downloader 및 separator 인스턴스 생성
downloader = YouTubeDownloader(cfg.TEMP_DIR)
separator = AudioSeparator(output_dir=cfg.OUTPUT_DIR)

@app.route('/')
def index():
    """
    메인 페이지 렌더링
    """
    return render_template('index.html')

@app.route('/seperate', methods=['POST'])
def seperate_audio():
    """
    음원 분리 API 엔드포인트
    """
    try:
        data = request.json
        youtube_url = data.get('url')

        if not youtube_url:
            return jsonify({'error': '유효한 YouTube URL을 제공해주세요.'}), 400

        # 1. Youtube에서 오디오 다운로드
        audio_file, title = downloader.download_audio(youtube_url)

        # 2. 음원 분리
        result = separator.separate(audio_file, title)

        return jsonify({
            'success': True,
            **result
        })

    except Exception as e:
        return jsonify({'error': f'잘못된 요청입니다: {e}'}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("YouTube 음원 분리 웹앱 시작")
    print(f"브라우저에서 http://127.0.0.1:{cfg.PORT} 접속")
    print("=" * 50)
    app.run(debug=cfg.DEBUG, host=cfg.HOST, port=cfg.PORT)