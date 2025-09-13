# Parkinson's Disease Speech Analysis Prototype

## Project Overview
A comprehensive web-based prototype for collecting and analyzing speech data to detect Parkinson's Disease (PD). The system extracts 20+ acoustic biomarkers from voice recordings and stores them in numerical format for research and analysis.

## Current State
✅ **COMPLETED** - Full functional prototype ready for use

## Recent Changes (September 13, 2025)
- **Backend**: Created Flask server with comprehensive feature extraction using Parselmouth and librosa
- **Frontend**: Implemented web-based audio recording interface with medical-grade styling  
- **Features**: Successfully extracting all 20+ acoustic biomarkers as specified:
  - Fundamental frequency (F0/Pitch) analysis with statistical measures
  - Jitter and Shimmer calculations (cycle-to-cycle variations)  
  - Harmonics-to-Noise Ratio (HNR) and Noise-to-Harmonics Ratio (NHR)
  - Formant frequency analysis (F1, F2, F3) with bandwidths
  - Voice intensity/loudness and voice onset time measurements
  - MFCC (Mel-Frequency Cepstral Coefficients) extraction
  - Advanced entropy measures (RPDE, PPE)
  - Spectral features (centroid, flux, roll-off, short-time energy)
  - Detrended Fluctuation Analysis (DFA) implementation
  - Duration and articulation rate analysis  
  - Pause detection and frequency analysis

## Project Architecture

### Backend (main.py)
- Flask web server running on port 5000
- ComprehensiveSpeechAnalyzer class for feature extraction
- Global dataset dictionary for in-memory storage
- Endpoints: `/` (main page), `/upload-audio` (processing), `/get-dataset` (data retrieval)

### Frontend
- **HTML** (templates/index.html): Clean interface with metadata form and recording controls
- **CSS** (static/style.css): Medical-grade styling with responsive design
- **JavaScript** (static/script.js): Web Audio API integration, MediaRecorder, and file upload

### Dependencies
- **Backend**: Flask, parselmouth, librosa, numpy, scipy, scikit-learn, werkzeug
- **Frontend**: Vanilla JavaScript with Web Audio API and MediaRecorder API

## Data Structure
```python
dataset = {
    "participant_001": [
        {
            "timestamp": "2024-01-01T10:30:00",
            "metadata": {
                "phone_model": "iPhone 12",
                "recording_environment": "quiet_room", 
                "pd_status": "PD"
            },
            "acoustic_biomarkers": {
                "f0_mean": 115.7,      # All 20+ features stored as numerical values
                "jitter_local": 0.018,
                "shimmer_local": 0.052,
                # ... (complete feature set)
            }
        }
    ]
}
```

## User Workflow
1. Fill participant metadata (ID, device, PD status, environment)
2. Click "Start Recording" and speak into microphone
3. Click "Stop Recording" when finished
4. Review audio preview
5. Click "Upload & Analyze" to process and extract all biomarkers
6. View comprehensive results with all 20+ numerical features

## Technical Features
- Real-time audio recording with Web Audio API
- Comprehensive acoustic analysis using Parselmouth (Praat wrapper) and librosa
- Medical-grade interface design optimized for clinical use
- Responsive design for various screen sizes
- Error handling and validation throughout the pipeline
- Console logging for debugging and research purposes

## Ready for Research Use
The prototype successfully extracts all requested acoustic biomarkers in numerical format, making it ready for integration into Parkinson's disease research datasets and machine learning pipelines.