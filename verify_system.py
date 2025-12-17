import os
import numpy as np
import feature_extractor
import sys

def test_feature_extraction():
    print("Testing Feature Extraction Module...")
    
    # Generate a dummy sine wave audio file
    import soundfile as sf
    sr = 44100
    t = np.linspace(0, 1, sr)
    # Generate a complex signal akin to voice: F0=120Hz + harmonics
    y = 0.5 * np.sin(2 * np.pi * 120 * t) + 0.3 * np.sin(2 * np.pi * 240 * t) + 0.1 * np.random.normal(0, 0.05, len(t))
    
    test_file = "test_audio.wav"
    sf.write(test_file, y, sr)
    
    try:
        analyzer = feature_extractor.ComprehensiveSpeechAnalyzer()
        features = analyzer.extract_all_features(test_file)
        
        # Verify key features exist
        required_keys = ['f0_mean', 'jitter_local', 'shimmer_local', 'hnr', 'mfcc_1', 'ppe']
        missing = [k for k in required_keys if k not in features]
        
        if missing:
            print(f"FAILED: Missing features: {missing}")
            return False
            
        print(f"SUCCESS: Extracted {len(features)} features.")
        print(f"F0 Mean: {features.get('f0_mean', 0):.2f} Hz (Expected ~120)")
        return True
        
    except Exception as e:
        print(f"FAILED: Exception during extraction: {e}")
        return False
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def test_env_setup():
    print("\nTesting Environment Setup...")
    from dotenv import load_dotenv
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("FAILED: SUPABASE_URL or SUPABASE_KEY missing in .env")
        return False
    
    print("SUCCESS: Environment variables found.")
    return True

if __name__ == "__main__":
    tests = [
        test_env_setup(),
        test_feature_extraction()
    ]
    
    if all(tests):
        print("\n=== SYSTEM VERIFICATION PASSED ===")
        sys.exit(0)
    else:
        print("\n=== SYSTEM VERIFICATION FAILED ===")
        sys.exit(1)
