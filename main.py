import os
import tempfile
import numpy as np
import librosa
import parselmouth
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from datetime import datetime
import json
from scipy.stats import entropy
from scipy.signal import hilbert
from sklearn.feature_extraction.text import TfidfVectorizer
import warnings
import pandas as pd
import soundfile as sf
warnings.filterwarnings('ignore')

# Allowed file extensions for security
ALLOWED_EXTENSIONS = {'wav', 'webm', 'mp3', 'ogg', 'm4a'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit

app = Flask(__name__)

# Global dataset storage
dataset = {}

class ComprehensiveSpeechAnalyzer:
    def __init__(self):
        pass
    
    def extract_all_features(self, audio_path):
        """Extract all 20+ acoustic biomarkers from audio file"""
        try:
            # Load audio with robust loading
            y, sr = robust_audio_load(audio_path)
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
                def dfa(signal, scales):
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
                
                scales = [4, 8, 16, 32, 64]
                features['dfa'] = float(dfa(y, scales))
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
                frame_times = librosa.frames_to_time(np.arange(len(voiced_frames)), sr=sr, hop_length=hop_length)
                
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

# Initialize analyzer
analyzer = ComprehensiveSpeechAnalyzer()

# Create data storage directory
os.makedirs('data', exist_ok=True)
DATA_FILE = 'data/parkinson_speech_analysis.csv'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_to_csv(participant_id, metadata, acoustic_biomarkers):
    """Save analysis results to CSV file for persistent storage"""
    try:
        # Prepare row data
        row_data = {
            'participant_id': participant_id,
            'timestamp': datetime.now().isoformat(),
            'phone_model': metadata.get('phone_model', ''),
            'pd_status': metadata.get('pd_status', ''),
            'recording_environment': metadata.get('recording_environment', ''),
            'preferred_language': metadata.get('preferred_language', ''),
            'additional_notes': metadata.get('additional_notes', ''),
            'browser': metadata.get('browser', ''),
            'recording_duration': metadata.get('recording_duration', 0)
        }
        
        # Add all acoustic biomarkers
        row_data.update(acoustic_biomarkers)
        
        # Convert to DataFrame
        df_new = pd.DataFrame([row_data])
        
        # Append to existing file or create new one
        if os.path.exists(DATA_FILE):
            df_existing = pd.read_csv(DATA_FILE)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_combined = df_new
            
        # Save to CSV
        df_combined.to_csv(DATA_FILE, index=False)
        print(f"Data saved to {DATA_FILE}")
        
    except Exception as e:
        print(f"Error saving to CSV: {str(e)}")

def robust_audio_load(file_path):
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    try:
        # Check if audio file is present
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400
            
        # Validate file size
        audio_file.seek(0, 2)  # Seek to end
        file_size = audio_file.tell()
        audio_file.seek(0)  # Seek back to beginning
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': f'File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB'}), 400
        
        # Validate file type
        filename = secure_filename(audio_file.filename or 'audio.wav')
        if not allowed_file(filename):
            return jsonify({'error': f'File type not allowed. Allowed types: {ALLOWED_EXTENSIONS}'}), 400
        
        # Get metadata
        metadata_str = request.form.get('metadata', '{}')
        metadata = json.loads(metadata_str)
        
        participant_id = metadata.get('participant_id', 'unknown')
        
        # Save audio file temporarily with proper extension
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'wav'
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as temp_file:
            audio_file.save(temp_file.name)
            temp_audio_path = temp_file.name
        
        try:
            # Extract comprehensive acoustic biomarkers
            acoustic_biomarkers = analyzer.extract_all_features(temp_audio_path)
            
            # Print extracted features to console for debugging
            print(f"\n=== EXTRACTED ACOUSTIC BIOMARKERS ===")
            print(f"Participant ID: {participant_id}")
            print(f"Total features extracted: {len(acoustic_biomarkers)}")
            for feature, value in acoustic_biomarkers.items():
                print(f"{feature}: {value}")
            print(f"=====================================\n")
            
            # Store data in global dataset
            if participant_id not in dataset:
                dataset[participant_id] = []
            
            recording_data = {
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata,
                'acoustic_biomarkers': acoustic_biomarkers
            }
            
            dataset[participant_id].append(recording_data)
            
            # Save to persistent CSV storage
            save_to_csv(participant_id, metadata, acoustic_biomarkers)
            
            # Clean up temporary file
            os.unlink(temp_audio_path)
            
            return jsonify({
                'success': True,
                'message': 'Audio processed successfully',
                'participant_id': participant_id,
                'features_extracted': len(acoustic_biomarkers),
                'acoustic_biomarkers': acoustic_biomarkers,
                'csv_saved': True
            })
            
        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)
            raise e
            
    except Exception as e:
        return jsonify({'error': f'Error processing audio: {str(e)}'}), 500

@app.route('/get-dataset')
def get_dataset():
    """Get the current dataset for inspection"""
    return jsonify(dataset)

@app.route('/export-csv')
def export_csv():
    """Export the analysis results as CSV file for research use"""
    try:
        if os.path.exists(DATA_FILE):
            from flask import send_file
            return send_file(DATA_FILE, as_attachment=True, 
                           download_name='parkinson_speech_analysis.csv',
                           mimetype='text/csv')
        else:
            return jsonify({'error': 'No data available for export'}), 404
    except Exception as e:
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@app.route('/data-summary')
def data_summary():
    """Get summary statistics of collected data"""
    try:
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            summary = {
                'total_recordings': len(df),
                'unique_participants': df['participant_id'].nunique(),
                'pd_patients': len(df[df['pd_status'] == 'PD']),
                'control_patients': len(df[df['pd_status'] == 'Control']),
                'latest_recording': df['timestamp'].max() if not df.empty else None,
                'features_extracted': len([col for col in df.columns if col not in 
                    ['participant_id', 'timestamp', 'phone_model', 'pd_status', 
                     'recording_environment', 'preferred_language', 'additional_notes', 'browser', 'recording_duration']])
            }
            return jsonify(summary)
        else:
            return jsonify({'total_recordings': 0, 'unique_participants': 0})
    except Exception as e:
        return jsonify({'error': f'Summary failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)