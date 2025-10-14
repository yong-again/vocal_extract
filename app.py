from flask import Flask, render_template_string, request, jsonify
from pathlib import Path
import os
import torch
from pytubefix import YouTube
from demucs.pretrained import get_model
from demucs.apply import apply_model
from pydub import AudioSegment
import numpy as np
from scipy.io import wavfile

# ==================== 설정 ====================
OUTPUT_DIR = Path("./output")
TEMP_DIR = Path("./temp")
DEMUCS_MODEL = 'htdemucs'
USE_GPU = True
HOST = '0.0.0.0'
PORT = 8888
DEBUG = True

# 디렉토리 생성
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# ==================== Flask 앱 ====================
app = Flask(__name__)

# ==================== HTML 템플릿 ====================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube 음원 분리기 (Demucs)</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 100%;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            text-align: center;
            font-size: 2em;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 0.9em;
        }
        .input-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 600;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        #status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            display: none;
            white-space: pre-line;
        }
        .success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .info {
            background-color: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
            display: none;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .audio-player {
            margin-top: 30px;
            display: none;
        }
        .player-title {
            font-size: 1.2em;
            font-weight: 600;
            color: #333;
            margin-bottom: 15px;
            text-align: center;
        }
        .stem-player {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
        }
        .stem-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        .stem-name {
            font-weight: 600;
            color: #555;
            font-size: 1em;
        }
        .download-btn {
            padding: 5px 15px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 0.9em;
            cursor: pointer;
            text-decoration: none;
            transition: background 0.2s;
        }
        .download-btn:hover {
            background: #5568d3;
        }
        audio {
            width: 100%;
            margin-top: 5px;
        }

        /* 모바일 최적화 */
        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            h1 {
                font-size: 1.5em;
            }
            .stem-header {
                flex-direction: column;
                gap: 10px;
            }
            .download-btn {
                width: 100%;
                text-align: center;
            }
        }

        /* iOS Safari 오디오 플레이어 스타일 */
        audio::-webkit-media-controls-panel {
            background-color: #f8f9fa;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 YouTube 음원 분리기</h1>
        <div class="subtitle">Powered by Demucs AI</div>
        <div class="input-group">
            <label for="youtube_url">YouTube URL</label>
            <input type="text" id="youtube_url" placeholder="https://www.youtube.com/watch?v=..." />
        </div>
        <button onclick="separateAudio()">분리 시작</button>
        <div class="spinner" id="spinner"></div>
        <div id="status"></div>

        <!-- 오디오 플레이어 섹션 -->
        <div class="audio-player" id="audioPlayer">
            <div class="player-title" id="playerTitle"></div>
            <div id="playersContainer"></div>
        </div>
    </div>

    <script>
        let wakeLock = null;

        // Wake Lock 요청 (화면 꺼짐 방지)
        async function requestWakeLock() {
            try {
                if ('wakeLock' in navigator) {
                    wakeLock = await navigator.wakeLock.request('screen');
                    console.log('Wake Lock 활성화');

                    wakeLock.addEventListener('release', () => {
                        console.log('Wake Lock 해제됨');
                    });
                }
            } catch (err) {
                console.log('Wake Lock 오류:', err);
            }
        }

        // 오디오 재생 시 Wake Lock 활성화
        document.addEventListener('play', (e) => {
            if (e.target.tagName === 'AUDIO') {
                requestWakeLock();
            }
        }, true);

        // 오디오 정지 시 Wake Lock 해제
        document.addEventListener('pause', (e) => {
            if (e.target.tagName === 'AUDIO') {
                if (wakeLock !== null) {
                    wakeLock.release().then(() => {
                        wakeLock = null;
                    });
                }
            }
        }, true);

        async function separateAudio() {
            const url = document.getElementById('youtube_url').value;
            const statusDiv = document.getElementById('status');
            const spinner = document.getElementById('spinner');
            const button = document.querySelector('button');
            const audioPlayer = document.getElementById('audioPlayer');

            if (!url) {
                showStatus('YouTube URL을 입력해주세요.', 'error');
                return;
            }

            button.disabled = true;
            spinner.style.display = 'block';
            audioPlayer.style.display = 'none'; // 이전 플레이어 숨기기
            showStatus('처리 중입니다... 잠시만 기다려주세요.\\n(첫 실행 시 모델 다운로드로 시간이 걸릴 수 있습니다)', 'info');

            try {
                const response = await fetch('/separate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ url: url })
                });

                const data = await response.json();

                if (response.ok) {
                    showStatus('✅ 완료! 아래에서 바로 들어보세요.', 'success');
                    createAudioPlayers(data);
                } else {
                    showStatus(`❌ 오류: ${data.error}`, 'error');
                }
            } catch (error) {
                showStatus(`❌ 오류: ${error.message}`, 'error');
            } finally {
                button.disabled = false;
                spinner.style.display = 'none';
            }
        }

        function createAudioPlayers(data) {
            const audioPlayer = document.getElementById('audioPlayer');
            const playerTitle = document.getElementById('playerTitle');
            const playersContainer = document.getElementById('playersContainer');

            // 타이틀 설정
            playerTitle.textContent = data.title;

            // 기존 플레이어 제거
            playersContainer.innerHTML = '';

            // 모바일 안내 메시지
            if (/iPhone|iPad|iPod|Android/i.test(navigator.userAgent)) {
                const mobileNotice = document.createElement('div');
                mobileNotice.style.cssText = `
                    background: #fff3cd;
                    border: 1px solid #ffc107;
                    border-radius: 8px;
                    padding: 12px;
                    margin-bottom: 15px;
                    font-size: 0.9em;
                    color: #856404;
                `;
                mobileNotice.innerHTML = `
                    <strong>📱 모바일 재생 팁:</strong><br>
                    • Chrome/Safari에서 백그라운드 재생이 제한될 수 있습니다<br>
                    • 화면을 켜둔 상태로 사용하세요<br>
                    • 다운로드 후 기본 음악 앱에서 재생하면 더 좋습니다
                `;
                playersContainer.appendChild(mobileNotice);
            }

            // stem 이름 한글 매핑
            const stemNames = {
                'vocals': '🎤 보컬',
                'drums': '🥁 드럼',
                'bass': '🎸 베이스',
                'other': '🎹 기타 악기',
                'accompaniment': '🎵 반주 (전체)'
            };

            // 각 stem에 대한 플레이어 생성
            if (data.stems) {
                for (const [stem, path] of Object.entries(data.stems)) {
                    createStemPlayer(stem, path, stemNames[stem] || stem);
                }
            }

            // 반주 플레이어 추가
            if (data.accompaniment) {
                createStemPlayer('accompaniment', data.accompaniment, stemNames['accompaniment']);
            }

            // 플레이어 표시
            audioPlayer.style.display = 'block';
        }

        function createStemPlayer(stem, filepath, displayName) {
            const playersContainer = document.getElementById('playersContainer');
            const filename = filepath.split('/').pop();

            const playerDiv = document.createElement('div');
            playerDiv.className = 'stem-player';

            playerDiv.innerHTML = `
                <div class="stem-header">
                    <span class="stem-name">${displayName}</span>
                    <a href="/audio/${filename}" download class="download-btn">다운로드</a>
                </div>
                <audio controls preload="metadata" id="audio-${stem}">
                    <source src="/audio/${filename}" type="audio/wav">
                    브라우저가 오디오 재생을 지원하지 않습니다.
                </audio>
            `;

            playersContainer.appendChild(playerDiv);

            // 오디오 엘리먼트 가져오기
            const audioElement = document.getElementById(`audio-${stem}`);

            // iOS Safari에서 오디오 로드 강제
            if (/iPhone|iPad|iPod/i.test(navigator.userAgent)) {
                audioElement.load();
            }

            // Media Session API 설정 (백그라운드 재생 지원)
            if ('mediaSession' in navigator) {
                audioElement.addEventListener('play', () => {
                    updateMediaSession(displayName, filename);
                });

                // 오디오 종료 시 다음 트랙으로 자동 이동 방지
                audioElement.addEventListener('ended', () => {
                    if ('mediaSession' in navigator) {
                        navigator.mediaSession.playbackState = 'paused';
                    }
                });
            }
        }

        function updateMediaSession(title, filename) {
            if ('mediaSession' in navigator) {
                navigator.mediaSession.metadata = new MediaMetadata({
                    title: title,
                    artist: document.getElementById('playerTitle').textContent || 'YouTube 음원 분리기',
                    album: '분리된 음원',
                    artwork: [
                        { src: 'https://via.placeholder.com/96', sizes: '96x96', type: 'image/png' },
                        { src: 'https://via.placeholder.com/128', sizes: '128x128', type: 'image/png' },
                        { src: 'https://via.placeholder.com/192', sizes: '192x192', type: 'image/png' },
                        { src: 'https://via.placeholder.com/256', sizes: '256x256', type: 'image/png' },
                        { src: 'https://via.placeholder.com/384', sizes: '384x384', type: 'image/png' },
                        { src: 'https://via.placeholder.com/512', sizes: '512x512', type: 'image/png' }
                    ]
                });

                // 재생 컨트롤 핸들러 설정
                navigator.mediaSession.setActionHandler('play', () => {
                    const audios = document.querySelectorAll('audio');
                    audios.forEach(audio => {
                        if (!audio.paused) {
                            audio.play();
                        }
                    });
                });

                navigator.mediaSession.setActionHandler('pause', () => {
                    const audios = document.querySelectorAll('audio');
                    audios.forEach(audio => audio.pause());
                });
            }
        }

        function showStatus(message, type) {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = message;
            statusDiv.className = type;
            statusDiv.style.display = 'block';
        }
    </script>
</body>
</html>
'''


# ==================== 유틸리티 함수 ====================
def clean_filename(filename):
    """파일명에서 특수문자 제거"""
    return "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).strip()


def cleanup_temp_files(temp_file):
    """임시 파일 정리"""
    try:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    except Exception as e:
        print(f"정리 중 오류: {e}")


def convert_to_wav(input_file):
    """mp4/m4a 파일을 wav로 변환"""
    try:
        output_file = str(TEMP_DIR / "temp_audio.wav")
        print(f"   파일 변환 중: {Path(input_file).suffix} → wav")

        audio = AudioSegment.from_file(input_file)
        audio.export(output_file, format="wav")

        # 원본 mp4 파일 삭제
        if os.path.exists(input_file):
            os.remove(input_file)

        return output_file
    except Exception as e:
        raise Exception(f"오디오 변환 실패: {str(e)}")


def load_audio_with_pydub(audio_file):
    """pydub를 사용해 오디오 파일을 torch tensor로 로드"""
    try:
        audio = AudioSegment.from_wav(audio_file)
        sr = audio.frame_rate

        # numpy 배열로 변환
        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
        samples = samples / (2 ** 15)  # 정규화

        # 스테레오 처리
        if audio.channels == 2:
            samples = samples.reshape((-1, 2)).T
        else:
            samples = samples.reshape((1, -1))

        wav = torch.from_numpy(samples)
        return wav, sr
    except Exception as e:
        raise Exception(f"오디오 로드 실패: {str(e)}")


def save_audio_scipy(audio_tensor, sample_rate, output_path):
    """torch tensor를 wav 파일로 저장 (scipy 사용)"""
    try:
        # CPU로 이동 및 numpy 변환
        audio_np = audio_tensor.cpu().numpy()

        # (channels, samples) -> (samples, channels)
        if audio_np.ndim == 2:
            audio_np = audio_np.T
        else:
            audio_np = audio_np.reshape(-1, 1)

        # int16으로 변환
        audio_np = np.clip(audio_np, -1.0, 1.0)
        audio_np = (audio_np * 32767).astype(np.int16)

        # wav 파일로 저장
        wavfile.write(str(output_path), sample_rate, audio_np)

    except Exception as e:
        raise Exception(f"오디오 저장 실패: {str(e)}")


# ==================== Demucs 모델 초기화 ====================
print(f"Demucs 모델 로딩 중: {DEMUCS_MODEL}")
demucs_model = get_model(DEMUCS_MODEL)

# 디바이스 설정
if USE_GPU:
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print("✓ MPS (Metal Performance Shaders) 사용")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
        print("✓ CUDA GPU 사용")
    else:
        device = torch.device("cpu")
        print("✓ CPU 사용")
else:
    device = torch.device("cpu")
    print("✓ CPU 사용")

demucs_model.to(device)
print("✓ 모델 로딩 완료!\n")


# ==================== 라우트 ====================
@app.route('/')
def index():
    """메인 페이지"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/audio/<path:filename>')
def serve_audio(filename):
    """오디오 파일 서빙"""
    from flask import send_from_directory
    return send_from_directory(OUTPUT_DIR, filename)


@app.route('/separate', methods=['POST'])
def separate_audio():
    """음원 분리 API"""
    try:
        data = request.json
        youtube_url = data.get('url')

        if not youtube_url:
            return jsonify({'error': 'URL이 제공되지 않았습니다.'}), 400

        print(f"\n{'=' * 50}")
        print(f"처리 시작: {youtube_url}")
        print(f"{'=' * 50}\n")

        # 1. YouTube 다운로드
        print("1️⃣ YouTube에서 다운로드 중...")
        yt = YouTube(youtube_url)
        audio_stream = yt.streams.filter(only_audio=True).first()

        if not audio_stream:
            return jsonify({'error': '오디오 스트림을 찾을 수 없습니다.'}), 400

        temp_file = audio_stream.download(
            output_path=str(TEMP_DIR),
            filename="temp_audio.mp4"
        )
        print(f"✓ 다운로드 완료: {yt.title}\n")

        # 2. mp4를 wav로 변환
        print("2️⃣ 오디오 파일 변환 중...")
        wav_file = convert_to_wav(temp_file)
        print(f"✓ 변환 완료\n")

        # 3. 오디오 로드
        print("3️⃣ 오디오 파일 로드 중...")
        wav, sr = load_audio_with_pydub(wav_file)

        # 스테레오 확인
        if wav.shape[0] == 1:
            wav = wav.repeat(2, 1)

        # 리샘플링
        if sr != demucs_model.samplerate:
            print(f"   리샘플링: {sr} Hz → {demucs_model.samplerate} Hz")
            from torchaudio.transforms import Resample
            resampler = Resample(sr, demucs_model.samplerate)
            wav = resampler(wav)
            sr = demucs_model.samplerate

        print("✓ 오디오 로드 완료\n")

        # 4. 음원 분리
        print("4️⃣ 음원 분리 중... (시간이 걸릴 수 있습니다)")
        wav = wav.unsqueeze(0).to(device)

        with torch.no_grad():
            sources = apply_model(demucs_model, wav, device=device)

        sources = sources.cpu()
        print("✓ 음원 분리 완료\n")

        # 5. 파일 저장
        print("5️⃣ 파일 저장 중...")
        safe_title = clean_filename(yt.title)
        sources_names = demucs_model.sources

        saved_files = {}
        for i, source_name in enumerate(sources_names):
            output_path = OUTPUT_DIR / f"{safe_title}_{source_name}.wav"
            save_audio_scipy(sources[0, i], sr, output_path)
            saved_files[source_name] = str(output_path)
            print(f"   ✓ {source_name}: {output_path.name}")

        # 반주 생성
        accompaniment = torch.zeros_like(sources[0, 0])
        for i, name in enumerate(sources_names):
            if name != 'vocals':
                accompaniment += sources[0, i]

        accompaniment_path = OUTPUT_DIR / f"{safe_title}_accompaniment.wav"
        save_audio_scipy(accompaniment, sr, accompaniment_path)
        print(f"   ✓ accompaniment: {accompaniment_path.name}")

        # 임시 파일 정리
        cleanup_temp_files(wav_file)

        print(f"\n{'=' * 50}")
        print("✅ 모든 작업 완료!")
        print(f"{'=' * 50}\n")

        return jsonify({
            'success': True,
            'title': yt.title,
            'stems': saved_files,
            'accompaniment': str(accompaniment_path)
        })

    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==================== 실행 ====================
if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("🎵 YouTube 음원 분리 웹앱 (Demucs)")
    print(f"모델: {DEMUCS_MODEL}")
    print(f"디바이스: {device}")
    print(f"브라우저에서 http://127.0.0.1:{PORT} 접속")
    print("=" * 50 + "\n")

    app.run(debug=DEBUG, host=HOST, port=PORT)