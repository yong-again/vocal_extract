from pathlib import Path

class Config:
    """
    Setting application
    """
    OUTPUT_DIR = Path("./output")
    TEMP_DIR = Path("./temp")
    SPLEETER_MODEL = 'spleeter:2stems'
    HOST = '0.0.0.0'
    PORT = 8888
    DEBUG = True
    
    @classmethod
    def init_directories(cls):
        """
        make directory
        """
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        cls.TEMP_DIR.mkdir(exist_ok=True)