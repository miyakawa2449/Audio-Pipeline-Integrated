#!/usr/bin/env python3
"""
Audio Pipeline Integrated - 統合ファイルユーティリティ
全プロジェクト共通のファイル・ディレクトリ操作機能
"""

import os
import shutil
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Union, Any
from .logger import get_logger


class FileUtils:
    """統合ファイル操作ユーティリティクラス"""
    
    def __init__(self):
        """初期化"""
        self.logger = get_logger("FileUtils")
        self.logger.info("FileUtils初期化完了")
    
    def setup_directories(self, directories: List[Union[str, Path]], 
                         base_path: Optional[Union[str, Path]] = None) -> bool:
        """
        ディレクトリ一括作成（統合版）
        
        Args:
            directories: 作成するディレクトリリスト
            base_path: ベースパス（None: カレントディレクトリ）
            
        Returns:
            全ディレクトリ作成成功フラグ
        """
        base = Path(base_path) if base_path else Path.cwd()
        success_count = 0
        
        self.logger.info(f"ディレクトリ作成開始: {len(directories)}個")
        
        for directory in directories:
            dir_path = base / directory
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"ディレクトリ作成成功: {dir_path}")
                success_count += 1
            except Exception as e:
                self.logger.error(f"ディレクトリ作成失敗 {dir_path}: {e}")
        
        all_success = success_count == len(directories)
        if all_success:
            self.logger.success(f"全ディレクトリ作成完了: {success_count}個")
        else:
            self.logger.warning(f"ディレクトリ作成: {success_count}/{len(directories)}個成功")
        
        return all_success
    
    def sync_directory(self, src_dir: Union[str, Path], dst_dir: Union[str, Path], 
                      pattern: str = "*", overwrite: bool = True) -> int:
        """
        ディレクトリ同期（shared_dataset_manager統合版）
        
        Args:
            src_dir: ソースディレクトリ
            dst_dir: 宛先ディレクトリ
            pattern: ファイルパターン
            overwrite: 上書きフラグ
            
        Returns:
            同期されたファイル数
        """
        src_path = Path(src_dir)
        dst_path = Path(dst_dir)
        
        if not src_path.exists():
            self.logger.error(f"ソースディレクトリが存在しません: {src_path}")
            return 0
        
        # 宛先ディレクトリ作成
        dst_path.mkdir(parents=True, exist_ok=True)
        
        synced_count = 0
        self.logger.info(f"ディレクトリ同期開始: {src_path} → {dst_path}")
        
        for file_path in src_path.glob(pattern):
            if file_path.is_file():
                dst_file = dst_path / file_path.name
                
                try:
                    # 上書き判定
                    should_copy = overwrite or not dst_file.exists()
                    
                    if not should_copy and dst_file.exists():
                        # 更新時刻比較
                        should_copy = file_path.stat().st_mtime > dst_file.stat().st_mtime
                    
                    if should_copy:
                        shutil.copy2(file_path, dst_file)
                        synced_count += 1
                        self.logger.debug(f"ファイル同期: {file_path.name}")
                        
                except Exception as e:
                    self.logger.error(f"ファイル同期エラー {file_path}: {e}")
        
        self.logger.success(f"ディレクトリ同期完了: {synced_count}ファイル")
        return synced_count
    
    def save_json(self, data: Any, file_path: Union[str, Path], 
                  indent: int = 2, ensure_ascii: bool = False) -> bool:
        """
        JSON保存（統合版）
        
        Args:
            data: 保存するデータ
            file_path: ファイルパス
            indent: インデント
            ensure_ascii: ASCII強制フラグ
            
        Returns:
            保存成功フラグ
        """
        file_path = Path(file_path)
        
        try:
            # ディレクトリ作成
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent, default=str)
            
            self.logger.debug(f"JSON保存成功: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"JSON保存失敗 {file_path}: {e}")
            return False
    
    def load_json(self, file_path: Union[str, Path], default: Any = None) -> Any:
        """
        JSON読み込み（統合版）
        
        Args:
            file_path: ファイルパス
            default: デフォルト値
            
        Returns:
            読み込まれたデータ
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            self.logger.warning(f"JSONファイルが存在しません: {file_path}")
            return default
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.debug(f"JSON読み込み成功: {file_path}")
            return data
            
        except Exception as e:
            self.logger.error(f"JSON読み込み失敗 {file_path}: {e}")
            return default
    
    def save_text_file(self, text: str, file_path: Union[str, Path], 
                      encoding: str = 'utf-8') -> bool:
        """
        テキストファイル保存
        
        Args:
            text: テキスト内容
            file_path: ファイルパス
            encoding: エンコーディング
            
        Returns:
            保存成功フラグ
        """
        file_path = Path(file_path)
        
        try:
            # ディレクトリ作成
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(text)
            
            self.logger.debug(f"テキストファイル保存成功: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"テキストファイル保存失敗 {file_path}: {e}")
            return False
    
    def load_text_file(self, file_path: Union[str, Path], 
                      encoding: str = 'utf-8') -> Optional[str]:
        """
        テキストファイル読み込み
        
        Args:
            file_path: ファイルパス
            encoding: エンコーディング
            
        Returns:
            テキスト内容（None: 読み込み失敗）
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            self.logger.warning(f"テキストファイルが存在しません: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            self.logger.debug(f"テキストファイル読み込み成功: {file_path}")
            return content
            
        except Exception as e:
            self.logger.error(f"テキストファイル読み込み失敗 {file_path}: {e}")
            return None
    
    def get_file_hash(self, file_path: Union[str, Path], algorithm: str = 'md5') -> Optional[str]:
        """
        ファイルハッシュ計算
        
        Args:
            file_path: ファイルパス
            algorithm: ハッシュアルゴリズム（md5, sha1, sha256）
            
        Returns:
            ハッシュ値（None: 計算失敗）
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            self.logger.error(f"ファイルが存在しません: {file_path}")
            return None
        
        try:
            hash_func = getattr(hashlib, algorithm)()
            
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    hash_func.update(chunk)
            
            hash_value = hash_func.hexdigest()
            self.logger.debug(f"ハッシュ計算成功: {file_path} ({algorithm}: {hash_value[:8]}...)")
            return hash_value
            
        except Exception as e:
            self.logger.error(f"ハッシュ計算失敗 {file_path}: {e}")
            return None
    
    def find_duplicate_files(self, directory: Union[str, Path], 
                            pattern: str = "*") -> Dict[str, List[str]]:
        """
        重複ファイル検出
        
        Args:
            directory: 検索ディレクトリ
            pattern: ファイルパターン
            
        Returns:
            重複ファイル辞書（ハッシュ: ファイルパスリスト）
        """
        dir_path = Path(directory)
        file_hashes = {}
        duplicates = {}
        
        self.logger.info(f"重複ファイル検索開始: {dir_path}")
        
        for file_path in dir_path.rglob(pattern):
            if file_path.is_file():
                file_hash = self.get_file_hash(file_path)
                if file_hash:
                    if file_hash in file_hashes:
                        if file_hash not in duplicates:
                            duplicates[file_hash] = [file_hashes[file_hash], str(file_path)]
                        else:
                            duplicates[file_hash].append(str(file_path))
                    else:
                        file_hashes[file_hash] = str(file_path)
        
        if duplicates:
            self.logger.warning(f"重複ファイル検出: {len(duplicates)}組")
        else:
            self.logger.info("重複ファイルは見つかりませんでした")
        
        return duplicates
    
    def cleanup_empty_directories(self, directory: Union[str, Path]) -> int:
        """
        空ディレクトリ削除
        
        Args:
            directory: 対象ディレクトリ
            
        Returns:
            削除されたディレクトリ数
        """
        dir_path = Path(directory)
        removed_count = 0
        
        self.logger.info(f"空ディレクトリクリーンアップ開始: {dir_path}")
        
        # 末端から順に削除（再帰的に空になったディレクトリも削除）
        for dirpath, dirnames, filenames in os.walk(dir_path, topdown=False):
            current_dir = Path(dirpath)
            
            # ファイルがなく、サブディレクトリもない場合
            if not filenames and not dirnames:
                try:
                    current_dir.rmdir()
                    self.logger.debug(f"空ディレクトリ削除: {current_dir}")
                    removed_count += 1
                except Exception as e:
                    self.logger.warning(f"ディレクトリ削除失敗 {current_dir}: {e}")
        
        if removed_count > 0:
            self.logger.success(f"空ディレクトリクリーンアップ完了: {removed_count}個削除")
        else:
            self.logger.info("削除対象の空ディレクトリはありませんでした")
        
        return removed_count
    
    def create_metadata_file(self, audio_file: Union[str, Path], text: str, 
                           metadata_dir: Optional[Union[str, Path]] = None) -> bool:
        """
        メタデータファイル作成（Python_Audio_dataset統合版）
        
        Args:
            audio_file: 音声ファイルパス
            text: テキスト内容
            metadata_dir: メタデータディレクトリ（None: 自動判定）
            
        Returns:
            作成成功フラグ
        """
        audio_path = Path(audio_file)
        
        # メタデータディレクトリ決定
        if metadata_dir:
            meta_dir = Path(metadata_dir)
        else:
            meta_dir = audio_path.parent.parent / "meta_files"
        
        # メタファイルパス生成
        meta_filename = audio_path.stem.replace("audio_", "meta_") + ".txt"
        meta_path = meta_dir / meta_filename
        
        return self.save_text_file(text, meta_path)
    
    def update_dataset_metadata(self, dataset_dir: Union[str, Path], 
                               audio_filename: str, text: str) -> bool:
        """
        データセットメタデータ更新
        
        Args:
            dataset_dir: データセットディレクトリ
            audio_filename: 音声ファイル名
            text: テキスト内容
            
        Returns:
            更新成功フラグ
        """
        dataset_path = Path(dataset_dir)
        metadata_file = dataset_path / "metadata.txt"
        
        try:
            # 既存のメタデータ読み込み
            existing_lines = []
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    existing_lines = f.readlines()
            
            # 新しいエントリ作成
            new_entry = f"{audio_filename}|{text}\n"
            
            # 重複チェック
            audio_name = audio_filename.split('.')[0]
            existing_lines = [line for line in existing_lines if not line.startswith(audio_name)]
            
            # 新しいエントリ追加
            existing_lines.append(new_entry)
            
            # ファイル保存
            with open(metadata_file, 'w', encoding='utf-8') as f:
                f.writelines(existing_lines)
            
            self.logger.debug(f"データセットメタデータ更新: {audio_filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"データセットメタデータ更新失敗: {e}")
            return False
    
    def get_directory_info(self, directory: Union[str, Path]) -> Dict[str, Any]:
        """
        ディレクトリ情報取得
        
        Args:
            directory: 対象ディレクトリ
            
        Returns:
            ディレクトリ情報辞書
        """
        dir_path = Path(directory)
        
        if not dir_path.exists():
            return {"error": "Directory not found"}
        
        file_count = 0
        total_size = 0
        file_types = {}
        
        for file_path in dir_path.rglob('*'):
            if file_path.is_file():
                file_count += 1
                total_size += file_path.stat().st_size
                
                suffix = file_path.suffix.lower()
                file_types[suffix] = file_types.get(suffix, 0) + 1
        
        info = {
            'path': str(dir_path),
            'file_count': file_count,
            'total_size_mb': total_size / (1024 * 1024),
            'file_types': file_types,
            'last_modified': datetime.fromtimestamp(dir_path.stat().st_mtime).isoformat()
        }
        
        self.logger.debug(f"ディレクトリ情報取得: {file_count}ファイル, {info['total_size_mb']:.1f}MB")
        return info


# グローバルファイルユーティリティインスタンス
_file_utils_instance = None

def get_file_utils() -> FileUtils:
    """
    グローバルファイルユーティリティインスタンス取得
    
    Returns:
        FileUtilsインスタンス
    """
    global _file_utils_instance
    if _file_utils_instance is None:
        _file_utils_instance = FileUtils()
    return _file_utils_instance


# 便利関数
def setup_directories(directories: List[Union[str, Path]], 
                     base_path: Optional[Union[str, Path]] = None) -> bool:
    """ディレクトリ作成便利関数"""
    utils = get_file_utils()
    return utils.setup_directories(directories, base_path)

def sync_directory(src_dir: Union[str, Path], dst_dir: Union[str, Path], 
                  pattern: str = "*") -> int:
    """ディレクトリ同期便利関数"""
    utils = get_file_utils()
    return utils.sync_directory(src_dir, dst_dir, pattern)

def save_json(data: Any, file_path: Union[str, Path]) -> bool:
    """JSON保存便利関数"""
    utils = get_file_utils()
    return utils.save_json(data, file_path)

def load_json(file_path: Union[str, Path], default: Any = None) -> Any:
    """JSON読み込み便利関数"""
    utils = get_file_utils()
    return utils.load_json(file_path, default)