import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from common.logger import get_logger
from common.error_handler import error_handler, ErrorSeverity, handle_error
from common.exceptions import (
    AudioPipelineError, AudioFileError, SystemError
)

class SharedDatasetManager:
    def __init__(self):
        self.logger = get_logger("SharedDatasetManager")
        self.root_dir = Path(__file__).parent
        self.shared_dataset_dir = self.root_dir / "shared_dataset"
        self.python_dataset_dir = self.root_dir / "Python_Audio_dataset" / "dataset"
        self.audioopt_dataset_dir = self.root_dir / "AudioOpt" / "dataset"
        
        # ログファイル
        self.log_file = self.shared_dataset_dir / "sync_log.txt"
    
    def setup_shared_directories(self):
        """共有ディレクトリ構造の作成"""
        directories = [
            self.shared_dataset_dir / "audio_files",
            self.shared_dataset_dir / "meta_files", 
            self.shared_dataset_dir / "processed",
            self.shared_dataset_dir / "phoneme_data",
            self.shared_dataset_dir / "backup",
            self.shared_dataset_dir / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        self._log("共有ディレクトリ構造を作成しました")
        self.logger.success("共有ディレクトリ構造を作成しました")
    
    @error_handler(severity=ErrorSeverity.MEDIUM, recovery=True)
    def sync_all_projects(self):
        """全プロジェクトのデータ同期"""
        self._log("=== 全プロジェクト同期開始 ===")
        
        try:
            # Python_Audio_dataset → shared_dataset
            self.sync_from_python_audio()
            
            # shared_dataset → AudioOpt
            self.sync_to_audioopt()
            
            # 統合メタデータ作成
            self.create_integration_metadata()
            
            self._log("全プロジェクト同期完了")
            self.logger.complete_operation("全プロジェクト同期")
            
        except Exception as e:
            error_msg = f"同期エラー: {e}"
            self._log(error_msg)
            raise AudioPipelineError(error_msg)
    
    def sync_from_python_audio(self):
        """Python_Audio_datasetからshared_datasetへ同期"""
        self._log("Python_Audio_dataset → shared_dataset 同期開始")
        
        if not self.python_dataset_dir.exists():
            self.logger.warning("Python_Audio_dataset/dataset が見つかりません")
            return
        
        # 音声ファイル同期
        audio_src = self.python_dataset_dir / "audio_files"
        audio_dst = self.shared_dataset_dir / "audio_files"
        
        if audio_src.exists():
            synced_count = self._sync_directory(audio_src, audio_dst, "*.wav")
            self.logger.audio_info(f"音声ファイル同期: {synced_count} 件")
            self._log(f"音声ファイル同期: {synced_count} 件")
        
        # メタファイル同期
        meta_src = self.python_dataset_dir / "meta_files"
        meta_dst = self.shared_dataset_dir / "meta_files"
        
        if meta_src.exists():
            synced_count = self._sync_directory(meta_src, meta_dst, "*.txt")
            self.logger.info(f"📝 メタファイル同期: {synced_count} 件")
            self._log(f"メタファイル同期: {synced_count} 件")
        
        # metadata.txt同期
        metadata_src = self.python_dataset_dir / "metadata.txt"
        metadata_dst = self.shared_dataset_dir / "metadata.txt"
        
        if metadata_src.exists():
            shutil.copy2(metadata_src, metadata_dst)
            self.logger.success("metadata.txt 同期完了")
            self._log("metadata.txt 同期完了")
    
    def sync_to_audioopt(self):
        """shared_datasetからAudioOptへ同期"""
        self._log("shared_dataset → AudioOpt 同期開始")
        
        # AudioOptのディレクトリ構造を作成
        audioopt_dirs = [
            self.audioopt_dataset_dir / "audio_files",
            self.audioopt_dataset_dir / "meta_files",
            self.audioopt_dataset_dir / "processed"
        ]
        
        for directory in audioopt_dirs:
            directory.mkdir(parents=True, exist_ok=True)
        
        # 音声ファイル同期
        audio_src = self.shared_dataset_dir / "audio_files"
        audio_dst = self.audioopt_dataset_dir / "audio_files"
        
        if audio_src.exists():
            synced_count = self._sync_directory(audio_src, audio_dst, "*.wav")
            self.logger.audio_info(f"AudioOpt音声同期: {synced_count} 件")
        
        # メタファイル同期
        meta_src = self.shared_dataset_dir / "meta_files"
        meta_dst = self.audioopt_dataset_dir / "meta_files"
        
        if meta_src.exists():
            synced_count = self._sync_directory(meta_src, meta_dst, "*.txt")
            self.logger.info(f"📝 AudioOptメタ同期: {synced_count} 件")
        
        # metadata.txt同期
        metadata_src = self.shared_dataset_dir / "metadata.txt"
        metadata_dst = self.audioopt_dataset_dir / "metadata.txt"
        
        if metadata_src.exists():
            shutil.copy2(metadata_src, metadata_dst)
            self.logger.success("AudioOpt metadata.txt 同期完了")
        
        self.logger.complete_operation("AudioOpt への同期")
        self._log("AudioOpt への同期完了")
    
    def _sync_directory(self, src_dir, dst_dir, pattern):
        """ディレクトリ同期（改良版）"""
        dst_dir.mkdir(parents=True, exist_ok=True)
        synced_count = 0
        
        for file_path in src_dir.glob(pattern):
            dst_file = dst_dir / file_path.name
            
            # ファイルが存在しないか、更新されている場合のみコピー
            if not dst_file.exists() or file_path.stat().st_mtime > dst_file.stat().st_mtime:
                try:
                    shutil.copy2(file_path, dst_file)
                    synced_count += 1
                except Exception as e:
                    error_msg = f"ファイル同期エラー {file_path}: {e}"
                    self._log(error_msg)
                    self.logger.warning(error_msg)
        
        return synced_count
    
    def create_integration_metadata(self):
        """統合メタデータの作成"""
        metadata_path = self.shared_dataset_dir / "integration_status.json"
        
        # 各プロジェクトのファイル数取得
        python_audio_count = len(list(self.python_dataset_dir.glob("audio_files/*.wav"))) if self.python_dataset_dir.exists() else 0
        audioopt_count = len(list(self.audioopt_dataset_dir.glob("audio_files/*.wav"))) if self.audioopt_dataset_dir.exists() else 0
        shared_count = len(list(self.shared_dataset_dir.glob("audio_files/*.wav")))
        
        status = {
            "last_sync": datetime.now().isoformat(),
            "file_counts": {
                "python_audio_dataset": python_audio_count,
                "audioopt": audioopt_count,
                "shared_dataset": shared_count
            },
            "directory_status": {
                "python_dataset_exists": self.python_dataset_dir.exists(),
                "audioopt_exists": self.audioopt_dataset_dir.exists(),
                "shared_dataset_exists": self.shared_dataset_dir.exists()
            },
            "sync_status": "completed" if python_audio_count == shared_count == audioopt_count else "partial"
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
        
        self._log(f"統合メタデータ更新: {status}")
    
    def show_integration_status(self):
        """統合ステータス表示"""
        print("\n" + "="*50)
        print("📊 統合ステータス")
        print("="*50)
        
        # 各プロジェクトのデータ数確認
        python_audio_count = len(list(self.python_dataset_dir.glob("audio_files/*.wav"))) if self.python_dataset_dir.exists() else 0
        audioopt_count = len(list(self.audioopt_dataset_dir.glob("audio_files/*.wav"))) if self.audioopt_dataset_dir.exists() else 0
        shared_count = len(list(self.shared_dataset_dir.glob("audio_files/*.wav")))
        
        print(f"🎙️ Python_Audio_dataset: {python_audio_count} 音声ファイル")
        print(f"🤖 AudioOpt: {audioopt_count} 音声ファイル")
        print(f"📁 Shared_dataset: {shared_count} 音声ファイル")
        
        # 同期状況確認
        if python_audio_count > 0 and python_audio_count == shared_count == audioopt_count:
            print("✅ 全プロジェクト同期済み")
        elif shared_count > 0:
            print("⚠️ 部分的に同期済み - 再同期を推奨")
        else:
            print("❌ 同期が必要です")
        
        # ディスク使用量
        total_size = sum(f.stat().st_size for f in self.shared_dataset_dir.rglob('*') if f.is_file())
        print(f"💾 共有データサイズ: {total_size / (1024*1024):.1f} MB")
        
        # 最新同期時刻
        metadata_path = self.shared_dataset_dir / "integration_status.json"
        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                status = json.load(f)
                last_sync = status.get('last_sync', 'Unknown')
                print(f"🕒 最終同期: {last_sync}")
        
        print("="*50)
    
    @error_handler(severity=ErrorSeverity.LOW, recovery=True)
    def cleanup_and_organize(self):
        """データ整理・最適化"""
        self.logger.start_operation("データ整理")
        
        # 重複ファイルチェック
        duplicates = self._find_duplicate_files()
        if duplicates:
            self.logger.warning(f"重複ファイル発見: {len(duplicates)} 件")
            for dup in duplicates[:5]:  # 最初の5件のみ表示
                self.logger.debug(f"   {dup}")
        
        # 空ディレクトリクリーンアップ
        empty_dirs = self._find_empty_directories()
        for empty_dir in empty_dirs:
            try:
                empty_dir.rmdir()
                self.logger.info(f"🗑️ 空ディレクトリ削除: {empty_dir}")
            except OSError:
                pass
        
        # ログファイルローテーション
        self._rotate_log_files()
        
        self.logger.complete_operation("データ整理")
    
    def _find_duplicate_files(self):
        """重複ファイル検出"""
        import hashlib
        
        file_hashes = {}
        duplicates = []
        
        for file_path in self.shared_dataset_dir.rglob('*'):
            if file_path.is_file():
                try:
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                    
                    if file_hash in file_hashes:
                        duplicates.append(f"{file_path} (duplicate of {file_hashes[file_hash]})")
                    else:
                        file_hashes[file_hash] = file_path
                except Exception:
                    continue
        
        return duplicates
    
    def _find_empty_directories(self):
        """空ディレクトリ検出"""
        empty_dirs = []
        for dir_path in self.shared_dataset_dir.rglob('*'):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                empty_dirs.append(dir_path)
        return empty_dirs
    
    def _rotate_log_files(self):
        """ログファイルローテーション"""
        if self.log_file.exists() and self.log_file.stat().st_size > 1024 * 1024:  # 1MB以上
            backup_log = self.log_file.with_suffix('.txt.bak')
            shutil.move(self.log_file, backup_log)
            self.logger.info("📋 ログファイルをローテーションしました")
    
    def _log(self, message):
        """ログ記録"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_message)
        except Exception as e:
            # ログ書き込みエラーは無視（非クリティカル）
            self.logger.debug(f"ログ書き込みエラー: {e}")
            pass