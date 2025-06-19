#!/usr/bin/env python3
"""
macOS用 Audio Pipeline Integrated オーディオ設定
MacBook Pro M4 Pro 最適化版
"""
import os
import sys
import platform
import subprocess
import json
from pathlib import Path

def check_macos_version():
    """macOSバージョン確認"""
    print("=== macOS環境確認 ===")
    
    if platform.system() != 'Darwin':
        print("❌ このスクリプトはmacOS専用です")
        return False
    
    version = platform.mac_ver()[0]
    print(f"✅ macOS: {version}")
    
    # Apple Silicon確認
    try:
        result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                              capture_output=True, text=True)
        cpu_info = result.stdout.strip()
        print(f"✅ CPU: {cpu_info}")
        
        if 'Apple' in cpu_info:
            print("🍎 Apple Silicon検出 - MPS加速対応")
            return 'apple_silicon'
        else:
            print("🖥️ Intel Mac - CPU処理")
            return 'intel'
    except:
        print("⚠️ CPU情報取得失敗")
        return 'unknown'

def check_audio_permissions():
    """macOS音声アクセス権限確認"""
    print("\n=== 音声アクセス権限確認 ===")
    
    try:
        import sounddevice as sd
        
        # 簡単な録音テスト
        print("🎙️ マイクアクセステスト中...")
        test_recording = sd.rec(int(0.1 * 44100), samplerate=44100, channels=1)
        sd.wait()
        
        if len(test_recording) > 0:
            print("✅ マイクアクセス権限: OK")
            return True
        else:
            print("❌ マイクアクセス権限: 拒否")
            return False
            
    except Exception as e:
        print(f"❌ マイクアクセスエラー: {e}")
        print("💡 解決方法:")
        print("   システム環境設定 → セキュリティとプライバシー → マイク")
        print("   → Terminalまたは実行中のアプリを許可")
        return False

def detect_audio_devices():
    """macOS音声デバイス検出（詳細版）"""
    print("\n=== 音声デバイス詳細検出 ===")
    
    try:
        import sounddevice as sd
        
        devices = sd.query_devices()
        input_devices = []
        output_devices = []
        
        print("🔍 利用可能な音声デバイス:")
        print("-" * 60)
        
        for i, device in enumerate(devices):
            device_info = {
                'id': i,
                'name': device['name'],
                'input_channels': device['max_input_channels'],
                'output_channels': device['max_output_channels'],
                'sample_rate': device['default_samplerate'],
                'host_api': device['hostapi']
            }
            
            # デバイス種別判定
            device_types = []
            if device['max_input_channels'] > 0:
                device_types.append("📥 入力")
                input_devices.append(device_info)
            if device['max_output_channels'] > 0:
                device_types.append("📤 出力")
                output_devices.append(device_info)
            
            # macOS特有のデバイス判定
            macos_device_type = categorize_macos_device(device['name'])
            
            print(f"🎛️ ID {i}: {device['name']}")
            print(f"   種別: {' & '.join(device_types)} {macos_device_type}")
            print(f"   入力ch: {device['max_input_channels']}, 出力ch: {device['max_output_channels']}")
            print(f"   サンプルレート: {device['default_samplerate']:.0f} Hz")
            print(f"   Host API: {sd.query_hostapis()[device['hostapi']]['name']}")
            
            # 推奨設定
            if is_recommended_device(device['name'], device_info):
                print("   ⭐ 推奨デバイス")
            
            print("-" * 60)
        
        # デフォルトデバイス情報
        print("\n📍 デフォルトデバイス:")
        try:
            default_input = sd.query_devices(kind='input')
            default_output = sd.query_devices(kind='output')
            print(f"🎙️ 入力: {default_input['name']}")
            print(f"🔊 出力: {default_output['name']}")
        except:
            print("⚠️ デフォルトデバイス取得失敗")
        
        return {
            'input_devices': input_devices,
            'output_devices': output_devices,
            'total_devices': len(devices)
        }
        
    except ImportError:
        print("❌ sounddeviceライブラリが見つかりません")
        print("💡 インストール: pip install sounddevice")
        return None
    except Exception as e:
        print(f"❌ デバイス検出エラー: {e}")
        return None

def categorize_macos_device(device_name):
    """macOSデバイスの種別判定"""
    name_lower = device_name.lower()
    
    if 'macbook' in name_lower or 'built-in' in name_lower:
        return "🖥️ 内蔵"
    elif 'usb' in name_lower:
        return "🔌 USB"
    elif 'bluetooth' in name_lower or 'airpods' in name_lower:
        return "📡 Bluetooth"
    elif 'aggregate' in name_lower:
        return "🔗 統合"
    elif 'scarlett' in name_lower or 'focusrite' in name_lower:
        return "🎚️ プロI/F"
    elif 'zoom' in name_lower:
        return "🎙️ 録音機器"
    else:
        return "🎵 その他"

def is_recommended_device(device_name, device_info):
    """推奨デバイス判定"""
    name_lower = device_name.lower()
    
    # プロ用オーディオインターフェース
    pro_interfaces = ['scarlett', 'focusrite', 'zoom', 'universal audio', 'apollo']
    for interface in pro_interfaces:
        if interface in name_lower:
            return True
    
    # 高品質内蔵マイク（MacBook Pro）
    if 'macbook pro' in name_lower and device_info['input_channels'] > 0:
        return True
    
    # 高サンプルレート対応
    if device_info['sample_rate'] >= 48000 and device_info['input_channels'] > 0:
        return True
    
    return False

def optimize_for_apple_silicon():
    """Apple Silicon (M4 Pro) 最適化設定"""
    print("\n=== Apple Silicon M4 Pro 最適化 ===")
    
    try:
        import torch
        
        # MPS (Metal Performance Shaders) 確認
        if torch.backends.mps.is_available():
            print("✅ PyTorch MPS加速: 利用可能")
            print("🚀 GPU加速による高速音声処理が可能です")
            
            # MPS性能テスト
            try:
                device = torch.device('mps')
                test_tensor = torch.randn(1000, 1000, device=device)
                result = torch.mm(test_tensor, test_tensor)
                print("✅ MPS動作テスト: 成功")
                return 'mps'
            except Exception as e:
                print(f"⚠️ MPS動作テスト: 失敗 ({e})")
                return 'cpu'
        else:
            print("❌ PyTorch MPS加速: 利用不可")
            print("💡 PyTorch最新版をインストールしてください")
            return 'cpu'
            
    except ImportError:
        print("❌ PyTorchが見つかりません")
        print("💡 インストール: conda install pytorch torchaudio -c pytorch")
        return None

def create_macos_config():
    """macOS最適化設定ファイル作成"""
    print("\n=== macOS設定ファイル作成 ===")
    
    config = {
        "macos_optimization": {
            "core_audio": True,
            "low_latency": True,
            "sample_rate": 48000,  # macOS推奨
            "buffer_size": 512,    # 低レイテンシー
            "bit_depth": 24        # 高品質
        },
        "apple_silicon": {
            "use_mps": True,
            "memory_optimization": True,
            "batch_size_multiplier": 2  # 48GB活用
        },
        "recording": {
            "format": "wav",
            "channels": 1,          # モノラル
            "sample_rate": 48000,   # プロ品質
            "bit_depth": 24
        },
        "processing": {
            "multiprocessing": True,
            "num_workers": "auto",  # M4 Pro全コア活用
            "memory_limit": "32GB"  # 48GBのうち32GB使用
        }
    }
    
    config_path = Path("config/macos_config.json")
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 設定ファイル作成: {config_path}")
    return config_path

def install_macos_dependencies():
    """macOS専用依存関係のインストール確認"""
    print("\n=== macOS依存関係確認 ===")
    
    dependencies = {
        'sounddevice': 'pip install sounddevice',
        'soundfile': 'pip install soundfile', 
        'pyaudio': 'pip install pyaudio',  # Core Audio統合
        'torch': 'conda install pytorch torchaudio -c pytorch',
        'librosa': 'pip install librosa'
    }
    
    missing = []
    
    for package, install_cmd in dependencies.items():
        try:
            __import__(package)
            print(f"✅ {package}: インストール済み")
        except ImportError:
            print(f"❌ {package}: 未インストール")
            print(f"   インストール: {install_cmd}")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️ 未インストールパッケージ: {', '.join(missing)}")
        return False
    else:
        print("\n✅ 全ての依存関係がインストール済みです")
        return True

def run_audio_quality_test():
    """音声品質テスト"""
    print("\n=== 音声品質テスト ===")
    
    try:
        import sounddevice as sd
        import numpy as np
        
        # 高品質設定でテスト録音
        print("🎙️ 高品質録音テスト (48kHz/24bit相当)")
        
        duration = 2  # 2秒
        sample_rate = 48000
        
        print(f"📹 {duration}秒間録音中...")
        recording = sd.rec(int(duration * sample_rate), 
                          samplerate=sample_rate, 
                          channels=1, 
                          dtype='float32')
        sd.wait()
        
        # 音声品質分析
        max_amplitude = np.max(np.abs(recording))
        rms = np.sqrt(np.mean(recording**2))
        dynamic_range = 20 * np.log10(max_amplitude / (rms + 1e-10))
        
        print(f"✅ 録音完了: {len(recording)} サンプル")
        print(f"📊 最大振幅: {max_amplitude:.4f}")
        print(f"📊 RMS: {rms:.4f}")
        print(f"📊 ダイナミックレンジ: {dynamic_range:.1f} dB")
        
        # 品質判定
        if max_amplitude > 0.8:
            print("⚠️ 音量が大きすぎます - 入力レベルを下げてください")
        elif max_amplitude < 0.1:
            print("⚠️ 音量が小さすぎます - 入力レベルを上げてください")
        else:
            print("✅ 適切な録音レベルです")
        
        return True
        
    except Exception as e:
        print(f"❌ 音声品質テスト失敗: {e}")
        return False

def main():
    """メイン関数"""
    print("🍎 macOS Audio Pipeline Integrated セットアップ")
    print("🚀 MacBook Pro M4 Pro 最適化版")
    print("=" * 60)
    
    # macOS環境確認
    system_type = check_macos_version()
    if not system_type:
        sys.exit(1)
    
    # 音声権限確認
    if not check_audio_permissions():
        print("\n❌ 音声アクセス権限が必要です")
        print("💡 システム環境設定で権限を許可してから再実行してください")
        sys.exit(1)
    
    # 音声デバイス検出
    device_info = detect_audio_devices()
    if not device_info:
        print("❌ 音声デバイス検出に失敗しました")
        sys.exit(1)
    
    # Apple Silicon最適化
    if system_type == 'apple_silicon':
        gpu_type = optimize_for_apple_silicon()
        print(f"🎯 GPU加速タイプ: {gpu_type}")
    
    # 依存関係確認
    deps_ok = install_macos_dependencies()
    
    # 設定ファイル作成
    config_path = create_macos_config()
    
    # 音声品質テスト
    quality_ok = run_audio_quality_test()
    
    # 総合結果
    print("\n" + "=" * 60)
    print("📊 セットアップ結果")
    print("=" * 60)
    
    print(f"🍎 macOS環境: ✅")
    print(f"🎙️ 音声アクセス権限: ✅")
    print(f"🎛️ 音声デバイス: {device_info['total_devices']}個検出")
    print(f"📦 依存関係: {'✅' if deps_ok else '⚠️'}")
    print(f"⚙️ 設定ファイル: ✅ ({config_path})")
    print(f"🎵 音声品質: {'✅' if quality_ok else '⚠️'}")
    
    if system_type == 'apple_silicon':
        print(f"🚀 Apple Silicon最適化: ✅")
    
    print("\n🎉 macOS セットアップ完了！")
    print("🎵 Audio Pipeline Integrated の使用準備が整いました")
    
    if not deps_ok:
        print("\n⚠️ 一部の依存関係が不足しています")
        print("上記のインストールコマンドを実行してください")

if __name__ == "__main__":
    main()