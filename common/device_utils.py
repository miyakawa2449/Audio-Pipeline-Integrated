#!/usr/bin/env python3
"""
Audio Pipeline Integrated - 統合デバイスユーティリティ
全プロジェクト共通のデバイス検出・管理機能
"""

import platform
import sys
import subprocess
from typing import Dict, List, Optional, Any
from .logger import get_logger

# オプショナルライブラリ
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class DeviceUtils:
    """統合デバイス管理ユーティリティクラス"""
    
    def __init__(self):
        """初期化"""
        self.logger = get_logger("DeviceUtils")
        self.system_info = None
        self.audio_devices = None
        self.compute_devices = None
        self.logger.info("DeviceUtils初期化完了")
    
    def get_system_info(self, refresh: bool = False) -> Dict[str, Any]:
        """
        システム情報取得
        
        Args:
            refresh: 情報更新フラグ
            
        Returns:
            システム情報辞書
        """
        if self.system_info is None or refresh:
            self.system_info = self._collect_system_info()
        
        return self.system_info
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """システム情報収集"""
        info = {
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'architecture': platform.architecture()[0]
            },
            'python': {
                'version': platform.python_version(),
                'implementation': platform.python_implementation(),
                'executable': sys.executable
            }
        }
        
        # CPU情報
        if PSUTIL_AVAILABLE:
            try:
                cpu_info = {
                    'physical_cores': psutil.cpu_count(logical=False),
                    'logical_cores': psutil.cpu_count(logical=True),
                    'max_frequency': psutil.cpu_freq().max if psutil.cpu_freq() else None,
                    'current_frequency': psutil.cpu_freq().current if psutil.cpu_freq() else None,
                }
                info['cpu'] = cpu_info
            except Exception as e:
                self.logger.warning(f"CPU情報取得失敗: {e}")
        
        # メモリ情報
        if PSUTIL_AVAILABLE:
            try:
                memory = psutil.virtual_memory()
                memory_info = {
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'used_gb': memory.used / (1024**3),
                    'percentage': memory.percent
                }
                info['memory'] = memory_info
            except Exception as e:
                self.logger.warning(f"メモリ情報取得失敗: {e}")
        
        self.logger.debug("システム情報収集完了")
        return info
    
    def get_compute_devices(self, refresh: bool = False) -> Dict[str, Any]:
        """
        計算デバイス情報取得（GPU/CPU）
        
        Args:
            refresh: 情報更新フラグ
            
        Returns:
            計算デバイス情報辞書
        """
        if self.compute_devices is None or refresh:
            self.compute_devices = self._collect_compute_devices()
        
        return self.compute_devices
    
    def _collect_compute_devices(self) -> Dict[str, Any]:
        """計算デバイス情報収集"""
        devices = {
            'cpu': {'available': True, 'name': 'CPU'},
            'cuda': {'available': False, 'devices': []},
            'mps': {'available': False, 'name': 'Apple Silicon MPS'},
            'recommended': 'cpu'
        }
        
        if TORCH_AVAILABLE:
            # CUDA情報
            if torch.cuda.is_available():
                devices['cuda']['available'] = True
                devices['cuda']['device_count'] = torch.cuda.device_count()
                devices['cuda']['devices'] = []
                
                for i in range(torch.cuda.device_count()):
                    gpu_info = {
                        'id': i,
                        'name': torch.cuda.get_device_name(i),
                        'memory_total': torch.cuda.get_device_properties(i).total_memory / (1024**3),
                        'memory_allocated': torch.cuda.memory_allocated(i) / (1024**3),
                        'compute_capability': torch.cuda.get_device_properties(i).major
                    }
                    devices['cuda']['devices'].append(gpu_info)
                
                devices['recommended'] = 'cuda'
                self.logger.info(f"CUDA利用可能: {torch.cuda.device_count()}デバイス")
            
            # Apple Silicon MPS情報
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                devices['mps']['available'] = True
                devices['recommended'] = 'mps'
                self.logger.info("Apple Silicon MPS利用可能")
        
        return devices
    
    def get_recommended_device(self) -> str:
        """
        推奨計算デバイス取得
        
        Returns:
            推奨デバイス名 ('cuda', 'mps', 'cpu')
        """
        devices = self.get_compute_devices()
        return devices['recommended']
    
    def get_torch_device(self) -> Any:
        """
        PyTorchデバイスオブジェクト取得
        
        Returns:
            torch.deviceオブジェクト（TORCH_AVAILABLE=Falseの場合は文字列）
        """
        if not TORCH_AVAILABLE:
            return self.get_recommended_device()
        
        recommended = self.get_recommended_device()
        
        if recommended == 'cuda':
            return torch.device('cuda')
        elif recommended == 'mps':
            return torch.device('mps')
        else:
            return torch.device('cpu')
    
    def get_audio_devices(self, refresh: bool = False) -> Dict[str, Any]:
        """
        音声デバイス情報取得
        
        Args:
            refresh: 情報更新フラグ
            
        Returns:
            音声デバイス情報辞書
        """
        if self.audio_devices is None or refresh:
            self.audio_devices = self._collect_audio_devices()
        
        return self.audio_devices
    
    def _collect_audio_devices(self) -> Dict[str, Any]:
        """音声デバイス情報収集"""
        devices = {
            'available': SOUNDDEVICE_AVAILABLE,
            'input_devices': [],
            'output_devices': [],
            'default_input': None,
            'default_output': None
        }
        
        if SOUNDDEVICE_AVAILABLE:
            try:
                device_list = sd.query_devices()
                default_input = sd.default.device[0]
                default_output = sd.default.device[1]
                
                for i, device in enumerate(device_list):
                    device_info = {
                        'id': i,
                        'name': device['name'],
                        'channels': device['max_input_channels'] if device['max_input_channels'] > 0 else device['max_output_channels'],
                        'sample_rate': device['default_samplerate']
                    }
                    
                    if device['max_input_channels'] > 0:
                        devices['input_devices'].append(device_info)
                        if i == default_input:
                            devices['default_input'] = device_info
                    
                    if device['max_output_channels'] > 0:
                        devices['output_devices'].append(device_info)
                        if i == default_output:
                            devices['default_output'] = device_info
                
                self.logger.info(f"音声デバイス検出: 入力{len(devices['input_devices'])}個, 出力{len(devices['output_devices'])}個")
                
            except Exception as e:
                self.logger.error(f"音声デバイス情報取得失敗: {e}")
        
        return devices
    
    def test_audio_device(self, device_id: Optional[int] = None, 
                         duration: float = 1.0, sample_rate: int = 44100) -> bool:
        """
        音声デバイステスト
        
        Args:
            device_id: デバイスID（None: デフォルト）
            duration: テスト時間（秒）
            sample_rate: サンプルレート
            
        Returns:
            テスト成功フラグ
        """
        if not SOUNDDEVICE_AVAILABLE:
            self.logger.error("sounddeviceが利用できません")
            return False
        
        try:
            # 短時間の録音テスト
            test_data = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                device=device_id
            )
            sd.wait()
            
            # 音声データの基本チェック
            if test_data is not None and len(test_data) > 0:
                max_amplitude = abs(test_data).max()
                self.logger.info(f"音声デバイステスト成功: 最大振幅 {max_amplitude:.4f}")
                return True
            else:
                self.logger.error("音声データが取得できませんでした")
                return False
                
        except Exception as e:
            self.logger.error(f"音声デバイステスト失敗: {e}")
            return False
    
    def check_dependencies(self) -> Dict[str, Dict[str, Any]]:
        """
        依存関係チェック
        
        Returns:
            依存関係情報辞書
        """
        dependencies = {
            'torch': {
                'available': TORCH_AVAILABLE,
                'version': None,
                'cuda_available': False,
                'mps_available': False
            },
            'sounddevice': {
                'available': SOUNDDEVICE_AVAILABLE,
                'version': None
            },
            'psutil': {
                'available': PSUTIL_AVAILABLE,
                'version': None
            }
        }
        
        # PyTorch情報
        if TORCH_AVAILABLE:
            dependencies['torch']['version'] = torch.__version__
            dependencies['torch']['cuda_available'] = torch.cuda.is_available()
            if hasattr(torch.backends, 'mps'):
                dependencies['torch']['mps_available'] = torch.backends.mps.is_available()
        
        # sounddevice情報
        if SOUNDDEVICE_AVAILABLE:
            dependencies['sounddevice']['version'] = sd.__version__
        
        # psutil情報
        if PSUTIL_AVAILABLE:
            dependencies['psutil']['version'] = psutil.__version__
        
        return dependencies
    
    def log_system_summary(self):
        """システム情報サマリーをログ出力"""
        self.logger.info("=== システム情報サマリー ===")
        
        # 基本システム情報
        system_info = self.get_system_info()
        platform_info = system_info['platform']
        
        self.logger.info(f"OS: {platform_info['system']} {platform_info['release']}")
        self.logger.info(f"アーキテクチャ: {platform_info['architecture']}")
        self.logger.info(f"Python: {system_info['python']['version']}")
        
        # CPU/メモリ情報
        if 'cpu' in system_info:
            cpu = system_info['cpu']
            self.logger.info(f"CPU: {cpu.get('physical_cores', 'N/A')}コア（物理）, {cpu.get('logical_cores', 'N/A')}コア（論理）")
        
        if 'memory' in system_info:
            memory = system_info['memory']
            self.logger.info(f"メモリ: {memory['total_gb']:.1f}GB（利用可能: {memory['available_gb']:.1f}GB）")
        
        # 計算デバイス情報
        compute_devices = self.get_compute_devices()
        if compute_devices['cuda']['available']:
            cuda_count = compute_devices['cuda']['device_count']
            self.logger.device_info(f"CUDA GPU: {cuda_count}デバイス利用可能")
        elif compute_devices['mps']['available']:
            self.logger.device_info("Apple Silicon MPS利用可能")
        else:
            self.logger.device_info("CPU計算モード")
        
        # 音声デバイス情報
        audio_devices = self.get_audio_devices()
        if audio_devices['available']:
            input_count = len(audio_devices['input_devices'])
            output_count = len(audio_devices['output_devices'])
            self.logger.device_info(f"音声デバイス: 入力{input_count}個, 出力{output_count}個")
        else:
            self.logger.warning("音声デバイス検出機能が利用できません")
        
        self.logger.info("=" * 30)


# グローバルデバイスユーティリティインスタンス
_device_utils_instance = None

def get_device_utils() -> DeviceUtils:
    """
    グローバルデバイスユーティリティインスタンス取得
    
    Returns:
        DeviceUtilsインスタンス
    """
    global _device_utils_instance
    if _device_utils_instance is None:
        _device_utils_instance = DeviceUtils()
    return _device_utils_instance


# 便利関数
def get_recommended_device() -> str:
    """推奨デバイス取得便利関数"""
    utils = get_device_utils()
    return utils.get_recommended_device()

def get_torch_device() -> Any:
    """PyTorchデバイス取得便利関数"""
    utils = get_device_utils()
    return utils.get_torch_device()

def get_system_info() -> Dict[str, Any]:
    """システム情報取得便利関数"""
    utils = get_device_utils()
    return utils.get_system_info()

def get_audio_devices() -> Dict[str, Any]:
    """音声デバイス情報取得便利関数"""
    utils = get_device_utils()
    return utils.get_audio_devices()

def log_system_summary():
    """システム情報サマリーログ出力便利関数"""
    utils = get_device_utils()
    utils.log_system_summary()