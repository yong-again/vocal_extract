"""
HTML 템플릿 모음
"""

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
            audioPlayer.style.display = 'none';
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

            playerTitle.textContent = data.title;
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

            const stemNames = {
                'vocals': '🎤 보컬',
                'drums': '🥁 드럼',
                'bass': '🎸 베이스',
                'other': '🎹 기타 악기',
                'accompaniment': '🎵 반주 (전체)'
            };

            if (data.stems) {
                for (const [stem, path] of Object.entries(data.stems)) {
                    createStemPlayer(stem, path, stemNames[stem] || stem);
                }
            }

            if (data.accompaniment) {
                createStemPlayer('accompaniment', data.accompaniment, stemNames['accompaniment']);
            }

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

            const audioElement = document.getElementById(`audio-${stem}`);

            // iOS Safari에서 오디오 로드 강제
            if (/iPhone|iPad|iPod/i.test(navigator.userAgent)) {
                audioElement.load();
            }

            // Media Session API 설정
            if ('mediaSession' in navigator) {
                audioElement.addEventListener('play', () => {
                    updateMediaSession(displayName, filename);
                });

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