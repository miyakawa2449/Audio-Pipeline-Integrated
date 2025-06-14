import os
import shutil
from datetime import datetime

def rename_all_files():
    """音声ファイルとメタファイルを同時に正しい形式に変換"""
    
    audio_dir = "dataset/audio_files"
    meta_dir = "dataset/meta_files"
    
    # 現在のファイル一覧を取得
    current_audio = [f for f in os.listdir(audio_dir) 
                    if f.startswith('audio_cocoro.txt_') and f.endswith('.wav')]
    current_meta = [f for f in os.listdir(meta_dir) 
                   if f.startswith('meta_cocoro.txt_') and f.endswith('.txt')]
    
    # ファイルを番号順にソート
    current_audio.sort()
    current_meta.sort()
    
    print("=== 現在のファイル状況 ===")
    print(f"音声ファイル: {len(current_audio)}個")
    print(f"メタファイル: {len(current_meta)}個")
    
    # サンプル表示
    print(f"\n音声ファイル例:")
    for i, file in enumerate(current_audio[:3]):
        print(f"  {i+1}. {file}")
    if len(current_audio) > 3:
        print(f"  ... and {len(current_audio)-3} more files")
    
    print(f"\nメタファイル例:")
    for i, file in enumerate(current_meta[:3]):
        print(f"  {i+1}. {file}")
    if len(current_meta) > 3:
        print(f"  ... and {len(current_meta)-3} more files")
    
    # ファイル数の確認
    if len(current_audio) != len(current_meta):
        print(f"\n⚠️  警告: 音声ファイル({len(current_audio)}個)とメタファイル({len(current_meta)}個)の数が一致しません")
        choice = input("続行しますか？ (y/N): ")
        if choice.lower() != 'y':
            print("キャンセルしました")
            return
    
    # 確認
    total_files = len(current_audio) + len(current_meta)
    confirm = input(f"\n合計{total_files}個のファイルをリネームしますか？ (y/N): ")
    if confirm.lower() != 'y':
        print("キャンセルしました")
        return
    
    # バックアップディレクトリを作成
    backup_dir = "dataset/backup_original_names"
    os.makedirs(backup_dir, exist_ok=True)
    
    # リネーム実行
    results = {
        'audio_success': 0,
        'audio_errors': [],
        'meta_success': 0,
        'meta_errors': []
    }
    
    print(f"\n=== リネーム開始 ===")
    
    # 1. 音声ファイルのリネーム
    print("音声ファイルを処理中...")
    for i, old_filename in enumerate(current_audio):
        try:
            new_filename = f"audio_{i+1}.wav"
            old_path = os.path.join(audio_dir, old_filename)
            new_path = os.path.join(audio_dir, new_filename)
            
            # バックアップ情報を保存
            save_backup_info(backup_dir, f"audio_{i+1:03d}_backup.txt", old_filename, new_filename, old_path)
            
            # ファイルをリネーム
            shutil.move(old_path, new_path)
            print(f"  ✓ {old_filename} → {new_filename}")
            results['audio_success'] += 1
            
        except Exception as e:
            error_msg = f"Failed to rename {old_filename}: {e}"
            results['audio_errors'].append(error_msg)
            print(f"  ❌ {error_msg}")
    
    # 2. メタファイルのリネーム
    print(f"\nメタファイルを処理中...")
    for i, old_filename in enumerate(current_meta):
        try:
            new_filename = f"meta_{i+1}.txt"
            old_path = os.path.join(meta_dir, old_filename)
            new_path = os.path.join(meta_dir, new_filename)
            
            # バックアップ情報を保存
            save_backup_info(backup_dir, f"meta_{i+1:03d}_backup.txt", old_filename, new_filename, old_path)
            
            # ファイルをリネーム
            shutil.move(old_path, new_path)
            print(f"  ✓ {old_filename} → {new_filename}")
            results['meta_success'] += 1
            
        except Exception as e:
            error_msg = f"Failed to rename {old_filename}: {e}"
            results['meta_errors'].append(error_msg)
            print(f"  ❌ {error_msg}")
    
    # 結果表示
    print_results(results, backup_dir)
    
    # 最終確認
    verify_final_structure()

def save_backup_info(backup_dir: str, backup_filename: str, old_name: str, new_name: str, old_path: str):
    """バックアップ情報を保存"""
    backup_path = os.path.join(backup_dir, backup_filename)
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(f"Rename Log - {datetime.now()}\n")
        f.write(f"Original: {old_name}\n")
        f.write(f"Renamed: {new_name}\n")
        f.write(f"Original Path: {old_path}\n")
        f.write(f"File Size: {os.path.getsize(old_path) if os.path.exists(old_path) else 'Unknown'} bytes\n")

def print_results(results: dict, backup_dir: str):
    """結果を表示"""
    print(f"\n=== リネーム完了 ===")
    print(f"音声ファイル:")
    print(f"  成功: {results['audio_success']}個")
    print(f"  失敗: {len(results['audio_errors'])}個")
    
    print(f"メタファイル:")
    print(f"  成功: {results['meta_success']}個")
    print(f"  失敗: {len(results['meta_errors'])}個")
    
    total_success = results['audio_success'] + results['meta_success']
    total_errors = len(results['audio_errors']) + len(results['meta_errors'])
    
    print(f"\n総計:")
    print(f"  ✓ 成功: {total_success}個")
    print(f"  ❌ 失敗: {total_errors}個")
    
    # エラー詳細
    all_errors = results['audio_errors'] + results['meta_errors']
    if all_errors:
        print(f"\nエラー詳細:")
        for error in all_errors:
            print(f"  - {error}")
    
    print(f"\nバックアップ情報: {backup_dir}")

def verify_final_structure():
    """最終的なファイル構造を確認"""
    audio_dir = "dataset/audio_files"
    meta_dir = "dataset/meta_files"
    
    print(f"\n=== 最終ファイル構造確認 ===")
    
    # 新しい形式のファイルを取得
    audio_files = [f for f in os.listdir(audio_dir) 
                  if f.startswith('audio_') and f.endswith('.wav') and f != 'audio_cocoro.txt_0001.wav']
    meta_files = [f for f in os.listdir(meta_dir) 
                 if f.startswith('meta_') and f.endswith('.txt') and f != 'meta_cocoro.txt_0001.txt']
    
    # 番号順にソート
    audio_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
    meta_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
    
    print(f"新しい音声ファイル: {len(audio_files)}個")
    print(f"新しいメタファイル: {len(meta_files)}個")
    
    # 対応関係をチェック
    print(f"\n対応関係チェック (最初の10個):")
    
    max_check = min(10, max(len(audio_files), len(meta_files)))
    mismatches = []
    
    for i in range(1, max_check + 1):
        audio_expected = f"audio_{i}.wav"
        meta_expected = f"meta_{i}.txt"
        
        audio_exists = audio_expected in audio_files
        meta_exists = meta_expected in meta_files
        
        if audio_exists and meta_exists:
            print(f"  ✓ {i:2d}: {audio_expected} ↔ {meta_expected}")
        else:
            status = []
            if not audio_exists:
                status.append("音声なし")
            if not meta_exists:
                status.append("メタなし")
            print(f"  ❌ {i:2d}: {audio_expected} ↔ {meta_expected} ({', '.join(status)})")
            mismatches.append(i)
    
    if len(audio_files) > 10 or len(meta_files) > 10:
        print(f"  ... and more files")
    
    # 総合判定
    if len(audio_files) == len(meta_files) and len(mismatches) == 0:
        print(f"\n✅ 完璧！全{len(audio_files)}ペアのファイル構造が正常です")
        print("システムがデータセットを正常に認識できます")
    else:
        print(f"\n⚠️  注意: {len(mismatches)}個の不整合があります")
        if len(audio_files) != len(meta_files):
            print(f"ファイル数不一致: 音声{len(audio_files)}個 vs メタ{len(meta_files)}個")

def show_content_sample():
    """変換後のファイル内容サンプルを表示"""
    meta_dir = "dataset/meta_files"
    
    print(f"\n=== ファイル内容サンプル ===")
    
    # 最初のメタファイルの内容を表示
    first_meta = os.path.join(meta_dir, "meta_1.txt")
    if os.path.exists(first_meta):
        try:
            with open(first_meta, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            print(f"meta_1.txt の内容:")
            print(f"  「{content}」")
            print(f"  文字数: {len(content)}文字")
        except Exception as e:
            print(f"meta_1.txt の読み込みエラー: {e}")
    else:
        print("meta_1.txt が見つかりません")

if __name__ == "__main__":
    print("=== 音声・メタファイル一括リネームツール ===")
    print("audio_cocoro.txt_NNNN.wav → audio_N.wav")
    print("meta_cocoro.txt_NNNN.txt → meta_N.txt")
    print()
    
    choice = input("実行しますか？ (y/N): ").strip()
    
    if choice.lower() == 'y':
        rename_all_files()
        show_content_sample()
    else:
        print("キャンセルしました")