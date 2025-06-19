#!/usr/bin/env python3
"""
Audio Pipeline Integrated - 統合音声ユーティリティ
全プロジェクト共通の音声処理機能
"""

import numpy as np
import torch
import torchaudio
import torchaudio.transforms as T
from pathlib import Path
from typing import Optional, Tuple, Union
from .logger import get_logger

# オプショナルライブラリ
try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False

try:
    from scipy import signal
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


class AudioUtils:
    """統合音声処理ユーティリティクラス"""
    
    def __init__(self, sample_rate: int = 22050):
        """
        初期化
        
        Args:
            sample_rate (int): デフォルトサンプルレート
        """
        self.sample_rate = sample_rate
        self.logger = get_logger("AudioUtils")
        self.resamplers = {}
        self.logger.info(f"AudioUtils初期化: デフォルトサンプルレート {sample_rate}Hz")
    
    def load_audio(self, file_path: Union[str, Path], target_sr: Optional[int] = None) -> Tuple[np.ndarray, int]:
        """
        統一音声読み込み（AudioOpt + Python_Audio_dataset統合版）
        
        Args:
            file_path: 音声ファイルパス
            target_sr: 目標サンプルレート（None: 元のサンプルレート）
            
        Returns:
            Tuple[音声データ, サンプルレート]
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            self.logger.error(f"音声ファイルが見つかりません: {file_path}")
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        self.logger.debug(f"音声ファイル読み込み開始: {file_path}")
        
        try:
            # PyTorchを優先使用
            audio, orig_sr = torchaudio.load(str(file_path))
            
            # モノラル化
            if audio.shape[0] > 1:
                audio = torch.mean(audio, dim=0, keepdim=True)
            
            # NumPy配列に変換
            audio_np = audio.squeeze().numpy()
            
            # リサンプリング
            if target_sr and target_sr != orig_sr:
                audio_np = self.resample_audio(audio_np, orig_sr, target_sr)
                orig_sr = target_sr
            
            self.logger.debug(f"音声読み込み成功: {audio_np.shape}, {orig_sr}Hz")
            return audio_np, orig_sr
            
        except Exception as e:
            # フォールバック: soundfile使用
            if SOUNDFILE_AVAILABLE:
                try:
                    audio_np, orig_sr = sf.read(str(file_path))
                    
                    # モノラル化
                    if len(audio_np.shape) > 1:
                        audio_np = np.mean(audio_np, axis=1)
                    
                    # リサンプリング
                    if target_sr and target_sr != orig_sr:
                        audio_np = self.resample_audio(audio_np, orig_sr, target_sr)
                        orig_sr = target_sr
                    
                    self.logger.info(f"音声読み込み成功（soundfile使用）: {audio_np.shape}, {orig_sr}Hz")
                    return audio_np, orig_sr
                    
                except Exception as sf_error:
                    self.logger.error(f"soundfileでの読み込みも失敗: {sf_error}")
                    
            self.logger.error(f"音声ファイル読み込み失敗: {e}")
            raise
    
    def save_audio(self, audio_data: np.ndarray, file_path: Union[str, Path], 
                   sample_rate: Optional[int] = None) -> bool:
        """
        統一音声保存
        
        Args:
            audio_data: 音声データ（NumPy配列）
            file_path: 保存パス
            sample_rate: サンプルレート（None: デフォルト値使用）
            
        Returns:
            保存成功フラグ
        """
        file_path = Path(file_path)
        sr = sample_rate or self.sample_rate
        
        # ディレクトリ作成
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger.debug(f"音声保存開始: {file_path}, {sr}Hz")
        
        try:
            # 音声データの正規化
            audio_normalized = self._normalize_audio(audio_data)
            
            # PyTorchで保存
            audio_tensor = torch.from_numpy(audio_normalized).unsqueeze(0)
            torchaudio.save(str(file_path), audio_tensor, sr)
            
            self.logger.info(f"音声保存成功: {file_path}")
            return True
            
        except Exception as e:
            # フォールバック: soundfile使用
            if SOUNDFILE_AVAILABLE:
                try:
                    audio_normalized = self._normalize_audio(audio_data)
                    sf.write(str(file_path), audio_normalized, sr, subtype='PCM_16')
                    self.logger.info(f"音声保存成功（soundfile使用）: {file_path}")
                    return True
                    
                except Exception as sf_error:
                    self.logger.error(f"soundfileでの保存も失敗: {sf_error}")
            
            self.logger.error(f"音声保存失敗: {e}")
            return False
    
    def resample_audio(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """
        統一リサンプリング
        
        Args:
            audio: 音声データ
            orig_sr: 元のサンプルレート
            target_sr: 目標サンプルレート
            
        Returns:
            リサンプリング後の音声データ
        """
        if orig_sr == target_sr:
            return audio
        
        resampler_key = f"{orig_sr}_{target_sr}"
        
        try:
            # PyTorchリサンプラーを使用
            if resampler_key not in self.resamplers:
                self.resamplers[resampler_key] = T.Resample(orig_sr, target_sr)
            
            audio_tensor = torch.from_numpy(audio).float()
            resampled = self.resamplers[resampler_key](audio_tensor)
            
            self.logger.debug(f"リサンプリング: {orig_sr}Hz → {target_sr}Hz")
            return resampled.numpy()
            
        except Exception as e:
            # フォールバック: scipy使用
            if SCIPY_AVAILABLE:
                try:
                    ratio = target_sr / orig_sr
                    resampled = signal.resample(audio, int(len(audio) * ratio))
                    self.logger.debug(f"リサンプリング（scipy使用）: {orig_sr}Hz → {target_sr}Hz")
                    return resampled.astype(np.float32)
                    
                except Exception as scipy_error:
                    self.logger.error(f"scipyリサンプリング失敗: {scipy_error}")
            
            # 最終フォールバック: 単純間引き/補間
            self.logger.warning("高度なリサンプリングが利用不可、単純間引き/補間を使用")
            return self._simple_resample(audio, orig_sr, target_sr)
    
    def _normalize_audio(self, audio: np.ndarray, target_db: float = -3.0) -> np.ndarray:
        """
        音声の正規化
        
        Args:
            audio: 音声データ
            target_db: 目標音量（dB）
            
        Returns:
            正規化後の音声データ
        """
        # NaN・無限大チェック
        if not np.isfinite(audio).all():
            self.logger.warning("音声データに無効な値を検出、修正中")
            audio = np.nan_to_num(audio, nan=0.0, posinf=0.0, neginf=0.0)
        
        # 無音チェック
        max_amp = np.max(np.abs(audio))
        if max_amp < 1e-6:
            self.logger.warning("音声データが無音または非常に小さい")
            return audio
        
        # ピーク正規化
        audio = audio / max_amp
        
        # 目標音量に調整
        target_amp = 10 ** (target_db / 20)
        audio = audio * target_amp
        
        # クリッピング防止
        audio = np.clip(audio, -1.0, 1.0)
        
        return audio
    
    def _simple_resample(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """
        単純なリサンプリング（フォールバック用）
        
        Args:
            audio: 音声データ
            orig_sr: 元のサンプルレート
            target_sr: 目標サンプルレート
            
        Returns:
            リサンプリング後の音声データ
        """
        ratio = target_sr / orig_sr
        new_length = int(len(audio) * ratio)
        
        # 線形補間
        old_indices = np.linspace(0, len(audio) - 1, len(audio))
        new_indices = np.linspace(0, len(audio) - 1, new_length)
        resampled = np.interp(new_indices, old_indices, audio)
        
        return resampled.astype(np.float32)
    
    def apply_noise_reduction(self, audio: np.ndarray, noise_level: float = 0.1) -> np.ndarray:
        """
        簡単なノイズ除去
        
        Args:
            audio: 音声データ
            noise_level: ノイズレベル閾値
            
        Returns:
            ノイズ除去後の音声データ
        """
        # 簡易的なノイズゲート
        mask = np.abs(audio) > noise_level
        denoised = audio * mask
        
        self.logger.debug(f"ノイズ除去適用: 閾値 {noise_level}")
        return denoised
    
    def get_audio_info(self, file_path: Union[str, Path]) -> dict:
        """
        音声ファイル情報取得
        
        Args:
            file_path: 音声ファイルパス
            
        Returns:
            音声ファイル情報辞書
        """
        try:
            audio, sr = self.load_audio(file_path)
            duration = len(audio) / sr
            
            info = {
                'file_path': str(file_path),
                'sample_rate': sr,
                'channels': 1,  # モノラル化後
                'duration': duration,
                'samples': len(audio),
                'max_amplitude': float(np.max(np.abs(audio))),
                'rms': float(np.sqrt(np.mean(audio ** 2)))
            }
            
            self.logger.debug(f"音声情報取得: {duration:.2f}秒, {sr}Hz")
            return info
            
        except Exception as e:
            self.logger.error(f"音声情報取得失敗: {e}")
            return {}


# グローバル音声ユーティリティインスタンス
_audio_utils_instance = None

def get_audio_utils(sample_rate: int = 22050) -> AudioUtils:
    """
    グローバル音声ユーティリティインスタンス取得
    
    Args:
        sample_rate: デフォルトサンプルレート
        
    Returns:
        AudioUtilsインスタンス
    """
    global _audio_utils_instance
    if _audio_utils_instance is None:
        _audio_utils_instance = AudioUtils(sample_rate)
    return _audio_utils_instance


# 便利関数
def load_audio(file_path: Union[str, Path], sample_rate: int = 22050) -> Tuple[np.ndarray, int]:
    """音声読み込み便利関数"""
    utils = get_audio_utils(sample_rate)
    return utils.load_audio(file_path, sample_rate)

def save_audio(audio_data: np.ndarray, file_path: Union[str, Path], sample_rate: int = 22050) -> bool:
    """音声保存便利関数"""
    utils = get_audio_utils(sample_rate)
    return utils.save_audio(audio_data, file_path, sample_rate)

def resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """リサンプリング便利関数"""
    utils = get_audio_utils()
    return utils.resample_audio(audio, orig_sr, target_sr)