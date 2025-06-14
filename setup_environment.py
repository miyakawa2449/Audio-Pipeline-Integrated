# setup_environment.py
import subprocess
import sys
from pathlib import Path

def setup_integrated_environment():
    """統合プロジェクトの環境をセットアップ"""
    current_dir = Path(__file__).parent
    
    print("🔧 統合環境をセットアップ中...")
    
    # 各プロジェクトのrequirements.txtを確認
    requirements_files = [
        current_dir / "AudioOpt" / "requirements.txt",
        current_dir / "Python_Audio_dataset" / "requirements.txt"
    ]
    
    for req_file in requirements_files:
        if req_file.exists():
            print(f"📦 {req_file.parent.name} の依存関係をインストール中...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_file)], 
                             check=True)
                print(f"✅ {req_file.parent.name} の依存関係インストール完了")
            except subprocess.CalledProcessError as e:
                print(f"❌ {req_file.parent.name} のインストールエラー: {e}")
        else:
            print(f"⚠️ {req_file} が見つかりません")
    
    # 追加の統合用パッケージ
    additional_packages = ["tqdm", "colorama"]
    for package in additional_packages:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
            print(f"✅ {package} インストール完了")
        except subprocess.CalledProcessError:
            print(f"❌ {package} インストール失敗")
    
    print("🎉 環境セットアップ完了！")

if __name__ == "__main__":
    setup_integrated_environment()