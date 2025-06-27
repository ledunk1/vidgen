"""
GPU Detection dan Hardware Acceleration untuk Video Processing
"""

import subprocess
import platform
import os
import cv2

class GPUDetector:
    """
    Kelas untuk mendeteksi GPU dan kemampuan hardware acceleration
    """
    
    def __init__(self):
        self.intel_gpu_detected = False
        self.amd_gpu_detected = False
        self.nvidia_gpu_detected = False
        self.opencl_support = False
        self.supported_encoders = []
        self.supported_decoders = []
        self.gpu_acceleration_available = False
        
        self._detect_gpus()
        self._check_opencl_support()
        self._detect_hardware_codecs()
    
    def _detect_gpus(self):
        """Deteksi GPU yang tersedia di sistem"""
        try:
            # Deteksi Intel GPU
            if platform.system() == "Windows":
                # Windows: Cek melalui wmic atau dxdiag
                try:
                    result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                                          capture_output=True, text=True, timeout=10)
                    gpu_info = result.stdout.lower()
                    
                    if 'intel' in gpu_info:
                        self.intel_gpu_detected = True
                        print("🔷 Intel GPU detected")
                    
                    if 'amd' in gpu_info or 'radeon' in gpu_info:
                        self.amd_gpu_detected = True
                        print("🔴 AMD GPU detected")
                    
                    if 'nvidia' in gpu_info or 'geforce' in gpu_info:
                        self.nvidia_gpu_detected = True
                        print("🟢 NVIDIA GPU detected")
                        
                except Exception as e:
                    print(f"Warning: Could not detect GPU via wmic: {e}")
            
            elif platform.system() == "Linux":
                # Linux: Cek melalui lspci
                try:
                    result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=10)
                    gpu_info = result.stdout.lower()
                    
                    if 'intel' in gpu_info and ('vga' in gpu_info or 'display' in gpu_info):
                        self.intel_gpu_detected = True
                        print("🔷 Intel GPU detected")
                    
                    if ('amd' in gpu_info or 'radeon' in gpu_info) and ('vga' in gpu_info or 'display' in gpu_info):
                        self.amd_gpu_detected = True
                        print("🔴 AMD GPU detected")
                    
                    if 'nvidia' in gpu_info and ('vga' in gpu_info or 'display' in gpu_info):
                        self.nvidia_gpu_detected = True
                        print("🟢 NVIDIA GPU detected")
                        
                except Exception as e:
                    print(f"Warning: Could not detect GPU via lspci: {e}")
            
            # Set flag jika ada GPU yang terdeteksi
            if self.intel_gpu_detected or self.amd_gpu_detected or self.nvidia_gpu_detected:
                self.gpu_acceleration_available = True
                print("✅ GPU acceleration available")
            else:
                print("⚠️ No GPU detected, using CPU only")
                
        except Exception as e:
            print(f"Error detecting GPUs: {e}")
    
    def _check_opencl_support(self):
        """Cek dukungan OpenCL untuk OpenCV"""
        try:
            # Cek apakah OpenCV mendukung OpenCL
            if hasattr(cv2, 'ocl') and cv2.ocl.haveOpenCL():
                self.opencl_support = True
                print("🔷 OpenCV OpenCL support detected")
                
                # Aktifkan OpenCL jika tersedia
                cv2.ocl.setUseOpenCL(True)
                print("✅ OpenCL enabled for OpenCV")
            else:
                print("⚠️ OpenCL not available for OpenCV")
                
        except Exception as e:
            print(f"Error checking OpenCL support: {e}")
    
    def _detect_hardware_codecs(self):
        """Deteksi codec hardware yang tersedia melalui FFmpeg"""
        try:
            # Cek encoder yang tersedia
            result = subprocess.run(['ffmpeg', '-encoders'], 
                                  capture_output=True, text=True, timeout=15)
            encoders_output = result.stdout.lower()
            
            # Deteksi Intel Quick Sync encoders
            if 'h264_qsv' in encoders_output and self.intel_gpu_detected:
                self.supported_encoders.append('h264_qsv')
            
            if 'hevc_qsv' in encoders_output and self.intel_gpu_detected:
                self.supported_encoders.append('hevc_qsv')
            
            # Deteksi NVIDIA NVENC encoders
            if 'h264_nvenc' in encoders_output and self.nvidia_gpu_detected:
                self.supported_encoders.append('h264_nvenc')
            
            if 'hevc_nvenc' in encoders_output and self.nvidia_gpu_detected:
                self.supported_encoders.append('hevc_nvenc')
            
            # Deteksi AMD AMF encoders
            if 'h264_amf' in encoders_output and self.amd_gpu_detected:
                self.supported_encoders.append('h264_amf')
            
            if 'hevc_amf' in encoders_output and self.amd_gpu_detected:
                self.supported_encoders.append('hevc_amf')
            
            # CPU fallback selalu tersedia
            if 'libx264' in encoders_output:
                self.supported_encoders.append('libx264')
            
            # Cek decoder yang tersedia
            result = subprocess.run(['ffmpeg', '-decoders'], 
                                  capture_output=True, text=True, timeout=15)
            decoders_output = result.stdout.lower()
            
            # Deteksi hardware decoders
            if 'h264_qsv' in decoders_output and self.intel_gpu_detected:
                self.supported_decoders.append('h264_qsv')
            
            if 'hevc_qsv' in decoders_output and self.intel_gpu_detected:
                self.supported_decoders.append('hevc_qsv')
            
            if 'h264_cuvid' in decoders_output and self.nvidia_gpu_detected:
                self.supported_decoders.append('h264_cuvid')
            
            if 'hevc_cuvid' in decoders_output and self.nvidia_gpu_detected:
                self.supported_decoders.append('hevc_cuvid')
            
            # Log hasil deteksi
            if self.supported_encoders:
                print(f"🎬 Supported hardware encoders: {', '.join(self.supported_encoders)}")
            else:
                print("⚠️ No hardware encoders detected")
            
            if self.supported_decoders:
                print(f"🎞️ Supported hardware decoders: {', '.join(self.supported_decoders)}")
            else:
                print("⚠️ No hardware decoders detected")
                
        except Exception as e:
            print(f"Error detecting hardware codecs: {e}")
            # Fallback ke CPU
            self.supported_encoders = ['libx264']
    
    def get_best_encoder(self, prefer_hardware=True):
        """Mendapatkan encoder terbaik berdasarkan preferensi"""
        if not prefer_hardware:
            return 'libx264'
        
        # Prioritas: Intel QSV > NVIDIA NVENC > AMD AMF > CPU
        priority_order = ['h264_qsv', 'h264_nvenc', 'h264_amf', 'libx264']
        
        for encoder in priority_order:
            if encoder in self.supported_encoders:
                return encoder
        
        return 'libx264'  # Fallback
    
    def get_best_decoder(self, prefer_hardware=True):
        """Mendapatkan decoder terbaik berdasarkan preferensi"""
        if not prefer_hardware or not self.supported_decoders:
            return None  # Gunakan decoder default
        
        # Prioritas: Intel QSV > NVIDIA CUVID
        priority_order = ['h264_qsv', 'h264_cuvid']
        
        for decoder in priority_order:
            if decoder in self.supported_decoders:
                return decoder
        
        return None  # Gunakan decoder default
    
    def log_gpu_status(self, gpu_acceleration_enabled=True):
        """Log status GPU acceleration"""
        if gpu_acceleration_enabled and self.gpu_acceleration_available:
            print("🎮 GPU acceleration: Enabled")
        else:
            print("🎮 GPU acceleration: Disabled (using CPU)")

# Instance global untuk digunakan di seluruh aplikasi
gpu_detector = GPUDetector()