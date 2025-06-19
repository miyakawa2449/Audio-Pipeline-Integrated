#!/usr/bin/env python3
"""
macOS専用 Audio Pipeline Integrated セットアップスクリプト
MacBook Pro M4 Pro 統合環境構築
"""
import os
import sys
import json
import platform
import subprocess
import shutil
from pathlib import Path

class MacOSSetup:
    """macOS用セットアップクラス"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.is_apple_silicon = self._detect_apple_silicon()
        self.setup_log = []
        
    def _detect_apple_silicon(self):
        """Apple Silicon検出"""
        if platform.system() != 'Darwin':
            return False
        try:
            result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                                  capture_output=True, text=True)
            return 'Apple' in result.stdout
        except:
            return False
    
    def log(self, message, level="INFO"):
        """ログ記録"""
        log_entry = f"[{level}] {message}"
        self.setup_log.append(log_entry)
        
        if level == "ERROR":
            print(f"❌ {message}")
        elif level == "WARNING":
            print(f"⚠️ {message}")
        elif level == "SUCCESS":
            print(f"✅ {message}")
        else:
            print(f"🔍 {message}")
    
    def check_prerequisites(self):
        """前提条件チェック"""
        self.log("前提条件をチェック中...")
        
        # macOS確認
        if platform.system() != 'Darwin':
            self.log("このスクリプトはmacOS専用です", "ERROR")
            return False
        
        macos_version = platform.mac_ver()[0]
        self.log(f"macOS {macos_version} 検出", "SUCCESS")
        
        # Apple Silicon確認
        if self.is_apple_silicon:
            self.log("Apple Silicon CPU検出 - 最適化有効", "SUCCESS")
        else:
            self.log("Intel Mac検出", "INFO")
        
        return True
    
    def setup_directories(self):
        """必要なディレクトリ構造を作成"""
        self.log("ディレクトリ構造を作成中...")
        
        directories = [
            # 設定・ログ
            "config",
            "logs",
            
            # Python_Audio_dataset
            "Python_Audio_dataset/dataset/audio_files",
            "Python_Audio_dataset/dataset/meta_files",
            "Python_Audio_dataset/dataset/processed",
            "Python_Audio_dataset/dataset/backup",
            "Python_Audio_dataset/data",
            
            # AudioOpt
            "AudioOpt/dataset/audio_files",
            "AudioOpt/dataset/meta_files", 
            "AudioOpt/dataset/processed",
            "AudioOpt/models",
            "AudioOpt/output",
            
            # shared_dataset
            "shared_dataset/audio_files",
            "shared_dataset/meta_files",
            "shared_dataset/processed",
            "shared_dataset/phoneme_data",
            "shared_dataset/backup",
            "shared_dataset/logs",
        ]
        
        created_count = 0
        for directory in directories:
            dir_path = self.project_root / directory
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                created_count += 1
        
        self.log(f"{created_count} 個のディレクトリを作成", "SUCCESS")
        return True
    
    def create_macos_config(self):
        """macOS最適化設定ファイル作成"""
        self.log("macOS設定ファイルを作成中...")
        
        # 基本設定
        config = {
            "system": {
                "platform": "macos",
                "apple_silicon": self.is_apple_silicon,
                "optimization_level": "high" if self.is_apple_silicon else "medium"
            },
            "audio": {
                "core_audio": True,
                "sample_rate": 48000,
                "bit_depth": 24,
                "channels": 1,
                "buffer_size": 512,
                "low_latency": True
            },
            "processing": {
                "use_mps": self.is_apple_silicon,
                "batch_size": 8 if self.is_apple_silicon else 4,
                "num_workers": "auto",
                "memory_optimization": True
            },
            "paths": {
                "python_audio_dataset": "Python_Audio_dataset/dataset",
                "audioopt_dataset": "AudioOpt/dataset", 
                "shared_dataset": "shared_dataset",
                "models": "AudioOpt/models",
                "output": "AudioOpt/output"
            }
        }
        
        # Apple Silicon特化設定
        if self.is_apple_silicon:
            config["apple_silicon"] = {
                "mps_acceleration": True,
                "memory_limit": "32GB",
                "high_performance_mode": True,
                "core_audio_integration": True
            }
        
        # 設定ファイル保存
        config_path = self.project_root / "config" / "macos_config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        self.log(f"設定ファイル作成: {config_path}", "SUCCESS")
        return config_path
    
    def create_launch_scripts(self):
        """macOS用起動スクリプト作成"""
        self.log("起動スクリプトを作成中...")
        
        # 統合システム起動スクリプト
        launch_script = '''#!/bin/bash
# Audio Pipeline Integrated macOS起動スクリプト

# conda環境確認・アクティベート
if command -v conda >/dev/null 2>&1; then
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate audio-pipeline
else
    echo "❌ condaが見つかりません"
    exit 1
fi

# macOS設定読み込み
export MACOS_CONFIG="config/macos_config.json"

# Apple Silicon最適化
if [[ $(sysctl -n machdep.cpu.brand_string) == *"Apple"* ]]; then
    export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
    echo "🍎 Apple Silicon最適化有効"
fi

# 統合システム起動
echo "🎵 Audio Pipeline Integrated 起動中..."
python integrated_main.py

echo "👋 Audio Pipeline Integrated 終了"
'''
        
        launch_path = self.project_root / "launch_macos.sh"
        with open(launch_path, 'w', encoding='utf-8') as f:
            f.write(launch_script)
        
        # 実行権限付与
        os.chmod(launch_path, 0o755)
        
        # Python_Audio_dataset起動スクリプト
        audio_script = '''#!/bin/bash
# Python_Audio_dataset macOS起動スクリプト

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate audio-pipeline

cd Python_Audio_dataset
echo "🎙️ Python_Audio_dataset 起動中..."
python src/main.py
'''
        
        audio_path = self.project_root / "launch_audio_dataset.sh"
        with open(audio_path, 'w', encoding='utf-8') as f:
            f.write(audio_script)
        os.chmod(audio_path, 0o755)
        
        # AudioOpt起動スクリプト
        audioopt_script = '''#!/bin/bash
# AudioOpt macOS起動スクリプト

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate audio-pipeline

cd AudioOpt
echo "🤖 AudioOpt 起動中..."
python main.py
'''
        
        audioopt_path = self.project_root / "launch_audioopt.sh"
        with open(audioopt_path, 'w', encoding='utf-8') as f:
            f.write(audioopt_script)
        os.chmod(audioopt_path, 0o755)
        
        self.log("起動スクリプト作成完了", "SUCCESS")
        return [launch_path, audio_path, audioopt_path]
    
    def create_requirements_macos(self):
        """macOS用requirements.txt作成"""
        self.log("macOS用requirements.txtを作成中...")
        
        requirements = [
            "# Audio Pipeline Integrated - macOS Requirements",
            "# Core audio processing",
            "sounddevice>=0.4.4",
            "soundfile>=0.10.0", 
            "librosa>=0.9.0",
            "scipy>=1.9.0",
            "numpy>=1.20.0",
            "",
            "# macOS audio integration",
            "pyaudio>=0.2.11",
            "",
            "# Machine learning",
            "# PyTorch: conda install pytorch torchaudio -c pytorch",
            "",
            "# Visualization",
            "matplotlib>=3.5.0",
            "",
            "# System utilities",
            "psutil>=5.8.0",
            "pathlib2>=2.3.0",
            "",
            "# Development tools",
            "pytest>=6.0.0",
            "black>=22.0.0",
        ]
        
        req_path = self.project_root / "requirements_macos.txt"
        with open(req_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(requirements))
        
        self.log(f"requirements作成: {req_path}", "SUCCESS")
        return req_path
    
    def create_gitignore_macos(self):
        """macOS用.gitignore更新"""
        self.log("macOS用.gitignore設定...")
        
        macos_ignores = [
            "",
            "# macOS specific",
            ".DS_Store",
            ".AppleDouble",
            ".LSOverride",
            "",
            "# macOS Thumbnails",
            "._*",
            "",
            "# macOS Directories potentially created on remote AFP share",
            ".AppleDB",
            ".AppleDesktop", 
            "Network Trash Folder",
            "Temporary Items",
            ".apdisk",
            "",
            "# Audio files (large)",
            "*.wav",
            "*.mp3",
            "*.m4a",
            "*.aiff",
            "",
            "# Model files (large)",
            "*.pth",
            "*.ckpt",
            "*.pkl",
            "",
            "# Logs",
            "logs/",
            "*.log",
            "",
            "# Config (may contain personal settings)",
            "config/personal_*.json",
        ]
        
        gitignore_path = self.project_root / ".gitignore"
        
        # 既存の.gitignoreに追記
        if gitignore_path.exists():
            with open(gitignore_path, 'a', encoding='utf-8') as f:
                f.write('\n'.join(macos_ignores))
        else:
            with open(gitignore_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(macos_ignores))
        
        self.log(".gitignore更新完了", "SUCCESS")
        return gitignore_path
    
    def setup_test_environment(self):
        """テスト環境セットアップ"""
        self.log("テスト環境をセットアップ中...")
        
        # テスト用サンプルファイル作成
        test_script = '''#!/usr/bin/env python3
"""
macOS環境テストスクリプト
"""
import platform
import torch
import sounddevice as sd

def test_macos_environment():
    print("🧪 macOS環境テスト実行中...")
    
    # システム情報
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"CPU: {platform.processor()}")
    
    # PyTorch MPS確認
    if torch.backends.mps.is_available():
        print("✅ PyTorch MPS加速: 利用可能")
        
        # MPS性能テスト
        device = torch.device('mps')
        x = torch.randn(1000, 1000, device=device)
        y = torch.mm(x, x)
        print("✅ MPS動作テスト: 成功")
    else:
        print("❌ PyTorch MPS加速: 利用不可")
    
    # 音声デバイス確認
    print("\\n🎙️ 音声デバイス:")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"  入力 {i}: {device['name']}")
    
    print("\\n✅ 環境テスト完了")

if __name__ == "__main__":
    test_macos_environment()
'''
        
        test_path = self.project_root / "test_macos_environment.py"
        with open(test_path, 'w', encoding='utf-8') as f:
            f.write(test_script)
        
        self.log("テスト環境セットアップ完了", "SUCCESS")
        return test_path
    
    def create_readme_macos(self):
        """macOS用README作成"""
        self.log("macOS用READMEを作成中...")
        
        readme_content = f'''# Audio Pipeline Integrated - macOS版

MacBook Pro M4 Pro 最適化版の Audio Pipeline Integrated セットアップが完了しました。

## 🚀 クイックスタート

### 1. 環境アクティベート
```bash
conda activate audio-pipeline
```

### 2. 統合システム起動
```bash
./launch_macos.sh
```

### 3. 個別アプリケーション起動
```bash
# 録音システム
./launch_audio_dataset.sh

# 音声合成システム  
./launch_audioopt.sh
```

## 🍎 macOS最適化機能

{'### Apple Silicon M4 Pro 最適化' if self.is_apple_silicon else '### Intel Mac'}
- {'✅ MPS GPU加速' if self.is_apple_silicon else '✅ CPU最適化'}
- ✅ Core Audio統合
- ✅ 48kHz高品質録音
- ✅ 低レイテンシー処理

## 📁 重要なファイル

- `config/macos_config.json` - macOS設定
- `macos_migration_guide.md` - 詳細ガイド
- `macos_audio_setup.py` - 音声設定
- `test_macos_environment.py` - 環境テスト

## 🔧 トラブルシューティング

### マイクアクセス拒否
システム環境設定 → セキュリティとプライバシー → マイク
で、Terminalまたはアプリケーションを許可

### 音声デバイス問題
```bash
python macos_audio_setup.py
```

### 環境テスト
```bash
python test_macos_environment.py
```

## 📊 性能ベンチマーク

{'M4 Pro + 48GB メモリでの期待性能:' if self.is_apple_silicon else 'Intel Mac での期待性能:'}
- 録音: リアルタイム処理
- 前処理: 10分音声 → 30秒処理  
- 学習: 100エポック → {'15分' if self.is_apple_silicon else '45分'}
- 音声合成: 1文 → {'2秒' if self.is_apple_silicon else '5秒'}

---

🎵 **MacBook Pro で最高品質の音声処理をお楽しみください！**
'''
        
        readme_path = self.project_root / "README_macOS.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        self.log("macOS用README作成完了", "SUCCESS")
        return readme_path
    
    def save_setup_log(self):
        """セットアップログ保存"""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = log_dir / f"macos_setup_{timestamp}.log"
        
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write("Audio Pipeline Integrated - macOS Setup Log\\n")
            f.write("=" * 50 + "\\n")
            for entry in self.setup_log:
                f.write(entry + "\\n")
        
        self.log(f"セットアップログ保存: {log_path}", "SUCCESS")
        return log_path
    
    def run_setup(self):
        """メインセットアップ実行"""
        self.log("🍎 macOS用 Audio Pipeline Integrated セットアップ開始")
        
        try:
            # 基本チェック
            if not self.check_prerequisites():
                return False
            
            # セットアップ実行
            self.setup_directories()
            config_path = self.create_macos_config()
            scripts = self.create_launch_scripts()
            req_path = self.create_requirements_macos()
            gitignore_path = self.create_gitignore_macos()
            test_path = self.setup_test_environment()
            readme_path = self.create_readme_macos()
            log_path = self.save_setup_log()
            
            # 完了メッセージ
            self.log("🎉 macOSセットアップ完了!", "SUCCESS")
            self.log("", "INFO")
            self.log("📋 作成されたファイル:", "INFO")
            self.log(f"  • {config_path}", "INFO")
            self.log(f"  • {req_path}", "INFO") 
            self.log(f"  • {readme_path}", "INFO")
            self.log(f"  • {test_path}", "INFO")
            self.log("", "INFO")
            self.log("🚀 次のステップ:", "INFO")
            self.log("1. conda activate audio-pipeline", "INFO")
            self.log("2. ./launch_macos.sh", "INFO")
            
            return True
            
        except Exception as e:
            self.log(f"セットアップエラー: {e}", "ERROR")
            return False

def main():
    """メイン関数"""
    setup = MacOSSetup()
    success = setup.run_setup()
    
    if success:
        print("\\n🎵 Audio Pipeline Integrated macOS版の準備完了!")
        sys.exit(0)
    else:
        print("\\n❌ セットアップに失敗しました")
        sys.exit(1)

if __name__ == "__main__":
    main()