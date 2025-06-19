#!/bin/bash
# MacBook Pro M4 Pro 環境移行スクリプト
# Audio Pipeline Integrated セットアップ自動化

set -e  # エラー時に停止

echo "🍎 MacBook Pro M4 Pro 環境移行スクリプト"
echo "🚀 Audio Pipeline Integrated 自動セットアップ"
echo "=================================================="

# 色付きメッセージ関数
print_success() { echo -e "✅ \033[32m$1\033[0m"; }
print_warning() { echo -e "⚠️  \033[33m$1\033[0m"; }
print_error() { echo -e "❌ \033[31m$1\033[0m"; }
print_info() { echo -e "🔍 \033[34m$1\033[0m"; }

# macOS環境確認
check_macos() {
    print_info "macOS環境を確認中..."
    
    if [[ "$(uname)" != "Darwin" ]]; then
        print_error "このスクリプトはmacOS専用です"
        exit 1
    fi
    
    macos_version=$(sw_vers -productVersion)
    print_success "macOS $macos_version を検出"
    
    # Apple Silicon確認
    cpu_brand=$(sysctl -n machdep.cpu.brand_string)
    if [[ $cpu_brand == *"Apple"* ]]; then
        print_success "Apple Silicon CPU検出: $cpu_brand"
        export APPLE_SILICON=true
    else
        print_info "Intel Mac検出: $cpu_brand"
        export APPLE_SILICON=false
    fi
}

# Homebrewインストール
install_homebrew() {
    print_info "Homebrewの確認・インストール..."
    
    if command -v brew >/dev/null 2>&1; then
        print_success "Homebrew: インストール済み"
        brew update
    else
        print_info "Homebrewをインストール中..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Apple Siliconの場合のPATH設定
        if [[ $APPLE_SILICON == true ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
        
        print_success "Homebrew インストール完了"
    fi
}

# 必要なシステムパッケージインストール
install_system_packages() {
    print_info "システムパッケージをインストール中..."
    
    # 音声処理に必要なライブラリ
    packages=(
        "portaudio"
        "ffmpeg"
        "git"
        "wget"
    )
    
    for package in "${packages[@]}"; do
        print_info "インストール中: $package"
        brew install "$package" || print_warning "$package のインストールに失敗"
    done
    
    print_success "システムパッケージインストール完了"
}

# Miniconda インストール
install_miniconda() {
    print_info "Miniconda の確認・インストール..."
    
    if command -v conda >/dev/null 2>&1; then
        print_success "Conda: インストール済み"
        return
    fi
    
    # Apple Silicon用のMiniconda URL
    if [[ $APPLE_SILICON == true ]]; then
        MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh"
    else
        MINICONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
    fi
    
    print_info "Minicondaをダウンロード中..."
    wget -O miniconda.sh "$MINICONDA_URL"
    
    print_info "Minicondaをインストール中..."
    bash miniconda.sh -b -p "$HOME/miniconda3"
    rm miniconda.sh
    
    # PATH設定
    echo 'export PATH="$HOME/miniconda3/bin:$PATH"' >> ~/.zprofile
    export PATH="$HOME/miniconda3/bin:$PATH"
    
    # conda初期化
    conda init zsh
    
    print_success "Miniconda インストール完了"
}

# Python環境作成
create_python_environment() {
    print_info "Python環境を作成中..."
    
    # conda環境作成
    conda create -n audio-pipeline python=3.10 -y
    
    print_success "Python環境 'audio-pipeline' 作成完了"
    print_warning "次のコマンドで環境をアクティベート: conda activate audio-pipeline"
}

# PyTorchインストール（Apple Silicon最適化）
install_pytorch() {
    print_info "PyTorch（Apple Silicon最適化版）をインストール中..."
    
    # conda環境をアクティベート
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate audio-pipeline
    
    if [[ $APPLE_SILICON == true ]]; then
        # Apple Silicon用PyTorch（MPS対応）
        conda install pytorch torchaudio -c pytorch -y
        print_success "PyTorch (Apple Silicon MPS対応版) インストール完了"
    else
        # Intel Mac用PyTorch
        conda install pytorch torchaudio cpuonly -c pytorch -y
        print_success "PyTorch (Intel Mac CPU版) インストール完了"
    fi
}

# 音声処理ライブラリインストール
install_audio_libraries() {
    print_info "音声処理ライブラリをインストール中..."
    
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate audio-pipeline
    
    # conda経由でインストール
    conda install numpy matplotlib scipy soundfile librosa -c conda-forge -y
    
    # pip経由でインストール
    pip install sounddevice
    
    # macOS特化ライブラリ
    pip install pyaudio
    
    print_success "音声処理ライブラリインストール完了"
}

# プロジェクトファイルセットアップ
setup_project() {
    print_info "プロジェクトセットアップ中..."
    
    # 現在の場所がプロジェクトルートか確認
    if [[ ! -f "integrated_main.py" ]]; then
        print_error "プロジェクトルートディレクトリで実行してください"
        exit 1
    fi
    
    # 必要なディレクトリ作成
    mkdir -p config
    mkdir -p logs
    mkdir -p Python_Audio_dataset/dataset/{audio_files,meta_files,processed,backup}
    mkdir -p AudioOpt/dataset/{audio_files,meta_files,processed,models,output}
    mkdir -p shared_dataset/{audio_files,meta_files,processed,phoneme_data,backup}
    
    print_success "プロジェクトディレクトリ構造作成完了"
}

# macOS音声権限設定ガイド
setup_audio_permissions() {
    print_info "音声権限設定ガイド"
    print_warning "以下の手順で音声アクセス権限を設定してください:"
    echo ""
    echo "1. システム環境設定を開く"
    echo "2. セキュリティとプライバシー → プライバシー"
    echo "3. 左側の「マイク」を選択"
    echo "4. ターミナル または 使用するアプリケーションにチェック"
    echo ""
    print_warning "権限設定後、音声テストを実行します"
    
    read -p "権限設定が完了したらEnterを押してください..."
}

# 音声テスト実行
test_audio_setup() {
    print_info "音声セットアップテスト実行中..."
    
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate audio-pipeline
    
    # macOS音声セットアップスクリプト実行
    if [[ -f "macos_audio_setup.py" ]]; then
        python macos_audio_setup.py
    else
        print_warning "macos_audio_setup.py が見つかりません"
    fi
}

# Apple Silicon最適化テスト
test_apple_silicon_optimization() {
    if [[ $APPLE_SILICON != true ]]; then
        return
    fi
    
    print_info "Apple Silicon最適化テスト実行中..."
    
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate audio-pipeline
    
    if [[ -f "apple_silicon_optimizations.py" ]]; then
        python apple_silicon_optimizations.py
    else
        print_warning "apple_silicon_optimizations.py が見つかりません"
    fi
}

# 統合システムテスト
test_integrated_system() {
    print_info "統合システムテスト実行中..."
    
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate audio-pipeline
    
    # ファイル命名テスト
    if [[ -f "test_final_naming.py" ]]; then
        python test_final_naming.py
    fi
    
    print_success "統合システムテスト完了"
}

# セットアップ完了メッセージ
show_completion_message() {
    echo ""
    echo "🎉 MacBook Pro M4 Pro セットアップ完了！"
    echo "=================================================="
    print_success "環境移行が正常に完了しました"
    echo ""
    echo "📋 次のステップ:"
    echo "1. conda activate audio-pipeline"
    echo "2. python integrated_main.py"
    echo ""
    echo "🎵 Audio Pipeline Integrated の使用準備完了"
    
    if [[ $APPLE_SILICON == true ]]; then
        echo ""
        print_success "🍎 Apple Silicon M4 Pro 最適化有効"
        echo "   • MPS GPU加速"
        echo "   • 48GB大容量メモリ活用"
        echo "   • macOS Core Audio統合"
    fi
    
    echo ""
    echo "📁 重要なファイル:"
    echo "   • macos_migration_guide.md - 詳細ガイド"
    echo "   • macos_audio_setup.py - 音声設定"
    echo "   • apple_silicon_optimizations.py - 最適化"
    echo ""
    print_warning "問題が発生した場合は上記ファイルを参照してください"
}

# メイン実行
main() {
    check_macos
    install_homebrew
    install_system_packages
    install_miniconda
    create_python_environment
    install_pytorch
    install_audio_libraries
    setup_project
    setup_audio_permissions
    test_audio_setup
    test_apple_silicon_optimization
    test_integrated_system
    show_completion_message
}

# スクリプト実行
print_info "MacBook Pro M4 Pro 環境移行を開始します"
read -p "続行しますか？ (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    main
else
    print_info "セットアップをキャンセルしました"
    exit 0
fi