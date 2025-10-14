import os
import shutil
from pathlib import Path

def clean_filename(filename):
    """
    파일명에서 특수문자 제거
    """
    return "".join(c for c in filename in c.isalnum() or c in (' ', '-', '_')).strip()

def cleanup_temp_files(temp_file, output_folder):
    """
    임시 파일 및 폴더 정리
    """
    try:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        if output_folder.exists():
            shutil.rmtree(output_folder)
    except Exception as e:
        print(f"정리 중 오류: {e}")