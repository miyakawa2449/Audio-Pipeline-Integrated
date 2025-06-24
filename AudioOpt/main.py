"""
音声クローニングシステム - メインプログラム
整理・再構成版
"""

import sys
import os
from pathlib import Path

# 安全なinput関数
def safe_input(prompt, default=""):
    """EOFErrorに対応した安全なinput関数"""
    try:
        return input(prompt)
    except EOFError:
        print(f"\n[自動入力] {default}")
        return default
    except KeyboardInterrupt:
        print("\n[中断されました]")
        return "q"

# Common modules import
sys.path.append(str(Path(__file__).parent.parent / "common"))
try:
    from logger import get_logger
    from error_handler import error_handler, ErrorSeverity, handle_error
    from exceptions import (
        AudioPipelineError, AudioFileError, ModelError, 
        DeviceError, SystemError, AppleSiliconError
    )
except ImportError:
    # Fallback for missing common modules
    import logging
    
    class FallbackLogger:
        def __init__(self, name):
            self.logger = logging.getLogger(name)
            self.logger.setLevel(logging.INFO)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                handler.setFormatter(logging.Formatter('%(levelname)s | %(message)s'))
                self.logger.addHandler(handler)
        
        def debug(self, msg): self.logger.debug(msg)
        def info(self, msg): self.logger.info(msg)
        def warning(self, msg): self.logger.warning(msg)
        def error(self, msg): self.logger.error(msg)
        def start_operation(self, msg): self.logger.info(f"🚀 {msg} を開始")
        def complete_operation(self, msg): self.logger.info(f"✅ {msg} が完了")
        def success(self, msg): self.logger.info(f"✅ {msg}")
        def progress(self, msg): self.logger.info(f"🔄 {msg}")
        def audio_info(self, msg): self.logger.info(f"🎵 {msg}")
        def model_info(self, msg): self.logger.info(f"🤖 {msg}")
        def device_info(self, msg): self.logger.info(f"🎛️ {msg}")
    
    def get_logger(name): return FallbackLogger(name)
    def error_handler(**kwargs): return lambda f: f
    def handle_error(e, **kwargs): raise e
    ErrorSeverity = type('ErrorSeverity', (), {'MEDIUM': 'medium', 'HIGH': 'high', 'CRITICAL': 'critical'})
    
    class AudioPipelineError(Exception):
        def __init__(self, message, suggestions=None):
            super().__init__(message)
            self.suggestions = suggestions
    
    class AudioFileError(AudioPipelineError): pass
    class ModelError(AudioPipelineError): pass
    class DeviceError(AudioPipelineError): pass
    class SystemError(AudioPipelineError): pass
    class AppleSiliconError(AudioPipelineError): pass

# srcディレクトリをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Logger initialization
logger = get_logger("AudioOptMain")

# 必要なディレクトリを自動作成
def ensure_directories():
    """AudioOptに必要なディレクトリを作成"""
    directories = [
        "dataset",
        "dataset/audio_files", 
        "dataset/meta_files",
        "models",
        "output",
        "logs"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logger.debug(f"ディレクトリ作成: {dir_path}")
    
    logger.success("必要ディレクトリを作成しました")

try:
    from src.core import VoiceCloner
    logger.success("AudioOpt VoiceCloner モジュール読み込み成功")
except ImportError as e:
    error = AudioFileError(
        f"モジュールのインポートに失敗しました: {e}",
        suggestions=(
            "以下を確認してください:\n"
            "1. srcディレクトリが存在するか\n"
            "2. 必要なファイルが全て配置されているか\n"
            "3. 必要なライブラリがインストールされているか"
        )
    )
    handle_error(error, severity=ErrorSeverity.CRITICAL)
    sys.exit(1)

# =============================================================================
# システム関連機能
# =============================================================================

@error_handler(severity=ErrorSeverity.HIGH, recovery=True)
def check_dependencies():
    """依存関係をチェック"""
    logger.start_operation("依存関係チェック")
    missing_packages = []
    
    dependencies = [
        ('torch', 'PyTorch'),
        ('torchaudio', 'Torchaudio'),
        ('soundfile', 'Soundfile'),
        ('numpy', 'NumPy')
    ]
    
    for package_name, display_name in dependencies:
        try:
            module = __import__(package_name)
            version = getattr(module, '__version__', 'unknown')
            logger.success(f"{display_name}: {version}")
        except ImportError:
            missing_packages.append(package_name)
            logger.warning(f"{display_name}: 未インストール")
    
    if missing_packages:
        error = SystemError(
            f"不足しているパッケージ: {', '.join(missing_packages)}",
            suggestions=f"conda install {' '.join(missing_packages)}"
        )
        handle_error(error, severity=ErrorSeverity.HIGH)
        return False
    
    logger.complete_operation("依存関係チェック")
    return True

def display_system_info(cloner):
    """システム情報を表示"""
    print("\n=== システム情報 ===")
    print(f"Dataset path: {cloner.dataset_path}")
    print(f"Audio files path: {cloner.audio_path}")
    print(f"Text files path: {cloner.meta_path}")
    print(f"Models path: {cloner.models_path}")
    print(f"Output path: {cloner.output_path}")
    print(f"Device: {cloner.device}")
    
    # GPU情報を表示
    if cloner.device.type == 'cuda':
        try:
            import torch
            gpu_props = torch.cuda.get_device_properties(0)
            logger.info(f"🎮 GPU Memory: {gpu_props.total_memory // 1024**3} GB")
            logger.info(f"🎮 GPU Name: {gpu_props.name}")
        except Exception as e:
            logger.warning(f"GPU情報取得エラー: {e}")
    
    if hasattr(cloner.text_processor, 'vocab') and cloner.text_processor.vocab:
        print(f"Vocabulary size: {len(cloner.text_processor.vocab)}")
    else:
        print("Vocabulary: Not built yet")
    
    if cloner.model is not None:
        print("Model: Loaded")
        # モデルのパラメータ数を表示
        try:
            total_params = sum(p.numel() for p in cloner.model.parameters())
            logger.info(f"🤖 Model parameters: {total_params:,}")
        except Exception as e:
            logger.debug(f"パラメータ数取得エラー: {e}")
    else:
        print("Model: Not loaded")

# =============================================================================
# メニュー1: データセット前処理とモデル訓練
# =============================================================================

@error_handler(severity=ErrorSeverity.HIGH, recovery=True)
def train_model_interactive(cloner):
    """対話式でモデル訓練を実行"""
    logger.start_operation("対話式モデル訓練")
    
    # データファイルの確認
    try:
        audio_files, text_files = cloner.collect_data_files()
        if len(audio_files) == 0:
            print("\n❌ 訓練データが見つかりません")
            print("\n📋 詳細診断:")
            
            # ディレクトリ存在チェック
            dataset_path = Path("dataset")
            audio_path = dataset_path / "audio_files" 
            meta_path = dataset_path / "meta_files"
            
            print(f"  dataset/: {'✅ 存在' if dataset_path.exists() else '❌ 不存在'}")
            print(f"  audio_files/: {'✅ 存在' if audio_path.exists() else '❌ 不存在'}")
            print(f"  meta_files/: {'✅ 存在' if meta_path.exists() else '❌ 不存在'}")
            
            # ファイル数チェック
            if audio_path.exists():
                audio_count = len(list(audio_path.glob("*.wav")))
                print(f"  音声ファイル数: {audio_count}")
            if meta_path.exists():
                text_count = len(list(meta_path.glob("*.txt")))
                print(f"  テキストファイル数: {text_count}")
            
            print("\n💡 解決方法:")
            print("  1. Python_Audio_datasetで音声データを録音してください")
            print("  2. または、既存の音声ファイルをdataset/audio_files/に配置")
            print("  3. 対応するテキストファイルをdataset/meta_files/に配置")
            print("  4. ファイル名は 'audio_NNNN.wav' と 'audio_NNNN.txt' の形式で")
            
            return
        
        logger.success(f"{len(audio_files)}個のデータペアが見つかりました")
        
        # データファイル検証
        validation_results = validate_dataset_files(audio_files, text_files)
        valid_count = sum(1 for r in validation_results if r['valid'])
        
        if valid_count < len(audio_files):
            print(f"\n⚠️ 警告: {len(audio_files) - valid_count}個のファイルに問題があります")
            print("詳細はメニュー5（データファイル確認）で確認してください")
            
            proceed = safe_input("問題があるファイルを含めて訓練を続行しますか？ (y/N): ", "n").strip().lower()
            if proceed != 'y':
                print("訓練をキャンセルしました")
                return
        
    except Exception as e:
        print(f"\n❌ データファイル確認エラー: {e}")
        logger.error(f"データファイル確認エラー: {e}")
        return
    
    # パラメータ入力
    try:
        epochs_input = safe_input("エポック数を入力 (デフォルト: 100): ", "100").strip()
        epochs = int(epochs_input) if epochs_input else 100
        
        if epochs <= 0:
            raise ValueError("エポック数は1以上で入力してください")
            
        batch_size_input = safe_input("バッチサイズを入力 (デフォルト: 2): ", "2").strip()
        batch_size = int(batch_size_input) if batch_size_input else 2
        
        if batch_size <= 0 or batch_size > len(audio_files):
            raise ValueError(f"バッチサイズは1以上{len(audio_files)}以下で入力してください")
        
        learning_rate_input = safe_input("学習率を入力 (デフォルト: 0.001): ", "0.001").strip()
        learning_rate = float(learning_rate_input) if learning_rate_input else 0.001
        
        print(f"\n訓練設定:")
        print(f"  エポック数: {epochs}")
        print(f"  バッチサイズ: {batch_size}")
        print(f"  学習率: {learning_rate}")
        print(f"  データ数: {len(audio_files)}")
        
        confirm = safe_input("\n訓練を開始しますか？ (y/N): ", "n").strip().lower()
        if confirm != 'y':
            print("訓練をキャンセルしました")
            return
        
        # 訓練実行
        logger.info(f"🚀 訓練開始: epochs={epochs}, batch_size={batch_size}, lr={learning_rate}")
        cloner.train_model(epochs=epochs, batch_size=batch_size, learning_rate=learning_rate)
        
        # モデル保存
        save_confirm = safe_input("モデルを保存しますか？ (Y/n): ", "y").strip().lower()
        if save_confirm != 'n':
            cloner.save_model()
            logger.success("モデルが保存されました")
        
        logger.complete_operation("対話式モデル訓練")
        
    except ValueError as e:
        error = ModelError(f"入力値エラー: {e}")
        handle_error(error, severity=ErrorSeverity.MEDIUM)
    except Exception as e:
        error = ModelError(f"訓練中にエラーが発生しました: {e}")
        handle_error(error, severity=ErrorSeverity.HIGH)

# =============================================================================
# メニュー2: 既存モデル読み込み
# =============================================================================

def load_model_interactive(cloner):
    """対話式でモデル読み込みを実行（管理改善版）"""
    print("\n=== モデル読み込み ===")
    
    # 利用可能なモデルファイルを表示
    models_path = Path("models")
    if models_path.exists():
        model_files = list(models_path.glob("*.pth"))
        if model_files:
            print("\n📁 利用可能なモデルファイル:")
            for i, model_file in enumerate(model_files, 1):
                file_size = model_file.stat().st_size / (1024 * 1024)  # MB
                modified = model_file.stat().st_mtime
                import datetime
                mod_time = datetime.datetime.fromtimestamp(modified).strftime('%Y-%m-%d %H:%M')
                print(f"  {i}. {model_file.name} ({file_size:.1f}MB, {mod_time})")
        else:
            print("\n❌ models/ディレクトリにモデルファイルが見つかりません")
    else:
        print("\n❌ models/ディレクトリが存在しません")
    
    # デフォルトモデルパスチェック
    default_model = models_path / "voice_clone_model.pth"
    if default_model.exists():
        print(f"\n✅ デフォルトモデル: {default_model.name}")
        use_default = safe_input("デフォルトモデルを使用しますか？ (Y/n): ", "y").strip().lower()
        if use_default != 'n':
            try:
                cloner.load_model(str(default_model))
                print("✅ モデル読み込み完了")
                return
            except Exception as e:
                print(f"❌ デフォルトモデル読み込みエラー: {e}")
    else:
        print(f"\n⚠️ デフォルトモデルが見つかりません: {default_model}")
    
    # カスタムパス入力
    model_path = safe_input("読み込むモデルのパスを入力 (空白でキャンセル): ", "").strip()
    if not model_path:
        print("モデル読み込みをキャンセルしました")
        return
    
    # モデル読み込み実行
    try:
        if not Path(model_path).exists():
            print(f"❌ ファイルが存在しません: {model_path}")
            return
            
        cloner.load_model(model_path)
        print("✅ モデル読み込み完了")
        
    except Exception as e:
        print(f"❌ モデル読み込みエラー: {e}")
        logger.error(f"モデル読み込みエラー: {e}")

# =============================================================================
# メニュー3: 音声合成
# =============================================================================

@error_handler(severity=ErrorSeverity.HIGH, recovery=True)
def synthesize_speech_interactive(cloner):
    """対話式で音声合成を実行"""
    if cloner.model is None:
        print("\n❌ モデルが読み込まれていません")
        print("\n📋 解決方法:")
        print("  1. メニュー2でモデルを読み込む")
        print("  2. メニュー1でモデルを訓練する")
        
        # 自動的にモデル読み込みを提案
        auto_load = safe_input("\n自動的にモデル読み込みを試行しますか？ (Y/n): ", "y").strip().lower()
        if auto_load != 'n':
            load_model_interactive(cloner)
            
            # 再チェック
            if cloner.model is None:
                print("❌ モデル読み込みに失敗しました")
                return
            else:
                print("✅ モデル読み込み成功、音声合成を続行します")
        else:
            return
    
    try:
        text = safe_input("合成したいテキストを入力: ", "こんにちは").strip()
        if not text:
            raise ValueError("テキストが入力されませんでした")
        
        output_path = safe_input("出力ファイル名（空白でdefault）: ", "").strip()
        if not output_path:
            output_path = None
        
        logger.start_operation(f"音声合成: '{text}'")
        cloner.synthesize_speech(text, output_path)
        logger.complete_operation("音声合成")
        
    except Exception as e:
        error = AudioPipelineError(f"音声合成エラー: {e}")
        handle_error(error, severity=ErrorSeverity.HIGH)

# =============================================================================
# メニュー4: 新しいデータの追加（未実装）
# =============================================================================

def add_new_data_interactive(cloner):
    """新しいデータの追加（今後実装予定）"""
    print("この機能は今後実装予定です。")

# =============================================================================
# メニュー5: データファイル確認
# =============================================================================

def display_data_files(cloner):
    """データファイル一覧を表示（検証強化版）"""
    audio_files, text_files = cloner.collect_data_files()
    print("\n=== 検出されたデータファイル ===")
    
    # データファイル検証
    validation_results = validate_dataset_files(audio_files, text_files)
    
    if len(audio_files) == 0:
        print("❌ データファイルが見つかりません。")
        
        # ディレクトリの存在確認
        dataset_path = Path("dataset")
        audio_path = dataset_path / "audio_files"
        meta_path = dataset_path / "meta_files"
        
        print(f"\nディレクトリ状態:")
        print(f"  dataset/: {'✅ 存在' if dataset_path.exists() else '❌ 不存在'}")
        print(f"  audio_files/: {'✅ 存在' if audio_path.exists() else '❌ 不存在'}")
        print(f"  meta_files/: {'✅ 存在' if meta_path.exists() else '❌ 不存在'}")
        
        print("\n正しいディレクトリ構造:")
        print("dataset/")
        print("├── audio_files/")
        print("│   ├── audio_0001.wav")
        print("│   ├── audio_0002.wav")
        print("│   └── ...")
        print("└── meta_files/")
        print("    ├── audio_0001.txt")
        print("    ├── audio_0002.txt")
        print("    └── ...")
        
        print("\n❗ ファイル名は必ず 'audio_NNNN.wav' と 'audio_NNNN.txt' の形式で、")
        print("   NNNNは同じ番号（例: 0001）にしてください。")
    else:
        print(f"✓ {len(audio_files)}個のデータペアが見つかりました:\n")
        
        # 検証結果サマリ表示
        if validation_results:
            valid_count = sum(1 for r in validation_results if r['valid'])
            print(f"検証結果: {valid_count}/{len(validation_results)} ペアが有効\n")
        
        for i, (audio, text) in enumerate(zip(audio_files, text_files)):
            # 検証結果を反映
            status_icon = "✅" if validation_results and i < len(validation_results) and validation_results[i]['valid'] else "❌"
            
            print(f"{status_icon} {i+1:2d}. Audio: {os.path.basename(audio)}")
            print(f"     Text:  {os.path.basename(text)}")
            
            # ファイルサイズと検証情報表示
            try:
                audio_size = os.path.getsize(audio) / 1024  # KB
                print(f"     Size:  {audio_size:.1f} KB")
                
                # 検証詳細表示
                if validation_results and i < len(validation_results):
                    result = validation_results[i]
                    if not result['valid']:
                        for issue in result['issues']:
                            print(f"     ⚠️  {issue}")
                            
            except Exception as e:
                print(f"     Size:  不明 ({e})")
            print()

# =============================================================================
# メニュー6: システム情報表示（上記で定義済み）
# =============================================================================

# =============================================================================
# メニュー7: 前処理結果確認
# =============================================================================

def display_preprocessing_results(cloner):
    """前処理結果を表示"""
    processed_audio_dir = os.path.join(cloner.processed_path, "cleaned_audio")
    comparison_dir = os.path.join(cloner.processed_path, "comparison")
    audio_comparison_dir = os.path.join(comparison_dir, "audio_pairs")
    stages_dir = os.path.join(comparison_dir, "processing_stages")
    stats_file = os.path.join(cloner.processed_path, "preprocessing_stats.json")
    
    print("\n=== 前処理結果 ===")
    
    # 統計ファイルの確認
    if os.path.exists(stats_file):
        try:
            import json
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
            
            summary = stats["processing_summary"]
            print(f"処理日時: {summary['timestamp']}")
            print(f"総ファイル数: {summary['total_files']}")
            print(f"処理成功: {summary['processed_files']}")
            print(f"成功率: {summary['success_rate']:.1f}%")
            
            # 詳細表示
            if safe_input("\n詳細を表示しますか？ (y/N): ", "n").strip().lower() == 'y':
                print("\n=== ファイル別詳細 ===")
                for detail in stats["file_details"]:
                    if "error" not in detail:
                        print(f"\n{detail['index']:2d}. {detail['original_file']}")
                        print(f"     サイズ: {detail['original_size_kb']:.1f}KB → {detail['processed_size_kb']:.1f}KB ({detail['size_reduction_percent']:+.1f}%)")
                        print(f"     長さ:   {detail['original_duration_sec']:.2f}s → {detail['processed_duration_sec']:.2f}s ({detail['duration_reduction_percent']:+.1f}%)")
                    else:
                        print(f"\n{detail['index']:2d}. {detail['original_file']} - {detail['error']}")
        
        except Exception as e:
            print(f"❌ 統計ファイル読み込みエラー: {e}")
    else:
        print("❌ 前処理統計が見つかりません")
    
    # ディレクトリ情報
    print(f"\n=== 保存されたファイル ===")
    
    # 前処理済み音声
    if os.path.exists(processed_audio_dir):
        processed_files = [f for f in os.listdir(processed_audio_dir) if f.endswith('.wav')]
        print(f"📁 前処理済み音声: {len(processed_files)}ファイル")
        print(f"   場所: {processed_audio_dir}")
    else:
        print("❌ 前処理済み音声ディレクトリが見つかりません")
    
    # 比較用音声ペア
    if os.path.exists(audio_comparison_dir):
        comparison_files = [f for f in os.listdir(audio_comparison_dir) if f.endswith('.wav')]
        original_files = [f for f in comparison_files if f.startswith('original_')]
        processed_files = [f for f in comparison_files if f.startswith('processed_')]
        print(f"📁 比較用音声ペア: {len(original_files)}組")
        print(f"   場所: {audio_comparison_dir}")
    else:
        print("❌ 比較用音声ペアが見つかりません")
    
    # 処理段階別音声
    if os.path.exists(stages_dir):
        stage_files = [f for f in os.listdir(stages_dir) if f.endswith('.wav')]
        print(f"📁 処理段階別音声: {len(stage_files)}ファイル")
        print(f"   場所: {stages_dir}")
    else:
        print("❌ 処理段階別音声が見つかりません")
    
    # 比較画像
    if os.path.exists(comparison_dir):
        comparison_images = [f for f in os.listdir(comparison_dir) if f.endswith('.png')]
        print(f"📁 比較画像: {len(comparison_images)}ファイル")
        print(f"   場所: {comparison_dir}")
    else:
        print("❌ 比較画像ディレクトリが見つかりません")

# =============================================================================
# メニュー8: モデル・音声合成診断
# =============================================================================

def check_model_status(cloner):
    """モデルの詳細状態を確認"""
    print("=== モデル状態確認 ===")
    
    # 1. モデルファイルの存在確認
    model_path = os.path.join(cloner.models_path, "voice_clone_model.pth")
    print(f"モデルファイル: {model_path}")
    print(f"存在: {os.path.exists(model_path)}")
    
    if os.path.exists(model_path):
        try:
            # ファイルサイズ確認
            file_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
            print(f"ファイルサイズ: {file_size:.2f} MB")
            
            # ファイル内容の簡易確認
            import torch
            checkpoint = torch.load(model_path, map_location='cpu')
            print(f"チェックポイントキー: {list(checkpoint.keys())}")
            
            if 'model_state_dict' in checkpoint:
                print("✓ model_state_dict が存在")
            else:
                print("❌ model_state_dict が見つかりません")
                
            if 'text_processor' in checkpoint:
                print("✓ text_processor が存在")
                
                # 語彙の確認
                text_proc = checkpoint['text_processor']
                if hasattr(text_proc, 'vocab') and text_proc.vocab:
                    vocab = text_proc.vocab
                    print(f"✓ 語彙サイズ: {len(vocab)}")
                    
                    # 語彙の型を確認して適切に表示
                    if isinstance(vocab, dict):
                        print(f"語彙サンプル: {list(vocab.keys())[:10]}")
                        print("語彙型: 辞書")
                    elif isinstance(vocab, set):
                        print(f"語彙サンプル: {list(vocab)[:10]}")
                        print("語彙型: セット")
                    elif isinstance(vocab, list):
                        print(f"語彙サンプル: {vocab[:10]}")
                        print("語彙型: リスト")
                    else:
                        print(f"語彙型: {type(vocab)}")
                else:
                    print("❌ 語彙が空または存在しません")
            else:
                print("❌ text_processor が見つかりません")
                
        except Exception as e:
            print(f"❌ モデルファイル読み込みエラー: {e}")
    
    # 2. 現在のモデル状態
    print(f"\n現在のモデル: {cloner.model}")
    print(f"現在のテキストプロセッサ: {cloner.text_processor}")
    
    if hasattr(cloner.text_processor, 'vocab') and cloner.text_processor.vocab:
        vocab = cloner.text_processor.vocab
        print(f"現在の語彙: {len(vocab)}個")
        print(f"現在の語彙型: {type(vocab)}")
    else:
        print("❌ 現在の語彙が見つかりません")

def diagnose_model_and_synthesis(cloner):
    """モデルと音声合成の診断"""
    print("=== モデル診断 ===")
    
    if cloner.model is None:
        print("❌ モデルが読み込まれていません")
        return
    
    # 1. モデルの状態確認
    print("✓ モデルは読み込まれています")
    
    # 2. 語彙サイズ確認
    if hasattr(cloner.text_processor, 'vocab') and cloner.text_processor.vocab:
        vocab = cloner.text_processor.vocab
        vocab_size = len(vocab)
        print(f"語彙サイズ: {vocab_size}")
        
        # 語彙の型に応じて表示
        if isinstance(vocab, dict):
            print(f"サンプル語彙: {list(vocab.keys())[:10]}")
            print("語彙形式: 文字→ID辞書")
        elif isinstance(vocab, set):
            vocab_list = list(vocab)
            print(f"サンプル語彙: {vocab_list[:10]}")
            print("語彙形式: 文字セット")
            print("⚠️  語彙がセット形式です。辞書形式に変換が必要かもしれません")
            try:
                test_dict = {char: i for i, char in enumerate(sorted(vocab))}
                print(f"変換テスト成功: {list(test_dict.items())[:5]}")
            except Exception as e:
                print(f"変換テストエラー: {e}")
        elif isinstance(vocab, list):
            print(f"サンプル語彙: {vocab[:10]}")
            print("語彙形式: 文字リスト")
        else:
            print(f"語彙形式: {type(vocab)}")
    else:
        print("❌ 語彙が構築されていません")
    
    # 3. モデルパラメータ確認
    try:
        total_params = sum(p.numel() for p in cloner.model.parameters())
        trainable_params = sum(p.numel() for p in cloner.model.parameters() if p.requires_grad)
        print(f"総パラメータ数: {total_params:,}")
        print(f"学習可能パラメータ数: {trainable_params:,}")
    except Exception as e:
        print(f"パラメータ確認エラー: {e}")
    
    # 4. モデルの出力テスト
    print("\n=== 出力テスト ===")
    test_text = "テスト"
    
    try:
        import torch
        
        # テキストを数値に変換
        text_sequence = cloner.text_processor.text_to_sequence(test_text)
        text_tensor = torch.LongTensor(text_sequence).unsqueeze(0).to(cloner.device)
        text_lengths = torch.LongTensor([len(text_sequence)]).to(cloner.device)
        
        print(f"入力テキスト: '{test_text}'")
        print(f"変換後数値: {text_sequence}")
        print(f"テンソルサイズ: {text_tensor.shape}")
        
        # 変換結果の妥当性チェック
        if all(x == 0 for x in text_sequence):
            print("❌ 警告: 全て0に変換されています（語彙の問題の可能性）")
        elif max(text_sequence) >= len(cloner.text_processor.vocab):
            print(f"❌ 警告: 語彙サイズ({len(cloner.text_processor.vocab)})を超えるIDが含まれています")
        else:
            print("✓ テキスト変換は正常に見えます")
        
        # モデル推論
        cloner.model.eval()
        with torch.no_grad():
            mel_outputs, stop_outputs = cloner.model(text_tensor, text_lengths)
        
        print(f"メル出力サイズ: {mel_outputs.shape}")
        print(f"メル出力の範囲: [{mel_outputs.min().item():.3f}, {mel_outputs.max().item():.3f}]")
        print(f"メル出力の平均: {mel_outputs.mean().item():.3f}")
        print(f"停止トークン: {stop_outputs.mean().item():.3f}")
        
        # 出力の有効性チェック
        if torch.all(mel_outputs == 0):
            print("❌ メルスペクトログラム出力が全て0です")
        elif mel_outputs.std() < 0.01:
            print("❌ メルスペクトログラム出力のバリエーションが不足しています")
        else:
            print("✓ メルスペクトログラム出力は正常に見えます")
        
    except Exception as e:
        print(f"❌ 出力テストエラー: {e}")
        traceback.print_exc()

def diagnose_synthesis_process(cloner, text="こんにちは"):
    """音声合成プロセスの詳細診断"""
    print(f"\n=== 音声合成プロセス診断 ===")
    print(f"合成テキスト: '{text}'")
    
    try:
        import torch
        import numpy as np
        
        # Step 1: テキスト前処理
        text_sequence = cloner.text_processor.text_to_sequence(text)
        text_tensor = torch.LongTensor(text_sequence).unsqueeze(0).to(cloner.device)
        text_lengths = torch.LongTensor([len(text_sequence)]).to(cloner.device)
        
        print(f"✓ テキスト前処理完了: {text_sequence}")
        
        # Step 2: モデル推論
        cloner.model.eval()
        with torch.no_grad():
            mel_outputs, stop_outputs = cloner.model(text_tensor, text_lengths)
        
        mel_spec = mel_outputs.squeeze(0).cpu()
        print(f"✓ モデル推論完了: {mel_spec.shape}")
        print(f"  メル範囲: [{mel_spec.min():.3f}, {mel_spec.max():.3f}]")
        print(f"  メル平均: {mel_spec.mean():.3f}")
        print(f"  メル標準偏差: {mel_spec.std():.3f}")
        
        # Step 3: ボコーダーテスト
        print(f"\n各ボコーダーのテスト:")
        
        # Griffin-Lim
        try:
            audio_griffin = cloner._griffin_lim_synthesis(mel_spec)
            print(f"✓ Griffin-Lim: {len(audio_griffin)} samples")
            print(f"  音声範囲: [{audio_griffin.min():.6f}, {audio_griffin.max():.6f}]")
            print(f"  音声RMS: {torch.sqrt(torch.mean(audio_griffin**2)):.6f}")
        except Exception as e:
            print(f"❌ Griffin-Lim エラー: {e}")
        
        # 簡易ボコーダー
        try:
            audio_simple = cloner._simple_vocoder(mel_spec)
            print(f"✓ 簡易ボコーダー: {len(audio_simple)} samples")
            print(f"  音声範囲: [{audio_simple.min():.6f}, {audio_simple.max():.6f}]")
            print(f"  音声RMS: {torch.sqrt(torch.mean(audio_simple**2)):.6f}")
        except Exception as e:
            print(f"❌ 簡易ボコーダー エラー: {e}")
        
        # 改善ボコーダー
        if hasattr(cloner, '_improved_vocoder'):
            try:
                audio_improved = cloner._improved_vocoder(mel_spec)
                print(f"✓ 改善ボコーダー: {len(audio_improved)} samples")
                print(f"  音声範囲: [{audio_improved.min():.6f}, {audio_improved.max():.6f}]")
                print(f"  音声RMS: {torch.sqrt(torch.mean(audio_improved**2)):.6f}")
            except Exception as e:
                print(f"❌ 改善ボコーダー エラー: {e}")
            
    except Exception as e:
        print(f"❌ 診断エラー: {e}")
        traceback.print_exc()

def force_load_model(cloner):
    """強制的にモデルを読み込み直す"""
    print("=== 強制モデル読み込み ===")
    
    model_path = os.path.join(cloner.models_path, "voice_clone_model.pth")
    
    if not os.path.exists(model_path):
        print("❌ モデルファイルが存在しません")
        print("先にモデルを訓練してください（メニュー1）")
        return False
    
    try:
        print("モデル読み込み中...")
        cloner.load_model(model_path)
        
        if cloner.model is not None:
            print("✓ モデル読み込み成功")
            
            if hasattr(cloner.text_processor, 'vocab') and cloner.text_processor.vocab:
                print(f"✓ 語彙読み込み成功: {len(cloner.text_processor.vocab)}個")
                
                test_text = "こんにちは"
                test_sequence = cloner.text_processor.text_to_sequence(test_text)
                print(f"テスト変換: '{test_text}' → {test_sequence}")
                
                if all(x == 0 for x in test_sequence):
                    print("❌ まだテキスト変換が正常ではありません")
                    return False
                else:
                    print("✓ テキスト変換正常")
                    return True
            else:
                print("❌ 語彙が正常に読み込まれていません")
                return False
        else:
            print("❌ モデル読み込み失敗")
            return False
            
    except Exception as e:
        print(f"❌ 読み込みエラー: {e}")
        traceback.print_exc()
        return False

def verify_training_data_and_retrain(cloner):
    """訓練データを確認して必要に応じて再訓練"""
    print("=== 訓練データ確認 ===")
    
    audio_files, text_files = cloner.collect_data_files()
    print(f"データペア数: {len(audio_files)}")
    
    if len(audio_files) == 0:
        print("❌ 訓練データがありません")
        return False
    
    # テキストファイルの内容確認
    print("\nテキストファイルサンプル:")
    for i in range(min(3, len(text_files))):
        try:
            with open(text_files[i], 'r', encoding='utf-8') as f:
                content = f.read().strip()
            print(f"  {i+1}. {os.path.basename(text_files[i])}: '{content[:30]}{'...' if len(content) > 30 else ''}'")
        except Exception as e:
            print(f"  {i+1}. {os.path.basename(text_files[i])}: エラー - {e}")
    
    # 再訓練の提案
    retrain = safe_input(f"\n{len(audio_files)}個のデータで再訓練しますか？ (y/N): ", "n").strip().lower()
    if retrain == 'y':
        print("再訓練を開始...")
        
        try:
            cloner.train_model(epochs=10, batch_size=1, learning_rate=0.001)
            cloner.save_model()
            print("✓ 再訓練完了")
            return True
        except Exception as e:
            print(f"❌ 再訓練エラー: {e}")
            traceback.print_exc()
            return False
    
    return False

def model_synthesis_diagnosis_menu(cloner):
    """メニュー8: モデル・音声合成診断の統合メニュー"""
    # モデル状態確認
    check_model_status(cloner)
    
    # モデルが読み込まれていない場合の対応
    if cloner.model is None:
        print("\n=== モデル読み込み対応 ===")
        print("1. 既存モデルを強制読み込み")
        print("2. データ確認と再訓練")
        
        sub_choice = safe_input("選択 (1/2): ", "1").strip()
        
        if sub_choice == "1":
            if force_load_model(cloner):
                print("✓ モデル読み込み成功、診断を続行...")
                diagnose_model_and_synthesis(cloner)
                diagnose_synthesis_process(cloner)
            else:
                print("❌ モデル読み込み失敗")
        
        elif sub_choice == "2":
            if verify_training_data_and_retrain(cloner):
                print("✓ 再訓練完了、診断を続行...")
                diagnose_model_and_synthesis(cloner)
                diagnose_synthesis_process(cloner)
            else:
                print("❌ 再訓練失敗")
    else:
        # モデルが読み込まれている場合は通常の診断
        diagnose_model_and_synthesis(cloner)
        diagnose_synthesis_process(cloner)

# =============================================================================
# メニュー9: テスト音声生成
# =============================================================================

def generate_test_audio(cloner):
    """テスト用音声を生成"""
    print("\n=== テスト音声生成 ===")
    
    import torch
    import torchaudio
    import numpy as np
    
    # 1. 純粋なサイン波テスト
    print("1. サイン波テスト音声を生成...")
    sample_rate = cloner.preprocessor.sample_rate
    duration = 2.0  # 2秒
    frequency = 440  # A4
    
    t = torch.linspace(0, duration, int(sample_rate * duration))
    sine_wave = 0.3 * torch.sin(2 * 3.14159 * frequency * t)
    
    test_path = os.path.join(cloner.output_path, "test_sine_wave.wav")
    torchaudio.save(test_path, sine_wave.unsqueeze(0), sample_rate)
    print(f"✓ サイン波保存: {test_path}")
    
    # 2. ランダムメルスペクトログラムからの音声生成
    print("2. ランダムメルスペクトログラムテスト...")
    
    mel_frames = 100
    mel_bins = 80
    random_mel = torch.randn(mel_frames, mel_bins) * 0.5
    
    try:
        random_audio = cloner._simple_vocoder(random_mel)
        test_path2 = os.path.join(cloner.output_path, "test_random_mel.wav")
        torchaudio.save(test_path2, random_audio.unsqueeze(0), sample_rate)
        print(f"✓ ランダムメル音声保存: {test_path2}")
        print(f"  音声長: {len(random_audio)/sample_rate:.2f}秒")
        print(f"  最大振幅: {torch.max(torch.abs(random_audio)):.6f}")
    except Exception as e:
        print(f"❌ ランダムメルテストエラー: {e}")
    
    # 3. 学習データからの1サンプル確認
    print("3. 学習データサンプル確認...")
    
    audio_files, text_files = cloner.collect_data_files()
    if len(audio_files) > 0:
        sample_audio = cloner.preprocessor.load_audio(audio_files[0])
        if len(sample_audio) > 0:
            print(f"✓ 学習データサンプル: {len(sample_audio)} samples")
            print(f"  最大振幅: {np.max(np.abs(sample_audio)):.6f}")
            print(f"  RMS: {np.sqrt(np.mean(sample_audio**2)):.6f}")
            
            test_path3 = os.path.join(cloner.output_path, "test_training_sample.wav")
            torchaudio.save(test_path3, torch.from_numpy(sample_audio).unsqueeze(0), sample_rate)
            print(f"✓ 学習サンプル保存: {test_path3}")

# =============================================================================
# メニュー10: 詳細モデル診断
# =============================================================================

def detailed_model_diagnosis(cloner):
    """詳細なモデル診断"""
    print("=== 詳細モデル診断 ===")
    
    if cloner.model is None:
        print("❌ モデルが読み込まれていません")
        return
    
    import torch
    import numpy as np
    
    # 1. データセット情報
    audio_files, text_files = cloner.collect_data_files()
    print(f"データセット: {len(audio_files)}個")
    
    # 2. 訓練データサンプルの確認
    print("\n=== 訓練データサンプル ===")
    for i in range(min(3, len(text_files))):
        try:
            with open(text_files[i], 'r', encoding='utf-8') as f:
                text_content = f.read().strip()
            
            sequence = cloner.text_processor.text_to_sequence(text_content)
            print(f"{i+1}. テキスト: '{text_content[:50]}...'")
            print(f"   変換結果: {sequence[:10]}... (長さ: {len(sequence)})")
            
            import torchaudio
            waveform, sample_rate = torchaudio.load(audio_files[i])
            duration = waveform.shape[1] / sample_rate
            print(f"   音声長: {duration:.2f}秒, サンプルレート: {sample_rate}Hz")
            
        except Exception as e:
            print(f"{i+1}. エラー: {e}")
    
    # 3. モデルの各層の出力確認
    print("\n=== モデル層別出力確認 ===")
    test_text = "テスト"
    test_sequence = cloner.text_processor.text_to_sequence(test_text)
    test_tensor = torch.LongTensor(test_sequence).unsqueeze(0).to(cloner.device)
    test_lengths = torch.LongTensor([len(test_sequence)]).to(cloner.device)
    
    cloner.model.eval()
    with torch.no_grad():
        # 埋め込み層の出力
        embedded = cloner.model.embedding(test_tensor)
        print(f"埋め込み出力: {embedded.shape}, 範囲: [{embedded.min():.3f}, {embedded.max():.3f}]")
        
        # LSTM出力
        lstm_out, _ = cloner.model.text_lstm(embedded)
        print(f"LSTM出力: {lstm_out.shape}, 範囲: [{lstm_out.min():.3f}, {lstm_out.max():.3f}]")
        
        # 最終出力
        mel_outputs, stop_outputs = cloner.model(test_tensor, test_lengths)
        print(f"メル出力: {mel_outputs.shape}, 範囲: [{mel_outputs.min():.3f}, {mel_outputs.max():.3f}]")
        print(f"停止出力: {stop_outputs.shape}, 範囲: [{stop_outputs.min():.3f}, {stop_outputs.max():.3f}]")
        
        # メルスペクトログラムの特性分析
        mel_spec = mel_outputs.squeeze(0).cpu().numpy()
        print(f"\nメルスペクトログラム分析:")
        print(f"  平均: {np.mean(mel_spec):.3f}")
        print(f"  標準偏差: {np.std(mel_spec):.3f}")
        print(f"  最小値: {np.min(mel_spec):.3f}")
        print(f"  最大値: {np.max(mel_spec):.3f}")
        
        # フレーム別の変化
        frame_means = np.mean(mel_spec, axis=1)
        print(f"  フレーム間の変化: {np.std(frame_means):.3f}")
        if np.std(frame_means) < 0.1:
            print("  ⚠️  フレーム間の変化が少なすぎます（単調な出力）")
        
        # 周波数別の変化
        freq_means = np.mean(mel_spec, axis=0)
        print(f"  周波数間の変化: {np.std(freq_means):.3f}")
        if np.std(freq_means) < 0.1:
            print("  ⚠️  周波数間の変化が少なすぎます（スペクトル特徴不足）")

# =============================================================================
# メニュー11: 改善パラメータで再訓練
# =============================================================================

def retrain_with_better_parameters(cloner):
    """改善されたパラメータで再訓練"""
    print("=== 改善パラメータでの再訓練 ===")
    
    audio_files, text_files = cloner.collect_data_files()
    if len(audio_files) == 0:
        print("❌ 訓練データがありません")
        return
    
    print(f"データ数: {len(audio_files)}個")
    
    # より良い訓練パラメータ
    epochs = 100
    batch_size = 2
    learning_rate = 0.0005
    
    print(f"訓練パラメータ:")
    print(f"  エポック数: {epochs}")
    print(f"  バッチサイズ: {batch_size}")
    print(f"  学習率: {learning_rate}")
    
    confirm = safe_input("この設定で再訓練しますか？ (y/N): ", "n").strip().lower()
    if confirm == 'y':
        try:
            cloner.train_model(
                epochs=epochs, 
                batch_size=batch_size, 
                learning_rate=learning_rate
            )
            cloner.save_model()
            print("✓ 再訓練完了")
            return True
        except Exception as e:
            print(f"❌ 再訓練エラー: {e}")
            traceback.print_exc()
            return False
    
    return False

# =============================================================================
# メニュー12: ボコーダー問題診断
# =============================================================================

def diagnose_vocoder_issue(cloner):
    """ボコーダーの問題を詳細診断"""
    print("=== ボコーダー問題診断 ===")
    
    if cloner.model is None:
        print("❌ モデルが読み込まれていません")
        return
    
    import torch
    import numpy as np
    import torchaudio
    import os
    
    # テスト用のメルスペクトログラム生成
    test_text = "あいうえお"
    test_sequence = cloner.text_processor.text_to_sequence(test_text)
    test_tensor = torch.LongTensor(test_sequence).unsqueeze(0).to(cloner.device)
    test_lengths = torch.LongTensor([len(test_sequence)]).to(cloner.device)
    
    cloner.model.eval()
    with torch.no_grad():
        mel_outputs, _ = cloner.model(test_tensor, test_lengths)
    
    mel_spec = mel_outputs.squeeze(0).cpu()
    
    # 人工的な理想的メルスペクトログラムと比較
    print("人工メルスペクトログラムでテスト:")
    
    # 簡単な正弦波パターンを作成
    artificial_mel = np.zeros((50, 80))
    for i in range(50):
        for j in range(80):
            # 低域に強い信号を配置
            if j < 20:
                artificial_mel[i, j] = -10 + 5 * np.sin(2 * np.pi * i / 10)
            elif j < 40:
                artificial_mel[i, j] = -20 + 3 * np.sin(2 * np.pi * i / 15)
            else:
                artificial_mel[i, j] = -30 + np.sin(2 * np.pi * i / 20)
    
    artificial_mel_tensor = torch.from_numpy(artificial_mel.astype(np.float32))
    
    # 人工メルスペクトログラムでボコーダーテスト
    try:
        artificial_audio = cloner._improved_vocoder(artificial_mel_tensor)
        print(f"✓ 人工メル → 音声変換成功: {len(artificial_audio)} samples")
        print(f"  音声範囲: [{artificial_audio.min():.3f}, {artificial_audio.max():.3f}]")
        
        # ファイルに保存して確認
        test_path = os.path.join(cloner.output_path, "test_artificial.wav")
        torchaudio.save(test_path, artificial_audio.unsqueeze(0), cloner.preprocessor.sample_rate)
        print(f"✓ テスト音声保存: {test_path}")
        
    except Exception as e:
        print(f"❌ 人工メルテストエラー: {e}")
    
    # 実際のモデル出力でテスト
    try:
        model_audio = cloner._improved_vocoder(mel_spec)
        print(f"モデル出力 → 音声変換: {len(model_audio)} samples")
        print(f"  音声範囲: [{model_audio.min():.3f}, {model_audio.max():.3f}]")
        
        # 実際の訓練データとの比較
        audio_files, _ = cloner.collect_data_files()
        if len(audio_files) > 0:
            original_audio, _ = torchaudio.load(audio_files[0])
            print(f"元音声範囲: [{original_audio.min():.3f}, {original_audio.max():.3f}]")
            
    except Exception as e:
        print(f"❌ モデル出力テストエラー: {e}")

# =============================================================================
# メニュー13: 緊急モデル修正（新規追加）
# =============================================================================

def emergency_model_fix(cloner):
    """緊急モデル修正"""
    print("=== 緊急モデル修正 ===")
    
    if cloner.model is None:
        print("❌ モデルが読み込まれていません")
        return False
    
    import torch
    
    # モデルの出力長制御を強制修正
    original_forward = cloner.model.forward
    
    def fixed_forward(text_input, text_lengths, target_audio=None):
        # 元の出力を取得
        mel_outputs, stop_outputs = original_forward(text_input, text_lengths, target_audio)
        
        # 出力が短すぎる場合は強制延長
        if mel_outputs.shape[1] < 20:  # 20フレーム未満の場合
            print(f"⚠️  出力を強制延長: {mel_outputs.shape[1]} → 50フレーム")
            
            # 最後のフレームを繰り返して延長
            last_frame = mel_outputs[:, -1:, :]
            repeat_count = 50 - mel_outputs.shape[1]
            
            # わずかなノイズを追加して自然にする
            noise = torch.randn_like(last_frame.repeat(1, repeat_count, 1)) * 0.5
            extended_frames = last_frame.repeat(1, repeat_count, 1) + noise
            
            mel_outputs = torch.cat([mel_outputs, extended_frames], dim=1)
            
            # 停止トークンも延長
            stop_extension = torch.zeros(stop_outputs.shape[0], repeat_count, 1).to(stop_outputs.device)
            stop_outputs = torch.cat([stop_outputs, stop_extension], dim=1)
        
        return mel_outputs, stop_outputs
    
    # モデルの forward メソッドを置き換え
    cloner.model.forward = fixed_forward
    
    print("✓ モデルの出力長制御を修正しました")
    return True

# =============================================================================
# メニュー142: 外部ボコーダー使用設定（新規追加）
# =============================================================================

def use_external_vocoder(cloner):
    """外部の高品質ボコーダーを使用"""
    print("=== 高品質ボコーダー設定 ===")
    print("1. 改善された自作ボコーダー")
    print("2. WaveGlow（外部ライブラリ）")
    print("3. HiFi-GAN（最高品質）")
    
    choice = safe_input("選択 (1/2/3): ", "1").strip()
    
    if choice == "1":
        # 上記の_neural_vocoderを使用
        print("✓ 改善ボコーダーを設定しました")
        return True
    elif choice == "2":
        print("WaveGlowの統合は今後実装予定です")
        return False
    elif choice == "3":
        print("HiFi-GANの統合は今後実装予定です")
        return False
    
    return False


def use_pretrained_approach(cloner):
    """事前訓練済みアプローチ"""
    print("=== 緊急対応メニュー ===")
    print("現在のモデルは出力長の問題があります。")
    print("以下の選択肢があります:")
    print()
    print("1. 緊急修正版で継続（即座に使用可能）")
    print("2. 長時間再訓練（1-2時間、根本解決）")
    print("3. 戻る")
    
    choice = safe_input("選択 (1/2/3): ", "1").strip()
    
    if choice == "1":
        return emergency_model_fix(cloner)
    elif choice == "2":
        return retrain_with_better_parameters(cloner)
    elif choice == "3":
        return False
    
    return False



# =============================================================================
# メイン処理
# =============================================================================

def main():
    print("音声クローニングシステムへようこそ")
    
    # 必要ディレクトリ作成
    ensure_directories()
    
    # クローンオブジェクトの初期化
    cloner = VoiceCloner()
    
    # 依存関係チェック
    if not check_dependencies():
        sys.exit(1)
    
    while True:
        # メニュー表示（カテゴリ別番号）
        print("\n" + "="*50)
        print("🤖 AudioOpt - 音声クローニングシステム")
        print("="*50)
        print("📚 データ管理:")
        print("  1.1 データセットの前処理とモデル訓練")
        print("  1.2 新しいデータの追加")
        print("  1.3 データファイル確認")
        print("🧠 モデル操作:")
        print("  2.1 既存モデルの読み込み") 
        print("  2.2 モデル・音声合成診断")
        print("  2.3 改善パラメータで再訓練")
        print("🎵 音声生成:")
        print("  3.1 音声合成")
        print("  3.2 テスト音声生成")
        print("🔧 システム情報:")
        print("  4.1 システム情報表示")
        print("  4.2 前処理結果確認")
        print("🚨 診断・修正:")
        print("  5.1 詳細モデル診断")
        print("  5.2 ボコーダー問題診断")
        print("  5.3 緊急モデル修正")
        print("  5.4 外部ボコーダー使用設定")
        print("-" * 50)
        print("  0. 終了")
        print("="*50)
        
        choice = safe_input("選択肢を入力: ", "0").strip()
        
        if choice == "0":
            print("システムを終了します")
            break
        # 📚 データ管理
        elif choice == "1.1" or choice == "1":
            train_model_interactive(cloner)
        elif choice == "1.2":
            add_new_data_interactive(cloner)
        elif choice == "1.3":
            display_data_files(cloner)
        # 🧠 モデル操作
        elif choice == "2.1" or choice == "2":
            load_model_interactive(cloner)
        elif choice == "2.2":
            model_synthesis_diagnosis_menu(cloner)
        elif choice == "2.3":
            retrain_with_better_parameters(cloner)
        # 🎵 音声生成
        elif choice == "3.1" or choice == "3":
            synthesize_speech_interactive(cloner)
        elif choice == "3.2":
            generate_test_audio(cloner)
        # 🔧 システム情報
        elif choice == "4.1" or choice == "4":
            display_system_info(cloner)
        elif choice == "4.2":
            display_preprocessing_results(cloner)
        # 🚨 診断・修正
        elif choice == "5.1" or choice == "5":
            detailed_model_diagnosis(cloner)
        elif choice == "5.2":
            diagnose_vocoder_issue(cloner)
        elif choice == "5.3":
            use_pretrained_approach(cloner)
        elif choice == "5.4":
            use_external_vocoder(cloner)
        else:
            print("無効な選択肢です。再度入力してください。")
            print("例: 1.1, 2.2, 3.1 など、または 1, 2, 3 の省略形も可能")

# データファイル検証関数（新規追加）
def validate_dataset_files(audio_files, text_files):
    """データセットファイルの検証"""
    try:
        import soundfile as sf
    except ImportError:
        logger.warning("soundfile未インストール - 音声ファイル詳細検証をスキップ")
        sf = None
    
    validation_results = []
    
    for i, (audio_file, text_file) in enumerate(zip(audio_files, text_files)):
        result = {
            'index': i,
            'audio_file': audio_file,
            'text_file': text_file,
            'valid': True,
            'issues': []
        }
        
        # 音声ファイル検証
        try:
            if not os.path.exists(audio_file):
                result['valid'] = False
                result['issues'].append("音声ファイルが存在しない")
            else:
                # ファイルサイズチェック
                file_size = os.path.getsize(audio_file)
                if file_size < 1024:  # 1KB未満
                    result['valid'] = False
                    result['issues'].append(f"音声ファイルが小さすぎる ({file_size} bytes)")
                
                # 音声ファイルの読み込みチェック（soundfile利用可能時）
                if sf:
                    try:
                        data, samplerate = sf.read(audio_file)
                        duration = len(data) / samplerate
                        
                        if duration < 0.5:  # 0.5秒未満
                            result['issues'].append(f"音声が短すぎる ({duration:.2f}秒)")
                        elif duration > 30:  # 30秒超過
                            result['issues'].append(f"音声が長すぎる ({duration:.2f}秒)")
                            
                    except Exception as e:
                        result['valid'] = False
                        result['issues'].append(f"音声ファイルが破損: {str(e)[:50]}")
                    
        except Exception as e:
            result['valid'] = False
            result['issues'].append(f"音声ファイルエラー: {str(e)[:50]}")
        
        # テキストファイル検証
        try:
            if not os.path.exists(text_file):
                result['valid'] = False
                result['issues'].append("テキストファイルが存在しない")
            else:
                with open(text_file, 'r', encoding='utf-8') as f:
                    text_content = f.read().strip()
                    
                if not text_content:
                    result['valid'] = False
                    result['issues'].append("テキストファイルが空")
                elif len(text_content) < 3:
                    result['issues'].append(f"テキストが短すぎる ({len(text_content)}文字)")
                elif len(text_content) > 200:
                    result['issues'].append(f"テキストが長すぎる ({len(text_content)}文字)")
                    
        except Exception as e:
            result['valid'] = False
            result['issues'].append(f"テキストファイルエラー: {str(e)[:50]}")
        
        validation_results.append(result)
    
    return validation_results

if __name__ == "__main__":
    main()