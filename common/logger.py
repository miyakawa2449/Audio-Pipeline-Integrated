#!/usr/bin/env python3
"""
Audio Pipeline Integrated 統一ログシステム
全プロジェクト共通のログ機能
"""
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

class AudioPipelineLogger:
    """Audio Pipeline Integrated 専用ログシステム"""
    
    _instances = {}
    
    def __new__(cls, name: str = "AudioPipeline"):
        if name not in cls._instances:
            cls._instances[name] = super().__new__(cls)
        return cls._instances[name]
    
    def __init__(self, name: str = "AudioPipeline"):
        if hasattr(self, '_initialized'):
            return
        
        self.name = name
        self.logger = logging.getLogger(name)
        self._initialized = True
        
        # ログレベル設定
        log_level = os.getenv('AUDIO_PIPELINE_LOG_LEVEL', 'INFO').upper()
        self.logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        # ハンドラーが既に設定されている場合はスキップ
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """ログハンドラー設定"""
        # ログディレクトリ作成
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # フォーマッター作成
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(module)s:%(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self._get_console_formatter())
        self.logger.addHandler(console_handler)
        
        # ファイルハンドラー（全ログ）
        file_handler = logging.FileHandler(
            log_dir / f"{self.name.lower()}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # デバッグファイルハンドラー
        debug_handler = logging.FileHandler(
            log_dir / f"{self.name.lower()}_debug.log",
            encoding='utf-8'
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)
        self.logger.addHandler(debug_handler)
    
    def _get_console_formatter(self):
        """コンソール用カラーフォーマッター"""
        class ColoredFormatter(logging.Formatter):
            COLORS = {
                'DEBUG': '\033[36m',    # シアン
                'INFO': '\033[32m',     # 緑
                'WARNING': '\033[33m',  # 黄色
                'ERROR': '\033[31m',    # 赤
                'CRITICAL': '\033[35m', # マゼンタ
                'RESET': '\033[0m'      # リセット
            }
            
            def format(self, record):
                # レベル別のアイコン
                icons = {
                    'DEBUG': '🔍',
                    'INFO': '✅',
                    'WARNING': '⚠️',
                    'ERROR': '❌',
                    'CRITICAL': '🚨'
                }
                
                # カラー適用
                color = self.COLORS.get(record.levelname, '')
                reset = self.COLORS['RESET']
                icon = icons.get(record.levelname, '📝')
                
                # フォーマット
                record.levelname = f"{color}{record.levelname}{reset}"
                formatted = f"{icon} {record.levelname} | {record.getMessage()}"
                
                return formatted
        
        return ColoredFormatter()
    
    def debug(self, message: str, **kwargs):
        """デバッグレベルログ"""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """情報レベルログ"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """警告レベルログ"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """エラーレベルログ"""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """クリティカルレベルログ"""
        self.logger.critical(message, **kwargs)
    
    def success(self, message: str, **kwargs):
        """成功メッセージ（info扱い）"""
        self.info(f"✅ {message}", **kwargs)
    
    def progress(self, message: str, **kwargs):
        """進捗メッセージ（info扱い）"""
        self.info(f"🔄 {message}", **kwargs)
    
    def start_operation(self, operation: str, **kwargs):
        """操作開始ログ"""
        self.info(f"🚀 {operation} を開始", **kwargs)
    
    def complete_operation(self, operation: str, **kwargs):
        """操作完了ログ"""
        self.success(f"{operation} が完了", **kwargs)
    
    def audio_info(self, message: str, **kwargs):
        """音声処理専用ログ"""
        self.info(f"🎵 {message}", **kwargs)
    
    def model_info(self, message: str, **kwargs):
        """モデル関連ログ"""
        self.info(f"🤖 {message}", **kwargs)
    
    def device_info(self, message: str, **kwargs):
        """デバイス関連ログ"""
        self.info(f"🎛️ {message}", **kwargs)

# グローバルロガーインスタンス
def get_logger(name: str = "AudioPipeline") -> AudioPipelineLogger:
    """ログシステム取得"""
    return AudioPipelineLogger(name)

# デフォルトロガー
logger = get_logger()

# 便利関数
def log_debug(message: str, **kwargs):
    """デバッグログ"""
    logger.debug(message, **kwargs)

def log_info(message: str, **kwargs):
    """情報ログ"""
    logger.info(message, **kwargs)

def log_warning(message: str, **kwargs):
    """警告ログ"""
    logger.warning(message, **kwargs)

def log_error(message: str, **kwargs):
    """エラーログ"""
    logger.error(message, **kwargs)

def log_success(message: str, **kwargs):
    """成功ログ"""
    logger.success(message, **kwargs)

def log_progress(message: str, **kwargs):
    """進捗ログ"""
    logger.progress(message, **kwargs)

def log_audio(message: str, **kwargs):
    """音声処理ログ"""
    logger.audio_info(message, **kwargs)

def log_model(message: str, **kwargs):
    """モデルログ"""
    logger.model_info(message, **kwargs)

def log_device(message: str, **kwargs):
    """デバイスログ"""
    logger.device_info(message, **kwargs)

# 設定関数
def setup_logging(level: str = "INFO", console_output: bool = True):
    """ログ設定"""
    os.environ['AUDIO_PIPELINE_LOG_LEVEL'] = level.upper()
    
    if not console_output:
        # コンソール出力を無効化
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                root_logger.removeHandler(handler)

def log_system_info():
    """システム情報ログ"""
    import platform
    import torch
    
    logger.info("=== Audio Pipeline Integrated システム情報 ===")
    logger.info(f"OS: {platform.system()} {platform.release()}")
    logger.info(f"Python: {platform.python_version()}")
    
    try:
        logger.info(f"PyTorch: {torch.__version__}")
        if torch.cuda.is_available():
            logger.device_info("CUDA GPU 利用可能")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            logger.device_info("Apple Silicon MPS 利用可能")
        else:
            logger.device_info("CPU処理モード")
    except ImportError:
        logger.warning("PyTorch未インストール")
    
    logger.info("=" * 50)

# 例外ハンドリング用デコレータ
def log_exceptions(func):
    """例外ログデコレータ"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"{func.__name__} でエラー発生: {e}")
            raise
    return wrapper

# 実行時間測定デコレータ
def log_execution_time(func):
    """実行時間ログデコレータ"""
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        logger.debug(f"{func.__name__} 開始")
        
        try:
            result = func(*args, **kwargs)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.debug(f"{func.__name__} 完了 (実行時間: {duration:.2f}秒)")
            return result
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.error(f"{func.__name__} エラー終了 (実行時間: {duration:.2f}秒): {e}")
            raise
    
    return wrapper

if __name__ == "__main__":
    # テスト実行
    print("🧪 ログシステムテスト")
    
    # システム情報表示
    log_system_info()
    
    # 各種ログテスト
    log_debug("これはデバッグメッセージです")
    log_info("これは情報メッセージです")
    log_warning("これは警告メッセージです")
    log_error("これはエラーメッセージです")
    log_success("これは成功メッセージです")
    log_progress("これは進捗メッセージです")
    log_audio("音声ファイルを処理中")
    log_model("モデルを学習中")
    log_device("音声デバイスを検出")
    
    print("\n✅ ログシステムテスト完了")
    print("📁 ログファイル: logs/audiopipeline.log")