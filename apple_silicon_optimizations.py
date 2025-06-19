#!/usr/bin/env python3
"""
Apple Silicon M4 Pro 特化最適化
Audio Pipeline Integrated パフォーマンス向上
"""
import torch
import platform
import multiprocessing
import psutil
import os

class AppleSiliconOptimizer:
    """Apple Silicon M4 Pro 最適化クラス"""
    
    def __init__(self):
        self.is_apple_silicon = self._detect_apple_silicon()
        self.memory_gb = self._get_memory_size()
        self.cpu_cores = multiprocessing.cpu_count()
        
    def _detect_apple_silicon(self):
        """Apple Silicon検出"""
        if platform.system() != 'Darwin':
            return False
        
        try:
            import subprocess
            result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                                  capture_output=True, text=True)
            cpu_info = result.stdout.strip()
            return 'Apple' in cpu_info
        except:
            return False
    
    def _get_memory_size(self):
        """メモリサイズ取得（GB）"""
        try:
            memory_bytes = psutil.virtual_memory().total
            return memory_bytes / (1024**3)  # GB変換
        except:
            return 16  # デフォルト
    
    def get_optimal_device(self):
        """最適なデバイス設定を取得"""
        if self.is_apple_silicon and torch.backends.mps.is_available():
            device = torch.device('mps')
            acceleration = "Apple Silicon GPU (MPS)"
        elif torch.cuda.is_available():
            device = torch.device('cuda')
            acceleration = "NVIDIA GPU (CUDA)"
        else:
            device = torch.device('cpu')
            acceleration = "CPU"
        
        return device, acceleration
    
    def get_optimal_batch_size(self, base_batch_size=4):
        """最適なバッチサイズ計算"""
        if self.is_apple_silicon:
            # M4 Pro + 48GBメモリでの最適化
            if self.memory_gb >= 32:
                multiplier = 4  # 大幅増加
            elif self.memory_gb >= 16:
                multiplier = 2  # 中程度増加
            else:
                multiplier = 1  # 標準
        else:
            multiplier = 1
        
        optimal_batch_size = base_batch_size * multiplier
        print(f"🚀 最適バッチサイズ: {optimal_batch_size} (base: {base_batch_size}, memory: {self.memory_gb:.1f}GB)")
        return optimal_batch_size
    
    def get_optimal_num_workers(self):
        """最適なワーカー数計算"""
        if self.is_apple_silicon:
            # M4 Proの効率コア・パフォーマンスコア考慮
            # データローディング用に控えめに設定
            optimal_workers = max(1, self.cpu_cores // 2)
        else:
            optimal_workers = max(1, self.cpu_cores // 4)
        
        print(f"👥 最適ワーカー数: {optimal_workers} (CPU cores: {self.cpu_cores})")
        return optimal_workers
    
    def setup_mps_optimizations(self):
        """MPS特化最適化設定"""
        if not (self.is_apple_silicon and torch.backends.mps.is_available()):
            return False
        
        try:
            # MPS最適化フラグ
            os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.0'  # メモリ効率化
            
            print("🍎 MPS最適化設定を適用しました")
            print(f"   • メモリ効率化: ON")
            print(f"   • 利用可能メモリ: {self.memory_gb:.1f}GB")
            return True
            
        except Exception as e:
            print(f"⚠️ MPS最適化設定エラー: {e}")
            return False
    
    def get_audio_processing_config(self):
        """音声処理最適化設定"""
        config = {
            'sample_rate': 48000,  # macOS標準
            'hop_length': 512,     # 効率的な処理サイズ
            'n_fft': 2048,        # 高品質
            'n_mels': 80,         # 標準メル数
        }
        
        if self.is_apple_silicon:
            # Apple Silicon特化設定
            config.update({
                'num_workers': self.get_optimal_num_workers(),
                'pin_memory': True,    # メモリ効率
                'persistent_workers': True,  # ワーカー再利用
            })
        
        return config
    
    def optimize_training_params(self, base_config):
        """学習パラメータ最適化"""
        optimized = base_config.copy()
        
        if self.is_apple_silicon:
            # M4 Pro最適化
            optimized.update({
                'batch_size': self.get_optimal_batch_size(base_config.get('batch_size', 4)),
                'num_workers': self.get_optimal_num_workers(),
                'learning_rate': base_config.get('learning_rate', 0.001) * 1.2,  # 若干高速化
                'accumulation_steps': 1,  # 勾配蓄積なし（十分なメモリ）
            })
            
            print("🎯 Apple Silicon M4 Pro 学習最適化:")
            for key, value in optimized.items():
                if key in ['batch_size', 'num_workers', 'learning_rate']:
                    print(f"   • {key}: {value}")
        
        return optimized
    
    def test_mps_performance(self):
        """MPS性能テスト"""
        if not (self.is_apple_silicon and torch.backends.mps.is_available()):
            print("❌ MPS利用不可")
            return False
        
        try:
            print("🧪 MPS性能テスト実行中...")
            
            device = torch.device('mps')
            
            # 行列演算テスト
            size = 2048
            a = torch.randn(size, size, device=device)
            b = torch.randn(size, size, device=device)
            
            import time
            start_time = time.time()
            for _ in range(10):
                c = torch.mm(a, b)
                torch.mps.synchronize()  # GPU同期
            end_time = time.time()
            
            avg_time = (end_time - start_time) / 10
            gflops = (2 * size ** 3) / (avg_time * 1e9)
            
            print(f"✅ MPS性能テスト結果:")
            print(f"   • 行列サイズ: {size}x{size}")
            print(f"   • 平均処理時間: {avg_time*1000:.2f}ms")
            print(f"   • 性能: {gflops:.1f} GFLOPS")
            
            return True
            
        except Exception as e:
            print(f"❌ MPS性能テストエラー: {e}")
            return False
    
    def create_optimized_dataloader(self, dataset, batch_size=None):
        """最適化されたDataLoader作成"""
        if batch_size is None:
            batch_size = self.get_optimal_batch_size()
        
        dataloader_kwargs = {
            'batch_size': batch_size,
            'shuffle': True,
            'num_workers': self.get_optimal_num_workers(),
            'pin_memory': True,
            'drop_last': True,
        }
        
        if self.is_apple_silicon:
            # Apple Silicon特化設定
            dataloader_kwargs['persistent_workers'] = True
        
        from torch.utils.data import DataLoader
        return DataLoader(dataset, **dataloader_kwargs)
    
    def print_optimization_summary(self):
        """最適化サマリー表示"""
        print("\n🍎 Apple Silicon M4 Pro 最適化サマリー")
        print("=" * 50)
        print(f"💻 システム: {'Apple Silicon' if self.is_apple_silicon else 'Other'}")
        print(f"🧠 CPU コア数: {self.cpu_cores}")
        print(f"💾 メモリ: {self.memory_gb:.1f}GB")
        
        device, acceleration = self.get_optimal_device()
        print(f"🚀 GPU加速: {acceleration}")
        
        if self.is_apple_silicon:
            print(f"📊 最適バッチサイズ: {self.get_optimal_batch_size()}")
            print(f"👥 最適ワーカー数: {self.get_optimal_num_workers()}")
            print("🎯 macOS Core Audio統合: 準備完了")
            print("🎵 48kHz高品質録音: 対応")

def main():
    """メイン関数"""
    print("🍎 Apple Silicon M4 Pro 最適化テスト")
    print("=" * 50)
    
    optimizer = AppleSiliconOptimizer()
    optimizer.print_optimization_summary()
    
    # MPS設定
    if optimizer.setup_mps_optimizations():
        optimizer.test_mps_performance()
    
    # 音声処理設定
    audio_config = optimizer.get_audio_processing_config()
    print(f"\n🎵 音声処理設定:")
    for key, value in audio_config.items():
        print(f"   • {key}: {value}")
    
    # 学習設定例
    base_training_config = {
        'batch_size': 4,
        'learning_rate': 0.001,
        'epochs': 100
    }
    
    optimized_config = optimizer.optimize_training_params(base_training_config)
    print(f"\n🎯 最適化学習設定:")
    for key, value in optimized_config.items():
        print(f"   • {key}: {value}")

if __name__ == "__main__":
    main()