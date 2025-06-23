#!/bin/bash
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
