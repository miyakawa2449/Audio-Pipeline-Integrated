import os
import sys
import time
from pathlib import Path

# 必要なモジュールのインポート
from text_manager import TextManager
from audio_recorder import AudioRecorder

class AudioDatasetCreator:
    def __init__(self):
        print("🚀 AI音声学習用データセット作成ツールを初期化中...")
        
        # TextManager初期化
        self.text_manager = TextManager()
        
        # AudioRecorder初期化
        self.audio_recorder = AudioRecorder()
        self.current_audio = None
        
        # ディレクトリセットアップ
        self.setup_directories()
        
        # 初期化確認
        self.check_initialization()

    def check_initialization(self):
        """初期化状態の確認"""
        print("\n📋 初期化状態確認:")
        
        # テキストファイル確認
        if self.text_manager.all_texts:
            print(f"✅ テキスト読み込み: {len(self.text_manager.all_texts)}行")
            print(f"📄 ファイル名: {self.text_manager.filename}")
        else:
            print("❌ テキストが読み込まれていません")
            print("   'rf' コマンドでテキストファイルを読み込んでください")
        
        # AudioRecorder確認
        print(f"✅ AudioRecorder初期化: 成功")
        print(f"🎤 サンプルレート: {self.audio_recorder.sample_rate}Hz")
        
        # ディレクトリ確認
        required_dirs = ["dataset/audio_files", "dataset/meta_files"]
        for dir_path in required_dirs:
            if Path(dir_path).exists():
                print(f"✅ ディレクトリ: {dir_path}")
            else:
                print(f"❌ ディレクトリ: {dir_path}")
        
        print("="*50)

    def setup_directories(self):
        """必要なディレクトリを作成"""
        Path("dataset/audio_files").mkdir(parents=True, exist_ok=True)
        Path("dataset/meta_files").mkdir(parents=True, exist_ok=True)

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
                return input("コマンド: ").strip().lower()
                
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
                command = input("\nコマンドを入力してください: ").strip().lower()
            
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
        """録音停止・保存処理"""
        if not self.audio_recorder.is_recording:
            print("⚠️ 録音中ではありません")
            return

        current_text = self.text_manager.get_current_text()
        if not current_text:
            print("❌ 現在のテキストが見つかりません")
            return

        try:
            file_number = current_text['line_number']
            audio_filename = f"audio_{file_number:04d}.wav"
            audio_path = Path("dataset/audio_files") / audio_filename
            
            # 既存ファイル確認
            if audio_path.exists():
                print(f"\n⚠️ {audio_filename} は既に存在します。")
                overwrite = input("上書きしますか？ (y/n): ").strip().lower()
                if overwrite not in ['y', 'yes']:
                    print("❌ 保存をキャンセルしました")
                    return
            
            # 録音停止
            if hasattr(self.audio_recorder, 'stop_recording'):
                self.current_audio = self.audio_recorder.stop_recording()
            else:
                self.audio_recorder.is_recording = False
                self.current_audio = self.audio_recorder.get_recorded_audio()
            
            if self.current_audio is not None:
                # 音声保存
                success = False
                if hasattr(self.audio_recorder, 'save_audio'):
                    # 新しいsave_audioメソッド（引数2つ）
                    if len(self.audio_recorder.save_audio.__code__.co_varnames) > 2:
                        success = self.audio_recorder.save_audio(self.current_audio, audio_filename)
                    else:
                        success = self.audio_recorder.save_audio(str(audio_path))
                else:
                    # フォールバック保存
                    success = self.save_audio_fallback(self.current_audio, audio_path)
                
                if success:
                    # メタデータ保存
                    self.save_meta_file(str(audio_path), current_text['text'])
                    self.update_metadata_file(audio_filename, current_text['text'])
                    
                    # テキストマネージャー更新
                    self.text_manager.mark_as_recorded(audio_filename, file_number)
                    
                    print(f"💾 録音保存完了: {audio_filename}")
                    
                    # 次の行に自動移動
                    self.text_manager.next_line()
                else:
                    print("❌ 音声保存に失敗しました")
            else:
                print("❌ 録音データが見つかりません")
                
        except Exception as e:
            print(f"❌ 録音停止・保存エラー: {e}")
            import traceback
            traceback.print_exc()

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
            line_num = int(input("移動先の行番号を入力: "))
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