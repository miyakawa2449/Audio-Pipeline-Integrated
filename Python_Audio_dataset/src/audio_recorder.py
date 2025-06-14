import sounddevice as sd
import numpy as np
import threading
import time
import sys
import os
from pathlib import Path

class AudioRecorder:
    def __init__(self, sample_rate=44100, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self.is_paused = False
        self.recorded_data = []
        self.recording_thread = None
        self.input_thread = None
        self.should_stop = False
        
    def reset_recording(self):
        """録音状態をリセット"""
        self.is_recording = False
        self.is_paused = False
        self.recorded_data = []
        self.should_stop = False
        
        # 既存のスレッドが残っている場合は終了を待つ
        if self.recording_thread and self.recording_thread.is_alive():
            self.should_stop = True
            self.recording_thread.join(timeout=1)
            
        if self.input_thread and self.input_thread.is_alive():
            self.input_thread.join(timeout=1)
        
        print("🔄 録音状態をリセットしました")
        
    def start_recording(self):
        """録音開始（カウントダウンなし）"""
        if self.is_recording:
            print("⚠️ 既に録音中です")
            return False
            
        # 録音デバイス確認（簡潔に）
        try:
            devices = sd.query_devices()
            default_input = sd.default.device[0]
            print(f"🎤 使用デバイス: {devices[default_input]['name']}")
        except Exception as e:
            print(f"❌ 音声デバイスエラー: {e}")
            return False
            
        # カウントダウン除去 - 直接録音開始
        print("🔴 録音開始！")
        print("操作: [p]一時停止 [s]停止・保存")
        
        # 録音状態初期化
        self.is_recording = True
        self.is_paused = False
        self.should_stop = False
        self.recorded_data = []
        
        # 録音スレッド開始
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.daemon = True
        self.recording_thread.start()
        
        return True  # 即座にTrueを返す（録音継続は別スレッド）
    
    def _record_audio(self):
        """録音処理（別スレッド）"""
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"⚠️ 録音ステータス: {status}")
            
            if self.is_recording and not self.is_paused:
                self.recorded_data.append(indata.copy())
        
        try:
            with sd.InputStream(
                channels=self.channels,
                samplerate=self.sample_rate,
                callback=audio_callback,
                dtype=np.float32
            ) as stream:
                while self.is_recording and not self.should_stop:
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"❌ 録音エラー: {e}")
            self.is_recording = False
    
    def resume_recording(self):
        """録音再開"""
        if self.is_paused:
            self.is_paused = False
            print("▶️ 録音再開")
            return True
        return False
    
    def pause_recording(self):
        """録音一時停止"""
        if self.is_recording and not self.is_paused:
            self.is_paused = True
            print("⏸️ 録音一時停止")
            return True
        return False
    
    def stop_recording(self):
        """録音停止して音声データを返す"""
        if not self.is_recording:
            return None
            
        print("⏹️ 録音停止中...")
        self.is_recording = False
        self.is_paused = False
        
        # スレッド終了を待機
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2)
        
        print("✅ 録音完了")
        return self.get_recorded_audio()
    
    def get_recorded_audio(self):
        """録音データを取得"""
        if not self.recorded_data:
            return None
            
        try:
            audio_data = np.concatenate(self.recorded_data, axis=0)
            return audio_data
        except Exception as e:
            print(f"❌ 音声データ変換エラー: {e}")
            return None
    
    def save_audio(self, audio_data, filename):
        """音声ファイル保存（元の仕様に合わせる）"""
        if audio_data is None:
            print("❌ 保存する録音データがありません")
            return False
            
        try:
            import soundfile as sf
            
            # フルパスでない場合はdataset/audio_files/に保存
            if not os.path.isabs(filename):
                audio_dir = Path("dataset/audio_files")
                audio_dir.mkdir(parents=True, exist_ok=True)
                filepath = audio_dir / filename
            else:
                filepath = Path(filename)
                filepath.parent.mkdir(parents=True, exist_ok=True)
            
            sf.write(str(filepath), audio_data, self.sample_rate)
            duration = len(audio_data) / self.sample_rate
            print(f"💾 音声保存完了: {filename} ({duration:.2f}秒)")
            return True
            
        except Exception as e:
            print(f"❌ 音声保存エラー: {e}")
            return False
    
    def play_audio(self, audio_data=None):
        """録音音声の再生"""
        if audio_data is None:
            audio_data = self.get_recorded_audio()
            
        if audio_data is None:
            print("❌ 再生する音声データがありません")
            return False
            
        try:
            print("🔊 音声再生中...")
            sd.play(audio_data, self.sample_rate)
            sd.wait()  # 再生完了まで待機
            print("✅ 再生完了")
            return True
        except Exception as e:
            print(f"❌ 音声再生エラー: {e}")
            return False