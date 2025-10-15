"""
유틸리티 함수 모음
"""
import os
from pathlib import Path
from pydub import AudioSegment
import numpy as np
from scipy.io import wavfile
import torch
from logger import get_logger

logger = get_logger('utils')


def clean_filename(filename: str) -> str:
    """
    파일명에서 특수문자 제거

    Args:
        filename: 정리할 파일명

    Returns:
        특수문자가 제거된 파일명
    """
    cleaned = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).strip()
    logger.debug(f"파일명 정리: {filename} -> {cleaned}")
    return cleaned


def cleanup_temp_files(temp_file: str) -> None:
    """
    임시 파일 정리

    Args:
        temp_file: 삭제할 임시 파일 경로
    """
    try:
        if os.path.exists(temp_file):
            os.remove(temp_file)
            logger.info(f"임시 파일 삭제: {Path(temp_file).name}")
    except Exception as e:
        logger.warning(f"정리 중 오류: {e}")


def convert_to_wav(input_file: str, output_file: str) -> str:
    """
    오디오 파일을 WAV로 변환

    Args:
        input_file: 입력 파일 경로
        output_file: 출력 파일 경로

    Returns:
        변환된 WAV 파일 경로
    """
    try:
        logger.info(f"파일 변환 중: {Path(input_file).suffix} → .wav")
        audio = AudioSegment.from_file(input_file)
        audio.export(output_file, format="wav")

        # 원본 파일 삭제
        if os.path.exists(input_file):
            os.remove(input_file)
            logger.debug(f"원본 파일 삭제: {input_file}")

        logger.info(f"변환 완료: {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"오디오 변환 실패: {str(e)}", exc_info=True)
        raise Exception(f"오디오 변환 실패: {str(e)}")


def load_audio_with_pydub(audio_file: str) -> tuple:
    """
    pydub를 사용해 오디오 파일을 torch tensor로 로드

    Args:
        audio_file: 로드할 오디오 파일 경로

    Returns:
        tuple: (오디오 텐서, 샘플레이트)
    """
    try:
        logger.info(f"오디오 로드 중: {audio_file}")
        audio = AudioSegment.from_wav(audio_file)
        sr = audio.frame_rate

        # numpy 배열로 변환
        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
        samples = samples / (2**15)  # 정규화

        # 스테레오 처리
        if audio.channels == 2:
            samples = samples.reshape((-1, 2)).T
        else:
            samples = samples.reshape((1, -1))

        # torch tensor로 변환
        wav = torch.from_numpy(samples)
        logger.info(f"오디오 로드 완료: shape={wav.shape}, sr={sr}")
        return wav, sr
    except Exception as e:
        logger.error(f"오디오 로드 실패: {str(e)}", exc_info=True)
        raise Exception(f"오디오 로드 실패: {str(e)}")


def save_audio_scipy(audio_tensor: torch.Tensor, sample_rate: int, output_path: str) -> None:
    """
    torch tensor를 WAV 파일로 저장

    Args:
        audio_tensor: 저장할 오디오 텐서
        sample_rate: 샘플레이트
        output_path: 출력 파일 경로
    """
    try:
        logger.debug(f"오디오 저장 중: {output_path}")

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
        logger.debug(f"저장 완료: {output_path}")
    except Exception as e:
        logger.error(f"오디오 저장 실패: {str(e)}", exc_info=True)
        raise Exception(f"오디오 저장 실패: {str(e)}")