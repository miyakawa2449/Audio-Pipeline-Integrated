# Audio Pipeline Integrated - macOS版

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

### Apple Silicon M4 Pro 最適化
- ✅ MPS GPU加速
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

M4 Pro + 48GB メモリでの期待性能:
- 録音: リアルタイム処理
- 前処理: 10分音声 → 30秒処理  
- 学習: 100エポック → 15分
- 音声合成: 1文 → 2秒

---

🎵 **MacBook Pro で最高品質の音声処理をお楽しみください！**
