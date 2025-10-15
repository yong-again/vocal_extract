"""
로깅 설정 모듈
"""
import logging
import sys
from pathlib import Path
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """컬러풀한 콘솔 출력을 위한 포매터"""

    # ANSI 색상 코드
    COLORS = {
        'DEBUG': '\033[0;36m',    # Cyan
        'INFO': '\033[0;32m',     # Green
        'WARNING': '\033[1;33m',  # Yellow
        'ERROR': '\033[0;31m',    # Red
        'CRITICAL': '\033[1;35m', # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        # 로그 레벨에 따라 색상 추가
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)


def setup_logger(name: str = 'youtube-separator', log_dir: str = './logs') -> logging.Logger:
    """
    로거 설정

    Args:
        name: 로거 이름
        log_dir: 로그 파일 저장 디렉토리

    Returns:
        설정된 로거 인스턴스
    """

    # 로그 디렉토리 생성
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 기존 핸들러 제거 (중복 방지)
    if logger.handlers:
        logger.handlers.clear()

    # 1. 콘솔 핸들러 (컬러풀)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter(
        '%(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)

    # 2. 파일 핸들러 (상세 로그)
    log_file = log_path / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    # 3. 에러 파일 핸들러 (에러만 별도 저장)
    error_log_file = log_path / f"error_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)

    # 핸들러 추가
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    기존 로거 가져오기

    Args:
        name: 로거 이름 (없으면 root 로거)

    Returns:
        로거 인스턴스
    """
    if name:
        return logging.getLogger(f'youtube-separator.{name}')
    return logging.getLogger('youtube-separator')