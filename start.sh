#!/bin/bash

# YouTube 음원 분리기 실행 스크립트
# 사용법: ./start.sh [옵션]
#   --ngrok    : ngrok과 함께 실행 (원격 공유)
#   --local    : 로컬만 실행 (기본값)
#   --help     : 도움말

set -e  # 에러 발생 시 즉시 종료

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 배너 출력
print_banner() {
    echo -e "${MAGENTA}"
    echo "╔════════════════════════════════════════════╗"
    echo "║     🎵 YouTube 음원 분리기 v1.0               ║"
    echo "║     Powered by Demucs AI                   ║"
    echo "╚════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 성공 메시지
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# 에러 메시지
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# 경고 메시지
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 정보 메시지
print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

# 도움말
show_help() {
    echo "사용법: ./start.sh [옵션]"
    echo ""
    echo "옵션:"
    echo "  --local     로컬에서만 실행 (기본값)"
    echo "  --ngrok     ngrok과 함께 실행 (원격 공유)"
    echo "  --help      이 도움말 표시"
    echo ""
    echo "예시:"
    echo "  ./start.sh              # 로컬 실행"
    echo "  ./start.sh --ngrok      # ngrok과 함께 실행"
    exit 0
}

# 옵션 파싱
USE_NGROK=false
case "$1" in
    --ngrok)
        USE_NGROK=true
        ;;
    --local)
        USE_NGROK=false
        ;;
    --help)
        show_help
        ;;
    "")
        USE_NGROK=false
        ;;
    *)
        print_error "알 수 없는 옵션: $1"
        show_help
        ;;
esac

# 종료 시 정리 함수
cleanup() {
    echo ""
    print_info "종료 중..."

    # Flask 프로세스 종료
    if [ ! -z "$FLASK_PID" ]; then
        kill $FLASK_PID 2>/dev/null || true
        print_success "Flask 앱 종료"
    fi

    # ngrok 프로세스 종료
    if [ ! -z "$NGROK_PID" ]; then
        kill $NGROK_PID 2>/dev/null || true
        print_success "ngrok 종료"
    fi

    echo ""
    print_info "안전하게 종료되었습니다. 다음에 또 만나요! 👋"
    exit 0
}

# SIGINT, SIGTERM 시그널 처리
trap cleanup SIGINT SIGTERM

# 메인 실행
main() {
    print_banner

    # 1. Python 버전 확인
    print_info "환경 확인 중..."
    if ! command -v python3 &> /dev/null; then
        print_error "Python3이 설치되어 있지 않습니다."
        print_info "설치: brew install python3"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python ${PYTHON_VERSION} 발견"

    # 2. 가상환경 확인 및 활성화
    if [ ! -d ".venv" ]; then
        print_warning "가상환경이 없습니다. 생성하시겠습니까? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            print_info "가상환경 생성 중..."
            python3 -m venv venv
            print_success "가상환경 생성 완료"
        else
            print_error "가상환경이 필요합니다."
            exit 1
        fi
    fi

    print_info "가상환경 활성화 중..."
    source .venv/bin/activate
    print_success "가상환경 활성화 완료"

    # 3. 패키지 설치 확인
    print_info "패키지 확인 중..."
    if [ -f "requirements.txt" ]; then
        # Flask가 설치되어 있는지 확인
        if ! python3 -c "import flask" 2>/dev/null; then
            print_warning "필요한 패키지를 설치하시겠습니까? (y/n)"
            read -r response
            if [[ "$response" =~ ^[Yy]$ ]]; then
                print_info "패키지 설치 중... (시간이 걸릴 수 있습니다)"
                pip install -r requirements.txt
                print_success "패키지 설치 완료"
            else
                print_error "필요한 패키지가 설치되어 있지 않습니다."
                exit 1
            fi
        else
            print_success "필요한 패키지 확인 완료"
        fi
    else
        print_warning "requirements.txt 파일이 없습니다."
    fi

    # 4. ffmpeg 확인
    if ! command -v ffmpeg &> /dev/null; then
        print_warning "ffmpeg가 설치되어 있지 않습니다."
        print_info "설치: brew install ffmpeg"
        print_info "계속하시겠습니까? (y/n)"
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "ffmpeg 확인 완료"
    fi

    # 5. 출력 폴더 생성
    mkdir -p output temp
    print_success "출력 폴더 준비 완료"

    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # 6. Flask 앱 실행
    print_info "Flask 앱 실행 중..."
    python3 app.py &
    FLASK_PID=$!

    # Flask가 시작될 때까지 대기
    sleep 3

    # Flask가 정상 실행되었는지 확인
    if ! kill -0 $FLASK_PID 2>/dev/null; then
        print_error "Flask 앱 실행 실패"
        exit 1
    fi

    print_success "Flask 앱 실행 완료 (PID: $FLASK_PID)"

    # 7. ngrok 실행 (옵션)
    if [ "$USE_NGROK" = true ]; then
        echo ""

        # ngrok 설치 확인
        if ! command -v ngrok &> /dev/null; then
            print_error "ngrok가 설치되어 있지 않습니다."
            print_info "설치: brew install ngrok"
            print_info "또는 https://ngrok.com/download"
            print_info "로컬에서만 실행하시겠습니까? (y/n)"
            read -r response
            if [[ ! "$response" =~ ^[Yy]$ ]]; then
                cleanup
            fi
        else
            print_info "ngrok 실행 중..."
            ngrok http 8888 &
            NGROK_PID=$!

            sleep 2

            if ! kill -0 $NGROK_PID 2>/dev/null; then
                print_error "ngrok 실행 실패"
                print_info "ngrok 인증이 필요할 수 있습니다:"
                print_info "  1. https://ngrok.com 에서 회원가입"
                print_info "  2. ngrok config add-authtoken YOUR_TOKEN"
            else
                print_success "ngrok 실행 완료 (PID: $NGROK_PID)"
                echo ""
                print_info "ngrok 웹 인터페이스: http://127.0.0.1:4040"
            fi
        fi
    fi

    # 8. 접속 정보 출력
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✨ 서버가 실행 중입니다!${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # 로컬 IP 가져오기
    if command -v ipconfig &> /dev/null; then
        # macOS
        LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "N/A")
    else
        # Linux
        LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "N/A")
    fi

    echo -e "  ${CYAN}로컬 접속:${NC}"
    echo -e "    http://127.0.0.1:8888"
    echo -e "    http://localhost:8888"
    echo ""

    if [ "$LOCAL_IP" != "N/A" ]; then
        echo -e "  ${CYAN}네트워크 접속 (같은 WiFi):${NC}"
        echo -e "    http://${LOCAL_IP}:8888"
        echo ""
    fi

    if [ "$USE_NGROK" = true ] && [ ! -z "$NGROK_PID" ] && kill -0 $NGROK_PID 2>/dev/null; then
        echo -e "  ${CYAN}원격 접속 (ngrok):${NC}"
        echo -e "    http://127.0.0.1:4040 에서 URL 확인"
        echo ""
    fi

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    print_info "종료하려면 Ctrl+C를 누르세요"
    echo ""

    # 9. 로그 출력 (무한 대기)
    wait $FLASK_PID
}

# 스크립트 실행
main