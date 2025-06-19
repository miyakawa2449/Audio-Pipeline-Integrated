#!/usr/bin/env python3
"""
Audio Pipeline Integrated - 統一エラーハンドリングシステム
MacBook Pro M4 Pro環境対応の堅牢なエラー処理
"""

import sys
import traceback
import functools
import platform
from typing import Type, Union, Callable, Any, Optional, Dict, List
from enum import Enum
from datetime import datetime
from pathlib import Path

# Optional dependency
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from .logger import get_logger
from .exceptions import (
    AudioPipelineError, ErrorCode, AppleSiliconError,
    AudioFileError, DeviceError, ModelError, SystemError,
    error_stats
)


class ErrorSeverity(Enum):
    """エラー重要度"""
    LOW = "low"          # デバッグ情報レベル
    MEDIUM = "medium"    # 警告レベル
    HIGH = "high"        # エラーレベル
    CRITICAL = "critical" # クリティカルレベル


class RecoveryStrategy(Enum):
    """復旧戦略"""
    NONE = "none"                    # 復旧なし
    RETRY = "retry"                  # リトライ
    FALLBACK = "fallback"            # フォールバック処理
    CPU_FALLBACK = "cpu_fallback"    # CPU fallback
    RESTART = "restart"              # プロセス再開
    USER_INTERVENTION = "user"       # ユーザー介入


class ErrorHandler:
    """統一エラーハンドリングクラス"""
    
    def __init__(self, logger_name: str = "ErrorHandler", enable_recovery: bool = True):
        """
        初期化
        
        Args:
            logger_name: ロガー名
            enable_recovery: 自動復旧機能有効フラグ
        """
        self.logger = get_logger(logger_name)
        self.enable_recovery = enable_recovery
        self.error_callbacks: Dict[Type[Exception], List[Callable]] = {}
        self.recovery_strategies: Dict[ErrorCode, RecoveryStrategy] = self._setup_recovery_strategies()
        self.system_info = self._collect_system_info()
        
        # Apple Silicon環境の特別設定
        self.is_apple_silicon = self._is_apple_silicon()
        if self.is_apple_silicon:
            self.logger.info("🍎 Apple Silicon M4 Pro環境でのエラーハンドリングを初期化")
    
    def _setup_recovery_strategies(self) -> Dict[ErrorCode, RecoveryStrategy]:
        """復旧戦略の設定"""
        return {
            # 音声ファイル関連
            ErrorCode.AUDIO_FILE_NOT_FOUND: RecoveryStrategy.USER_INTERVENTION,
            ErrorCode.AUDIO_DECODE_FAILED: RecoveryStrategy.FALLBACK,
            ErrorCode.CORRUPTED_AUDIO: RecoveryStrategy.USER_INTERVENTION,
            
            # デバイス関連
            ErrorCode.MPS_ERROR: RecoveryStrategy.CPU_FALLBACK,
            ErrorCode.GPU_MEMORY_ERROR: RecoveryStrategy.RESTART,
            ErrorCode.DEVICE_NOT_AVAILABLE: RecoveryStrategy.FALLBACK,
            
            # モデル関連
            ErrorCode.MODEL_LOAD_FAILED: RecoveryStrategy.RETRY,
            ErrorCode.TRAINING_FAILED: RecoveryStrategy.USER_INTERVENTION,
            ErrorCode.INFERENCE_FAILED: RecoveryStrategy.FALLBACK,
            
            # システム関連
            ErrorCode.INSUFFICIENT_MEMORY: RecoveryStrategy.RESTART,
            ErrorCode.DISK_SPACE_ERROR: RecoveryStrategy.USER_INTERVENTION,
            ErrorCode.PERMISSION_ERROR: RecoveryStrategy.USER_INTERVENTION,
        }
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """システム情報収集"""
        info = {
            "platform": platform.system(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
            "timestamp": datetime.now().isoformat()
        }
        
        # メモリ情報（可能な場合）
        if PSUTIL_AVAILABLE:
            try:
                memory = psutil.virtual_memory()
                info["memory"] = {
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "usage_percent": memory.percent
                }
            except Exception:
                info["memory"] = "memory info unavailable"
        else:
            info["memory"] = "psutil not available"
        
        return info
    
    def _is_apple_silicon(self) -> bool:
        """Apple Silicon環境判定"""
        return (
            platform.system() == "Darwin" and 
            platform.machine() in ["arm64", "aarch64"]
        )
    
    def handle_error(
        self,
        error: Exception,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        reraise: bool = True,
        recovery_attempt: bool = True
    ) -> Optional[Any]:
        """
        統一エラー処理
        
        Args:
            error: 発生した例外
            severity: エラー重要度
            context: エラーコンテキスト情報
            reraise: 例外再投げフラグ
            recovery_attempt: 復旧試行フラグ
            
        Returns:
            復旧処理の結果（成功時）
        """
        context = context or {}
        context.update(self.system_info)
        
        # エラー統計記録
        if isinstance(error, AudioPipelineError):
            error_stats.record_error(error)
        
        # ログ出力
        self._log_error(error, severity, context)
        
        # Apple Silicon特有処理
        if self.is_apple_silicon:
            apple_silicon_result = self._handle_apple_silicon_specific(error, context)
            if apple_silicon_result is not None:
                return apple_silicon_result
        
        # 復旧試行
        recovery_result = None
        if recovery_attempt and self.enable_recovery:
            recovery_result = self._attempt_recovery(error, context)
            if recovery_result is not None:
                self.logger.success("エラー復旧に成功しました")
                return recovery_result
        
        # コールバック実行
        self._execute_callbacks(error, severity, context)
        
        # エラー報告
        self._report_error(error, context)
        
        if reraise:
            raise error
        
        return None
    
    def _log_error(self, error: Exception, severity: ErrorSeverity, context: Dict[str, Any]):
        """エラーログ出力"""
        # ログレベル選択
        log_level_map = {
            ErrorSeverity.LOW: self.logger.debug,
            ErrorSeverity.MEDIUM: self.logger.warning,
            ErrorSeverity.HIGH: self.logger.error,
            ErrorSeverity.CRITICAL: self.logger.critical
        }
        log_func = log_level_map[severity]
        
        # エラー情報構築
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "severity": severity.value,
            "context": context
        }
        
        # Audio Pipeline専用エラーの追加情報
        if isinstance(error, AudioPipelineError):
            error_info.update({
                "error_code": error.error_code.value,
                "suggestions": error.suggestions,
                "details": error.details
            })
        
        # トレースバック（高重要度以上）
        if severity.value in ["high", "critical"]:
            error_info["traceback"] = traceback.format_exc()
        
        # ログ出力
        log_func(f"🚨 エラー発生: {error_info}")
        
        # クリティカルエラーの特別処理
        if severity == ErrorSeverity.CRITICAL:
            self._handle_critical_error(error, context)
    
    def _handle_apple_silicon_specific(self, error: Exception, context: Dict[str, Any]) -> Optional[Any]:
        """Apple Silicon特有エラー処理"""
        error_str = str(error).lower()
        
        # MPS関連エラー
        if any(keyword in error_str for keyword in ["mps", "metal", "gpu"]):
            self.logger.warning("🍎 Apple Silicon MPS関連エラーを検出 - CPU fallbackを試行")
            
            # CPU fallbackの提案
            if "torch" in str(type(error).__module__):
                return self._suggest_cpu_fallback(error, context)
        
        # メモリ圧迫（Unified Memory）
        if "memory" in error_str or "out of memory" in error_str:
            self.logger.warning("🍎 Apple Silicon Unified Memoryの圧迫を検出")
            return self._handle_unified_memory_pressure(error, context)
        
        # Audio Unit関連
        if "audio" in error_str and "unit" in error_str:
            self.logger.warning("🍎 Apple Silicon Audio Unit問題を検出")
            return self._handle_audio_unit_error(error, context)
        
        return None
    
    def _suggest_cpu_fallback(self, error: Exception, context: Dict[str, Any]) -> Optional[str]:
        """CPU fallback提案"""
        suggestion = (
            "Apple Silicon MPS処理に失敗しました。以下を試してください:\n"
            "1. torch.device('cpu')を使用してCPU処理に切り替え\n"
            "2. バッチサイズを小さくして再試行\n"
            "3. macOSとPyTorchを最新版に更新\n"
            "4. システム再起動後に再試行"
        )
        self.logger.info(f"💡 CPU fallback提案: {suggestion}")
        return "cpu_fallback_suggested"
    
    def _handle_unified_memory_pressure(self, error: Exception, context: Dict[str, Any]) -> Optional[str]:
        """Unified Memory圧迫処理"""
        try:
            if "memory" in context and isinstance(context["memory"], dict):
                available_gb = context["memory"].get("available_gb")
                if available_gb and available_gb < 2.0:  # 2GB未満
                    self.logger.critical(f"🍎 Unified Memory不足: 利用可能 {available_gb:.1f}GB")
                    return "memory_cleanup_required"
        except (KeyError, TypeError):
            pass
        
        suggestion = (
            "Apple Silicon Unified Memory不足です:\n"
            "1. 他のアプリケーションを閉じてメモリを解放\n"
            "2. バッチサイズや処理サイズを縮小\n"
            "3. スワップファイルの使用を許可\n"
            "4. より多くのメモリを搭載したモデルへの移行を検討"
        )
        self.logger.warning(f"💡 メモリ最適化提案: {suggestion}")
        return "memory_optimization_suggested"
    
    def _handle_audio_unit_error(self, error: Exception, context: Dict[str, Any]) -> Optional[str]:
        """Audio Unit エラー処理"""
        suggestion = (
            "Apple Silicon Audio Unit問題です:\n"
            "1. システム設定 > サウンドで音声デバイスを確認\n"
            "2. Audio MIDIセットアップでデバイス設定を確認\n"
            "3. アプリケーションに音声アクセス権限を付与\n"
            "4. macOSの音声ドライバを再読み込み"
        )
        self.logger.warning(f"💡 Audio Unit修復提案: {suggestion}")
        return "audio_unit_fix_suggested"
    
    def _attempt_recovery(self, error: Exception, context: Dict[str, Any]) -> Optional[Any]:
        """復旧試行"""
        if not isinstance(error, AudioPipelineError):
            return None
        
        strategy = self.recovery_strategies.get(error.error_code, RecoveryStrategy.NONE)
        
        if strategy == RecoveryStrategy.NONE:
            return None
        
        self.logger.info(f"🔄 復旧戦略実行: {strategy.value}")
        
        try:
            if strategy == RecoveryStrategy.CPU_FALLBACK:
                return self._execute_cpu_fallback(error, context)
            elif strategy == RecoveryStrategy.FALLBACK:
                return self._execute_fallback(error, context)
            elif strategy == RecoveryStrategy.RETRY:
                return self._execute_retry(error, context)
            elif strategy == RecoveryStrategy.RESTART:
                return self._execute_restart(error, context)
        except Exception as recovery_error:
            self.logger.error(f"復旧処理失敗: {recovery_error}")
        
        return None
    
    def _execute_cpu_fallback(self, error: Exception, context: Dict[str, Any]) -> Optional[str]:
        """CPU fallback実行"""
        self.logger.info("CPU fallbackを実行中...")
        # 実際のfallback処理は呼び出し元で実装
        return "cpu_fallback_executed"
    
    def _execute_fallback(self, error: Exception, context: Dict[str, Any]) -> Optional[str]:
        """フォールバック処理実行"""
        self.logger.info("フォールバック処理を実行中...")
        # 実際のfallback処理は呼び出し元で実装
        return "fallback_executed"
    
    def _execute_retry(self, error: Exception, context: Dict[str, Any]) -> Optional[str]:
        """リトライ処理実行"""
        retry_count = context.get("retry_count", 0)
        if retry_count >= 3:
            self.logger.warning("最大リトライ回数に達しました")
            return None
        
        self.logger.info(f"リトライ実行 ({retry_count + 1}/3)")
        return "retry_executed"
    
    def _execute_restart(self, error: Exception, context: Dict[str, Any]) -> Optional[str]:
        """再開処理実行"""
        self.logger.warning("プロセス再開が必要です")
        return "restart_required"
    
    def _execute_callbacks(self, error: Exception, severity: ErrorSeverity, context: Dict[str, Any]):
        """エラーコールバック実行"""
        error_type = type(error)
        if error_type in self.error_callbacks:
            for callback in self.error_callbacks[error_type]:
                try:
                    callback(error, severity, context)
                except Exception as callback_error:
                    self.logger.error(f"エラーコールバック実行失敗: {callback_error}")
    
    def _handle_critical_error(self, error: Exception, context: Dict[str, Any]):
        """クリティカルエラー処理"""
        self.logger.critical("🚨 クリティカルエラーが発生しました")
        
        # エラーレポート保存
        error_report_path = Path("logs") / f"critical_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        error_report_path.parent.mkdir(exist_ok=True)
        
        try:
            with open(error_report_path, 'w', encoding='utf-8') as f:
                f.write(f"Critical Error Report\n")
                f.write(f"=====================\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Error Type: {type(error).__name__}\n")
                f.write(f"Error Message: {str(error)}\n")
                f.write(f"System Info: {self.system_info}\n")
                f.write(f"Context: {context}\n")
                f.write(f"Traceback:\n{traceback.format_exc()}\n")
            
            self.logger.critical(f"エラーレポートを保存: {error_report_path}")
        except Exception as report_error:
            self.logger.error(f"エラーレポート保存失敗: {report_error}")
    
    def _report_error(self, error: Exception, context: Dict[str, Any]):
        """エラー報告"""
        # 統計情報更新
        stats = error_stats.get_stats()
        if stats["total_errors"] % 10 == 0 and stats["total_errors"] > 0:
            self.logger.info(f"📊 エラー統計: 総計{stats['total_errors']}件")
    
    def register_callback(self, error_type: Type[Exception], callback: Callable):
        """エラーコールバック登録"""
        if error_type not in self.error_callbacks:
            self.error_callbacks[error_type] = []
        self.error_callbacks[error_type].append(callback)
        self.logger.debug(f"エラーコールバック登録: {error_type.__name__}")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """エラー統計取得"""
        return error_stats.get_stats()


# デコレータ
def error_handler(
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    reraise: bool = True,
    recovery: bool = True,
    context_func: Optional[Callable] = None
):
    """
    エラーハンドリングデコレータ
    
    Args:
        severity: エラー重要度
        reraise: 例外再投げフラグ
        recovery: 復旧試行フラグ
        context_func: コンテキスト生成関数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            handler = ErrorHandler(func.__module__)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    "function": func.__name__,
                    "module": func.__module__,
                    "args_summary": str(args)[:100],
                    "kwargs_summary": str(kwargs)[:100]
                }
                
                if context_func:
                    try:
                        additional_context = context_func(*args, **kwargs)
                        context.update(additional_context)
                    except Exception:
                        pass  # コンテキスト生成失敗は無視
                
                return handler.handle_error(e, severity, context, reraise, recovery)
        return wrapper
    return decorator


def apple_silicon_safe(func: Callable) -> Callable:
    """Apple Silicon環境での安全実行デコレータ"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if platform.machine() in ["arm64", "aarch64"]:
                # Apple Silicon特有エラーとして処理
                apple_error = AppleSiliconError(f"Apple Silicon環境でエラー: {str(e)}")
                handler = ErrorHandler()
                return handler.handle_error(apple_error, ErrorSeverity.HIGH)
            else:
                raise
    return wrapper


# グローバルエラーハンドラーインスタンス
_global_error_handler = None

def get_error_handler() -> ErrorHandler:
    """グローバルエラーハンドラー取得"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler("GlobalErrorHandler")
    return _global_error_handler


# 便利関数
def handle_error(error: Exception, severity: ErrorSeverity = ErrorSeverity.MEDIUM, **kwargs):
    """エラー処理便利関数"""
    handler = get_error_handler()
    return handler.handle_error(error, severity, **kwargs)

def register_error_callback(error_type: Type[Exception], callback: Callable):
    """エラーコールバック登録便利関数"""
    handler = get_error_handler()
    handler.register_callback(error_type, callback)

def get_error_statistics() -> Dict[str, Any]:
    """エラー統計取得便利関数"""
    handler = get_error_handler()
    return handler.get_error_stats()