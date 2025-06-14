import sys
from pathlib import Path

def analyze_main_py():
    """main.pyの構造を分析"""
    main_py_path = Path("Python_Audio_dataset/src/main.py")
    
    if not main_py_path.exists():
        print(f"❌ {main_py_path} が見つかりません")
        return
    
    print(f"📄 {main_py_path} の分析:")
    print("="*50)
    
    with open(main_py_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # クラスとメソッドを抽出
    classes = []
    methods = []
    functions = []
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        if line.startswith('class '):
            class_name = line.split('class ')[1].split('(')[0].split(':')[0]
            classes.append(f"Line {i}: {class_name}")
        elif line.startswith('def '):
            func_name = line.split('def ')[1].split('(')[0]
            if line.startswith('    def '):  # メソッド
                methods.append(f"Line {i}: {func_name}")
            else:  # 関数
                functions.append(f"Line {i}: {func_name}")
    
    print("🏛️ クラス:")
    for cls in classes:
        print(f"  {cls}")
    
    print("\n🔧 メソッド:")
    for method in methods:
        print(f"  {method}")
    
    print("\n⚙️ 関数:")
    for func in functions:
        print(f"  {func}")
    
    # 録音関連のキーワードを検索
    print("\n🎙️ 録音関連のコード:")
    recording_keywords = ['record', 'audio', 'mic', 'sound']
    for i, line in enumerate(lines, 1):
        for keyword in recording_keywords:
            if keyword.lower() in line.lower() and not line.strip().startswith('#'):
                print(f"  Line {i}: {line.strip()}")

if __name__ == "__main__":
    analyze_main_py()