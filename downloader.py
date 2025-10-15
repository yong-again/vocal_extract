"""
YouTube 다운로드 모듈
"""
from pathlib import Path
from pytubefix import YouTube
from logger import get_logger

logger = get_logger('downloader')


class YouTubeDownloader:
    """YouTube 비디오 다운로드 클래스"""

    def __init__(self, output_path: str):
        """
        Args:
            output_path: 다운로드 저장 경로
        """
        self.output_path = Path(output_path)
        logger.info(f"다운로더 초기화: {self.output_path}")

    def download_audio(self, url: str) -> tuple:
        """
        YouTube URL에서 오디오만 다운로드

        Args:
            url: YouTube URL

        Returns:
            tuple: (다운로드된 파일 경로, 비디오 제목)

        Raises:
            ValueError: 오디오 스트림을 찾을 수 없을 때
            Exception: 다운로드 실패 시
        """
        try:
            logger.info(f"YouTube에서 다운로드 중: {url}")
            yt = YouTube(url)

            # 오디오 스트림만 필터링
            audio_stream = yt.streams.filter(only_audio=True).first()

            if not audio_stream:
                logger.error("오디오 스트림을 찾을 수 없습니다")
                raise ValueError("오디오 스트림을 찾을 수 없습니다.")

            # 다운로드
            logger.debug(f"스트림 정보: {audio_stream}")
            temp_file = audio_stream.download(
                output_path=str(self.output_path),
                filename="temp_audio.mp4"
            )

            logger.info(f"다운로드 완료: {yt.title}")
            logger.debug(f"파일 경로: {temp_file}")
            return temp_file, yt.title

        except Exception as e:
            logger.error(f"다운로드 실패: {str(e)}", exc_info=True)
            raise Exception(f"다운로드 실패: {str(e)}")