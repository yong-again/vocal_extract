import torch
import torchaudio
from pathlib import Path
from demucs.pretrained import get_model
from demucs.apply import apply_model
from utils import clean_filename, cleanup_temp_files

class AudioSeparator:
    """
    Demucs를 이용한 음원 분리 클래스
    """
    def __init__(self, model_name='htdemucs', output_dir='./output', use_gpu=True):
        """
        Args:
            model_name (str): 사용할 Demucs 모델 이름
            output_dir (str): 분리된 음원을 저장할 디렉토리
            use_gpu (bool): GPU 사용 여부
        """
        self.output_dir = Path(output_dir)
        self.model_name = model_name

        print(f'Demucs 모델 로딩 중: {model_name}')
        self.model = get_model(model_name)

        if use_gpu:
            if torch.backends.mps.is_available():
                self.device = torch.device('mps')
                print('MPS (Metal Performance Shaders) 사용')
            elif torch.cuda.is_available():
                self.device = torch.device('cuda')
                print('CUDA 사용')
            else:
                self.device = torch.device('cpu')
                print('GPU를 사용할 수 없습니다. CPU 사용')
        else:
            self.device = torch.device('cpu')
            print('CPU 사용')

        self.model.to(self.device)
        print("모델 로딩 완료")

    def separate(self, audio_file, title):
        """
        오디오 파일을 stems로 분리

        Args:
            audio_file (str): 분리할 오디오 파일 경로
            title (str): 오디오 제목 (파일명에 사용)

        returns:
            dict: 분리된 오디오 파일 경로
        """
        try:
            print("음원 분리 시작")

            # 오디오 로드
            wav, sr = torchaudio.load(audio_file)

            # 스테로오 변환
            if wav.shape[0] == 1:
                wav = wav.repeat(2, 1)

            # Demucs 모델에 맞는 샘플레이트로 리샘플링
            if sr != self.model.samplerate:
                print(f'리샘플: {sr} -> {self.model.samplerate}')
                resampler = torchaudio.transforms.Resample(wav, self.model.samplerate)
                wav = resampler(wav)
                sr = self.model.samplerate

            # 배치 차원 추가 및 디바이스로 이동
            wav = wav.unsqueeze(0).to(self.device)

            # 음원 분리 실행
            with torch.no_grad():
                sources = apply_model(self.model, wav, device=self.device)

            # cpu로 이동
            sources = sources.cpu()

            print("음원 분리 완료")

            # stems 이름 (모델에 따라 다름)
            # htdemucs: ['drums', 'bass', 'other', 'vocals']
            # htdemucs_6s: ['drums', 'bass', 'other', 'vocals', 'guitar', 'piano']
            sources_names = self.model.sources

            # 안전한 파일 명 생성
            safe_title = clean_filename(title)

            # 각 stem 저장
            saved_file = {}
            for i, source_names in enumerate(sources_names):
                output_path = self.output_dir / f"{safe_title}_{source_names}.wav"

                # 저장
                torchaudio.save(
                    str(output_path),
                    sources[0, i],
                    sr
                )

                saved_file[source_names] = str(output_path)
                print(f"저장 완료: {output_path}")

            # 임시 파일 정리
            cleanup_temp_files(audio_file)

            return {
                'title': saved_file,
                'stems': saved_file,
                'vocals': saved_file.get('vocals', ''),
                'accompaniment': self._create_accompaniment(sources, sources_names, safe_title, sr),

            }

        except Exception as e:
            raise Exception(f"음원 분리 실패: {str(e)}")

    def _create_accompaniment(self, sources, sources_names, safe_title, sr):
        """
        보컬을 제외한 나머지를 합쳐서 반주 생성
        """
        try:
            accompaniment = torch.zeros_like(sources[0, 0])

            for i, name in enumerate(sources_names):
                if name != 'vocals':
                    accompaniment += sources[0, i]

            accompaniment_path = self.output_dir / f"{safe_title}_accompaniment.wav"
            torchaudio.save(str(accompaniment_path), accompaniment, sr)

            print(f"반주 저장 완료: {accompaniment_path}")
            return str(accompaniment_path)

        except Exception as e:
            raise Exception(f"반주 생성 실패: {str(e)}")
