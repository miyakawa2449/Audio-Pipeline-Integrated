# Audio Pipeline Integrated - macOS版

MacBook Pro M4 Pro 最適化版の Audio Pipeline Integrated セットアップガイドです。

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

### Apple Silicon M4 Pro 最適化
- ✅ MPS GPU加速
- ✅ Core Audio統合
- ✅ 48kHz高品質録音
- ✅ 低レイテンシー処理
- ✅ 48GB大容量メモリ活用
- ✅ 効率・パフォーマンスコア最適化

## 📁 重要なファイル

- `config/macos_config.json` - macOS設定
- `macos_migration_guide.md` - 詳細ガイド
- `macos_audio_setup.py` - 音声設定
- `apple_silicon_optimizations.py` - M4 Pro最適化
- `test_macos_environment.py` - 環境テスト

## 🔧 セットアップ手順

### 自動セットアップ（推奨）
```bash
# 完全自動セットアップ
./migrate_to_macos.sh
```

### 手動セットアップ
```bash
# 1. Homebrew インストール
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 必要なシステムライブラリ
brew install portaudio ffmpeg

# 3. Miniconda (Apple Silicon版)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh
bash Miniconda3-latest-MacOSX-arm64.sh

# 4. Python環境作成
conda create -n audio-pipeline python=3.10
conda activate audio-pipeline

# 5. PyTorch (MPS対応版)
conda install pytorch torchaudio -c pytorch

# 6. 音声処理ライブラリ
conda install numpy matplotlib scipy soundfile librosa -c conda-forge
pip install sounddevice pyaudio

# 7. macOS環境セットアップ
python setup_macos.py
```

## 🎙️ 音声設定

### マイクアクセス権限
1. システム環境設定を開く
2. セキュリティとプライバシー → プライバシー
3. 左側の「マイク」を選択
4. ターミナル または 使用するアプリケーションにチェック

### 音声デバイス確認
```bash
python macos_audio_setup.py
```

### 推奨オーディオインターフェース
- **内蔵マイク**: MacBook Pro の高品質マイク
- **Focusrite Scarlett Solo**: エントリーレベル
- **Zoom PodTrak P4**: ポッドキャスト特化
- **Universal Audio Apollo Twin**: プロ仕様

## 🔧 トラブルシューティング

### マイクアクセス拒否
```
解決: システム環境設定 → セキュリティとプライバシー → マイク
     でTerminalまたはアプリケーションを許可
```

### PyTorch MPS エラー
```bash
# MPS利用可能か確認
python -c "import torch; print('MPS available:', torch.backends.mps.is_available())"

# フォールバック設定
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
```

### 音声デバイス認識問題
```bash
# 音声システムリセット
sudo killall coreaudiod

# デバイス確認
python Python_Audio_dataset/script/check_audio_devices.py
```

### 環境テスト
```bash
python test_macos_environment.py
```

## 📊 性能ベンチマーク

### M4 Pro + 48GB メモリでの期待性能
- **録音**: リアルタイム処理（遅延 < 10ms）
- **前処理**: 10分音声 → 30秒処理  
- **学習**: 100エポック → 15分
- **音声合成**: 1文 → 2秒

### 最適化設定
```python
# M4 Pro最適化バッチサイズ
batch_size = 16  # 標準の4倍

# メモリ使用量（48GB活用）
memory_usage = {
    "dataset": "5GB",
    "model_training": "8GB", 
    "synthesis": "2GB",
    "system_reserve": "30GB+"
}
```

## 🎵 使用方法

### 基本ワークフロー

#### 1. データセット録音
```bash
./launch_audio_dataset.sh
# または
python Python_Audio_dataset/src/main.py
```

**録音操作:**
- `r`: 録音開始（3秒カウントダウン）
- `s`: 録音停止・保存
- `l`: 録音音声再生
- `n`: 次の台本
- `q`: 終了

#### 2. 自動データ同期
録音終了時に自動的に`shared_dataset/`に同期されます。

#### 3. 音声学習・生成
```bash
./launch_audioopt.sh
# または
cd AudioOpt && python main.py
```

**学習・合成操作:**
1. データセット前処理とモデル訓練
2. 音声合成
3. 詳細診断・最適化

### 統合システム
```bash
./launch_macos.sh
# または  
python integrated_main.py
```

**統合メニュー:**
1. 📚 データセット録音
2. 🤖 音声学習・生成  
3. 🔄 データセット同期
4. 📊 統合ステータス確認
5. 🧹 データ整理・最適化

## ⚙️ 設定カスタマイズ

### macOS設定ファイル
`config/macos_config.json`で各種設定をカスタマイズ可能:

```json
{
  "audio": {
    "sample_rate": 48000,
    "bit_depth": 24,
    "buffer_size": 512
  },
  "processing": {
    "batch_size": 16,
    "use_mps": true,
    "memory_optimization": true
  }
}
```

### Apple Silicon最適化
```python
# apple_silicon_optimizations.py でカスタマイズ
optimizer = AppleSiliconOptimizer()
config = optimizer.optimize_training_params(base_config)
```

## 📱 macOS統合機能（将来実装）

### Siri Shortcuts連携
- 音声録音の自動開始
- 音声合成のテキスト入力

### ウィジェット対応
- 学習進捗の表示
- クイックアクション

### iCloud同期
- 設定の複数Mac間同期
- データセットのバックアップ

## 🔒 セキュリティ

### FileVault暗号化
```bash
# 推奨: FileVault有効化
# 音声データの暗号化保護
```

### アクセス制御
- マイクアクセス: アプリケーション別管理
- フルディスクアクセス: 必要最小限

## 📈 開発環境

### Xcode統合
```bash
# 開発ツール（オプション）
xcode-select --install
```

### VS Code設定
```json
{
  "python.defaultInterpreterPath": "~/miniconda3/envs/audio-pipeline/bin/python",
  "python.terminal.activateEnvironment": true
}
```

## 🆘 サポート

### ログ確認
```bash
# セットアップログ
cat logs/macos_setup_*.log

# 実行ログ  
cat logs/audio_pipeline.log
```

### デバッグモード
```bash
# 詳細ログ出力
export DEBUG=1
python integrated_main.py
```

### 問題報告
GitHub Issues または以下の情報を添えてご連絡ください:
- macOSバージョン
- CPUタイプ（Apple Silicon/Intel）
- エラーメッセージ
- 実行したコマンド

---

## 🎯 次のステップ

1. **環境セットアップ**: `./migrate_to_macos.sh`
2. **音声権限設定**: システム環境設定
3. **録音テスト**: `./launch_audio_dataset.sh`
4. **統合システム**: `./launch_macos.sh`

🎵 **MacBook Pro M4 Pro で最高品質の音声処理をお楽しみください！**

---

**最終更新**: 2025年6月19日  
**対応環境**: macOS 12.0+ (Apple Silicon M4 Pro推奨)  
**ステータス**: Production Ready ✅