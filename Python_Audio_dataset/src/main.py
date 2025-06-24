import os
import sys
import time
from pathlib import Path

# 安全なinput関数
def safe_input(prompt, default=""):
    """EOFErrorに対応した安全なinput関数"""
    try:
        return input(prompt)
    except EOFError:
        print(f"\n[自動入力] {default}")
        return default
    except KeyboardInterrupt:
        print("\n[中断されました]")
        return "q"

# 統一ログシステムと共通モジュール
sys.path.append(str(Path(__file__).parent.parent.parent / "common"))
try:
    from logger import get_logger
    from audio_utils import get_audio_utils
    from file_utils import setup_directories, create_metadata_file, update_dataset_metadata
    from device_utils import get_audio_devices, log_system_summary
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
    
    def get_logger(name): return FallbackLogger(name)
    def get_audio_utils(*args): return None
    def setup_directories(*args): return True
    def create_metadata_file(*args): return True
    def update_dataset_metadata(*args): return True
    def get_audio_devices(): return {}
    def log_system_summary(): pass

# 必要なモジュールのインポート
from text_manager import TextManager
from audio_recorder import AudioRecorder

class AudioDatasetCreator:
    def __init__(self):
        self.logger = get_logger("AudioDataset")
        self.logger.start_operation("AI音声学習用データセット作成ツール初期化")
        
        # TextManager初期化
        self.text_manager = TextManager()
        
        # AudioRecorder初期化
        self.audio_recorder = AudioRecorder()
        self.current_audio = None
        
        # ディレクトリセットアップ（共通モジュール使用）
        self.setup_directories_common()
        
        # システム情報ログ
        log_system_summary()
        
        # 初期化確認
        self.check_initialization()
        
        # 共通音声ユーティリティ初期化
        self.audio_utils = get_audio_utils(self.audio_recorder.sample_rate)

    def check_initialization(self):
        """初期化状態の確認"""
        print("\n📋 初期化状態確認:")  # ユーザーインターフェース用のみ保持
        
        # テキストファイル確認
        if self.text_manager.all_texts:
            text_count = len(self.text_manager.all_texts)
            filename = self.text_manager.filename
            print(f"✅ テキスト読み込み: {text_count}行")
            print(f"📄 ファイル名: {filename}")
            self.logger.info(f"テキストファイル読み込み成功: {text_count}行 ({filename})")
        else:
            print("❌ テキストが読み込まれていません")
            print("   'rf' コマンドでテキストファイルを読み込んでください")
            self.logger.warning("テキストファイルが読み込まれていません")
        
        # AudioRecorder確認
        sample_rate = self.audio_recorder.sample_rate
        print(f"✅ AudioRecorder初期化: 成功")
        print(f"🎤 サンプルレート: {sample_rate}Hz")
        self.logger.info(f"AudioRecorder初期化成功: {sample_rate}Hz")
        
        # ディレクトリ確認
        required_dirs = ["dataset/audio_files", "dataset/meta_files"]
        for dir_path in required_dirs:
            if Path(dir_path).exists():
                print(f"✅ ディレクトリ: {dir_path}")
                self.logger.debug(f"ディレクトリ確認成功: {dir_path}")
            else:
                print(f"❌ ディレクトリ: {dir_path}")
                self.logger.error(f"ディレクトリが見つかりません: {dir_path}")
        
        self.logger.complete_operation("初期化状態確認")
        
        print("="*50)

    def setup_directories(self):
        """必要なディレクトリを作成（旧版）"""
        Path("dataset/audio_files").mkdir(parents=True, exist_ok=True)
        Path("dataset/meta_files").mkdir(parents=True, exist_ok=True)
    
    def setup_directories_common(self):
        """必要なディレクトリを作成（共通モジュール版）"""
        directories = ["dataset/audio_files", "dataset/meta_files", "data", "logs"]
        
        # フォールバックディレクトリ作成
        for dir_path in directories:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"ディレクトリ作成: {dir_path}")
        
        # 共通モジュール使用（利用可能な場合）
        try:
            success = setup_directories(directories)
            if success:
                self.logger.success("全ディレクトリ作成完了")
            else:
                self.logger.warning("一部ディレクトリ作成に失敗")
        except:
            self.logger.success("フォールバックディレクトリ作成完了")

    def display_interface(self):
        """メインインターフェース表示"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=" * 60)
        print("🎙️  AI音声学習用データセット作成ツール")
        print("=" * 60)
        print()

        # 原稿ファイル表示
        if hasattr(self.text_manager, 'filename'):
            print(f"📄 原稿ファイル: {self.text_manager.filename}")
        
        # 現在の台本表示
        current_text = self.text_manager.get_current_text()
        if current_text:
            total_lines = len(self.text_manager.all_texts)
            current_line = current_text['line_number']
            
            print(f"📝 台本 ({current_line}/{total_lines}):")
            print(f"   {current_text['text']}")
            print()

            # 進捗表示
            progress = self.text_manager.get_progress()
            print(f"📊 進捗: {progress['recorded']}/{progress['total']} 録音済み ({progress['progress_percent']:.1f}%)")
            
            # 録音状態表示
            status = "✅ 録音済み" if current_text['recorded'] else "⭕ 未録音"
            print(f"📍 状態: {status}")
            print()

        # 録音状態表示
        if self.audio_recorder.is_recording:
            if self.audio_recorder.is_paused:
                print("⏸️ 録音一時停止中")
            else:
                duration = self.get_recording_duration()
                print(f"🔴 録音中... ({duration:.1f}秒)")
            print("操作: [p]一時停止 [s]停止・保存 [q]終了")
        else:
            # 通常のコマンド表示
            print("=" * 60)
            print("🎛️  操作コマンド:")
            print("   r  : 録音開始/再開")
            print("   p  : 録音一時停止")
            print("   s  : 録音停止・保存")
            print("   l  : 録音音声の再生")
            print("   n  : 次の台本へ")
            print("   b  : 前の台本へ")
            print("   j  : 指定行にジャンプ")
            print("   rf : テキストファイル再読み込み")
            print("   q  : 終了")
            print("   sync : ファイルとセッション同期")
            print("=" * 60)

    def countdown(self):
        """録音開始前のカウントダウン"""
        print("🎙️ 録音準備中...")
        for i in range(3, 0, -1):
            print(f"⏰ {i}秒後に録音開始...")
            time.sleep(1)

    def get_recording_duration(self):
        """録音時間を取得"""
        if hasattr(self.audio_recorder, 'recorded_data') and self.audio_recorder.recorded_data:
            # 概算時間計算
            total_frames = sum(len(chunk) for chunk in self.audio_recorder.recorded_data)
            return total_frames / self.audio_recorder.sample_rate
        return 0.0

    def get_recording_command(self):
        """録音中のコマンド入力"""
        try:
            # Windows用のキー入力チェック
            if os.name == 'nt':
                import msvcrt
                start_time = time.time()
                
                while self.audio_recorder.is_recording:
                    if msvcrt.kbhit():
                        command = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                        return command
                    
                    # 録音時間表示更新
                    current_time = time.time()
                    duration = current_time - start_time
                    status = "⏸️ 一時停止中" if self.audio_recorder.is_paused else "🔴 録音中"
                    print(f"\r{status} | 時間: {duration:.1f}秒", end="", flush=True)
                    
                    time.sleep(0.1)
            else:
                # Linux/Mac用（簡易版）
                return safe_input("コマンド: ", "q").strip().lower()
                
        except KeyboardInterrupt:
            return 'q'
        
        return ''

    def run(self):
        """メインループ"""
        print("🚀 AI音声学習用データセット作成ツールを開始します")
        
        while True:
            self.display_interface()
            
            # 録音中の場合は特別な処理
            if self.audio_recorder.is_recording:
                command = self.get_recording_command()
            else:
                command = safe_input("\nコマンドを入力してください: ", "q").strip().lower()
            
            # コマンド処理
            if command == 'q':
                self.handle_quit()
                break
            elif command == 'r':
                self.handle_record_start()
            elif command == 'p':
                self.handle_record_pause()
            elif command == 's':
                self.handle_record_stop_save()
            elif command == 'l':
                self.handle_audio_playback()
            elif command == 'n':
                self.handle_next_line()
            elif command == 'b':
                self.handle_previous_line()
            elif command == 'j':
                self.handle_jump_to_line()
            elif command == 'rf':
                self.handle_reload_file()
            elif command == 'sync':
                self.handle_sync()
            else:
                if not self.audio_recorder.is_recording:
                    print("❌ 無効なコマンドです")

    def handle_quit(self):
        """終了処理"""
        if self.audio_recorder.is_recording:
            print("📁 録音を停止しています...")
            self.audio_recorder.stop_recording()
        
        self.text_manager.sync_session_file()
        print("👋 ツールを終了します")

    def handle_record_start(self):
        """録音開始処理"""
        try:
            # 録音状態リセット
            if hasattr(self.audio_recorder, 'reset_recording'):
                self.audio_recorder.reset_recording()
            
            if not self.audio_recorder.is_recording:
                # カウントダウン
                self.countdown()
                
                # 録音開始
                success = self.audio_recorder.start_recording()
                if success:
                    print("🔴 録音開始しました")
                else:
                    print("❌ 録音開始に失敗しました")
            else:
                # 録音再開
                if self.audio_recorder.is_paused:
                    if hasattr(self.audio_recorder, 'resume_recording'):
                        self.audio_recorder.resume_recording()
                    else:
                        self.audio_recorder.is_paused = False
                        print("▶️ 録音再開")
                else:
                    print("⚠️ 既に録音中です")
                    
        except Exception as e:
            print(f"❌ 録音開始エラー: {e}")

    def handle_record_pause(self):
        """録音一時停止処理"""
        if self.audio_recorder.is_recording:
            if hasattr(self.audio_recorder, 'pause_recording'):
                self.audio_recorder.pause_recording()
            else:
                self.audio_recorder.is_paused = True
                print("⏸️ 録音一時停止")
        else:
            print("⚠️ 録音中ではありません")

    def handle_record_stop_save(self):
        """録音停止・保存処理 - メイン制御関数"""
        try:
            # 1. 入力検証
            if not self._validate_recording_state():
                return
            
            current_text = self.text_manager.get_current_text()
            if not current_text:
                print("❌ 現在のテキストが見つかりません")
                self.logger.error("現在のテキストが見つかりません")
                return
            
            # 2. ファイル準備
            audio_filename, audio_path = self._prepare_audio_file(current_text)
            if not audio_filename:
                return
            
            # 3. 録音停止と音声取得
            audio_data = self._stop_recording_and_get_audio()
            if audio_data is None:
                print("❌ 録音データが見つかりません")
                self.logger.error("録音データが見つかりません")
                return
            
            # 4. 音声保存
            if self._save_audio_data(audio_data, audio_path, audio_filename):
                # 5. メタデータ処理
                self._process_metadata(audio_path, audio_filename, current_text)
                print(f"💾 録音保存完了: {audio_filename}")
                self.logger.success(f"録音保存完了: {audio_filename}")
            else:
                print("❌ 音声保存に失敗しました")
                self.logger.error("音声保存に失敗しました")
                
        except Exception as e:
            print(f"❌ 録音停止・保存エラー: {e}")
            self.logger.error(f"録音停止・保存エラー: {e}")
            import traceback
            traceback.print_exc()
    
    def _validate_recording_state(self) -> bool:
        """録音状態の検証"""
        if not self.audio_recorder.is_recording:
            print("⚠️ 録音中ではありません")
            self.logger.warning("録音中ではありません")
            return False
        return True
    
    def _prepare_audio_file(self, current_text) -> tuple:
        """音声ファイルの準備"""
        file_number = current_text['line_number']
        audio_filename = f"audio_{file_number:04d}.wav"
        audio_path = Path("dataset/audio_files") / audio_filename
        
        # 既存ファイル確認
        if audio_path.exists():
            print(f"\n⚠️ {audio_filename} は既に存在します。")
            overwrite = safe_input("上書きしますか？ (y/n): ", "n").strip().lower()
            if overwrite not in ['y', 'yes']:
                print("❌ 保存をキャンセルしました")
                self.logger.info(f"ファイル上書きをキャンセル: {audio_filename}")
                return None, None
            self.logger.info(f"既存ファイルを上書き: {audio_filename}")
        
        return audio_filename, audio_path
    
    def _stop_recording_and_get_audio(self):
        """録音停止と音声データ取得"""
        if hasattr(self.audio_recorder, 'stop_recording'):
            audio_data = self.audio_recorder.stop_recording()
            self.logger.debug("録音停止: stop_recordingメソッド使用")
        else:
            self.audio_recorder.is_recording = False
            audio_data = self.audio_recorder.get_recorded_audio()
            self.logger.debug("録音停止: get_recorded_audioメソッド使用")
        
        self.current_audio = audio_data
        return audio_data
    
    def _save_audio_data(self, audio_data, audio_path, audio_filename) -> bool:
        """音声データの保存"""
        success = False
        
        if hasattr(self.audio_recorder, 'save_audio'):
            # 新しいsave_audioメソッド（引数2つ）
            if len(self.audio_recorder.save_audio.__code__.co_varnames) > 2:
                success = self.audio_recorder.save_audio(audio_data, audio_filename)
                self.logger.debug(f"save_audioメソッド使用(引数2つ): {audio_filename}")
            else:
                success = self.audio_recorder.save_audio(str(audio_path))
                self.logger.debug(f"save_audioメソッド使用(引数1つ): {audio_path}")
        else:
            # フォールバック保存
            success = self.save_audio_fallback(audio_data, audio_path)
            self.logger.debug(f"フォールバック保存使用: {audio_path}")
        
        return success
    
    def _process_metadata(self, audio_path, audio_filename, current_text):
        """メタデータ処理"""
        file_number = current_text['line_number']
        
        # メタファイル保存
        self.save_meta_file(str(audio_path), current_text['text'])
        self.logger.debug(f"メタファイル保存: meta_{file_number:04d}.txt")
        
        # metadata.txt更新
        self.update_metadata_file(audio_filename, current_text['text'])
        self.logger.debug("metadata.txt更新")
        
        # テキストマネージャー更新
        self.text_manager.mark_as_recorded(audio_filename, file_number)
        self.logger.debug(f"テキストマネージャー更新: {file_number}")
        
        # 次の行に自動移動
        self.text_manager.next_line()
        self.logger.info("次のテキスト行に移動")

    def save_audio_fallback(self, audio_data, filepath):
        """フォールバック音声保存"""
        try:
            import soundfile as sf
            sf.write(str(filepath), audio_data, self.audio_recorder.sample_rate)
            return True
        except Exception as e:
            print(f"❌ フォールバック保存エラー: {e}")
            return False

    def handle_audio_playback(self):
        """音声再生処理"""
        if self.current_audio is not None:
            try:
                print("🔊 録音音声を再生中...")
                if hasattr(self.audio_recorder, 'play_audio'):
                    self.audio_recorder.play_audio(self.current_audio)
                else:
                    # フォールバック再生
                    import sounddevice as sd
                    sd.play(self.current_audio, self.audio_recorder.sample_rate)
                    sd.wait()
                    print("✅ 再生完了")
            except Exception as e:
                print(f"❌ 再生エラー: {e}")
        else:
            print("⚠️ 再生する音声がありません。まず録音してください。")

    def handle_next_line(self):
        """次の行へ移動"""
        if self.audio_recorder.is_recording:
            print("⚠️ 録音中です。先に停止してください")
            return
        
        self.current_audio = None
        if self.text_manager.next_line():
            print("➡️ 次の台本に移動しました")
        else:
            print("⚠️ 最後の台本です")

    def handle_previous_line(self):
        """前の行へ移動"""
        if self.audio_recorder.is_recording:
            print("⚠️ 録音中です。先に停止してください")
            return
            
        self.current_audio = None
        if self.text_manager.previous_line():
            print("⬅️ 前の台本に移動しました")
        else:
            print("⚠️ 最初の台本です")

    def handle_jump_to_line(self):
        """指定行へジャンプ"""
        if self.audio_recorder.is_recording:
            print("⚠️ 録音中です。先に停止してください")
            return
            
        try:
            line_num = int(safe_input("移動先の行番号を入力: ", "1"))
            self.current_audio = None
            if self.text_manager.jump_to_line(line_num):
                print(f"🎯 {line_num}行目に移動しました")
            else:
                print("❌ 無効な行番号です")
        except ValueError:
            print("❌ 有効な数字を入力してください")

    def handle_reload_file(self):
        """ファイル再読み込み"""
        if self.audio_recorder.is_recording:
            print("⚠️ 録音中です。先に停止してください")
            return
            
        self.current_audio = None
        if self.text_manager.reload_file():
            print("🔄 テキストファイルを再読み込みしました")
        else:
            print("❌ ファイル再読み込みに失敗しました")

    def handle_sync(self):
        """同期処理"""
        if self.audio_recorder.is_recording:
            print("⚠️ 録音中です。先に停止してください")
            return
            
        self.text_manager.sync_session_file()
        print("🔄 ファイルとセッションを同期しました")

    def save_meta_file(self, audio_path, text_content):
        """メタファイル保存"""
        try:
            meta_filename = Path(audio_path).stem + ".txt"
            meta_path = Path("dataset/meta_files") / meta_filename
            
            with open(meta_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
                
        except Exception as e:
            print(f"❌ メタファイル保存エラー: {e}")

    def update_metadata_file(self, audio_filename, text_content):
        """metadata.txt更新"""
        try:
            metadata_path = Path("dataset/metadata.txt")
            with open(metadata_path, 'a', encoding='utf-8') as f:
                f.write(f"{audio_filename}|{text_content}\n")
        except Exception as e:
            print(f"❌ metadata.txt更新エラー: {e}")

def main():
    """メイン関数"""
    try:
        app = AudioDatasetCreator()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 プログラムを終了しました")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()