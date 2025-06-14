import os
import shutil

def rename_audio_files():
    """音声ファイル名を正しい形式に変換"""
    
    audio_dir = "dataset/audio_files"
    meta_dir = "dataset/meta_files"
    
    # 現在のファイル一覧を取得
    current_files = [f for f in os.listdir(audio_dir) 
                    if f.startswith('audio_cocoro.txt_') and f.endswith('.wav')]
    
    # ファイルを番号順にソート
    current_files.sort()
    
    print(f"Found {len(current_files)} audio files to rename")
    print("Current files:")
    for i, file in enumerate(current_files[:5]):  # 最初の5つを表示
        print(f"  {i+1:2d}. {file}")
    if len(current_files) > 5:
        print(f"  ... and {len(current_files)-5} more files")
    
    # 確認
    confirm = input(f"\n{len(current_files)}個のファイルを audio_N.wav 形式にリネームしますか？ (y/N): ")
    if confirm.lower() != 'y':
        print("キャンセルしました")
        return
    
    # バックアップディレクトリを作成
    backup_dir = "dataset/backup_original_names"
    os.makedirs(backup_dir, exist_ok=True)
    
    # リネーム実行
    renamed_count = 0
    errors = []
    
    for i, old_filename in enumerate(current_files):
        try:
            # 新しいファイル名を生成
            new_filename = f"audio_{i+1}.wav"
            
            old_path = os.path.join(audio_dir, old_filename)
            new_path = os.path.join(audio_dir, new_filename)
            
            # バックアップ情報を保存
            backup_info_path = os.path.join(backup_dir, f"rename_log_{i+1:03d}.txt")
            with open(backup_info_path, 'w', encoding='utf-8') as f:
                f.write(f"Original: {old_filename}\n")
                f.write(f"Renamed: {new_filename}\n")
                f.write(f"Date: {os.path.getctime(old_path)}\n")
            
            # ファイルをリネーム
            shutil.move(old_path, new_path)
            print(f"  ✓ {old_filename} → {new_filename}")
            renamed_count += 1
            
        except Exception as e:
            error_msg = f"Failed to rename {old_filename}: {e}"
            errors.append(error_msg)
            print(f"  ❌ {error_msg}")
    
    # 結果表示
    print(f"\n=== リネーム完了 ===")
    print(f"成功: {renamed_count}個")
    print(f"失敗: {len(errors)}個")
    
    if errors:
        print("\nエラー詳細:")
        for error in errors:
            print(f"  - {error}")
    
    # メタファイルの確認と生成
    check_and_create_meta_files(renamed_count, meta_dir)
    
    print(f"\nバックアップ情報: {backup_dir}")
    print("リネーム完了！")

def check_and_create_meta_files(audio_count: int, meta_dir: str):
    """対応するメタファイルの確認と生成"""
    
    print(f"\n=== メタファイル確認 ===")
    
    # 既存のメタファイルを確認
    existing_meta = [f for f in os.listdir(meta_dir) 
                    if f.startswith('meta_') and f.endswith('.txt')]
    
    print(f"既存メタファイル: {len(existing_meta)}個")
    print(f"音声ファイル: {audio_count}個")
    
    if len(existing_meta) == audio_count:
        print("✓ メタファイル数が一致しています")
        return
    
    # 不足している場合、プレースホルダーを作成
    if len(existing_meta) < audio_count:
        missing_count = audio_count - len(existing_meta)
        print(f"❌ メタファイルが{missing_count}個不足しています")
        
        create_placeholder = input("プレースホルダーのメタファイルを作成しますか？ (y/N): ")
        if create_placeholder.lower() == 'y':
            for i in range(len(existing_meta) + 1, audio_count + 1):
                placeholder_path = os.path.join(meta_dir, f"meta_{i}.txt")
                with open(placeholder_path, 'w', encoding='utf-8') as f:
                    f.write(f"[プレースホルダー] audio_{i}.wav用のテキスト内容を入力してください")
                print(f"  作成: meta_{i}.txt")
            print(f"✓ {missing_count}個のプレースホルダーメタファイルを作成しました")

def verify_file_structure():
    """ファイル構造を確認"""
    
    audio_dir = "dataset/audio_files"
    meta_dir = "dataset/meta_files"
    
    print("=== ファイル構造確認 ===")
    
    # 音声ファイル確認
    audio_files = [f for f in os.listdir(audio_dir) 
                  if f.startswith('audio_') and f.endswith('.wav')]
    audio_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
    
    # メタファイル確認
    meta_files = [f for f in os.listdir(meta_dir) 
                 if f.startswith('meta_') and f.endswith('.txt')]
    meta_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
    
    print(f"音声ファイル: {len(audio_files)}個")
    print(f"メタファイル: {len(meta_files)}個")
    
    # 対応関係をチェック
    print(f"\n対応関係チェック:")
    mismatches = []
    
    for i in range(1, max(len(audio_files), len(meta_files)) + 1):
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
    
    if mismatches:
        print(f"\n不整合ファイル: {len(mismatches)}個")
        print("修正が必要です")
    else:
        print(f"\n✓ 全{len(audio_files)}ファイルの対応関係が正常です")

if __name__ == "__main__":
    print("=== 音声ファイル名変換ツール ===")
    print("1. ファイル名をリネーム")
    print("2. ファイル構造を確認")
    
    choice = input("選択してください (1/2): ").strip()
    
    if choice == "1":
        rename_audio_files()
    elif choice == "2":
        verify_file_structure()
    else:
        print("無効な選択です")