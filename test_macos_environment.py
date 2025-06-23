#!/usr/bin/env python3
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
    print("\n🎙️ 音声デバイス:")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"  入力 {i}: {device['name']}")
    
    print("\n✅ 環境テスト完了")

if __name__ == "__main__":
    test_macos_environment()
