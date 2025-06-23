#!/bin/bash
# AudioOpt macOS起動スクリプト

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate audio-pipeline

cd AudioOpt
echo "🤖 AudioOpt 起動中..."
python main.py
