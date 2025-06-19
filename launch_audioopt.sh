#!/bin/bash
# AudioOpt macOS起動スクリプト

# conda環境確認・アクティベート
if command -v conda >/dev/null 2>&1; then
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate audio-pipeline
else
    echo "❌ condaが見つかりません"
    exit 1
fi

cd AudioOpt
echo "🤖 AudioOpt 起動中..."
python main.py