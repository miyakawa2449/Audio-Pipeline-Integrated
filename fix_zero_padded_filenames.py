#!/usr/bin/env python3
"""
4桁ゼロパディング形式のファイルを新形式に変換
audio_0001.wav → audio_1.wav
meta_0001.txt → meta_1.txt
"""
import os
import shutil
import json
import re
from pathlib import Path

def convert_zero_padded_files():
    """4桁ゼロパディング形式のファイルを新形式に変換"""
    print("🔄 4桁ゼロパディング形式ファイルの変換を開始...")
    
    # ディレクトリパス
    audio_dir = Path("Python_Audio_dataset/dataset/audio_files")
    meta_dir = Path("Python_Audio_dataset/dataset/meta_files")
    metadata_path = Path("Python_Audio_dataset/dataset/metadata.txt")
    session_path = Path("Python_Audio_dataset/data/session.json")
    
    if not audio_dir.exists():
        print("❌ Python_Audio_dataset/dataset/audio_files が見つかりません")
        return False
    
    # バックアップディレクトリ作成
    backup_dir = audio_dir.parent / "backup_zero_padded"
    backup_dir.mkdir(exist_ok=True)
    
    conversions = []
    
    # 4桁ゼロパディング形式のファイルを検索
    for audio_file in audio_dir.glob("audio_*.wav"):
        filename = audio_file.name
        match = re.match(r"audio_(\d{4,})\.wav", filename)  # 4桁以上の数字
        
        if match:
            old_number = match.group(1)
            new_number = str(int(old_number))  # ゼロパディングを除去
            
            # 新しいファイル名が違う場合のみ変換対象とする
            if old_number != new_number:
                old_audio = f"audio_{old_number}.wav"
                new_audio = f"audio_{new_number}.wav"
                old_meta = f"meta_{old_number}.txt"
                new_meta = f"meta_{new_number}.txt"
                
                conversions.append({
                    'old_audio': old_audio,
                    'new_audio': new_audio,
                    'old_meta': old_meta,
                    'new_meta': new_meta,
                    'number': new_number
                })
    
    if not conversions:
        print("✅ 4桁ゼロパディング形式のファイルは見つかりませんでした")
        return True
    
    print(f"📊 {len(conversions)} 件のファイルを変換します:")
    for conv in conversions[:5]:  # 最初の5件表示
        print(f"  {conv['old_audio']} → {conv['new_audio']}")
    if len(conversions) > 5:
        print(f"  ... 他 {len(conversions) - 5} 件")
    
    confirm = input("\n変換を実行しますか？ (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ 変換をキャンセルしました")
        return False
    
    converted_count = 0
    
    # ファイル変換実行
    for conv in conversions:
        # 音声ファイル変換
        old_audio_path = audio_dir / conv['old_audio']
        new_audio_path = audio_dir / conv['new_audio']
        
        if old_audio_path.exists() and not new_audio_path.exists():
            # バックアップ
            shutil.copy2(old_audio_path, backup_dir / conv['old_audio'])
            # リネーム
            shutil.move(old_audio_path, new_audio_path)
            print(f"🔄 {conv['old_audio']} → {conv['new_audio']}")
            converted_count += 1
        
        # メタファイル変換
        old_meta_path = meta_dir / conv['old_meta']
        new_meta_path = meta_dir / conv['new_meta']
        
        if old_meta_path.exists() and not new_meta_path.exists():
            # バックアップ
            shutil.copy2(old_meta_path, backup_dir / conv['old_meta'])
            # リネーム
            shutil.move(old_meta_path, new_meta_path)
            print(f"📝 {conv['old_meta']} → {conv['new_meta']}")
    
    # metadata.txt更新
    if metadata_path.exists():
        print("📋 metadata.txt を更新中...")
        shutil.copy2(metadata_path, backup_dir / "metadata_original.txt")
        
        # metadata.txtの内容を読み込み、ファイル名を更新
        with open(metadata_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        updated_lines = []
        for line in lines:
            if '|' in line:
                filename, text = line.strip().split('|', 1)
                # ファイル名が変換対象かチェック
                for conv in conversions:
                    if filename == conv['old_audio']:
                        filename = conv['new_audio']
                        break
                updated_lines.append(f"{filename}|{text}\n")
            else:
                updated_lines.append(line)
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            f.writelines(updated_lines)
    
    # session.json更新
    if session_path.exists():
        print("🔄 session.json を更新中...")
        shutil.copy2(session_path, backup_dir / "session_original.json")
        
        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # session.jsonのファイル名を更新
            if 'all_texts' in session_data:
                for text_item in session_data['all_texts']:
                    if 'audio_filename' in text_item and text_item['audio_filename']:
                        old_filename = text_item['audio_filename']
                        for conv in conversions:
                            if old_filename == conv['old_audio']:
                                text_item['audio_filename'] = conv['new_audio']
                                break
            
            with open(session_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"⚠️ session.json更新エラー: {e}")
    
    print(f"✅ 変換完了: {converted_count} ファイル")
    print(f"💾 バックアップ保存先: {backup_dir}")
    return True

def verify_conversion():
    """変換結果の検証"""
    print("\n🔍 変換結果の検証...")
    
    audio_dir = Path("Python_Audio_dataset/dataset/audio_files")
    meta_dir = Path("Python_Audio_dataset/dataset/meta_files")
    
    # 残っている4桁ゼロパディングファイルをチェック
    remaining_padded = []
    for audio_file in audio_dir.glob("audio_*.wav"):
        match = re.match(r"audio_(\d{4,})\.wav", audio_file.name)
        if match and match.group(1) != str(int(match.group(1))):
            remaining_padded.append(audio_file.name)
    
    if remaining_padded:
        print(f"⚠️ まだ4桁ゼロパディング形式のファイルが残っています:")
        for filename in remaining_padded[:5]:
            print(f"  {filename}")
    else:
        print("✅ 全ての4桁ゼロパディングファイルが変換されました")
    
    # 新形式ファイル数をカウント
    audio_files = list(audio_dir.glob("audio_*.wav"))
    meta_files = list(meta_dir.glob("meta_*.txt"))
    
    print(f"📊 音声ファイル: {len(audio_files)} 件")
    print(f"📊 メタファイル: {len(meta_files)} 件")

def main():
    """メイン関数"""
    print("🎯 4桁ゼロパディング形式ファイル変換ツール")
    print("=" * 60)
    print("変換対象:")
    print("  • audio_0001.wav → audio_1.wav")
    print("  • meta_0001.txt → meta_1.txt")
    print("  • metadata.txt内のファイル名も更新")
    print("  • session.json内のファイル名も更新")
    print()
    
    if convert_zero_padded_files():
        verify_conversion()
        print("\n🎉 変換が完了しました！")
        print("📚 統合システムでの使用準備が整いました")
    else:
        print("\n❌ 変換に失敗しました")

if __name__ == "__main__":
    main()