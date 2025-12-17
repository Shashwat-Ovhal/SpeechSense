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
        """Extract all 20+ acoustic biomarkers from audio file"""
        try:
            # Load audio with robust loading
            y, sr = self.robust_audio_load(audio_path)
            sound = parselmouth.Sound(audio_path)
            
            # Initialize features dictionary
            features = {}
            
            # 1. Fundamental frequency (F0) / Pitch analysis
            pitch = sound.to_pitch()
            f0_values = pitch.selected_array['frequency']
            f0_values = f0_values[f0_values != 0]  # Remove unvoiced frames
            
            features['f0_mean'] = float(np.mean(f0_values)) if len(f0_values) > 0 else 0.0
            features['f0_std'] = float(np.std(f0_values)) if len(f0_values) > 0 else 0.0
            features['f0_min'] = float(np.min(f0_values)) if len(f0_values) > 0 else 0.0
            features['f0_max'] = float(np.max(f0_values)) if len(f0_values) > 0 else 0.0
            
            # 2. Jitter (cycle-to-cycle frequency variation)
            try:
                pointprocess = parselmouth.praat.call(sound, "To PointProcess (periodic, cc)", 75, 500)
                if pointprocess is not None:
                    jitter_local = parselmouth.praat.call(pointprocess, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
                    jitter_rap = parselmouth.praat.call(pointprocess, "Get jitter (rap)", 0, 0, 0.0001, 0.02, 1.3)
                    jitter_ppq5 = parselmouth.praat.call(pointprocess, "Get jitter (ppq5)", 0, 0, 0.0001, 0.02, 1.3)
                else:
                    jitter_local = jitter_rap = jitter_ppq5 = 0.0
                
                features['jitter_local'] = float(jitter_local)
                features['jitter_rap'] = float(jitter_rap)
                features['jitter_ppq5'] = float(jitter_ppq5)
            except:
                features['jitter_local'] = 0.0
                features['jitter_rap'] = 0.0
                features['jitter_ppq5'] = 0.0
            
            # 3. Shimmer (cycle-to-cycle amplitude variation)
            try:
                pointprocess = parselmouth.praat.call(sound, "To PointProcess (periodic, cc)", 75, 500)
                if pointprocess is not None:
                    shimmer_local = parselmouth.praat.call([sound, pointprocess], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
                    shimmer_apq3 = parselmouth.praat.call([sound, pointprocess], "Get shimmer (apq3)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
                    shimmer_apq5 = parselmouth.praat.call([sound, pointprocess], "Get shimmer (apq5)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
                else:
                    shimmer_local = shimmer_apq3 = shimmer_apq5 = 0.0
                
                features['shimmer_local'] = float(shimmer_local)
                features['shimmer_apq3'] = float(shimmer_apq3)
                features['shimmer_apq5'] = float(shimmer_apq5)
            except:
                features['shimmer_local'] = 0.0
                features['shimmer_apq3'] = 0.0
                features['shimmer_apq5'] = 0.0
            
            # 4. Harmonics-to-Noise Ratio (HNR)
            try:
                harmonicity = sound.to_harmonicity()
                hnr_mean = parselmouth.praat.call(harmonicity, "Get mean", 0, 0)
                features['hnr'] = float(hnr_mean)
            except:
                features['hnr'] = 0.0
            
            # 5. Noise-to-Harmonics Ratio (NHR) - proper calculation
            if features['hnr'] > -50:  # Avoid extreme values
                features['nhr'] = 1.0 / (10**(features['hnr']/10.0)) if features['hnr'] > 0 else 10.0
            else:
                features['nhr'] = 10.0  # Cap at reasonable value
            
            # 6 & 7. Formant frequencies and bandwidths (F1, F2, F3)
            try:
                formants = sound.to_formant_burg()
                
                # Extract F1, F2, F3 frequencies
                f1_values = []
                f2_values = []
                f3_values = []
                f1_bw_values = []
                f2_bw_values = []
                f3_bw_values = []
                
                for i in range(1, formants.get_number_of_frames() + 1):
                    f1 = formants.get_value_at_time(1, formants.get_time_from_frame_number(i))
                    f2 = formants.get_value_at_time(2, formants.get_time_from_frame_number(i))
                    f3 = formants.get_value_at_time(3, formants.get_time_from_frame_number(i))
                    
                    if not np.isnan(f1): f1_values.append(f1)
                    if not np.isnan(f2): f2_values.append(f2)
                    if not np.isnan(f3): f3_values.append(f3)
                    
                    # Bandwidths
                    bw1 = formants.get_bandwidth_at_time(1, formants.get_time_from_frame_number(i))
                    bw2 = formants.get_bandwidth_at_time(2, formants.get_time_from_frame_number(i))
                    bw3 = formants.get_bandwidth_at_time(3, formants.get_time_from_frame_number(i))
                    
                    if not np.isnan(bw1): f1_bw_values.append(bw1)
                    if not np.isnan(bw2): f2_bw_values.append(bw2)
                    if not np.isnan(bw3): f3_bw_values.append(bw3)
                
                features['f1_mean'] = float(np.mean(f1_values)) if f1_values else 0.0
                features['f2_mean'] = float(np.mean(f2_values)) if f2_values else 0.0
                features['f3_mean'] = float(np.mean(f3_values)) if f3_values else 0.0
                features['f1_bandwidth'] = float(np.mean(f1_bw_values)) if f1_bw_values else 0.0
                features['f2_bandwidth'] = float(np.mean(f2_bw_values)) if f2_bw_values else 0.0
                features['f3_bandwidth'] = float(np.mean(f3_bw_values)) if f3_bw_values else 0.0
            except:
                features.update({'f1_mean': 0.0, 'f2_mean': 0.0, 'f3_mean': 0.0, 
                               'f1_bandwidth': 0.0, 'f2_bandwidth': 0.0, 'f3_bandwidth': 0.0})
            
            # 8. Voice intensity / loudness
            try:
                intensity = sound.to_intensity()
                intensity_mean = parselmouth.praat.call(intensity, "Get mean", 0, 0)
                features['intensity'] = float(intensity_mean)
            except:
                features['intensity'] = 0.0
            
            # 9. Voice onset time (energy-based onset detection)
            try:
                # Use librosa's onset detection for better accuracy
                onset_frames = librosa.onset.onset_detect(y=y, sr=sr, units='time')
                features['voice_onset_time'] = float(onset_frames[0]) if len(onset_frames) > 0 else 0.0
            except:
                features['voice_onset_time'] = 0.0
            
            # 10. MFCC (Mel-Frequency Cepstral Coefficients)
            try:
                mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
                for i in range(13):
                    features[f'mfcc_{i+1}'] = float(np.mean(mfccs[i]))
            except:
                for i in range(13):
                    features[f'mfcc_{i+1}'] = 0.0
            
            # 11. Recurrence Period Density Entropy (RPDE) - simplified implementation
            try:
                # Use autocorrelation for periodicity analysis
                autocorr = np.correlate(y, y, mode='full')
                autocorr = autocorr[autocorr.size // 2:]
                autocorr = autocorr / autocorr[0]  # Normalize
                
                # Find peaks for period estimation
                peaks = []
                for i in range(1, min(len(autocorr)-1, 1000)):
                    if autocorr[i] > autocorr[i-1] and autocorr[i] > autocorr[i+1] and autocorr[i] > 0.3:
                        peaks.append(autocorr[i])
                
                if peaks:
                    features['rpde'] = float(entropy(peaks) if len(peaks) > 1 else 0.0)
                else:
                    features['rpde'] = 0.0
            except:
                features['rpde'] = 0.0
            
            # 12. Detrended Fluctuation Analysis (DFA) - simplified implementation
            try:
                scales = [4, 8, 16, 32, 64]
                features['dfa'] = float(self.dfa(y, scales))
            except:
                features['dfa'] = 0.0
            
            # 13. Pitch Period Entropy (PPE)
            try:
                if len(f0_values) > 1:
                    periods = 1.0 / f0_values[f0_values > 0]
                    if len(periods) > 1:
                        features['ppe'] = float(entropy(periods))
                    else:
                        features['ppe'] = 0.0
                else:
                    features['ppe'] = 0.0
            except:
                features['ppe'] = 0.0
            
            # 14. Spectral centroid
            try:
                spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
                features['spectral_centroid'] = float(np.mean(spectral_centroids))
            except:
                features['spectral_centroid'] = 0.0
            
            # 15. Spectral flux
            try:
                stft = librosa.stft(y)
                magnitude = np.abs(stft)
                spectral_flux = np.mean(np.diff(magnitude, axis=1) ** 2)
                features['spectral_flux'] = float(spectral_flux)
            except:
                features['spectral_flux'] = 0.0
            
            # 16. Spectral roll-off
            try:
                rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
                features['spectral_rolloff'] = float(np.mean(rolloff))
            except:
                features['spectral_rolloff'] = 0.0
            
            # 17. Short-time energy
            try:
                frame_length = 2048
                hop_length = 512
                frames = librosa.util.frame(y, frame_length=frame_length, hop_length=hop_length)
                energy = np.sum(frames ** 2, axis=0)
                features['short_time_energy'] = float(np.mean(energy))
            except:
                features['short_time_energy'] = 0.0
            
            # 18. Duration of sustained phonation
            features['duration'] = float(len(y) / sr)
            
            # 19. Articulation rate (improved syllable detection)
            try:
                # Voice Activity Detection based approach
                frame_length = 2048
                hop_length = 512
                
                # Get RMS energy
                rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
                
                # Adaptive thresholding for voice activity
                rms_mean = np.mean(rms)
                rms_std = np.std(rms)
                threshold = rms_mean + 0.5 * rms_std
                
                # Find voiced segments
                voiced_frames = rms > threshold
                frame_times = librosa.frames_to_time(np.arange(len(voiced_frames)), sr=sr, hop_length=hop_length)
                
                # Count syllables using peak detection in voiced segments
                if np.sum(voiced_frames) > 0:
                    voiced_energy = rms * voiced_frames
                    from scipy.signal import find_peaks
                    peaks, _ = find_peaks(voiced_energy, height=threshold, distance=int(0.1 * sr / hop_length))
                    num_syllables = len(peaks)
                    features['articulation_rate'] = float(num_syllables / features['duration']) if features['duration'] > 0 else 0.0
                else:
                    features['articulation_rate'] = 0.0
            except:
                features['articulation_rate'] = 0.0
            
            # 20. Pause duration & frequency (improved VAD-based detection)
            try:
                # Voice Activity Detection
                frame_length = 2048
                hop_length = 512
                
                # Get multiple features for better VAD
                rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
                zcr = librosa.feature.zero_crossing_rate(y, frame_length=frame_length, hop_length=hop_length)[0]
                
                # Adaptive thresholding
                rms_threshold = 0.02 * np.max(rms)  # More robust threshold
                zcr_threshold = 0.15
                
                # Combined VAD decision
                voiced_frames = (rms > rms_threshold) & (zcr < zcr_threshold)
                
                # Find pauses (silent segments longer than 100ms)
                silent_frames = ~voiced_frames
                min_pause_duration = 0.1  # 100ms minimum pause
                min_pause_frames = int(min_pause_duration * sr / hop_length)
                
                # Group consecutive silent frames
                pause_segments = []
                current_start = None
                
                for i, is_silent in enumerate(silent_frames):
                    if is_silent and current_start is None:
                        current_start = i
                    elif not is_silent and current_start is not None:
                        pause_length = i - current_start
                        if pause_length >= min_pause_frames:
                            pause_duration = pause_length * hop_length / sr
                            pause_segments.append(pause_duration)
                        current_start = None
                
                # Handle case where recording ends with pause
                if current_start is not None:
                    pause_length = len(silent_frames) - current_start
                    if pause_length >= min_pause_frames:
                        pause_duration = pause_length * hop_length / sr
                        pause_segments.append(pause_duration)
                
                # Calculate pause statistics
                features['pause_frequency'] = float(len(pause_segments))
                features['pause_duration_mean'] = float(np.mean(pause_segments)) if pause_segments else 0.0
                features['pause_duration_total'] = float(np.sum(pause_segments)) if pause_segments else 0.0
                
            except:
                features['pause_frequency'] = 0.0
                features['pause_duration_mean'] = 0.0
                features['pause_duration_total'] = 0.0
            
            return features
            
        except Exception as e:
            print(f"Error in feature extraction: {str(e)}")
            return {}

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
        """Robust audio loading with format conversion"""
        try:
            # Try librosa first (handles most formats)
            y, sr = librosa.load(file_path, sr=None)
            return y, sr
        except Exception as e1:
            try:
                # Try soundfile for other formats
                y, sr = sf.read(file_path)
                return y, sr
            except Exception as e2:
                # Try parselmouth directly
                sound = parselmouth.Sound(file_path)
                y = sound.values[0]  # Get first channel
                sr = sound.sampling_frequency
                return y, sr
