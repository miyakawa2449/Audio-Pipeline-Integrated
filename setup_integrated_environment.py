# setup_integrated_environment.py
import subprocess
import sys
from pathlib import Path

def setup_pytorch_for_cuda():
    """CUDA対応PyTorchをセットアップ"""
    print("🔥 CUDA対応PyTorchをインストール中...")
    
    pytorch_cmd = [
        sys.executable, "-m", "pip", "install", 
        "torch", "torchvision", "torchaudio",
        "--index-url", "https://download.pytorch.org/whl/cu121"
    ]
    
    try:
        subprocess.run(pytorch_cmd, check=True)
        print("✅ PyTorch (CUDA対応) インストール完了")
        
        # インストール確認
        test_cmd = [
            sys.executable, "-c",
            "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"
        ]
        subprocess.run(test_cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ PyTorchインストールエラー: {e}")
        return False
    
    return True

def setup_project_requirements():
    """プロジェクト固有の依存関係をセットアップ"""
    current_dir = Path(__file__).parent
    
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
                print(f"✅ {req_file.parent.name} 完了")
            except subprocess.CalledProcessError as e:
                print(f"❌ {req_file.parent.name} エラー: {e}")

if __name__ == "__main__":
    print("🚀 Audio Pipeline Integrated 環境セットアップ")
    print("="*50)
    
    # PyTorchセットアップ
    if setup_pytorch_for_cuda():
        # その他の依存関係
        setup_project_requirements()
        
        print("\n🎉 セットアップ完了！")
        print("次のコマンドで統合アプリを起動:")
        print("python integrated_main.py")
    else:
        print("❌ セットアップに失敗しました")