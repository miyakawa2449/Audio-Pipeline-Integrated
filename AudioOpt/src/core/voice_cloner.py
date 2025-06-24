"""
音声クローニングメインクラス
高品質な音声合成とメルスペクトログラム正規化機能を提供
"""

import os
import shutil
import json
from datetime import datetime
from typing import List, Tuple, Optional

import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import torchaudio
import torchaudio.transforms as T

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

# プロジェクト内モジュール
from ..audio import AudioPreprocessor
from ..text import TextProcessor
from ..model import VoiceDataset, VoiceCloneModel

# 統一ログシステムと共通モジュール
try:
    from common.logger import get_logger
    from common.audio_utils import get_audio_utils
    from common.device_utils import get_torch_device, get_device_utils
    from common.file_utils import setup_directories
except ImportError:
    # フォールバック用のダミーロガー
    import logging
    
    class FallbackLogger:
        def __init__(self, name):
            self.logger = logging.getLogger(name)
            self.logger.setLevel(logging.INFO)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(logging.Formatter('%(levelname)s | %(message)s'))
                self.logger.addHandler(handler)
        
        def debug(self, msg): self.logger.debug(msg)
        def info(self, msg): self.logger.info(msg)
        def warning(self, msg): self.logger.warning(msg)
        def error(self, msg): self.logger.error(msg)
        def start_operation(self, msg): self.logger.info(f"🚀 {msg} を開始")
        def complete_operation(self, msg): self.logger.info(f"✅ {msg} が完了")
        def success(self, msg): self.logger.info(f"✅ {msg}")
        def progress(self, msg): self.logger.info(f"🔄 {msg}")
        def audio_info(self, msg): self.logger.info(f"🎵 {msg}")
        def model_info(self, msg): self.logger.info(f"🤖 {msg}")
        def device_info(self, msg): self.logger.info(f"🎛️ {msg}")
    
    def get_logger(name): return FallbackLogger(name)
    def get_audio_utils(*args): return None
    def get_torch_device(): return torch.device('cpu')
    def get_device_utils(): return None
    def setup_directories(*args): return True


class VoiceCloner:
    """音声クローニングメインクラス"""
    
    # クラス定数
    DEFAULT_HOP_LENGTH = 256
    DEFAULT_N_FFT = 2048
    DEFAULT_N_MELS = 80
    MIN_FRAME_LENGTH = 50
    MEL_CLIP_MIN = -10
    MEL_CLIP_MAX = 10
    MEL_SCALE_MIN = -4
    MEL_SCALE_MAX = 4
    
    def __init__(self, dataset_path: str = "dataset"):
        """初期化"""
        self.logger = get_logger("VoiceCloner")
        self.dataset_path = dataset_path
        self.audio_path = os.path.join(dataset_path, "audio_files")
        self.meta_path = os.path.join(dataset_path, "meta_files")
        self.processed_path = os.path.join(dataset_path, "processed")
        self.models_path = "models"
        self.output_path = "output"
        
        # ディレクトリ作成（共通モジュール使用）
        directories = [self.audio_path, self.meta_path, self.processed_path, 
                      self.models_path, self.output_path]
        setup_directories(directories)
        
        # コンポーネント初期化
        self.preprocessor = AudioPreprocessor()
        self.text_processor = TextProcessor()
        self.model = None
        
        # 共通音声ユーティリティ
        self.audio_utils = get_audio_utils(self.preprocessor.sample_rate)
        
        # デバイス設定（共通モジュール使用）
        self.device = get_torch_device()
        device_utils = get_device_utils()
        if device_utils:
            device_info = device_utils.get_compute_devices()
            if device_info['mps']['available']:
                self.logger.device_info("デバイス: Apple Silicon MPS加速")
                self.logger.info("🍎 Apple Silicon M4 Pro optimizations enabled")
            elif device_info['cuda']['available']:
                gpu_count = device_info['cuda']['device_count']
                self.logger.device_info(f"デバイス: CUDA GPU加速 ({gpu_count}デバイス)")
            else:
                self.logger.device_info("デバイス: CPU処理")
        else:
            self.logger.info(f"デバイス: {self.device}")
    
    # ==================== データ管理 ====================
    
    def collect_data_files(self) -> Tuple[List[str], List[str]]:
        """データファイルを収集（柔軟な検索）"""
        import glob
        import re
        
        audio_files = []
        text_files = []
        
        # audio_*.wav ファイルを全て検索
        audio_pattern = os.path.join(self.audio_path, "audio_*.wav")
        found_audio_files = glob.glob(audio_pattern)
        
        for audio_file in sorted(found_audio_files):
            # ファイル名から番号を抽出
            basename = os.path.basename(audio_file)
            match = re.match(r"audio_(\d+)\.wav", basename)
            if match:
                number = match.group(1)
                meta_file = os.path.join(self.meta_path, f"audio_{number}.txt")
                
                # 対応するメタファイルが存在する場合のみ追加
                if os.path.exists(meta_file):
                    audio_files.append(audio_file)
                    text_files.append(meta_file)
                else:
                    self.logger.warning(f"Missing meta file for {basename}")
        
        self.logger.info(f"Found {len(audio_files)} audio-text pairs")
        return audio_files, text_files
    
    def add_new_data(self, new_audio_path: str, new_text_path: str):
        """新しいデータを追加"""
        existing_files, _ = self.collect_data_files()
        next_index = len(existing_files) + 1
        
        new_audio_dest = os.path.join(self.audio_path, f"audio_{next_index}.wav")
        new_text_dest = os.path.join(self.meta_path, f"meta_{next_index}.txt")
        
        try:
            shutil.copy2(new_audio_path, new_audio_dest)
            shutil.copy2(new_text_path, new_text_dest)
            print(f"Added new data: audio_{next_index}.wav, meta_{next_index}.txt")
        except Exception as e:
            print(f"Error adding new data: {e}")
    
    # ==================== モデル管理 ====================
    
    def train_model(self, epochs: int = 50, batch_size: int = 4, learning_rate: float = 1e-3):
        """モデル訓練メイン関数"""
        self.logger.start_operation("モデル訓練")
        
        try:
            # 1. データ準備フェーズ
            dataloader = self._prepare_training_data(batch_size)
            if dataloader is None:
                return
            
            # 2. 訓練コンポーネント初期化
            optimizer, criterion = self._initialize_training_components(learning_rate)
            
            # 3. 訓練ループ実行
            self._execute_training_loop(epochs, dataloader, optimizer, criterion)
            
            self.logger.complete_operation("モデル訓練")
            
        except Exception as e:
            self.logger.error(f"モデル訓練エラー: {e}")
            raise
    
    def _prepare_training_data(self, batch_size: int) -> Optional[DataLoader]:
        """訓練データの準備"""
        # データ収集
        audio_files, text_files = self.collect_data_files()
        if len(audio_files) == 0:
            self.logger.error("No training data found!")
            return None
        
        # テキスト処理と語彙構築
        texts = self._load_and_process_texts(text_files)
        self.text_processor.build_vocab(texts)
        self.logger.info(f"Built vocabulary with {len(self.text_processor.vocab)} characters")
        
        # データセット作成
        dataset = VoiceDataset(audio_files, text_files, self.preprocessor, self.text_processor)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True, 
                               collate_fn=dataset.collate_fn)
        
        self.logger.info(f"データセット準備完了: {len(audio_files)} ファイル, {len(dataloader)} バッチ")
        return dataloader
    
    def _load_and_process_texts(self, text_files: List[str]) -> List[str]:
        """テキストファイルの読み込みと前処理"""
        texts = []
        for text_file in text_files:
            try:
                with open(text_file, 'r', encoding='utf-8') as f:
                    texts.append(self.text_processor.clean_text(f.read()))
            except Exception as e:
                self.logger.warning(f"テキストファイル読み込みエラー {text_file}: {e}")
                continue
        return texts
    
    def _initialize_training_components(self, learning_rate: float) -> Tuple[optim.Optimizer, nn.Module]:
        """訓練コンポーネントの初期化"""
        # モデル初期化
        if self.model is None:
            vocab_size = len(self.text_processor.vocab)
            self.model = VoiceCloneModel(vocab_size).to(self.device)
            self.logger.info(f"モデル初期化完了: 語彙サイズ {vocab_size}")
        
        # 最適化器と損失関数
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()
        self.model.train()
        
        self.logger.info(f"最適化器設定: Adam, lr={learning_rate}")
        return optimizer, criterion
    
    def _execute_training_loop(self, epochs: int, dataloader: DataLoader, 
                              optimizer: optim.Optimizer, criterion: nn.Module):
        """訓練ループの実行"""
        for epoch in range(epochs):
            total_loss = 0
            num_batches = len(dataloader)
            
            for batch_idx, batch_data in enumerate(dataloader):
                loss = self._process_training_batch(batch_data, optimizer, criterion)
                total_loss += loss
            
            # 進捗ログ
            avg_loss = total_loss / num_batches
            self._log_training_progress(epoch + 1, epochs, avg_loss)
    
    def _process_training_batch(self, batch_data: Tuple, optimizer: optim.Optimizer, 
                               criterion: nn.Module) -> float:
        """単一バッチの訓練処理"""
        audio_features, audio_lengths, text_sequences, text_lengths = batch_data
        
        # データをデバイスに移動
        audio_features = audio_features.to(self.device)
        text_sequences = text_sequences.to(self.device)
        audio_lengths = audio_lengths.to(self.device)
        text_lengths = text_lengths.to(self.device)
        
        # 勾配リセット
        optimizer.zero_grad()
        
        # 順伝播
        mel_outputs, stop_tokens = self.model(text_sequences, text_lengths, audio_features)
        
        # 損失計算と逆伝播
        loss = criterion(mel_outputs, audio_features)
        loss.backward()
        optimizer.step()
        
        return loss.item()
    
    def _log_training_progress(self, epoch: int, total_epochs: int, avg_loss: float):
        """訓練進捗のログ出力"""
        self.logger.debug(f"Epoch [{epoch}/{total_epochs}], Loss: {avg_loss:.4f}")
        
        # 一定間隔で詳細ログ
        if epoch % 10 == 0 or epoch == total_epochs:
            self.logger.info(f"訓練進捗: Epoch {epoch}/{total_epochs}, 平均損失: {avg_loss:.4f}")
    
    def save_model(self, model_path: Optional[str] = None):
        """モデル保存"""
        if model_path is None:
            model_path = os.path.join(self.models_path, "voice_clone_model.pth")
        
        if self.model is not None:
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'text_processor': self.text_processor,
                'preprocessor': self.preprocessor
            }, model_path)
            print(f"Model saved to: {model_path}")
        else:
            print("No model to save!")
    
    def load_model(self, model_path: Optional[str] = None):
        """モデル読み込み"""
        if model_path is None:
            model_path = os.path.join(self.models_path, "voice_clone_model.pth")
        
        checkpoint = torch.load(model_path, map_location=self.device)
        
        # コンポーネント復元
        self.text_processor = checkpoint['text_processor']
        self.preprocessor = checkpoint['preprocessor']
        
        # モデル再構築
        vocab_size = len(self.text_processor.vocab)
        self.model = VoiceCloneModel(vocab_size=vocab_size).to(self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
        
        print(f"Model loaded from: {model_path}")
    
    # ==================== 音声合成 ====================
    
    def synthesize_speech(self, text: str, output_filename: Optional[str] = None) -> bool:
        """音声合成のメイン関数"""
        if self.model is None:
            print("❌ モデルが読み込まれていません。先にモデルを読み込んでください。")
            return False
        
        try:
            print(f"音声合成中: '{text}'")
            
            # テキスト前処理
            text_tensor, text_lengths = self._preprocess_text(text)
            
            # メルスペクトログラム生成
            mel_outputs = self._generate_mel_spectrogram(text_tensor, text_lengths)
            
            # 音声生成
            audio = self._generate_audio(mel_outputs)
            
            # 音声保存
            output_path = self._save_audio(audio, output_filename)
            
            # 結果表示
            self._display_results(text, output_path, audio)
            self.logger.complete_operation(f"音声合成: '{text}'")
            return True
            
        except Exception as e:
            self.logger.error(f"音声合成エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _preprocess_text(self, text: str) -> Tuple[torch.Tensor, torch.Tensor]:
        """テキスト前処理"""
        text_sequence = self.text_processor.text_to_sequence(text)
        text_tensor = torch.LongTensor(text_sequence).unsqueeze(0).to(self.device)
        text_lengths = torch.LongTensor([len(text_sequence)]).to(self.device)
        
        self.logger.debug(f"テキスト長: {len(text_sequence)} → 期待される音声長: {len(text_sequence) * 0.1:.1f}秒")
        return text_tensor, text_lengths
    
    def _generate_mel_spectrogram(self, text_tensor: torch.Tensor, text_lengths: torch.Tensor) -> torch.Tensor:
        """メルスペクトログラム生成"""
        self.model.eval()
        with torch.no_grad():
            # モデル推論
            mel_outputs, stop_outputs = self.model(text_tensor, text_lengths)
            
            # 正規化
            mel_outputs = self._normalize_mel_spectrogram(mel_outputs)
            
            # 長さ制御
            mel_outputs = self._control_length(mel_outputs, text_tensor)
        
        self.logger.debug(f"生成されたメルスペクトログラム:")
        self.logger.debug(f"  フレーム数: {mel_outputs.shape[1]}")
        self.logger.debug(f"  予想音声長: {mel_outputs.shape[1] * self.DEFAULT_HOP_LENGTH / self.preprocessor.sample_rate:.2f}秒")
        self.logger.debug(f"  メル範囲: [{mel_outputs.min():.3f}, {mel_outputs.max():.3f}]")
        
        return mel_outputs.squeeze(0).cpu()
    
    def _normalize_mel_spectrogram(self, mel_outputs: torch.Tensor) -> torch.Tensor:
        """メルスペクトログラムの正規化"""
        # 極端な値をクリッピング
        mel_clipped = torch.clamp(mel_outputs, min=self.MEL_CLIP_MIN, max=self.MEL_CLIP_MAX)
        
        # 正規化
        mel_min, mel_max = mel_clipped.min(), mel_clipped.max()
        if mel_max > mel_min:
            mel_normalized = (mel_clipped - mel_min) / (mel_max - mel_min)
            mel_normalized = mel_normalized * (self.MEL_SCALE_MAX - self.MEL_SCALE_MIN) + self.MEL_SCALE_MIN
        else:
            mel_normalized = mel_clipped
        
        self.logger.debug(f"✓ メル正規化: [{mel_normalized.min():.3f}, {mel_normalized.max():.3f}]")
        
        # 異常値チェック
        if torch.isnan(mel_normalized).any() or torch.isinf(mel_normalized).any():
            self.logger.warning("メルスペクトログラムに異常値を検出。修正中...")
            mel_normalized = torch.nan_to_num(mel_normalized, nan=0.0, 
                                            posinf=self.MEL_SCALE_MAX, neginf=self.MEL_SCALE_MIN)
        
        return mel_normalized
    
    def _control_length(self, mel_outputs: torch.Tensor, text_tensor: torch.Tensor) -> torch.Tensor:
        """音声長制御"""
        if mel_outputs.shape[1] < self.MIN_FRAME_LENGTH:
            self.logger.warning(f"出力が短すぎます（{mel_outputs.shape[1]}フレーム）。拡張中...")
            
            target_length = max(self.MIN_FRAME_LENGTH, len(text_tensor[0]) * 15)
            last_frame = mel_outputs[:, -1:, :]
            repeat_count = target_length - mel_outputs.shape[1]
            
            # 自然な拡張
            decay_factor = torch.linspace(1.0, 0.8, repeat_count).unsqueeze(0).unsqueeze(2).to(mel_outputs.device)
            noise = torch.randn_like(last_frame.repeat(1, repeat_count, 1)) * 0.05
            padding = last_frame.repeat(1, repeat_count, 1) * decay_factor + noise
            
            mel_outputs = torch.cat([mel_outputs, padding], dim=1)
            self.logger.debug(f"✓ {target_length}フレームに拡張しました")
        
        return mel_outputs
    
    def _generate_audio(self, mel_spec: torch.Tensor) -> torch.Tensor:
        """音声生成（ボコーダー選択）"""
        self.logger.info("音声合成中...")
        
        # 五十音台本データの有無をチェック
        has_phoneme_data = self._check_phoneme_training_data()
        
        if has_phoneme_data:
            # 台本データありの場合の優先順位
            vocoder_methods = [
                (self._trained_phoneme_vocoder, "訓練済み五十音ボコーダー"),
                (self._japanese_phoneme_vocoder, "理論五十音ボコーダー"),
                (self._reliable_vocoder, "確実シンプルボコーダー")
            ]
        else:
            # 台本データなしの場合の優先順位（現在の状態）
            vocoder_methods = [
                (self._japanese_phoneme_vocoder, "五十音対応ボコーダー"),
                (self._reliable_vocoder, "確実シンプルボコーダー"),
                (self._improved_vocoder, "改善ボコーダー")
            ]
        
        for vocoder_func, vocoder_name in vocoder_methods:
            try:
                audio = vocoder_func(mel_spec)
                self.logger.info(f"使用ボコーダー: {vocoder_name}")
                return self._postprocess_audio(audio)
            except Exception as e:
                self.logger.warning(f"{vocoder_name}エラー: {e}")
                continue
        
        # 最終フォールバック
        self.logger.error("全てのボコーダーが失敗。フォールバック音声を生成...")
        duration = mel_spec.shape[0] * self.DEFAULT_HOP_LENGTH / self.preprocessor.sample_rate
        t = np.linspace(0, duration, int(duration * self.preprocessor.sample_rate))
        audio = 0.1 * np.sin(2 * np.pi * 200 * t)
        return torch.from_numpy(audio.astype(np.float32))
    
    def _postprocess_audio(self, audio: torch.Tensor) -> torch.Tensor:
        """音声後処理"""
        max_amp = torch.max(torch.abs(audio))
        self.logger.debug(f"生成音声の最大振幅: {max_amp:.6f}")
        
        if max_amp > 1.0:
            audio = audio / max_amp * 0.8
        elif max_amp < 0.01:
            audio = audio / max_amp * 0.5
        
        return audio
    
    def _save_audio(self, audio: torch.Tensor, output_filename: Optional[str] = None) -> str:
        """音声保存"""
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"synthesized_{timestamp}.wav"
        
        if not output_filename.endswith('.wav'):
            output_filename += '.wav'
        
        output_path = os.path.join(self.output_path, output_filename)
        torchaudio.save(output_path, audio.unsqueeze(0), self.preprocessor.sample_rate)
        
        return output_path
    
    def _display_results(self, text: str, output_path: str, audio: torch.Tensor):
        """結果表示"""
        duration = len(audio) / self.preprocessor.sample_rate
        # これらはユーザーインターフェースとしてprintを保持
        print(f"✓ 音声合成完了!")
        print(f"  入力テキスト: '{text}'")
        print(f"  出力ファイル: {output_path}")
        print(f"  音声長: {duration:.2f}秒")
        print(f"  最終振幅範囲: [{torch.min(audio):.3f}, {torch.max(audio):.3f}]")
        # ログにも記録
        self.logger.info(f"音声合成完了: '{text}' → {output_path} ({duration:.2f}秒)")
    
    # ==================== ボコーダー実装 ====================
    
    def _reliable_vocoder(self, mel_spec: torch.Tensor) -> torch.Tensor:
        """確実に動作するシンプルボコーダー"""
        self.logger.debug(f"確実ボコーダー入力: {mel_spec.shape}")
        
        # メルスペクトログラムの基本パラメータ
        mel_np = mel_spec.T.numpy() if mel_spec.shape[1] == self.DEFAULT_N_MELS else mel_spec.numpy()
        n_frames, n_mels = mel_np.shape
        
        # パラメータ設定
        sample_rate = self.preprocessor.sample_rate
        hop_length = self.DEFAULT_HOP_LENGTH
        audio_length = n_frames * hop_length
        audio = np.zeros(audio_length)
        
        print(f"フレーム数: {n_frames}, 予想音声長: {audio_length / sample_rate:.2f}秒")
        
        # 基本周波数設定（日本語話者向け）
        f0_base = 150  # Hz
        
        # フレームごとの音声生成
        for frame_idx in range(n_frames):
            frame_start = frame_idx * hop_length
            frame_end = min(frame_start + hop_length, audio_length)
            frame_length = frame_end - frame_start
            
            frame_mel = mel_np[frame_idx, :]
            energy = np.mean(np.exp(frame_mel))
            
            if energy > 0.01:  # エネルギー閾値
                t = np.arange(frame_length) / sample_rate
                frame_audio = np.zeros(frame_length)
                
                # 基本周波数決定
                low_freq_energy = np.mean(frame_mel[:8])
                f0 = f0_base * (1 + low_freq_energy / 10)
                f0 = np.clip(f0, 80, 400)
                
                # 調波構造の生成
                for harmonic in range(1, 4):  # 1-3次調波
                    freq = f0 * harmonic
                    if freq < sample_rate / 2:
                        mel_idx = min(int(harmonic * 8), n_mels - 1)
                        amplitude = np.exp(frame_mel[mel_idx] / 4) / harmonic
                        amplitude = np.clip(amplitude, 0, 1)
                        
                        sine_wave = amplitude * np.sin(2 * np.pi * freq * t)
                        frame_audio += sine_wave
                
                audio[frame_start:frame_end] = frame_audio
        
        # 後処理
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio)) * 0.3
            
            # スムージング
            if len(audio) > 3:
                for i in range(1, len(audio) - 1):
                    audio[i] = (audio[i-1] + audio[i] + audio[i+1]) / 3
        
        print(f"確実ボコーダー完了: {len(audio)} samples, 範囲: [{audio.min():.3f}, {audio.max():.3f}]")
        return torch.from_numpy(audio.astype(np.float32))
    
    def _improved_vocoder(self, mel_spec: torch.Tensor) -> torch.Tensor:
        """改善されたボコーダー"""
        mel_np = mel_spec.T.numpy() if mel_spec.shape[1] == self.DEFAULT_N_MELS else mel_spec.numpy()
        
        sample_rate = self.preprocessor.sample_rate
        hop_length = self.DEFAULT_HOP_LENGTH
        audio_length = mel_np.shape[0] * hop_length
        audio = np.zeros(audio_length)
        
        # 基本周波数推定
        f0 = np.zeros(mel_np.shape[0])
        for i in range(mel_np.shape[0]):
            low_freq_power = mel_np[i, :30]
            if np.max(low_freq_power) > -35:
                f0[i] = 80 + np.argmax(low_freq_power) * 8
                
                if i > 0 and f0[i-1] > 0:
                    if abs(f0[i] - f0[i-1]) > 50:
                        f0[i] = (f0[i] + f0[i-1]) / 2
        
        # 音声合成
        for frame_idx in range(mel_np.shape[0]):
            frame_start = frame_idx * hop_length
            frame_end = min(frame_start + hop_length, audio_length)
            
            if f0[frame_idx] > 0:
                t = np.arange(frame_end - frame_start) / sample_rate
                
                for harmonic in range(1, 8):
                    freq = f0[frame_idx] * harmonic
                    if freq < sample_rate / 2:
                        freq_bin = min(int(freq * mel_np.shape[1] * 2 / sample_rate), mel_np.shape[1] - 1)
                        magnitude = mel_np[frame_idx, freq_bin]
                        
                        if magnitude > -45:
                            amplitude = np.exp(magnitude / 25) / (harmonic ** 0.7) * 0.15
                            phase = np.random.random() * 2 * np.pi
                            sine_wave = amplitude * np.sin(2 * np.pi * freq * t + phase)
                            audio[frame_start:frame_end] += sine_wave
        
        # 正規化とエンベロープ
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio)) * 0.7
            
            # フェード処理
            fade_samples = int(len(audio) * 0.02)
            if fade_samples > 0:
                audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
                audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        
        return torch.from_numpy(audio.astype(np.float32))
    
    def _simple_vocoder(self, mel_spec: torch.Tensor) -> torch.Tensor:
        """シンプルボコーダー"""
        mel_np = mel_spec.numpy() if hasattr(mel_spec, 'numpy') else mel_spec.detach().cpu().numpy()
        
        sample_rate = self.preprocessor.sample_rate
        hop_length = self.DEFAULT_HOP_LENGTH
        audio_length = mel_np.shape[0] * hop_length
        audio = np.zeros(audio_length)
        
        # 周波数マッピング
        mel_frequencies = np.linspace(0, sample_rate // 2, mel_np.shape[1])
        
        for frame_idx in range(mel_np.shape[0]):
            frame_start = frame_idx * hop_length
            frame_end = min(frame_start + hop_length, audio_length)
            
            for freq_bin in range(mel_np.shape[1]):
                magnitude = mel_np[frame_idx, freq_bin]
                frequency = mel_frequencies[freq_bin]
                
                if magnitude > -40:
                    t = np.arange(frame_end - frame_start) / sample_rate
                    amplitude = min(np.exp(magnitude / 20), 0.1)
                    phase = np.random.random() * 2 * np.pi
                    sine_wave = amplitude * np.sin(2 * np.pi * frequency * t + phase)
                    audio[frame_start:frame_end] += sine_wave
        
        # 正規化
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio)) * 0.8
        
        return torch.from_numpy(audio.astype(np.float32))

    def _japanese_phoneme_vocoder(self, mel_spec: torch.Tensor) -> torch.Tensor:
        """五十音表対応日本語音韻ボコーダー"""
        self.logger.debug(f"五十音対応ボコーダー入力: {mel_spec.shape}")
        
        # 五十音の音韻特徴データベース
        japanese_phonemes = {
            # あ行 (a-gyou)
            'a': {'formants': [730, 1090, 2440], 'f0_mod': 1.0, 'energy': 'high'},
            'i': {'formants': [270, 2290, 3010], 'f0_mod': 1.1, 'energy': 'medium'},
            'u': {'formants': [300, 870, 2240], 'f0_mod': 0.9, 'energy': 'low'},
            'e': {'formants': [530, 1840, 2480], 'f0_mod': 1.0, 'energy': 'medium'},
            'o': {'formants': [570, 840, 2410], 'f0_mod': 0.95, 'energy': 'medium'},
            
            # か行 (ka-gyou) - 子音k + 母音
            'ka': {'formants': [730, 1200, 2400], 'f0_mod': 1.0, 'energy': 'high', 'burst': True},
            'ki': {'formants': [270, 2400, 3100], 'f0_mod': 1.1, 'energy': 'medium', 'burst': True},
            'ku': {'formants': [300, 900, 2200], 'f0_mod': 0.9, 'energy': 'low', 'burst': True},
            'ke': {'formants': [530, 1900, 2500], 'f0_mod': 1.0, 'energy': 'medium', 'burst': True},
            'ko': {'formants': [570, 900, 2400], 'f0_mod': 0.95, 'energy': 'medium', 'burst': True},
            
            # さ行 (sa-gyou) - 摩擦音
            'sa': {'formants': [730, 1200, 2600], 'f0_mod': 1.0, 'energy': 'high', 'fricative': True},
            'shi': {'formants': [300, 2200, 3200], 'f0_mod': 1.1, 'energy': 'medium', 'fricative': True},
            'su': {'formants': [300, 900, 2400], 'f0_mod': 0.9, 'energy': 'low', 'fricative': True},
            'se': {'formants': [530, 1900, 2600], 'f0_mod': 1.0, 'energy': 'medium', 'fricative': True},
            'so': {'formants': [570, 900, 2500], 'f0_mod': 0.95, 'energy': 'medium', 'fricative': True},
            
            # た行 (ta-gyou) - 破裂音
            'ta': {'formants': [730, 1200, 2400], 'f0_mod': 1.0, 'energy': 'high', 'plosive': True},
            'chi': {'formants': [300, 2100, 3000], 'f0_mod': 1.1, 'energy': 'medium', 'plosive': True},
            'tsu': {'formants': [300, 900, 2300], 'f0_mod': 0.9, 'energy': 'low', 'plosive': True},
            'te': {'formants': [530, 1800, 2500], 'f0_mod': 1.0, 'energy': 'medium', 'plosive': True},
            'to': {'formants': [570, 900, 2400], 'f0_mod': 0.95, 'energy': 'medium', 'plosive': True},
            
            # な行 (na-gyou) - 鼻音
            'na': {'formants': [730, 1200, 2400], 'f0_mod': 1.0, 'energy': 'medium', 'nasal': True},
            'ni': {'formants': [270, 2200, 3000], 'f0_mod': 1.1, 'energy': 'medium', 'nasal': True},
            'nu': {'formants': [300, 900, 2200], 'f0_mod': 0.9, 'energy': 'low', 'nasal': True},
            'ne': {'formants': [530, 1800, 2500], 'f0_mod': 1.0, 'energy': 'medium', 'nasal': True},
            'no': {'formants': [570, 900, 2400], 'f0_mod': 0.95, 'energy': 'medium', 'nasal': True},
            
            # は行 (ha-gyou) - 摩擦音/半母音
            'ha': {'formants': [730, 1200, 2400], 'f0_mod': 1.0, 'energy': 'medium', 'breath': True},
            'hi': {'formants': [270, 2200, 3100], 'f0_mod': 1.1, 'energy': 'medium', 'breath': True},
            'fu': {'formants': [300, 900, 2200], 'f0_mod': 0.9, 'energy': 'low', 'breath': True},
            'he': {'formants': [530, 1800, 2500], 'f0_mod': 1.0, 'energy': 'medium', 'breath': True},
            'ho': {'formants': [570, 900, 2400], 'f0_mod': 0.95, 'energy': 'medium', 'breath': True},
            
            # ま行 (ma-gyou) - 鼻音
            'ma': {'formants': [730, 1200, 2400], 'f0_mod': 1.0, 'energy': 'medium', 'nasal': True},
            'mi': {'formants': [270, 2200, 3000], 'f0_mod': 1.1, 'energy': 'medium', 'nasal': True},
            'mu': {'formants': [300, 900, 2200], 'f0_mod': 0.9, 'energy': 'low', 'nasal': True},
            'me': {'formants': [530, 1800, 2500], 'f0_mod': 1.0, 'energy': 'medium', 'nasal': True},
            'mo': {'formants': [570, 900, 2400], 'f0_mod': 0.95, 'energy': 'medium', 'nasal': True},
            
            # や行 (ya-gyou) - 半母音
            'ya': {'formants': [730, 1200, 2400], 'f0_mod': 1.0, 'energy': 'medium', 'glide': True},
            'yu': {'formants': [300, 900, 2200], 'f0_mod': 0.9, 'energy': 'low', 'glide': True},
            'yo': {'formants': [570, 900, 2400], 'f0_mod': 0.95, 'energy': 'medium', 'glide': True},
            
            # ら行 (ra-gyou) - 流音
            'ra': {'formants': [730, 1300, 2400], 'f0_mod': 1.0, 'energy': 'medium', 'liquid': True},
            'ri': {'formants': [270, 2300, 3000], 'f0_mod': 1.1, 'energy': 'medium', 'liquid': True},
            'ru': {'formants': [300, 1000, 2200], 'f0_mod': 0.9, 'energy': 'low', 'liquid': True},
            're': {'formants': [530, 1900, 2500], 'f0_mod': 1.0, 'energy': 'medium', 'liquid': True},
            'ro': {'formants': [570, 1000, 2400], 'f0_mod': 0.95, 'energy': 'medium', 'liquid': True},
            
            # わ行 (wa-gyou) - 半母音
            'wa': {'formants': [730, 1200, 2400], 'f0_mod': 1.0, 'energy': 'medium', 'glide': True},
            'wo': {'formants': [570, 900, 2400], 'f0_mod': 0.95, 'energy': 'medium', 'glide': True},
            
            # ん (n) - 鼻音
            'n': {'formants': [400, 1200, 2400], 'f0_mod': 0.8, 'energy': 'low', 'nasal': True}
        }
        
        # メルスペクトログラムの基本パラメータ
        mel_np = mel_spec.T.numpy() if mel_spec.shape[1] == self.DEFAULT_N_MELS else mel_spec.numpy()
        n_frames, n_mels = mel_np.shape
        
        sample_rate = self.preprocessor.sample_rate
        hop_length = self.DEFAULT_HOP_LENGTH
        audio_length = n_frames * hop_length
        audio = np.zeros(audio_length)
        
        print(f"フレーム数: {n_frames}, 予想音声長: {audio_length / sample_rate:.2f}秒")
        
        # フレームごとの処理
        for frame_idx in range(n_frames):
            frame_start = frame_idx * hop_length
            frame_end = min(frame_start + hop_length, audio_length)
            frame_length = frame_end - frame_start
            
            frame_mel = mel_np[frame_idx, :]
            
            # エネルギー検出
            energy = np.mean(np.exp(frame_mel))
            if energy > 0.005:
                t = np.arange(frame_length) / sample_rate
                frame_audio = np.zeros(frame_length)
                
                # 音韻タイプの推定（より詳細）
                phoneme_type = self._estimate_phoneme_type(frame_mel)
                phoneme_data = japanese_phonemes.get(phoneme_type, japanese_phonemes['a'])
                
                # 基本周波数の決定
                low_freq_energy = np.mean(frame_mel[:12])
                f0_base = 140 * phoneme_data['f0_mod']  # 音韻に応じた基本周波数
                f0 = f0_base * (1 + low_freq_energy / 8)
                f0 = np.clip(f0, 70, 350)
                
                # フォルマント合成
                frame_audio += self._synthesize_formants(
                    t, phoneme_data['formants'], frame_mel, n_mels, sample_rate
                )
                
                # 音韻特性に応じた追加処理
                if phoneme_data.get('burst'):
                    frame_audio += self._add_burst_noise(t, frame_mel)
                elif phoneme_data.get('fricative'):
                    frame_audio += self._add_fricative_noise(t, frame_mel)
                elif phoneme_data.get('nasal'):
                    frame_audio += self._add_nasal_resonance(t, f0, frame_mel)
                elif phoneme_data.get('breath'):
                    frame_audio += self._add_breath_noise(t, frame_mel)
                
                # 基本周波数成分の追加
                frame_audio += self._add_fundamental_harmonics(t, f0, frame_mel, n_mels)
                
                audio[frame_start:frame_end] = frame_audio
        
        # 後処理
        audio = self._postprocess_japanese_audio(audio)
        
        print(f"五十音対応ボコーダー完了: {len(audio)} samples, 範囲: [{audio.min():.3f}, {audio.max():.3f}]")
        return torch.from_numpy(audio.astype(np.float32))

    def _estimate_phoneme_type(self, frame_mel):
        """メルスペクトログラムから音韻タイプを推定"""
        low_energy = np.mean(frame_mel[:15])      # 低域 (0-1500Hz)
        mid_energy = np.mean(frame_mel[15:40])    # 中域 (1500-4000Hz)  
        high_energy = np.mean(frame_mel[40:])     # 高域 (4000Hz+)
        
        # エネルギー分布に基づく音韻推定
        if high_energy > mid_energy and high_energy > low_energy:
            if mid_energy > low_energy:
                return 'i'  # い系
            else:
                return 'shi'  # し系（摩擦音）
        elif low_energy > mid_energy and low_energy > high_energy:
            if mid_energy < -30:
                return 'u'  # う系
            else:
                return 'o'  # お系
        elif mid_energy > low_energy and mid_energy > high_energy:
            return 'e'  # え系
        else:
            return 'a'  # あ系（デフォルト）

    def _synthesize_formants(self, t, formants, frame_mel, n_mels, sample_rate):
        """フォルマント合成"""
        audio = np.zeros(len(t))
        
        for formant_freq in formants:
            if formant_freq < sample_rate / 2:
                # フォルマント周波数に対応するメルbin
                mel_bin = min(int(formant_freq * n_mels / (sample_rate/2)), n_mels-1)
                formant_energy = frame_mel[mel_bin]
                
                if formant_energy > -35:
                    # フォルマントの振幅
                    amplitude = np.exp(formant_energy / 12) * 0.08
                    amplitude = np.clip(amplitude, 0, 0.2)
                    
                    # フォルマント帯域幅
                    bandwidth = formant_freq * 0.08
                    
                    # 帯域幅をシミュレート
                    for offset in [-bandwidth/2, 0, bandwidth/2]:
                        freq = formant_freq + offset
                        if freq > 0 and freq < sample_rate / 2:
                            sine_wave = amplitude * np.sin(2 * np.pi * freq * t)
                            audio += sine_wave / 3
        
        return audio

    def _add_burst_noise(self, t, frame_mel):
        """破裂音のバースト雑音"""
        if np.mean(frame_mel[20:40]) > -30:  # 中高域にエネルギーがある場合
            burst_duration = min(len(t), int(len(t) * 0.1))  # 10%の長さ
            burst_noise = np.random.random(burst_duration) * 0.05
            audio = np.zeros(len(t))
            audio[:burst_duration] = burst_noise
            return audio
        return np.zeros(len(t))

    def _add_fricative_noise(self, t, frame_mel):
        """摩擦音の雑音"""
        if np.mean(frame_mel[30:]) > -35:  # 高域にエネルギーがある場合
            # 高周波雑音
            noise = np.random.random(len(t)) * 0.03
            # 高域フィルタ
            cutoff_freq = 2000  # 2kHz以上
            noise_filtered = noise  # 簡易実装
            return noise_filtered
        return np.zeros(len(t))

    def _add_nasal_resonance(self, t, f0, frame_mel):
        """鼻音の共鳴"""
        if f0 > 0:
            # 鼻腔共鳴周波数 (約1000Hz)
            nasal_freq = 1000
            amplitude = np.exp(np.mean(frame_mel[:20]) / 15) * 0.05
            amplitude = np.clip(amplitude, 0, 0.1)
            
            nasal_tone = amplitude * np.sin(2 * np.pi * nasal_freq * t)
            return nasal_tone
        return np.zeros(len(t))

    def _add_breath_noise(self, t, frame_mel):
        """気息音の追加"""
        if np.mean(frame_mel) > -30:
            # 低レベルの広帯域雑音
            breath = np.random.random(len(t)) * 0.02
            return breath
        return np.zeros(len(t))

    def _add_fundamental_harmonics(self, t, f0, frame_mel, n_mels):
        """基本周波数と調波の追加"""
        audio = np.zeros(len(t))
        
        if f0 > 0:
            for harmonic in range(1, 6):  # 1-5次調波
                freq = f0 * harmonic
                if freq < 11000:  # サンプリング周波数の半分未満
                    mel_idx = min(int(harmonic * 10), n_mels - 1)
                    amplitude = np.exp(frame_mel[mel_idx] / 15) / (harmonic ** 0.7)
                    amplitude = np.clip(amplitude, 0, 0.15)
                    
                    sine_wave = amplitude * np.sin(2 * np.pi * freq * t)
                    audio += sine_wave
        
        return audio

    def _postprocess_japanese_audio(self, audio):
        """日本語音声特化の後処理"""
        if np.max(np.abs(audio)) > 0:
            # 正規化
            audio = audio / np.max(np.abs(audio)) * 0.35
            
            # より自然なスムージング
            if len(audio) > 7:
                window_size = 7
                for i in range(window_size//2, len(audio) - window_size//2):
                    audio[i] = np.mean(audio[i-window_size//2:i+window_size//2+1])
            
            # フェード処理
            fade_samples = int(len(audio) * 0.005)  # 0.5%
            if fade_samples > 0:
                audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
                audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        
        return audio

    def _check_phoneme_training_data(self) -> bool:
        """五十音台本データの存在チェック"""
        phoneme_data_path = os.path.join(self.dataset_path, "phoneme_data")
        return os.path.exists(phoneme_data_path) and len(os.listdir(phoneme_data_path)) > 0

    def _trained_phoneme_vocoder(self, mel_spec: torch.Tensor) -> torch.Tensor:
        """訓練済み五十音データを使用したボコーダー"""
        print("実測データに基づく五十音ボコーダーを使用")
        
        # 実際の録音データから抽出したフォルマント特徴を使用
        measured_phonemes = self._load_measured_phoneme_features()
        
        # 既存の_japanese_phoneme_vocoderをベースに
        # measured_phonemesの実測値で上書き
        return self._synthesize_with_measured_features(mel_spec, measured_phonemes)