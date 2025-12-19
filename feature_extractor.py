import numpy as np
import librosa
import parselmouth
from scipy.stats import entropy
import soundfile as sf
import warnings

# Filter warnings for cleaner output
warnings.filterwarnings('ignore')

class ComprehensiveSpeechAnalyzer:
    def __init__(self):
        pass
    
    def extract_all_features(self, audio_path):
        """Extract all 20+ acoustic biomarkers from audio file with clinical-grade preprocessing"""
        try:
            # 1. Standardized Audio Acquisition (16kHz, Mono)
            y, sr = self.robust_audio_load(audio_path)
            
            # 2. Pre-processing Pipeline
            y = self.preprocess_audio(y, sr)
            
            # Save preprocessed audio to a temporary file for parselmouth
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
                sf.write(tmp.name, y, sr, subtype='PCM_16')
                tmp_path = tmp.name
                
            try:
                sound = parselmouth.Sound(tmp_path)
                
                # Initialize features dictionary
                features = {
                    "feature_version": "v1.2",
                    "preprocessing_chain": ["dc_removal", "pre_emphasis", "rms_normalize", "silence_trim", "bandpass_80_4000"]
                }
                
                # Quality Control Layer
                quality_metrics = self.quality_control(y, sr)
                features.update(quality_metrics)
                
                # Windowing Strategy: 25ms window, 10ms hop
                win_length = int(0.025 * sr)
                hop_length = int(0.010 * sr)
                
                # 3. Feature Extraction with Statistical Robustness
                
                # Pitch / F0 Statistics
                pitch = sound.to_pitch(time_step=0.01, pitch_floor=75, pitch_ceiling=600)
                f0_values = pitch.selected_array['frequency']
                f0_values = f0_values[f0_values != 0] # VOICED FRAMES ONLY
                features.update(self.get_stats(f0_values, 'f0'))
                
                # Jitter & Shimmer (Strictly voiced segments)
                try:
                    pointprocess = parselmouth.praat.call(sound, "To PointProcess (periodic, cc)", 75, 600)
                    if pointprocess is not None:
                        features['jitter_local'] = float(parselmouth.praat.call(pointprocess, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3))
                        features['jitter_rap'] = float(parselmouth.praat.call(pointprocess, "Get jitter (rap)", 0, 0, 0.0001, 0.02, 1.3))
                        features['jitter_ppq5'] = float(parselmouth.praat.call(pointprocess, "Get jitter (ppq5)", 0, 0, 0.0001, 0.02, 1.3))
                        
                        features['shimmer_local'] = float(parselmouth.praat.call([sound, pointprocess], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6))
                        features['shimmer_apq3'] = float(parselmouth.praat.call([sound, pointprocess], "Get shimmer (apq3)", 0, 0, 0.0001, 0.02, 1.3, 1.6))
                        features['shimmer_apq5'] = float(parselmouth.praat.call([sound, pointprocess], "Get shimmer (apq5)", 0, 0, 0.0001, 0.02, 1.3, 1.6))
                    else:
                        features.update({k: 0.0 for k in ['jitter_local', 'jitter_rap', 'jitter_ppq5', 'shimmer_local', 'shimmer_apq3', 'shimmer_apq5']})
                except:
                    features.update({k: 0.0 for k in ['jitter_local', 'jitter_rap', 'jitter_ppq5', 'shimmer_local', 'shimmer_apq3', 'shimmer_apq5']})

                # HNR with Sanity Bounds
                try:
                    harmonicity = sound.to_harmonicity()
                    hnr_val = float(parselmouth.praat.call(harmonicity, "Get mean", 0, 0))
                    features['hnr'] = hnr_val
                    features['hnr_anomaly_flag'] = 1 if (hnr_val < 0 or hnr_val > 40) else 0
                except:
                    features['hnr'] = 0.0
                    features['hnr_anomaly_flag'] = 1

                # Formants (F1, F2, F3)
                try:
                    formants = sound.to_formant_burg(time_step=0.01, max_number_of_formants=5, maximum_formant=5500)
                    for f in [1, 2, 3]:
                        f_vals = [formants.get_value_at_time(f, t) for t in np.arange(0, sound.duration, 0.01)]
                        f_vals = [v for v in f_vals if not np.isnan(v)]
                        features.update(self.get_stats(f_vals, f'f{f}'))
                except:
                    for f in [1, 2, 3]:
                        features.update({f'f{f}_{s}': 0.0 for s in ['mean', 'std', 'median', 'iqr', 'skew', 'kurtosis']})

                # MFCC (1-13) + Delta + Delta-Delta
                try:
                    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, n_fft=win_length, hop_length=hop_length, window='hamming')
                    delta_mfcc = librosa.feature.delta(mfccs)
                    delta2_mfcc = librosa.feature.delta(mfccs, order=2)
                    
                    for i in range(13):
                        features.update(self.get_stats(mfccs[i], f'mfcc_{i+1}'))
                        features.update(self.get_stats(delta_mfcc[i], f'dmfcc_{i+1}'))
                        features.update(self.get_stats(delta2_mfcc[i], f'ddmfcc_{i+1}'))
                except:
                    pass

                # Spectral Features
                try:
                    sc = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=win_length, hop_length=hop_length)
                    features.update(self.get_stats(sc[0], 'spectral_centroid'))
                    
                    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, n_fft=win_length, hop_length=hop_length)
                    features.update(self.get_stats(rolloff[0], 'spectral_rolloff'))
                except:
                    pass

                features['duration'] = float(len(y) / sr)
                
                return features
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            print(f"Error in feature extraction: {str(e)}")
            return {}

    def preprocess_audio(self, y, sr):
        """Mandatory Clinical Pre-processing Pipeline"""
        # 1. DC Offset Removal
        y = y - np.mean(y)
        
        # 2. Pre-emphasis Filter
        y = librosa.effects.preemphasis(y, coef=0.97)
        
        # 3. RMS-based Amplitude Normalization
        rms = np.sqrt(np.mean(y**2))
        if rms > 0:
            y = y / rms * 0.1  # Target RMS of 0.1
            
        # 4. Silence Trimming (Energy + ZCR based)
        y, _ = librosa.effects.trim(y, top_db=30)
        
        # 5. Band-pass filtering (80 Hz – 4 kHz)
        from scipy.signal import butter, lfilter
        def butter_bandpass(lowcut, highcut, fs, order=5):
            nyq = 0.5 * fs
            low = lowcut / nyq
            high = highcut / nyq
            b, a = butter(order, [low, high], btype='band')
            return b, a

        b, a = butter_bandpass(80, 4000, sr, order=5)
        y = lfilter(b, a, y)
        
        return y.astype(np.float32)

    def quality_control(self, y, sr):
        """Outlier & Quality Control Layer with Raw Metrics"""
        rejection_reasons = []
        quality_score = 100
        
        # 1. Detect Clipping & Clipping Ratio
        abs_y = np.abs(y)
        clip_count = np.sum(abs_y > 0.99)
        clipping_ratio = float(clip_count / len(y))
        
        if clipping_ratio > 0.01: # More than 1% clipped
            rejection_reasons.append(f"Excessive clipping: {clipping_ratio:.2%}")
            quality_score -= 40
            
        # 2. Check Duration
        duration = len(y) / sr
        if duration < 1.0:
            rejection_reasons.append("Sample too short")
            quality_score -= 50
            
        # 3. SNR Estimation (RMS-based)
        rms_signal = np.sqrt(np.mean(y**2))
        noise_floor = np.percentile(abs_y, 10)
        snr_db = float(20 * np.log10(rms_signal / (noise_floor + 1e-6)))
        
        if snr_db < 15:
            rejection_reasons.append(f"Low SNR: {snr_db:.2f}dB")
            quality_score -= 30

        # 4. Voiced Frame Ratio (based on energy threshold)
        # Using a simple RMS approach for the ratio
        frame_length = int(0.025 * sr)
        hop_length = int(0.010 * sr)
        rms_frames = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
        voiced_frames = np.sum(rms_frames > (np.mean(rms_frames) * 0.5))
        voiced_frame_ratio = float(voiced_frames / len(rms_frames))

        reason_str = "; ".join(rejection_reasons) if rejection_reasons else "Passed"
        
        return {
            "quality_score": max(0, quality_score),
            "rejection_reason": reason_str,
            "snr_db": snr_db,
            "clipping_ratio": clipping_ratio,
            "voiced_frame_ratio": voiced_frame_ratio
        }

    def get_stats(self, data, name):
        """Calculate statistical moments with numerical safety guards"""
        from scipy.stats import skew, kurtosis, iqr
        
        # Numerical guards: empty, small N, or zero variance
        if len(data) < 3 or np.std(data) < 1e-6:
            return {f'{name}_{s}': 0.0 for s in ['mean', 'std', 'median', 'iqr', 'skew', 'kurtosis']}
        
        # Remove any NaNs just in case
        data = data[~np.isnan(data)]
        if len(data) < 3:
            return {f'{name}_{s}': 0.0 for s in ['mean', 'std', 'median', 'iqr', 'skew', 'kurtosis']}

        return {
            f'{name}_mean': float(np.mean(data)),
            f'{name}_std': float(np.std(data)),
            f'{name}_median': float(np.median(data)),
            f'{name}_iqr': float(iqr(data)),
            f'{name}_skew': float(skew(data)),
            f'{name}_kurtosis': float(kurtosis(data))
        }

    def dfa(self, signal, scales):
        """Simple DFA implementation"""
        fluctuations = []
        for scale in scales:
            if scale >= len(signal):
                continue
            
            # Integration
            y_int = np.cumsum(signal - np.mean(signal))
            
            # Divide into boxes
            n_boxes = len(y_int) // scale
            boxes = y_int[:n_boxes * scale].reshape(n_boxes, scale)
            
            # Detrend each box
            t = np.arange(scale)
            fluctuation = 0
            for box in boxes:
                coeffs = np.polyfit(t, box, 1)
                trend = np.polyval(coeffs, t)
                fluctuation += np.mean((box - trend) ** 2)
            
            fluctuations.append(fluctuation / n_boxes)
        
        return np.mean(fluctuations) if fluctuations else 0.0

    def robust_audio_load(self, file_path):
        """Standardized clinical audio loading: 16kHz, Mono"""
        try:
            # Force sr=16000 and mono=True
            y, sr = librosa.load(file_path, sr=16000, mono=True)
            return y, sr
        except Exception as e1:
            try:
                # Try soundfile then resample if needed
                y, sr = sf.read(file_path, always_2d=True)
                y = y[:, 0] # Take first channel
                if sr != 16000:
                    y = librosa.resample(y, orig_sr=sr, target_sr=16000)
                return y, 16000
            except Exception as e2:
                # Try parselmouth
                sound = parselmouth.Sound(file_path)
                y = sound.values[0]
                orig_sr = sound.sampling_frequency
                if orig_sr != 16000:
                    y = librosa.resample(y.astype(np.float32), orig_sr=orig_sr, target_sr=16000)
                return y, 16000
