#!/bin/bash
# Python_Audio_dataset macOS起動スクリプト

# conda環境確認・アクティベート
if command -v conda >/dev/null 2>&1; then
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate audio-pipeline
else
    echo "❌ condaが見つかりません"
    exit 1
fi

cd Python_Audio_dataset
echo "🎙️ Python_Audio_dataset 起動中..."
python src/main.py