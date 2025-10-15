# 🎵 YouTube 음원 분리기

AI 기반 YouTube 음원 분리 웹 애플리케이션입니다. 노래에서 보컬, 드럼, 베이스, 기타 악기를 자동으로 분리하고, 웹 브라우저에서 바로 재생하거나 다운로드할 수 있습니다.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![Demucs](https://img.shields.io/badge/Demucs-4.0+-orange.svg)](https://github.com/facebookresearch/demucs)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## ✨ 주요 기능

- 🎤 **보컬 분리** - 노래방 연습이나 커버 제작에 최적
- 🥁 **악기 분리** - 드럼, 베이스, 기타 악기 개별 추출
- 🎹 **반주 생성** - 보컬을 제외한 전체 반주 자동 생성
- 🌐 **웹 재생** - 브라우저에서 바로 듣기 (모바일 지원)
- 💾 **고음질 다운로드** - WAV 형식으로 각 파트별 저장
- 📱 **모바일 최적화** - 백그라운드 재생 및 잠금화면 제어
- ⚡ **GPU 가속** - M1/M2/M3 Mac 및 NVIDIA GPU 지원


## 🚀 빠른 시작

### 필수 요구사항

- Python 3.8 이상
- ffmpeg
- 최소 8GB RAM (16GB 권장)
- 저장 공간 약 2GB (모델 + 출력 파일)

### 설치

```bash
# 1. 저장소 클론
git clone https://github.com/YOUR_USERNAME/youtube-separator.git
cd youtube-separator

# 2. 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# 3. 패키지 설치
pip install -r requirements.txt

# 4. ffmpeg 설치
# Mac
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# https://ffmpeg.org/download.html 에서 다운로드
```

### 실행

```bash
python app.py
```

브라우저에서 `http://127.0.0.1:PORT` 접속

## 📖 사용 방법

### 1. 기본 사용법

1. YouTube에서 원하는 노래 URL 복사
2. 웹사이트에 URL 붙여넣기
3. "분리 시작" 버튼 클릭
4. 완료 후 웹에서 바로 재생 또는 다운로드


## 🛠️ 기술 스택

### Backend
- **Flask** - 웹 프레임워크
- **Demucs** - Facebook Research의 음원 분리 AI 모델
- **PyTorch** - 딥러닝 프레임워크
- **PyTubeFix** - YouTube 다운로드
- **Pydub** - 오디오 처리
- **SciPy** - WAV 파일 저장

### Frontend
- **HTML5** - 구조
- **CSS3** - 스타일링 (반응형 디자인)
- **JavaScript** - 인터랙션
- **Media Session API** - 백그라운드 재생 제어
- **Wake Lock API** - 화면 꺼짐 방지

## 📁 프로젝트 구조

```
vocal-separator/
├── app.py              # 메인 실행 파일
├── config.py           # 설정
├── utils.py            # 유틸리티 함수
├── downloader.py       # YouTube 다운로드
├── separator.py        # 음원 분리
├── routes.py           # Flask 라우트
├── templates.py        # HTML 템플릿 
├── requirements.txt
├── .gitignore
├── README.md
├── start.sh
├── output/               # 분리된 음원 저장 (자동 생성)
│   ├── [곡명]_vocals.wav
│   ├── [곡명]_drums.wav
│   ├── [곡명]_bass.wav
│   ├── [곡명]_other.wav
│   └── [곡명]_accompaniment.wav
└── temp/                 # 임시 파일 (자동 생성)
```

## ⚙️ 설정

### GPU 사용

**M1/M2/M3 Mac:**
```python
# app.py에서 (기본값)
USE_GPU = True  # MPS (Metal) 자동 사용
```

**NVIDIA GPU:**
```python
USE_GPU = True  # CUDA 자동 감지
```

**CPU만 사용:**
```python
USE_GPU = False  # 느리지만 호환성 높음
```

### 모델 변경

더 나은 음질을 원한다면:

```python
# app.py에서
DEMUCS_MODEL = 'htdemucs'     # 기본 (빠름)
DEMUCS_MODEL = 'htdemucs_ft'  # Fine-tuned (고품질, 느림)
DEMUCS_MODEL = 'htdemucs_6s'  # 6개 stems (guitar, piano 추가)
```

### 포트 변경

```python
# app.py에서
PORT = 5000  # 원하는 포트로 변경
```

## 🔧 문제 해결

### "모델 다운로드 중" 메시지가 오래 나와요

첫 실행 시 약 300MB 모델이 자동 다운로드됩니다. 2-3분 정도 기다려주세요.

```bash
# 수동으로 미리 다운로드
python -c "from demucs.pretrained import get_model; get_model('htdemucs')"
```

### 처리가 너무 느려요

**원인:** CPU만 사용 중
**해결:**
- GPU 사용 확인: `USE_GPU = True`
- M1 Mac: MPS 지원 PyTorch 설치
```bash
pip install torch torchvision torchaudio
```

**처리 시간 예상:**
- GPU (MPS/CUDA): 1-3분
- CPU: 5-15분

### 메모리 부족 오류

**원인:** 긴 영상 처리 시 메모리 부족
**해결:**
- 짧은 노래(3-5분)로 테스트
- 불필요한 앱 종료
- 더 많은 RAM 필요

### 모바일에서 백그라운드 재생이 안 돼요

**Android Chrome:**
- 정상 작동함
- 알림창에서 제어 가능

**iOS Safari:**
- 백그라운드 재생 제한적
- 해결: 다운로드 후 기본 음악 앱에서 재생

**권장:**
- 다운로드 버튼 → 파일 앱 → 음악 앱으로 재생

### "Couldn't find appropriate backend" 오류

**원인:** torchaudio 백엔드 문제
**해결:**
```bash
# ffmpeg 재설치
brew reinstall ffmpeg

# 또는 최신 torchaudio
pip install --upgrade torchaudio
```

### ngrok 무료 플랜 제한

- **2시간 후 종료**: 재시작 필요 (URL 변경됨)
- **동시 접속 제한**: 여러 명 사용 시 느려짐
- **해결**: 유료 플랜 ($8/월) 또는 각자 설치

## 📊 성능 최적화

### 처리 속도 비교

| 환경 | 3분 노래 처리 시간 |
|-----|-------------|
| M1 Mac (MPS) | 5-10분       |
| NVIDIA RTX 3060 | 1-2분        |
| Intel i7 (CPU) | 8-12분       |
| 클라우드 (CPU) | 10-15분      |

### 메모리 사용량

| 작업 | 메모리 사용 |
|-----|-----------|
| 모델 로딩 | 1-2GB |
| 3분 노래 처리 | 3-4GB |
| 10분 노래 처리 | 6-8GB |

## 🌐 ngrok 설정

### 1. 설치

```bash
# Mac
brew install ngrok

# 또는 직접 다운로드
# https://ngrok.com/download
```

### 2. 인증

```bash
# ngrok.com에서 회원가입 후 토큰 받기
ngrok config add-authtoken YOUR_TOKEN
```

### 3. 실행

```bash
# 터미널 1
python app_2.py

# 터미널 2
ngrok http your_PORT
```

### 4. URL 공유

ngrok이 생성한 `https://` URL을 복사해서 친구에게 공유하세요!

## 📱 모바일 지원

### 지원 기능

- ✅ 터치 최적화 UI
- ✅ 반응형 디자인
- ✅ 백그라운드 재생 (Android)
- ✅ 잠금화면 제어
- ✅ Media Session API
- ✅ Wake Lock API

### 브라우저 호환성

| 브라우저 | 재생 | 백그라운드 | 추천 |
|---------|------|----------|------|
| Chrome (Android) | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| Safari (iOS) | ✅ | ⚠️ | ⭐⭐⭐⭐ |
| Samsung Internet | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| Firefox Mobile | ✅ | ✅ | ⭐⭐⭐⭐ |

## 📝 출력 형식

### 파일 목록

모든 파일은 `output/` 폴더에 WAV 형식으로 저장됩니다:

```
output/
├── [곡명]_vocals.wav         # 보컬만 (노래방용)
├── [곡명]_drums.wav          # 드럼
├── [곡명]_bass.wav           # 베이스
├── [곡명]_other.wav          # 기타 악기
└── [곡명]_accompaniment.wav # 반주 전체
```

### 음질 사양

- **샘플레이트**: 44.1kHz
- **비트뎃스**: 16-bit
- **채널**: 스테레오 (2ch)
- **형식**: WAV (무손실)

## 🎯 사용 사례

### 1. 노래방 연습
- 보컬 트랙으로 음정 연습
- 반주 트랙으로 노래방 연습

### 2. 커버 제작
- 보컬 제거 후 자신의 목소리로 커버
- 악기만 분리해서 리믹스

### 3. 악기 연습
- 드럼 트랙으로 드럼 연습
- 베이스 트랙으로 베이스 카피

### 4. 음악 교육
- 각 파트별로 들으며 분석
- 편곡 및 작곡 공부

### 5. DJ/프로듀서
- 아카펠라 추출
- 인스트루멘탈 제작

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🙏 크레딧

- [Demucs](https://github.com/facebookresearch/demucs) - Facebook Research의 음원 분리 AI
- [PyTubeFix](https://github.com/JuanBindez/pytubefix) - YouTube 다운로드 라이브러리
- [Flask](https://flask.palletsprojects.com/) - Python 웹 프레임워크

## ⚠️ 면책 조항

이 도구는 교육 및 개인 사용 목적으로만 제공됩니다. 저작권이 있는 음악을 다운로드하거나 분리할 때는 해당 국가의 법률을 준수하세요. 개발자는 이 도구의 남용에 대해 책임지지 않습니다.

## 📧 문의

질문이나 제안사항이 있으시면 [Issues](https://github.com/yong-again/youtube-separator/issues)를 열어주세요.

---

⭐ 이 프로젝트가 유용하다면 Star를 눌러주세요!

Made with ❤️ by yong-again