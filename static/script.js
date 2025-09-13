// Parkinson's Disease Speech Analysis - JavaScript

let mediaRecorder = null;
let recordedChunks = [];
let isRecording = false;
let recordingStartTime = null;
let timerInterval = null;

// DOM Elements
const startBtn = document.getElementById('start-record-btn');
const stopBtn = document.getElementById('stop-record-btn');
const uploadBtn = document.getElementById('upload-btn');
const statusMessage = document.getElementById('status-message');
const timer = document.getElementById('recording-timer');
const audioPreview = document.getElementById('audio-preview');
const recordedAudio = document.getElementById('recorded-audio');
const resultsSection = document.getElementById('results-section');
const analysisResults = document.getElementById('analysis-results');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    checkMicrophonePermission();
});

function setupEventListeners() {
    startBtn.addEventListener('click', startRecording);
    stopBtn.addEventListener('click', stopRecording);
    uploadBtn.addEventListener('click', uploadAudio);
}

async function checkMicrophonePermission() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop()); // Stop the test stream
        updateStatus('Ready to record');
    } catch (error) {
        updateStatus('Microphone access required. Please grant permission and refresh the page.');
        console.error('Microphone permission denied:', error);
    }
}

async function startRecording() {
    try {
        // Validate form data
        if (!validateMetadata()) {
            return;
        }

        // Get media stream
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                sampleRate: 44100,
                channelCount: 1,
                echoCancellation: false,
                autoGainControl: false,
                noiseSuppression: false
            } 
        });

        // Setup MediaRecorder
        recordedChunks = [];
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: 'audio/webm;codecs=opus'
        });

        mediaRecorder.ondataavailable = function(event) {
            if (event.data.size > 0) {
                recordedChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = function() {
            stream.getTracks().forEach(track => track.stop());
            processRecording();
        };

        // Start recording
        mediaRecorder.start();
        isRecording = true;
        recordingStartTime = Date.now();
        
        // Update UI
        updateButtonStates();
        updateStatus('🔴 Recording... Speak clearly into your microphone');
        startBtn.classList.add('recording');
        startTimer();

    } catch (error) {
        console.error('Error starting recording:', error);
        updateStatus('Error accessing microphone. Please check permissions.');
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        stopTimer();
        
        // Update UI
        updateButtonStates();
        updateStatus('Recording stopped. Processing audio...');
        startBtn.classList.remove('recording');
    }
}

function processRecording() {
    if (recordedChunks.length === 0) {
        updateStatus('No audio recorded. Please try again.');
        return;
    }

    // Create blob from recorded chunks
    const blob = new Blob(recordedChunks, { type: 'audio/webm' });
    
    // Convert to WAV format (simplified - in real implementation you'd use a proper converter)
    convertToWav(blob).then(wavBlob => {
        // Create audio preview
        const audioUrl = URL.createObjectURL(wavBlob);
        recordedAudio.src = audioUrl;
        audioPreview.style.display = 'block';
        
        // Store the WAV blob for upload
        window.recordedWavBlob = wavBlob;
        
        updateStatus('Recording ready for upload');
        uploadBtn.disabled = false;
    });
}

async function convertToWav(webmBlob) {
    // This is a simplified conversion - in a real application,
    // you would use a proper audio conversion library
    return new Promise((resolve) => {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const fileReader = new FileReader();
        
        fileReader.onload = async function(e) {
            try {
                const arrayBuffer = e.target.result;
                const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
                
                // Convert to WAV
                const wavBuffer = audioBufferToWav(audioBuffer);
                const wavBlob = new Blob([wavBuffer], { type: 'audio/wav' });
                resolve(wavBlob);
            } catch (error) {
                console.error('Error converting audio:', error);
                // Fallback: use original blob
                resolve(webmBlob);
            }
        };
        
        fileReader.readAsArrayBuffer(webmBlob);
    });
}

function audioBufferToWav(buffer) {
    const length = buffer.length;
    const arrayBuffer = new ArrayBuffer(44 + length * 2);
    const view = new DataView(arrayBuffer);
    const channels = buffer.numberOfChannels;
    const sampleRate = buffer.sampleRate;
    
    // WAV header
    const writeString = (offset, string) => {
        for (let i = 0; i < string.length; i++) {
            view.setUint8(offset + i, string.charCodeAt(i));
        }
    };
    
    writeString(0, 'RIFF');
    view.setUint32(4, 36 + length * 2, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, channels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(36, 'data');
    view.setUint32(40, length * 2, true);
    
    // Convert audio data
    const channelData = buffer.getChannelData(0);
    let offset = 44;
    for (let i = 0; i < length; i++) {
        const sample = Math.max(-1, Math.min(1, channelData[i]));
        view.setInt16(offset, sample * 0x7FFF, true);
        offset += 2;
    }
    
    return arrayBuffer;
}

async function uploadAudio() {
    if (!window.recordedWavBlob) {
        updateStatus('No recording to upload');
        return;
    }

    if (!validateMetadata()) {
        return;
    }

    try {
        uploadBtn.disabled = true;
        updateStatus('Uploading and analyzing audio...');
        showLoadingSpinner();

        // Prepare form data
        const formData = new FormData();
        formData.append('audio', window.recordedWavBlob, 'recording.wav');
        
        // Collect metadata
        const metadata = {
            participant_id: document.getElementById('participant_id').value,
            phone_model: document.getElementById('phone_model').value,
            pd_status: document.getElementById('pd_status').value,
            recording_environment: document.getElementById('recording_environment').value,
            additional_notes: document.getElementById('additional_notes').value,
            timestamp: new Date().toISOString(),
            browser: navigator.userAgent,
            recording_duration: getRecordingDuration()
        };
        
        formData.append('metadata', JSON.stringify(metadata));

        // Upload to server
        const response = await fetch('/upload-audio', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok && result.success) {
            displayResults(result);
            updateStatus('Analysis complete! Results displayed below.');
        } else {
            throw new Error(result.error || 'Upload failed');
        }

    } catch (error) {
        console.error('Upload error:', error);
        updateStatus(`Upload failed: ${error.message}`);
        showErrorMessage(`Upload failed: ${error.message}`);
    } finally {
        hideLoadingSpinner();
        uploadBtn.disabled = false;
    }
}

function validateMetadata() {
    const requiredFields = ['participant_id', 'phone_model', 'pd_status', 'recording_environment'];
    const missingFields = [];

    for (const field of requiredFields) {
        const element = document.getElementById(field);
        if (!element.value.trim()) {
            missingFields.push(field.replace('_', ' '));
            element.style.borderColor = '#e74c3c';
        } else {
            element.style.borderColor = '#e1e8ed';
        }
    }

    if (missingFields.length > 0) {
        showErrorMessage(`Please fill in the following required fields: ${missingFields.join(', ')}`);
        return false;
    }

    return true;
}

function displayResults(result) {
    resultsSection.style.display = 'block';
    
    let resultsHtml = `
        <div class="success-message">
            <strong>Analysis Complete!</strong><br>
            Participant ID: ${result.participant_id}<br>
            Features extracted: ${result.features_extracted}
        </div>
        <div class="biomarkers-results">
            <h3>Extracted Acoustic Biomarkers</h3>
            <div class="features-list">
    `;

    // Group features by category for better display
    const featureCategories = {
        'Fundamental Features': ['f0_mean', 'f0_std', 'f0_min', 'f0_max', 'jitter_local', 'jitter_rap', 'jitter_ppq5', 'shimmer_local', 'shimmer_apq3', 'shimmer_apq5', 'hnr', 'nhr'],
        'Formant Features': ['f1_mean', 'f2_mean', 'f3_mean', 'f1_bandwidth', 'f2_bandwidth', 'f3_bandwidth'],
        'MFCC Features': Object.keys(result.acoustic_biomarkers).filter(key => key.startsWith('mfcc_')),
        'Spectral Features': ['spectral_centroid', 'spectral_flux', 'spectral_rolloff', 'short_time_energy'],
        'Advanced Features': ['rpde', 'dfa', 'ppe', 'intensity', 'voice_onset_time', 'duration', 'articulation_rate'],
        'Pause Analysis': ['pause_frequency', 'pause_duration_mean', 'pause_duration_total']
    };

    for (const [category, features] of Object.entries(featureCategories)) {
        resultsHtml += `<h4>${category}</h4><div class="category-features">`;
        
        for (const feature of features) {
            if (result.acoustic_biomarkers.hasOwnProperty(feature)) {
                const value = result.acoustic_biomarkers[feature];
                const displayValue = typeof value === 'number' ? value.toFixed(4) : value;
                resultsHtml += `
                    <div class="feature-result">
                        <span class="feature-name">${formatFeatureName(feature)}</span>
                        <span class="feature-value">${displayValue}</span>
                    </div>
                `;
            }
        }
        
        resultsHtml += `</div>`;
    }

    resultsHtml += `</div></div>`;
    analysisResults.innerHTML = resultsHtml;

    // Log to console for debugging
    console.log('Analysis Results:', result);
    console.log('Acoustic Biomarkers:', result.acoustic_biomarkers);
}

function formatFeatureName(feature) {
    return feature
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase())
        .replace('F0', 'F₀')
        .replace('F1', 'F₁')
        .replace('F2', 'F₂')
        .replace('F3', 'F₃')
        .replace('Hnr', 'HNR')
        .replace('Nhr', 'NHR')
        .replace('Rpde', 'RPDE')
        .replace('Dfa', 'DFA')
        .replace('Ppe', 'PPE')
        .replace('Mfcc', 'MFCC');
}

function updateButtonStates() {
    if (isRecording) {
        startBtn.disabled = true;
        stopBtn.disabled = false;
        uploadBtn.disabled = true;
    } else {
        startBtn.disabled = false;
        stopBtn.disabled = true;
        // uploadBtn state is managed by processRecording()
    }
}

function updateStatus(message) {
    statusMessage.textContent = message;
}

function startTimer() {
    timerInterval = setInterval(() => {
        if (recordingStartTime) {
            const elapsed = Date.now() - recordingStartTime;
            const seconds = Math.floor(elapsed / 1000);
            const minutes = Math.floor(seconds / 60);
            const displaySeconds = seconds % 60;
            timer.textContent = `${minutes.toString().padStart(2, '0')}:${displaySeconds.toString().padStart(2, '0')}`;
        }
    }, 1000);
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

function getRecordingDuration() {
    if (recordingStartTime) {
        return Math.floor((Date.now() - recordingStartTime) / 1000);
    }
    return 0;
}

function showLoadingSpinner() {
    const spinner = document.createElement('span');
    spinner.className = 'loading';
    spinner.id = 'loading-spinner';
    uploadBtn.insertBefore(spinner, uploadBtn.firstChild);
}

function hideLoadingSpinner() {
    const spinner = document.getElementById('loading-spinner');
    if (spinner) {
        spinner.remove();
    }
}

function showErrorMessage(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    // Insert before the results section
    resultsSection.parentNode.insertBefore(errorDiv, resultsSection);
    
    // Remove after 5 seconds
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.parentNode.removeChild(errorDiv);
        }
    }, 5000);
}

// Clear error messages when user starts typing
document.addEventListener('input', function(e) {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') {
        const errorMessages = document.querySelectorAll('.error-message');
        errorMessages.forEach(msg => {
            if (msg.parentNode) {
                msg.parentNode.removeChild(msg);
            }
        });
    }
});