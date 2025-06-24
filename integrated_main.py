import os
import sys
import subprocess
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
        return "6"
from common.logger import get_logger
from common.error_handler import error_handler, ErrorSeverity, handle_error
from common.exceptions import AudioPipelineError

# プロジェクトパスをPythonパスに追加
current_dir = Path(__file__).parent
python_audio_src = current_dir / "Python_Audio_dataset" / "src"
audioopt_src = current_dir / "AudioOpt" / "src"

sys.path.insert(0, str(python_audio_src))
sys.path.insert(0, str(audioopt_src))

from shared_dataset_manager import SharedDatasetManager

class IntegratedAudioPipeline:
    def __init__(self):
        self.logger = get_logger("IntegratedPipeline")
        self.dataset_manager = SharedDatasetManager()
        self.current_dir = Path(__file__).parent
        self.setup_environment()
    
    def setup_environment(self):
        """統合環境のセットアップ"""
        self.logger.start_operation("統合環境セットアップ")
        self.dataset_manager.setup_shared_directories()
        self.logger.complete_operation("統合環境セットアップ")
        
    def run(self):
        """統合メインメニュー"""
        while True:
            self.display_main_menu()
            choice = safe_input("\n選択してください (1-6): ", "6").strip()
            
            if choice == '1':
                self.run_dataset_creator()
            elif choice == '2':
                self.run_audioopt()
            elif choice == '3':
                self.sync_datasets()
            elif choice == '4':
                self.show_status()
            elif choice == '5':
                self.cleanup_and_organize()
            elif choice == '6':
                print("👋 統合パイプラインを終了します")
                break
            else:
                print("❌ 無効な選択です")
                
            safe_input("\nEnterを押して続行...", "")
    
    def display_main_menu(self):
        """統合メインメニュー表示"""
        print("\n" + "="*60)
        print("🎵 Audio Pipeline Integrated")
        print("="*60)
        print("1. 📚 データセット録音 (Python_Audio_dataset)")
        print("2. 🤖 音声学習・生成 (AudioOpt)")
        print("3. 🔄 データセット同期")
        print("4. 📊 統合ステータス確認")
        print("5. 🧹 データ整理・最適化")
        print("6. 🚪 終了")
        print("="*60)
    
    def run_dataset_creator(self):
        """Python_Audio_datasetを実行（分離プロセス）"""
        print("🎙️ データセット録音モードを開始...")
        
        python_audio_dir = self.current_dir / "Python_Audio_dataset"
        if not python_audio_dir.exists():
            self.logger.error("Python_Audio_dataset ディレクトリが見つかりません")
            return
        
        try:
            # 分離プロセスで実行（最も安全）
            original_cwd = os.getcwd()
            os.chdir(python_audio_dir)
            
            # Pythonパスを設定してサブプロセス実行
            env = os.environ.copy()
            env['PYTHONPATH'] = str(python_audio_dir / "src")
            
            self.logger.start_operation("Python_Audio_dataset 起動")
            result = subprocess.run([
                sys.executable, "src/main.py"
            ], cwd=python_audio_dir, env=env)
            
            if result.returncode == 0:
                self.logger.success("Python_Audio_dataset が正常に終了しました")
                # 自動同期
                self.logger.start_operation("自動同期")
                self.dataset_manager.sync_from_python_audio()
            else:
                self.logger.warning(f"Python_Audio_dataset が終了コード {result.returncode} で終了")
                
        except Exception as e:
            self.logger.error(f"Python_Audio_dataset 実行エラー: {e}")
        finally:
            os.chdir(original_cwd)
    
    def run_audioopt(self):
        """AudioOptを実行"""
        print("🤖 音声学習・生成モードを開始...")
        
        audioopt_dir = self.current_dir / "AudioOpt"
        if not audioopt_dir.exists():
            self.logger.error("AudioOpt ディレクトリが見つかりません")
            return
            
        try:
            # 事前同期
            self.logger.start_operation("AudioOpt用データ同期")
            self.dataset_manager.sync_to_audioopt()
            
            original_cwd = os.getcwd()
            os.chdir(audioopt_dir)
            
            self.logger.start_operation("AudioOpt 起動")
            result = subprocess.run([sys.executable, "main.py"], cwd=audioopt_dir)
            
            if result.returncode == 0:
                self.logger.success("AudioOpt が正常に終了しました")
            else:
                self.logger.warning(f"AudioOpt が終了コード {result.returncode} で終了")
                
        except Exception as e:
            self.logger.error(f"AudioOpt 実行エラー: {e}")
        finally:
            os.chdir(original_cwd)
    
    @error_handler(severity=ErrorSeverity.MEDIUM, recovery=True)
    def sync_datasets(self):
        """データセット同期"""
        self.logger.start_operation("データセット同期")
        try:
            self.dataset_manager.sync_all_projects()
            self.logger.complete_operation("データセット同期")
        except Exception as e:
            raise AudioPipelineError(f"データ同期エラー: {e}")
    
    @error_handler(severity=ErrorSeverity.LOW, recovery=True)
    def show_status(self):
        """統合ステータス表示"""
        try:
            self.dataset_manager.show_integration_status()
        except Exception as e:
            raise AudioPipelineError(f"ステータス表示エラー: {e}")
    
    @error_handler(severity=ErrorSeverity.LOW, recovery=True)
    def cleanup_and_organize(self):
        """データ整理・最適化"""
        self.logger.start_operation("データ整理・最適化")
        try:
            self.dataset_manager.cleanup_and_organize()
            self.logger.complete_operation("データ整理・最適化")
        except Exception as e:
            raise AudioPipelineError(f"データ整理エラー: {e}")

@error_handler(severity=ErrorSeverity.CRITICAL, recovery=False)
def main():
    """メイン実行関数"""
    pipeline = IntegratedAudioPipeline()
    pipeline.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 プログラムを終了しました")
    except Exception as e:
        logger = get_logger("Main")
        handle_error(e, severity=ErrorSeverity.CRITICAL)