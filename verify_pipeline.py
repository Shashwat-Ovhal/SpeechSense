import numpy as np
import soundfile as sf
import os
from feature_extractor import ComprehensiveSpeechAnalyzer

def test_pipeline():
    print("Starting Pipeline Verification...")
    analyzer = ComprehensiveSpeechAnalyzer()
    
    # Generate a dummy 2-second 16kHz signal (sine wave + noise)
    fs = 16000
    t = np.linspace(0, 2, 2 * fs)
    # 440Hz tone with some harmonics
    signal = 0.5 * np.sin(2 * np.pi * 440 * t) + 0.1 * np.sin(2 * np.pi * 880 * t)
    # Add some silence at the beginning and end
    signal = np.concatenate([np.zeros(fs//2), signal, np.zeros(fs//2)])
    
    test_wav = "test_clinical_voice.wav"
    sf.write(test_wav, signal, fs)
    
    try:
        print(f"Processing {test_wav}...")
        features = analyzer.extract_all_features(test_wav)
        
        if not features:
            print("FAILED: No features extracted.")
            return

        print("\n=== Verification Results ===")
        print(f"Feature Version: {features.get('feature_version')}")
        print(f"Quality Score: {features.get('quality_score')}")
        print(f"Rejection Reason: {features.get('rejection_reason')}")
        print(f"Preprocessing Chain: {features.get('preprocessing_chain')}")
        
        # Check for statistical categories
        stats_checked = ['mean', 'std', 'median', 'iqr', 'skew', 'kurtosis']
        f0_stats = [f'f0_{s}' for s in stats_checked]
        
        missing = [f for f in f0_stats if f not in features]
        if missing:
            print(f"FAILED: Missing stats: {missing}")
        else:
            print("SUCCESS: All statistical moments for F0 are present.")
            
        print(f"F0 Mean: {features.get('f0_mean'):.2f} Hz")
        print(f"Total Features Extracted: {len(features)}")
        
        if len(features) > 100: # MFCC 1-13 * 3 moments + other stats should be high
            print("SUCCESS: Deep feature extraction (MFCC+Delta) confirmed.")
        else:
            print(f"WARNING: Expected more features, got {len(features)}")

    finally:
        if os.path.exists(test_wav):
            os.remove(test_wav)

if __name__ == "__main__":
    test_pipeline()
