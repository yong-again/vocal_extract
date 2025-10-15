"""
Demucs 음원 분리 모듈
"""
import torch
from pathlib import Path
from demucs.pretrained import get_model
from demucs.apply import apply_model
from torchaudio.transforms import Resample

from utils import clean_filename, save_audio_scipy, cleanup_temp_files
from logger import get_logger

logger = get_logger('separator')


class AudioSeparator:
    """Demucs를 사용한 음원 분리 클래스"""

    def __init__(self, model_name: str = 'htdemucs', output_dir: str = './output', use_gpu: bool = True):
        """
        Args:
            model_name: Demucs 모델 이름 (htdemucs, htdemucs_ft, htdemucs_6s)
            output_dir: 출력 디렉토리
            use_gpu: GPU 사용 여부
        """
        self.output_dir = Path(output_dir)
        self.model_name = model_name

        logger.info(f"Demucs 모델 로딩 중: {model_name}")
        self.model = get_model(model_name)

        # 디바이스 설정
        if use_gpu:
            if torch.backends.mps.is_available():
                self.device = torch.device("mps")
                logger.info("MPS (Metal Performance Shaders) 사용")
            elif torch.cuda.is_available():
                self.device = torch.device("cuda")
                logger.info("CUDA GPU 사용")
            else:
                self.device = torch.device("cpu")
                logger.warning("GPU를 찾을 수 없어 CPU 사용")
        else:
            self.device = torch.device("cpu")
            logger.info("CPU 사용 (설정)")

        self.model.to(self.device)
        logger.info("모델 로딩 완료")

    def separate(self, wav: torch.Tensor, sr: int, title: str) -> dict:
        """
        오디오를 stems로 분리

        Args:
            wav: 오디오 텐서 (2, samples)
            sr: 샘플레이트
            title: 저장할 파일명

        Returns:
            dict: 분리된 파일 정보
        """
        try:
            logger.info("음원 분리 시작")
            logger.debug(f"입력 텐서 shape: {wav.shape}, 샘플레이트: {sr}")

            # 스테레오 확인
            if wav.shape[0] == 1:
                logger.debug("모노를 스테레오로 변환")
                wav = wav.repeat(2, 1)

            # 리샘플링
            if sr != self.model.samplerate:
                logger.info(f"리샘플링: {sr} Hz → {self.model.samplerate} Hz")
                resampler = Resample(sr, self.model.samplerate)
                wav = resampler(wav)
                sr = self.model.samplerate

            # 배치 차원 추가 및 디바이스로 이동
            wav = wav.unsqueeze(0).to(self.device)
            logger.debug(f"처리할 텐서 shape: {wav.shape}")

            # 음원 분리 실행
            logger.info("Demucs 모델 실행 중...")
            with torch.no_grad():
                sources = apply_model(self.model, wav, device=self.device)

            # CPU로 이동
            sources = sources.cpu()
            logger.info("음원 분리 완료")
            logger.debug(f"출력 sources shape: {sources.shape}")

            # 파일 저장
            safe_title = clean_filename(title)
            sources_names = self.model.sources
            logger.info(f"파일 저장 중: {safe_title}")

            saved_files = {}
            for i, source_name in enumerate(sources_names):
                output_path = self.output_dir / f"{safe_title}_{source_name}.wav"
                save_audio_scipy(sources[0, i], sr, output_path)
                saved_files[source_name] = str(output_path)
                logger.info(f"저장 완료: {source_name} -> {output_path.name}")

            # 반주 생성 (보컬 제외)
            logger.info("반주 생성 중...")
            accompaniment = torch.zeros_like(sources[0, 0])
            for i, name in enumerate(sources_names):
                if name != 'vocals':
                    accompaniment += sources[0, i]

            accompaniment_path = self.output_dir / f"{safe_title}_accompaniment.wav"
            save_audio_scipy(accompaniment, sr, accompaniment_path)
            logger.info(f"반주 저장 완료: {accompaniment_path.name}")

            return {
                'title': title,
                'stems': saved_files,
                'accompaniment': str(accompaniment_path)
            }

        except Exception as e:
            logger.error(f"음원 분리 실패: {str(e)}", exc_info=True)
            raise Exception(f"음원 분리 실패: {str(e)}")