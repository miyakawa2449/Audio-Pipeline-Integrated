import subprocess
import sys

def install_audio_packages():
    """音声処理用パッケージの一括インストール"""
    
    packages = [
        # 音声処理基本パッケージ
        "soundfile",
        "sounddevice", 
        "librosa",
        "scipy",
        "numpy",
        
        # UI・進捗表示
        "tqdm",
        "colorama",
        
        # ファイル処理
        "pathlib",
    ]
    
    print("🎵 音声処理用パッケージをインストール中...")
    
    for package in packages:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True, text=True)
            print(f"✅ {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ {package} - エラー: {e}")
    
    print("\n🎉 音声パッケージのインストール完了！")

if __name__ == "__main__":
    install_audio_packages()