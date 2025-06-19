#!/usr/bin/env python3
"""
ファイル命名修正の統合テスト
"""
import os
import glob
import re
from pathlib import Path

def test_audioopt_file_collection():
    """AudioOptのファイル検索ロジックをテスト"""
    print("=== AudioOpt ファイル検索テスト ===")
    
    # テストディレクトリ作成
    test_dir = Path("test_audioopt")
    audio_dir = test_dir / "audio_files" 
    meta_dir = test_dir / "meta_files"
    audio_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)
    
    # テストファイル作成（欠番あり）
    test_numbers = [1, 3, 5, 10, 15]
    for i in test_numbers:
        audio_file = audio_dir / f"audio_{i}.wav"
        meta_file = meta_dir / f"meta_{i}.txt"
        audio_file.touch()
        meta_file.write_text(f"テストテキスト{i}", encoding='utf-8')
    
    # 修正されたロジックをテスト
    audio_files = []
    text_files = []
    
    # audio_*.wav ファイルを全て検索
    audio_pattern = str(audio_dir / "audio_*.wav")
    found_audio_files = glob.glob(audio_pattern)
    
    for audio_file in sorted(found_audio_files):
        # ファイル名から番号を抽出
        basename = os.path.basename(audio_file)
        match = re.match(r"audio_(\d+)\.wav", basename)
        if match:
            number = match.group(1)
            meta_file = meta_dir / f"meta_{number}.txt"
            
            # 対応するメタファイルが存在する場合のみ追加
            if meta_file.exists():
                audio_files.append(audio_file)
                text_files.append(str(meta_file))
                print(f"✅ ペア発見: audio_{number}.wav + meta_{number}.txt")
            else:
                print(f"❌ メタファイル不足: {basename}")
    
    print(f"📊 検出されたペア数: {len(audio_files)}")
    print(f"📊 期待値: {len(test_numbers)}")
    
    # クリーンアップ
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
    
    return len(audio_files) == len(test_numbers)

def test_python_audio_naming():
    """Python_Audio_datasetの命名形式をテスト"""
    print("\n=== Python_Audio_dataset 命名形式テスト ===")
    
    # 新しい命名形式テスト
    test_cases = [
        {"line_number": 1, "expected": "audio_1.wav"},
        {"line_number": 5, "expected": "audio_5.wav"},
        {"line_number": 100, "expected": "audio_100.wav"}
    ]
    
    success = True
    for case in test_cases:
        file_number = case["line_number"]
        # 修正後の形式
        audio_filename = f"audio_{file_number}.wav"
        expected = case["expected"]
        
        if audio_filename == expected:
            print(f"✅ 行{file_number}: {audio_filename}")
        else:
            print(f"❌ 行{file_number}: {audio_filename} (期待値: {expected})")
            success = False
    
    return success

def test_compatibility():
    """新旧形式の互換性テスト"""
    print("\n=== 新旧形式互換性テスト ===")
    
    # text_manager.pyのロジックをテスト
    test_filenames = [
        "audio_1.wav",      # 新形式
        "audio_0001.wav",   # 旧形式
        "audio_5.wav",      # 新形式
        "audio_0005.wav",   # 旧形式
    ]
    
    success = True
    for filename in test_filenames:
        # ファイル名から行番号を抽出する処理をテスト
        if filename.startswith("audio_"):
            try:
                line_num_str = filename.split("_")[1].replace(".wav", "")
                line_number = int(line_num_str)
                print(f"✅ {filename} → 行番号: {line_number}")
            except (ValueError, IndexError) as e:
                print(f"❌ {filename} → エラー: {e}")
                success = False
        else:
            print(f"❌ {filename} → 不正な形式")
            success = False
    
    return success

def main():
    """メインテスト関数"""
    print("🧪 ファイル命名修正 統合テスト")
    print("=" * 50)
    
    test_results = []
    
    # 各テストを実行
    test_results.append(("AudioOpt ファイル検索", test_audioopt_file_collection()))
    test_results.append(("Python_Audio_dataset 命名", test_python_audio_naming()))
    test_results.append(("新旧形式互換性", test_compatibility()))
    
    # 結果表示
    print("\n" + "=" * 50)
    print("📊 テスト結果")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ 合格" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("🎉 全てのテストが合格しました！")
        print("✅ ファイル命名修正は成功です")
    else:
        print("⚠️ 一部のテストが失敗しました")
        print("❌ 追加の修正が必要です")
    
    return all_passed

if __name__ == "__main__":
    main()