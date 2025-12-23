from audio_processing.features import extract_features

class ComprehensiveSpeechAnalyzer:
    """
    Main interface for Speech Analysis.
    Wraps the logic in audio_processing/features.py
    """
    def __init__(self):
        pass

    def extract_all_features(self, audio_path):
        """
        Runs the full feature extraction pipeline.
        """
        print(f"Analyzing: {audio_path}")
        results = extract_features(audio_path)
        return results
