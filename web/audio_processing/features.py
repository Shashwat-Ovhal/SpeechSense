import numpy as np
import librosa
from scipy.signal import medfilt

def extract_features(audio_path):
    """
    Extracts acoustic features from an audio file.
    """
    try:
        # Load audio (downsample to 16kHz for consistency)
        y, sr = librosa.load(audio_path, sr=16000)
        
        # 1. Pitch (F0)
        # using pYIN to estimate fundamental frequency
        f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
        
        # Filter out unvoiced parts (where f0 is NaN)
        f0 = f0[~np.isnan(f0)]
        
        if len(f0) == 0:
            return {
                "status": "failed",
                "reason": "No voice detected"
            }

        mean_f0 = np.mean(f0)
        std_f0 = np.std(f0)
        
        # 2. Jitter (Local)
        # Jitter is the cycle-to-cycle variation of fundamental frequency
        jitter = 0
        if len(f0) > 1:
            # Calculate absolute difference between consecutive periods
            # (Approximated using F0)
            avg_abs_diff = np.mean(np.abs(np.diff(f0)))
            jitter = avg_abs_diff / mean_f0 if mean_f0 > 0 else 0

        # 3. Shimmer (Local)
        # Shimmer is the cycle-to-cycle variation of amplitude
        # We need the RMS energy of frames corresponding to pitch periods.
        # This is complex to do perfectly without raw Glottal Pulse data, 
        # so we approximate using frame-based RMS energy.
        hop_length = int(sr / mean_f0) if mean_f0 > 0 else 512
        rms = librosa.feature.rms(y=y, frame_length=hop_length * 2, hop_length=hop_length)[0]
        
        shimmer = 0
        if len(rms) > 1:
             avg_abs_diff_amp = np.mean(np.abs(np.diff(rms)))
             mean_amp = np.mean(rms)
             shimmer = avg_abs_diff_amp / mean_amp if mean_amp > 0 else 0

        # 4. HNR (Harmonics-to-Noise Ratio)
        # A simple approximation using autocorrelation
        # (For production, consider using 'parselmouth' which wraps PRAAT)
        hnr = 20 * np.log10(mean_f0 / (std_f0 + 1e-6)) # Very rough heuristic
        # Let's trust standard metrics instead if available, but librosa doesn't have direct HNR.
        # We'll stick to basic stats for MVP.

        return {
            "status": "success",
            "mean_f0": float(mean_f0),
            "std_f0": float(std_f0),
            "jitter_local": float(jitter),
            "shimmer_local": float(shimmer),
            "hnr_approx": float(hnr),
            "duration": len(y) / sr
        }

    except Exception as e:
        return {
            "status": "error",
            "error_msg": str(e)
        }
