#!/usr/bin/env python3
"""
Audio Pipeline Integrated - 統一例外クラス
MacBook Pro M4 Pro環境対応の例外定義
"""

from enum import Enum
from typing import Optional, Dict, Any


class ErrorCode(Enum):
    """エラーコード定義"""
    # 音声ファイル関連エラー
    AUDIO_FILE_NOT_FOUND = "AF001"
    AUDIO_DECODE_FAILED = "AF002"
    AUDIO_ENCODE_FAILED = "AF003"
    UNSUPPORTED_FORMAT = "AF004"
    CORRUPTED_AUDIO = "AF005"
    
    # デバイス関連エラー
    DEVICE_NOT_AVAILABLE = "DV001"
    GPU_MEMORY_ERROR = "DV002"
    MPS_ERROR = "DV003"
    AUDIO_DEVICE_ERROR = "DV004"
    
    # モデル関連エラー
    MODEL_LOAD_FAILED = "ML001"
    MODEL_SAVE_FAILED = "ML002"
    TRAINING_FAILED = "ML003"
    INFERENCE_FAILED = "ML004"
    INVALID_MODEL = "ML005"
    
    # システム関連エラー
    INSUFFICIENT_MEMORY = "SY001"
    DISK_SPACE_ERROR = "SY002"
    PERMISSION_ERROR = "SY003"
    NETWORK_ERROR = "SY004"
    
    # データ関連エラー
    INVALID_DATA_FORMAT = "DT001"
    DATA_CORRUPTION = "DT002"
    MISSING_METADATA = "DT003"
    VALIDATION_ERROR = "DT004"
    
    # 設定関連エラー
    INVALID_CONFIG = "CF001"
    MISSING_DEPENDENCY = "CF002"
    VERSION_MISMATCH = "CF003"


class AudioPipelineError(Exception):
    """Audio Pipeline統一エラー基底クラス"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[ErrorCode] = None, 
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[str] = None
    ):
        """
        初期化
        
        Args:
            message: エラーメッセージ
            error_code: エラーコード
            details: エラー詳細情報
            suggestions: 解決提案
        """
        super().__init__(message)
        self.error_code = error_code or ErrorCode.INVALID_DATA_FORMAT
        self.details = details or {}
        self.suggestions = suggestions
        
    def __str__(self):
        base_msg = f"[{self.error_code.value}] {super().__str__()}"
        if self.suggestions:
            base_msg += f"\n💡 解決提案: {self.suggestions}"
        return base_msg
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式でエラー情報を返却"""
        return {
            "error_code": self.error_code.value,
            "message": str(super()),
            "details": self.details,
            "suggestions": self.suggestions,
            "error_type": self.__class__.__name__
        }


class AudioFileError(AudioPipelineError):
    """音声ファイル関連エラー"""
    
    def __init__(self, message: str, file_path: Optional[str] = None, **kwargs):
        if file_path:
            kwargs.setdefault("details", {})["file_path"] = file_path
        
        # デフォルトのエラーコード設定
        if "error_code" not in kwargs:
            if "not found" in message.lower():
                kwargs["error_code"] = ErrorCode.AUDIO_FILE_NOT_FOUND
                kwargs.setdefault("suggestions", "ファイルパスを確認し、ファイルが存在することを確認してください")
            elif "decode" in message.lower() or "load" in message.lower():
                kwargs["error_code"] = ErrorCode.AUDIO_DECODE_FAILED
                kwargs.setdefault("suggestions", "サポートされている音声形式（WAV, MP3, FLAC等）を使用してください")
            else:
                kwargs["error_code"] = ErrorCode.CORRUPTED_AUDIO
        
        super().__init__(message, **kwargs)


class DeviceError(AudioPipelineError):
    """デバイス関連エラー"""
    
    def __init__(self, message: str, device_type: Optional[str] = None, **kwargs):
        if device_type:
            kwargs.setdefault("details", {})["device_type"] = device_type
        
        # Apple Silicon特化のエラーコード設定
        if "error_code" not in kwargs:
            if "mps" in message.lower() or "metal" in message.lower():
                kwargs["error_code"] = ErrorCode.MPS_ERROR
                kwargs.setdefault("suggestions", "CPUフォールバックを試すか、macOSとPyTorchを最新版に更新してください")
            elif "cuda" in message.lower() or "gpu" in message.lower():
                kwargs["error_code"] = ErrorCode.GPU_MEMORY_ERROR
                kwargs.setdefault("suggestions", "バッチサイズを小さくするか、より多くのGPUメモリを確保してください")
            elif "audio" in message.lower():
                kwargs["error_code"] = ErrorCode.AUDIO_DEVICE_ERROR
                kwargs.setdefault("suggestions", "システム設定で音声デバイスを確認してください")
            else:
                kwargs["error_code"] = ErrorCode.DEVICE_NOT_AVAILABLE
        
        super().__init__(message, **kwargs)


class ModelError(AudioPipelineError):
    """モデル関連エラー"""
    
    def __init__(self, message: str, model_path: Optional[str] = None, **kwargs):
        if model_path:
            kwargs.setdefault("details", {})["model_path"] = model_path
        
        # デフォルトのエラーコード設定
        if "error_code" not in kwargs:
            if "load" in message.lower() or "loading" in message.lower():
                kwargs["error_code"] = ErrorCode.MODEL_LOAD_FAILED
                kwargs.setdefault("suggestions", "モデルファイルの存在と形式を確認してください")
            elif "save" in message.lower() or "saving" in message.lower():
                kwargs["error_code"] = ErrorCode.MODEL_SAVE_FAILED
                kwargs.setdefault("suggestions", "保存先ディレクトリの書き込み権限を確認してください")
            elif "train" in message.lower():
                kwargs["error_code"] = ErrorCode.TRAINING_FAILED
                kwargs.setdefault("suggestions", "学習データと学習パラメータを確認してください")
            elif "inference" in message.lower() or "predict" in message.lower():
                kwargs["error_code"] = ErrorCode.INFERENCE_FAILED
                kwargs.setdefault("suggestions", "入力データの形式とモデルの互換性を確認してください")
            else:
                kwargs["error_code"] = ErrorCode.INVALID_MODEL
        
        super().__init__(message, **kwargs)


class SystemError(AudioPipelineError):
    """システム関連エラー"""
    
    def __init__(self, message: str, **kwargs):
        # デフォルトのエラーコード設定
        if "error_code" not in kwargs:
            if "memory" in message.lower():
                kwargs["error_code"] = ErrorCode.INSUFFICIENT_MEMORY
                kwargs.setdefault("suggestions", "メモリ使用量を減らすか、システムメモリを増設してください")
            elif "disk" in message.lower() or "space" in message.lower():
                kwargs["error_code"] = ErrorCode.DISK_SPACE_ERROR
                kwargs.setdefault("suggestions", "ディスク容量を確認し、不要ファイルを削除してください")
            elif "permission" in message.lower():
                kwargs["error_code"] = ErrorCode.PERMISSION_ERROR
                kwargs.setdefault("suggestions", "ファイル・ディレクトリの読み書き権限を確認してください")
            elif "network" in message.lower():
                kwargs["error_code"] = ErrorCode.NETWORK_ERROR
                kwargs.setdefault("suggestions", "ネットワーク接続を確認してください")
            else:
                kwargs["error_code"] = ErrorCode.INSUFFICIENT_MEMORY
        
        super().__init__(message, **kwargs)


class DataError(AudioPipelineError):
    """データ関連エラー"""
    
    def __init__(self, message: str, data_type: Optional[str] = None, **kwargs):
        if data_type:
            kwargs.setdefault("details", {})["data_type"] = data_type
        
        # デフォルトのエラーコード設定
        if "error_code" not in kwargs:
            if "format" in message.lower():
                kwargs["error_code"] = ErrorCode.INVALID_DATA_FORMAT
                kwargs.setdefault("suggestions", "データ形式を確認し、仕様に合わせて変換してください")
            elif "corrupt" in message.lower():
                kwargs["error_code"] = ErrorCode.DATA_CORRUPTION
                kwargs.setdefault("suggestions", "データファイルを再取得するか、バックアップを使用してください")
            elif "metadata" in message.lower():
                kwargs["error_code"] = ErrorCode.MISSING_METADATA
                kwargs.setdefault("suggestions", "必要なメタデータファイルを確認・生成してください")
            elif "validation" in message.lower():
                kwargs["error_code"] = ErrorCode.VALIDATION_ERROR
                kwargs.setdefault("suggestions", "データ検証ルールを確認し、データを修正してください")
            else:
                kwargs["error_code"] = ErrorCode.INVALID_DATA_FORMAT
        
        super().__init__(message, **kwargs)


class ConfigError(AudioPipelineError):
    """設定関連エラー"""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        if config_key:
            kwargs.setdefault("details", {})["config_key"] = config_key
        
        # デフォルトのエラーコード設定
        if "error_code" not in kwargs:
            if "dependency" in message.lower() or "missing" in message.lower():
                kwargs["error_code"] = ErrorCode.MISSING_DEPENDENCY
                kwargs.setdefault("suggestions", "requirements.txtから必要なライブラリをインストールしてください")
            elif "version" in message.lower():
                kwargs["error_code"] = ErrorCode.VERSION_MISMATCH
                kwargs.setdefault("suggestions", "ライブラリのバージョン互換性を確認してください")
            else:
                kwargs["error_code"] = ErrorCode.INVALID_CONFIG
                kwargs.setdefault("suggestions", "設定ファイルの形式と必須項目を確認してください")
        
        super().__init__(message, **kwargs)


# Apple Silicon M4 Pro特化例外
class AppleSiliconError(DeviceError):
    """Apple Silicon M4 Pro特化エラー"""
    
    def __init__(self, message: str, **kwargs):
        kwargs.setdefault("error_code", ErrorCode.MPS_ERROR)
        kwargs.setdefault("details", {})["platform"] = "Apple Silicon M4 Pro"
        
        if "suggestions" not in kwargs:
            kwargs["suggestions"] = (
                "Apple Silicon M4 Pro環境では以下を確認してください:\n"
                "1. macOS Sonoma以降を使用\n"
                "2. PyTorch 2.0以降のMPS対応版を使用\n"
                "3. メモリ使用量がUnified Memory容量内に収まることを確認\n"
                "4. CPUフォールバックオプションを有効化"
            )
        
        super().__init__(message, device_type="Apple Silicon M4 Pro", **kwargs)


# 便利関数
def raise_audio_error(message: str, file_path: Optional[str] = None, **kwargs):
    """音声エラー発生"""
    raise AudioFileError(message, file_path=file_path, **kwargs)

def raise_device_error(message: str, device_type: Optional[str] = None, **kwargs):
    """デバイスエラー発生"""
    raise DeviceError(message, device_type=device_type, **kwargs)

def raise_model_error(message: str, model_path: Optional[str] = None, **kwargs):
    """モデルエラー発生"""
    raise ModelError(message, model_path=model_path, **kwargs)

def raise_apple_silicon_error(message: str, **kwargs):
    """Apple Siliconエラー発生"""
    raise AppleSiliconError(message, **kwargs)


# エラーコード検索関数
def get_error_by_code(error_code: str) -> Optional[ErrorCode]:
    """エラーコードから ErrorCode を取得"""
    for code in ErrorCode:
        if code.value == error_code:
            return code
    return None


# エラー統計情報
class ErrorStats:
    """エラー統計クラス"""
    
    def __init__(self):
        self.error_counts = {}
        self.total_errors = 0
    
    def record_error(self, error: AudioPipelineError):
        """エラー記録"""
        error_type = type(error).__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        self.total_errors += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報取得"""
        return {
            "total_errors": self.total_errors,
            "error_breakdown": self.error_counts,
            "most_common": max(self.error_counts.items(), key=lambda x: x[1]) if self.error_counts else None
        }
    
    def reset(self):
        """統計リセット"""
        self.error_counts.clear()
        self.total_errors = 0


# グローバル統計インスタンス
error_stats = ErrorStats()