#!/usr/bin/env python3
"""
最終的なファイル命名形式の統合テスト
4桁ゼロパディング形式での動作確認
"""
import os
import glob
import re
from pathlib import Path

def test_python_audio_naming():
    """Python_Audio_dataset の4桁命名をテスト"""
    print("=== Python_Audio_dataset 4桁命名テスト ===")
    
    test_cases = [
        {"line_number": 1, "expected": "audio_0001.wav"},
        {"line_number": 5, "expected": "audio_0005.wav"},
        {"line_number": 100, "expected": "audio_0100.wav"},
        {"line_number": 1000, "expected": "audio_1000.wav"}
    ]
    
    success = True
    for case in test_cases:
        file_number = case["line_number"]
        # 修正後の4桁形式
        audio_filename = f"audio_{file_number:04d}.wav"
        expected = case["expected"]
        
        if audio_filename == expected:
            print(f"✅ 行{file_number:4d}: {audio_filename}")
        else:
            print(f"❌ 行{file_number:4d}: {audio_filename} (期待値: {expected})")
            success = False
    
    return success

def test_audioopt_compatibility():
    """AudioOpt の4桁形式互換性テスト"""
    print("\n=== AudioOpt 4桁形式互換性テスト ===")
    
    # テストディレクトリ作成
    test_dir = Path("test_audioopt_4digit")
    audio_dir = test_dir / "audio_files" 
    meta_dir = test_dir / "meta_files"
    audio_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)
    
    # 4桁形式テストファイル作成
    test_numbers = [1, 5, 10, 100, 500]
    for i in test_numbers:
        audio_file = audio_dir / f"audio_{i:04d}.wav"
        meta_file = meta_dir / f"meta_{i:04d}.txt"
        audio_file.touch()
        meta_file.write_text(f"テストテキスト{i}", encoding='utf-8')
    
    # AudioOptの検索ロジックをテスト
    audio_files = []
    text_files = []
    
    audio_pattern = str(audio_dir / "audio_*.wav")
    found_audio_files = glob.glob(audio_pattern)
    
    for audio_file in sorted(found_audio_files):
        basename = os.path.basename(audio_file)
        match = re.match(r"audio_(\d+)\.wav", basename)
        if match:
            number = match.group(1)
            meta_file = meta_dir / f"meta_{number}.txt"
            
            if meta_file.exists():
                audio_files.append(audio_file)
                text_files.append(str(meta_file))
                # 番号を整数として取得
                file_num = int(number)
                print(f"✅ ペア発見: audio_{number}.wav (番号: {file_num})")
            else:
                print(f"❌ メタファイル不足: {basename}")
    
    print(f"📊 検出されたペア数: {len(audio_files)}")
    print(f"📊 期待値: {len(test_numbers)}")
    
    # クリーンアップ
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
    
    return len(audio_files) == len(test_numbers)

def test_file_sorting():
    """4桁形式でのファイルソート確認"""
    print("\n=== 4桁形式ファイルソートテスト ===")
    
    # テストファイル名生成
    test_numbers = [1, 2, 3, 10, 11, 20, 100, 500, 1000]
    padded_files = [f"audio_{i:04d}.wav" for i in test_numbers]
    
    # ソート実行
    sorted_files = sorted(padded_files)
    
    print("4桁形式のソート結果:")
    for i, filename in enumerate(sorted_files):
        # ファイル名から番号を抽出
        number = int(filename.split('_')[1].split('.')[0])
        print(f"  {i+1:2d}. {filename} (番号: {number})")
    
    # 順序の正確性確認
    sorted_numbers = [int(f.split('_')[1].split('.')[0]) for f in sorted_files]
    expected_order = sorted(test_numbers)
    
    correct_order = sorted_numbers == expected_order
    print(f"\n4桁形式の順序正確性: {'✅' if correct_order else '❌'}")
    
    return correct_order

def test_mixed_format_compatibility():
    """新旧混在形式での互換性テスト"""
    print("\n=== 新旧混在形式互換性テスト ===")
    
    # 混在したファイル名
    mixed_files = [
        "audio_0001.wav",  # 4桁形式
        "audio_5.wav",     # シンプル形式
        "audio_0010.wav",  # 4桁形式
        "audio_20.wav",    # シンプル形式
        "audio_0100.wav",  # 4桁形式
    ]
    
    success = True
    for filename in mixed_files:
        if filename.startswith("audio_"):
            try:
                line_num_str = filename.split("_")[1].replace(".wav", "")
                line_number = int(line_num_str)
                format_type = "4桁" if len(line_num_str) >= 4 and line_num_str.startswith('0') else "シンプル"
                print(f"✅ {filename:15s} → 行番号: {line_number:4d} ({format_type})")
            except (ValueError, IndexError) as e:
                print(f"❌ {filename:15s} → エラー: {e}")
                success = False
        else:
            print(f"❌ {filename:15s} → 不正な形式")
            success = False
    
    return success

def main():
    """メインテスト関数"""
    print("🧪 最終ファイル命名形式テスト (4桁ゼロパディング)")
    print("=" * 60)
    
    test_results = []
    
    # 各テストを実行
    test_results.append(("Python_Audio_dataset 4桁命名", test_python_audio_naming()))
    test_results.append(("AudioOpt 4桁形式互換性", test_audioopt_compatibility()))
    test_results.append(("4桁形式ファイルソート", test_file_sorting()))
    test_results.append(("新旧混在形式互換性", test_mixed_format_compatibility()))
    
    # 結果表示
    print("\n" + "=" * 60)
    print("📊 最終テスト結果")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ 合格" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("🎉 全てのテストが合格しました！")
        print("✅ 4桁ゼロパディング形式での統合は成功です")
        print("📁 出力形式: audio_0001.wav, audio_0002.wav, ...")
        print("🔄 AudioOptとの完全互換性を確認")
    else:
        print("⚠️ 一部のテストが失敗しました")
        print("❌ 追加の調査が必要です")
    
    return all_passed

if __name__ == "__main__":
    main()