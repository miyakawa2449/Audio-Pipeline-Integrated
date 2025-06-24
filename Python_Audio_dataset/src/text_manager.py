import json
import sys
from pathlib import Path

# 統一ログシステム
sys.path.append(str(Path(__file__).parent.parent.parent / "common"))
try:
    from logger import get_logger
except ImportError:
    # フォールバック用のダミーロガー
    import logging
    def get_logger(name): return logging.getLogger(name)

class TextManager:
    def __init__(self, input_dir="data/input"):
        self.logger = get_logger("TextManager")
        self.input_dir = Path(input_dir)
        self.current_file = None
        self.current_index = 0  # current_line → current_index に変更
        self.all_texts = []
        self.session_file = Path("data/session.json")
        self.filename = None
        
        # 初期化時にテキストファイルを自動検索・読み込み
        self.auto_load_text_file()
        self.logger.info(f"TextManager初期化完了: {len(self.all_texts)}行")
        
    def auto_load_text_file(self):
        """テキストファイルの自動検索・読み込み"""
        # 優先順位でテキストファイルを検索（適切な日本語テキストファイルを優先）
        search_files = [
            "Japanese.txt",
            "cocoro.txt",
            "script.txt", 
            "text.txt",
            "input.txt",
            "dataset.txt"
        ]
        
        # カレントディレクトリから検索
        for filename in search_files:
            file_path = Path(filename)
            if file_path.exists():
                print(f"📄 テキストファイル発見: {filename}")
                self.load_file(filename)
                return True
        
        # data/input ディレクトリから検索
        if self.input_dir.exists():
            for filename in search_files:
                file_path = self.input_dir / filename
                if file_path.exists():
                    print(f"📄 テキストファイル発見: {file_path}")
                    self.load_file(str(file_path))
                    return True
        
        # .txtファイルを全検索（不適切なファイルを除外）
        excluded_patterns = [
            "requirements", "readme", "license", "changelog", 
            "version", "config", "setup", "install"
        ]
        
        for txt_file in Path(".").glob("*.txt"):
            if txt_file.is_file():
                # 不適切なファイルをスキップ
                if any(pattern in txt_file.name.lower() for pattern in excluded_patterns):
                    continue
                    
                print(f"📄 テキストファイル発見: {txt_file.name}")
                if self.validate_text_file(txt_file):
                    self.load_file(str(txt_file))
                    return True
        
        print("⚠️ テキストファイルが見つかりません")
        print("   以下のいずれかのファイルを作成してください:")
        for filename in search_files[:3]:
            print(f"   - {filename}")
        
        return False
    
    def validate_text_file(self, file_path):
        """テキストファイルが音声データセット用として適切かを検証"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 最低条件チェック
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            # 行数チェック
            if len(lines) < 3:
                print(f"   ⚠️ {file_path.name}: 行数が少なすぎます（{len(lines)}行）")
                return False
            
            # 日本語テキストかチェック
            japanese_chars = sum(1 for char in content if '\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' or '\u4E00' <= char <= '\u9FAF')
            if japanese_chars < len(content) * 0.1:  # 日本語文字が10%未満
                print(f"   ⚠️ {file_path.name}: 日本語テキストではないようです")
                return False
            
            print(f"   ✅ {file_path.name}: 音声データセット用テキストとして適切（{len(lines)}行）")
            return True
            
        except Exception as e:
            print(f"   ❌ {file_path.name}: ファイル検証エラー - {e}")
            return False
    
    def load_file(self, filename):
        """テキストファイルを読み込み"""
        try:
            file_path = Path(filename)
            if not file_path.exists():
                print(f"❌ ファイルが存在しません: {filename}")
                return False
            
            self.filename = file_path.name
            self.current_file = str(file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # テキストデータを構造化
            self.all_texts = []
            for i, line in enumerate(lines, 1):
                text = line.strip()
                if text:  # 空行をスキップ
                    self.all_texts.append({
                        'line_number': i,
                        'text': text,
                        'recorded': False,
                        'audio_filename': None
                    })
            
            print(f"✅ {len(self.all_texts)}行のテキストを読み込みました")
            
            # セッション情報があれば復元
            self.load_session()
            
            return True
            
        except Exception as e:
            print(f"❌ ファイル読み込みエラー: {e}")
            return False
    
    def load_all_texts(self):
        """全てのテキストファイルを読み込み（互換性用）"""
        return self.auto_load_text_file()
    
    def save_session(self):
        """セッション保存"""
        try:
            session_data = {
                'filename': self.filename,
                'current_file': self.current_file,
                'current_index': self.current_index,
                'total_texts': len(self.all_texts),
                'recorded_status': {
                    str(i): text.get('recorded', False) 
                    for i, text in enumerate(self.all_texts)
                }
            }
            
            # セッションディレクトリ作成
            self.session_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
                
            print("💾 セッション保存完了")
            return True
            
        except Exception as e:
            print(f"❌ セッション保存エラー: {e}")
            return False
    
    def load_session(self):
        """セッション読み込み"""
        try:
            if not self.session_file.exists():
                return False
            
            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # セッション情報を復元
            if session_data.get('filename') == self.filename:
                self.current_index = session_data.get('current_index', 0)
                
                # 録音状態を復元
                recorded_status = session_data.get('recorded_status', {})
                for i, status in recorded_status.items():
                    index = int(i)
                    if index < len(self.all_texts):
                        self.all_texts[index]['recorded'] = status
                
                print("📂 セッション復元完了")
                return True
            
        except Exception as e:
            print(f"⚠️ セッション読み込みエラー: {e}")
        
        return False
    
    def get_current_text(self):
        """現在のテキストを取得"""
        if not self.all_texts:
            return None
        
        if 0 <= self.current_index < len(self.all_texts):
            return self.all_texts[self.current_index]
        
        return None
    
    def next_line(self):
        """次の行に移動"""
        if self.current_index < len(self.all_texts) - 1:
            self.current_index += 1
            self.save_session()
            return True
        return False
    
    def previous_line(self):
        """前の行に移動"""
        if self.current_index > 0:
            self.current_index -= 1
            self.save_session()
            return True
        return False
    
    def jump_to_line(self, line_number):
        """指定行にジャンプ"""
        # line_number は1ベース、current_index は0ベース
        index = line_number - 1
        if 0 <= index < len(self.all_texts):
            self.current_index = index
            self.save_session()
            return True
        return False
    
    def mark_as_recorded(self, audio_filename, line_number):
        """録音済みとしてマーク"""
        try:
            # line_number は1ベース
            index = line_number - 1
            if 0 <= index < len(self.all_texts):
                self.all_texts[index]['recorded'] = True
                self.all_texts[index]['audio_filename'] = audio_filename
                self.save_session()
                return True
        except Exception as e:
            print(f"❌ 録音マークエラー: {e}")
        return False
    
    def get_progress(self):
        """進捗を取得"""
        if not self.all_texts:
            return {'recorded': 0, 'total': 0, 'progress_percent': 0}
        
        total = len(self.all_texts)
        recorded = sum(1 for text in self.all_texts if text.get('recorded', False))
        progress_percent = (recorded / total * 100) if total > 0 else 0
        
        return {
            'recorded': recorded,
            'total': total,
            'progress_percent': progress_percent
        }
    
    def reload_file(self):
        """ファイル再読み込み"""
        if self.current_file:
            current_index_backup = self.current_index
            success = self.load_file(self.current_file)
            if success:
                # 位置を復元（範囲チェック）
                if current_index_backup < len(self.all_texts):
                    self.current_index = current_index_backup
                else:
                    self.current_index = 0
            return success
        else:
            return self.auto_load_text_file()
    
    def sync_session_file(self):
        """セッション同期（互換性用）"""
        return self.save_session()
    
    def sync_with_actual_files(self):
        """実ファイルとの同期"""
        # dataset/audio_files/ から録音済みファイルをチェック
        audio_dir = Path("dataset/audio_files")
        if not audio_dir.exists():
            return
        
        for audio_file in audio_dir.glob("*.wav"):
            # ファイル名から行番号を抽出 (audio_0001.wav -> 1)
            try:
                filename = audio_file.stem  # audio_0001
                if filename.startswith("audio_"):
                    line_num_str = filename.split("_")[1]
                    line_number = int(line_num_str)
                    self.mark_as_recorded(audio_file.name, line_number)
            except (ValueError, IndexError):
                continue
        
        print("🔄 実ファイルとの同期完了")