import os
import sys
from pathlib import Path

def test_direct_execution():
    """Python_Audio_dataset を直接実行してテスト"""
    
    # 1. 単体での実行テスト
    print("🧪 Python_Audio_dataset 単体実行テスト")
    print("="*50)
    
    python_audio_dir = Path("Python_Audio_dataset")
    original_cwd = os.getcwd()
    
    try:
        # 作業ディレクトリを変更
        os.chdir(python_audio_dir)
        print(f"📁 作業ディレクトリ: {os.getcwd()}")
        
        # パス確認
        sys.path.insert(0, 'src')
        print(f"🛤️ Python パス: {sys.path[:3]}")
        
        # インポートテスト
        try:
            from audio_recorder import AudioRecorder
            print("✅ AudioRecorder インポート成功")
            
            # インスタンス作成テスト
            recorder = AudioRecorder()
            print("✅ AudioRecorder インスタンス作成成功")
            
            # メソッド存在確認
            methods = ['start_recording', 'get_recorded_audio', 'save_audio']
            for method in methods:
                if hasattr(recorder, method):
                    print(f"✅ {method} メソッド存在")
                else:
                    print(f"❌ {method} メソッド不足")
                    
        except ImportError as e:
            print(f"❌ インポートエラー: {e}")
            
        # main.py実行テスト
        try:
            print("\n🚀 main.py 実行テスト...")
            import main
            if hasattr(main, 'AudioDatasetCreator'):
                creator = main.AudioDatasetCreator()
                print("✅ AudioDatasetCreator 作成成功")
            else:
                print("❌ AudioDatasetCreator クラスが見つかりません")
                
        except Exception as e:
            print(f"❌ main.py エラー: {e}")
            
    finally:
        os.chdir(original_cwd)
        
    # 2. 統合環境での実行テスト
    print("\n🔗 統合環境実行テスト")
    print("="*50)
    
    try:
        # 統合環境でのパス設定
        sys.path.insert(0, str(python_audio_dir / "src"))
        
        from audio_recorder import AudioRecorder
        print("✅ 統合環境でのインポート成功")
        
    except Exception as e:
        print(f"❌ 統合環境エラー: {e}")

if __name__ == "__main__":
    test_direct_execution()