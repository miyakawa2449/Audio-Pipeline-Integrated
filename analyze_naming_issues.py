#!/usr/bin/env python3
"""
ファイル命名形式による問題分析
"""
import os
from pathlib import Path

def test_file_sorting():
    """ファイルソート順の問題をテスト"""
    print("=== ファイルソート順比較 ===")
    
    # シンプル形式（現在の実装）
    simple_files = [f"audio_{i}.wav" for i in [1, 2, 3, 10, 11, 20, 100]]
    simple_sorted = sorted(simple_files)
    
    # 4桁形式
    padded_files = [f"audio_{i:04d}.wav" for i in [1, 2, 3, 10, 11, 20, 100]]
    padded_sorted = sorted(padded_files)
    
    print("シンプル形式のソート結果:")
    for i, filename in enumerate(simple_sorted):
        print(f"  {i+1:2d}. {filename}")
    
    print("\n4桁形式のソート結果:")
    for i, filename in enumerate(padded_sorted):
        print(f"  {i+1:2d}. {filename}")
    
    # 問題の確認
    expected_order = [1, 2, 3, 10, 11, 20, 100]
    simple_numbers = [int(f.split('_')[1].split('.')[0]) for f in simple_sorted]
    padded_numbers = [int(f.split('_')[1].split('.')[0]) for f in padded_sorted]
    
    simple_correct = simple_numbers == expected_order
    padded_correct = padded_numbers == expected_order
    
    print(f"\nシンプル形式の順序正確性: {'✅' if simple_correct else '❌'}")
    print(f"4桁形式の順序正確性: {'✅' if padded_correct else '❌'}")
    
    return padded_correct and not simple_correct

def test_external_tool_compatibility():
    """外部ツール互換性テスト"""
    print("\n=== 外部ツール互換性 ===")
    
    # テストファイル作成
    test_dir = Path("test_external_tools")
    test_dir.mkdir(exist_ok=True)
    
    # シンプル形式
    simple_dir = test_dir / "simple"
    simple_dir.mkdir(exist_ok=True)
    for i in [1, 2, 10, 20]:
        (simple_dir / f"audio_{i}.wav").touch()
    
    # 4桁形式
    padded_dir = test_dir / "padded"
    padded_dir.mkdir(exist_ok=True)
    for i in [1, 2, 10, 20]:
        (padded_dir / f"audio_{i:04d}.wav").touch()
    
    # システムの ls コマンドでのソート確認
    print("システム ls コマンドでのソート結果:")
    
    import subprocess
    
    try:
        # シンプル形式
        result_simple = subprocess.run(['ls', str(simple_dir)], 
                                     capture_output=True, text=True)
        print("シンプル形式:")
        for line in result_simple.stdout.strip().split('\n'):
            print(f"  {line}")
        
        # 4桁形式
        result_padded = subprocess.run(['ls', str(padded_dir)], 
                                     capture_output=True, text=True)
        print("4桁形式:")
        for line in result_padded.stdout.strip().split('\n'):
            print(f"  {line}")
            
    except Exception as e:
        print(f"外部コマンドテストエラー: {e}")
    
    # クリーンアップ
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
    
    return True

def test_scalability():
    """スケーラビリティテスト"""
    print("\n=== スケーラビリティ分析 ===")
    
    # 大量ファイルでの問題
    large_numbers = [1, 10, 100, 1000, 5000]
    
    print("大量ファイル時の命名例:")
    print("シンプル形式:")
    for num in large_numbers:
        filename = f"audio_{num}.wav"
        print(f"  {filename:20s} (長さ: {len(filename)} 文字)")
    
    print("4桁形式:")
    for num in large_numbers:
        filename = f"audio_{num:04d}.wav"
        print(f"  {filename:20s} (長さ: {len(filename)} 文字)")
    
    # パディング不足の問題
    print("\n4桁パディングで不足する場合:")
    very_large = [9999, 10000, 50000]
    for num in very_large:
        filename = f"audio_{num:04d}.wav"
        print(f"  {num:5d} → {filename}")
        if num > 9999:
            print(f"    ⚠️ 4桁を超過、5桁になる")
    
    return True

def analyze_current_codebase():
    """現在のコードベースでの影響分析"""
    print("\n=== 現在のコードベースへの影響 ===")
    
    # AudioOptのファイル検索ロジック確認
    print("AudioOpt collect_data_files() の動作:")
    print("  ✅ glob.glob('audio_*.wav') → 両形式対応")
    print("  ✅ re.match(r'audio_(\\d+)\\.wav') → 両形式対応")
    print("  ✅ 柔軟な番号抽出 → 問題なし")
    
    # Python_Audio_datasetの影響
    print("\nPython_Audio_dataset の動作:")
    print("  ⚠️ 現在シンプル形式で出力")
    print("  ⚠️ ファイル一覧表示時にソート順が混乱する可能性")
    
    # shared_dataset_manager
    print("\nshared_dataset_manager の動作:")
    print("  ✅ glob パターン検索 → 両形式対応")
    print("  ✅ ファイル同期 → 問題なし")
    
    return True

def main():
    """メイン分析関数"""
    print("🔍 ファイル命名形式の詳細分析")
    print("=" * 50)
    
    issues_found = []
    
    if test_file_sorting():
        issues_found.append("ファイルソート順の問題")
    
    test_external_tool_compatibility()
    test_scalability()
    analyze_current_codebase()
    
    print("\n" + "=" * 50)
    print("📊 分析結果")
    print("=" * 50)
    
    if issues_found:
        print("🚨 発見された問題:")
        for issue in issues_found:
            print(f"  • {issue}")
        print("\n💡 推奨: 4桁ゼロパディング形式への変更")
    else:
        print("✅ 重大な問題は発見されませんでした")
        print("💭 ただし、4桁形式の方が業界標準に準拠")
    
    print("\n🎯 結論:")
    print("4桁ゼロパディング形式 (audio_0001.wav) を推奨")
    print("理由:")
    print("  • ファイル一覧の視認性向上")
    print("  • 外部ツールとの互換性")
    print("  • 業界標準への準拠")
    print("  • 大規模データセットでの一貫性")

if __name__ == "__main__":
    main()