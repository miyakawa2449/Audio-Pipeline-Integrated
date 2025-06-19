# MacBook Pro M4 Pro 環境移行ガイド

## 🍎 MacBook Pro M4 Pro / 48GB での Audio Pipeline Integrated セットアップ

### ハードウェア仕様確認
- **CPU**: M4 Pro (高効率音声処理)
- **メモリ**: 48GB (大規模データセット対応)
- **GPU**: 統合GPU (PyTorch MPS加速)
- **音声**: 高品質内蔵マイク + 外部オーディオI/F対応

## 🛠️ macOS セットアップ手順

### 1. Homebrew インストール
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Python環境構築 (conda推奨)
```bash
# Miniconda for Apple Silicon
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh
bash Miniconda3-latest-MacOSX-arm64.sh

# 環境作成
conda create -n audio-pipeline python=3.10
conda activate audio-pipeline
```

### 3. 音声処理ライブラリ (Apple Silicon最適化版)
```bash
# PyTorch (MPS対応版)
conda install pytorch torchaudio -c pytorch

# 音声処理ライブラリ
conda install numpy matplotlib scipy -c conda-forge
pip install sounddevice soundfile librosa

# macOS音声処理拡張
brew install portaudio
pip install pyaudio  # macOS Core Audio 統合
```

### 4. プロジェクト移行
```bash
# リポジトリクローン
git clone <your-repo-url> Audio-Pipeline-Integrated
cd Audio-Pipeline-Integrated

# 依存関係インストール
pip install -r requirements.txt
```

## 🎙️ macOS 音声設定

### オーディオデバイス設定
```bash
# 音声デバイス確認スクリプト実行
python Python_Audio_dataset/script/check_audio_devices.py
```

### 内蔵マイクの品質設定
- **システム環境設定** → **サウンド** → **入力**
- **入力レベル**: 適切に調整
- **周囲音除去**: 必要に応じて有効

### 外部オーディオインターフェース (推奨)
プロ品質録音のため、以下を推奨：
- **Focusrite Scarlett Solo** (エントリー)
- **Zoom PodTrak P4** (ポッドキャスト特化)
- **Universal Audio Apollo Twin** (プロ仕様)

## ⚡ Apple Silicon M4 Pro 最適化

### PyTorch MPS (Metal Performance Shaders) 有効化
```python
# voice_cloner.py での自動MPS検出
import torch
device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
print(f"Using device: {device}")
```

### メモリ最適化 (48GB活用)
```python
# 大バッチサイズでの高速学習
batch_size = 16  # 通常の4倍
learning_rate = 0.001
```

### 並列処理最適化
```python
# マルチコア活用
import multiprocessing
num_workers = multiprocessing.cpu_count()  # M4 Pro の全コア活用
```

## 🔧 macOS 固有の設定

### 1. 音声録音権限
```bash
# マイクアクセス許可が必要
# システム環境設定 → セキュリティとプライバシー → マイク
# Terminalまたは使用するアプリケーションを許可
```

### 2. ファイル書き込み権限
```bash
# フルディスクアクセス許可 (必要時)
# システム環境設定 → セキュリティとプライバシー → フルディスクアクセス
```

### 3. Gatekeeper設定
```bash
# 未署名アプリの実行許可 (必要時)
sudo spctl --master-disable  # 注意: セキュリティリスクあり
```

## 📁 プロジェクト構造の最適化

### macOS特化ディレクトリ構造
```
Audio-Pipeline-Integrated/
├── dataset/
│   ├── audio_files/         # 録音ファイル
│   ├── meta_files/          # メタデータ
│   └── processed/           # 前処理済み
├── models/
│   ├── pytorch_models/      # MPS最適化モデル
│   └── checkpoints/         # 学習チェックポイント
├── output/
│   ├── synthesized/         # 合成音声
│   └── analysis/           # 分析結果
└── config/
    ├── macos_audio.yaml     # macOS音声設定
    └── m4_pro_config.yaml   # M4 Pro最適化設定
```

## 🧪 動作確認手順

### 1. 基本機能テスト
```bash
# 統合システム起動
python integrated_main.py

# メニュー「4」で統合ステータス確認
```

### 2. 録音機能テスト
```bash
# Python_Audio_dataset 起動
python Python_Audio_dataset/src/main.py

# 'r' コマンドで録音テスト
```

### 3. AudioOpt 学習テスト
```bash
# AudioOpt 起動
cd AudioOpt
python main.py

# メニュー「1」でモデル訓練テスト
```

## 🎵 macOS音声品質最適化

### 録音品質設定
```python
# audio_recorder.py での最適化
sample_rate = 48000  # macOS推奨レート
channels = 1         # モノラル録音
dtype = 'float32'    # 高精度
```

### Core Audio統合 (将来の拡張)
```python
# AVFoundation経由での高品質録音
import AVFoundation  # 将来実装
```

## 🚀 性能ベンチマーク (予想値)

### M4 Pro での処理時間
- **録音**: リアルタイム (遅延 < 10ms)
- **前処理**: 10分音声 → 30秒処理
- **モデル学習**: 100エポック → 15分
- **音声合成**: 1文 → 2秒生成

### メモリ使用量 (48GB活用)
- **データセット**: 5GB (1000ファイル)
- **モデル学習**: 8GB
- **音声合成**: 2GB
- **システム余裕**: 30GB以上

## 📱 macOS統合機能 (将来拡張)

### Siri Shortcuts連携
- **音声録音**: Siriコマンドで録音開始
- **音声合成**: テキスト読み上げ自動化

### ウィジェット対応
- **進捗表示**: 学習・録音進捗をウィジェットで確認
- **クイックアクション**: よく使う機能のショートカット

### iCloud同期
- **データセット**: 複数Mac間での自動同期
- **設定**: プロファイル・設定の同期

## 🔐 セキュリティ設定

### マイクアクセス管理
```bash
# アプリケーション毎のマイクアクセス制御
# システム環境設定で個別に管理
```

### データ暗号化
```bash
# FileVault有効化推奨
# 音声データの暗号化保護
```

## 🛠️ トラブルシューティング

### よくある問題

#### 1. マイクアクセス拒否
```
解決: システム環境設定 → セキュリティとプライバシー → マイク
     Terminalまたはアプリを許可
```

#### 2. PyTorch MPS エラー
```python
# フォールバック設定
device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
```

#### 3. 音声デバイス認識問題
```bash
# 音声システムリセット
sudo killall coreaudiod
```

#### 4. ポート競合
```bash
# ポート使用状況確認
lsof -i :8080
```

## 📊 移行チェックリスト

### 事前準備
- [ ] MacBook Pro M4 Pro セットアップ完了
- [ ] Homebrew インストール
- [ ] Conda環境構築
- [ ] 音声デバイス接続・テスト

### プロジェクト移行
- [ ] リポジトリクローン
- [ ] 依存関係インストール
- [ ] 設定ファイル調整
- [ ] 権限設定完了

### 動作確認
- [ ] 統合システム起動確認
- [ ] 録音機能テスト
- [ ] AudioOpt学習テスト
- [ ] 音声合成テスト

### 最適化
- [ ] MPS加速確認
- [ ] 大バッチサイズテスト
- [ ] メモリ使用量最適化
- [ ] 処理速度ベンチマーク

## 🎉 移行完了後の利点

### パフォーマンス向上
- **処理速度**: 3-5倍高速化
- **メモリ効率**: 大規模データセット対応
- **音声品質**: プロレベルの録音・処理

### 開発効率向上
- **統合環境**: Xcode, Logic Pro等との連携
- **macOS連携**: システム全体との統合
- **プロツール**: 豊富な音声処理ツール

---

**🍎 MacBook Pro M4 Pro で最高品質の音声処理環境を構築しましょう！**