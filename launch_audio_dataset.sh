#!/bin/bash
# Python_Audio_dataset macOS起動スクリプト

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate audio-pipeline

cd Python_Audio_dataset
echo "🎙️ Python_Audio_dataset 起動中..."
python src/main.py
