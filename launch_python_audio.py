import os
import sys
import subprocess
from pathlib import Path

def launch_python_audio_isolated():
    """Python_Audio_dataset を完全分離環境で実行"""
    
    python_audio_dir = Path("Python_Audio_dataset")
    
    if not python_audio_dir.exists():
        print(f"❌ {python_audio_dir} が見つかりません")
        return
    
    print("🚀 Python_Audio_dataset を分離環境で起動中...")
    
    # 新しいPythonプロセスで実行
    try:
        # Python_Audio_dataset ディレクトリで main.py を実行
        result = subprocess.run([
            sys.executable, "src/main.py"
        ], cwd=python_audio_dir, capture_output=False)
        
        if result.returncode == 0:
            print("✅ Python_Audio_dataset 正常終了")
        else:
            print(f"❌ Python_Audio_dataset エラー終了: {result.returncode}")
            
    except Exception as e:
        print(f"❌ 起動エラー: {e}")

def launch_python_audio_direct():
    """直接実行（作業ディレクトリ変更）"""
    
    python_audio_dir = Path("Python_Audio_dataset")
    original_cwd = os.getcwd()
    
    try:
        os.chdir(python_audio_dir)
        
        # 元の環境で実行
        sys.path.insert(0, 'src')
        
        import main
        if hasattr(main, 'AudioDatasetCreator'):
            creator = main.AudioDatasetCreator()
            creator.run()
        else:
            print("❌ AudioDatasetCreator が見つかりません")
            
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    print("Python_Audio_dataset 起動方法を選択:")
    print("1. 分離プロセス実行（推奨）")
    print("2. 直接実行")
    
    choice = input("選択 (1/2): ").strip()
    
    if choice == "1":
        launch_python_audio_isolated()
    elif choice == "2":
        launch_python_audio_direct()
    else:
        print("❌ 無効な選択")