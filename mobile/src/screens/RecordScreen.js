import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ActivityIndicator, Alert, ScrollView } from 'react-native';
import { Audio } from 'expo-av';
import { useAuth } from '../components/AuthProvider';
import { uploadAudio } from '../services/storageService';
import { Ionicons } from '@expo/vector-icons';

export default function RecordScreen({ navigation }) {
    const { user } = useAuth();
    const [recording, setRecording] = useState(null);
    const [isRecording, setIsRecording] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [recordedUri, setRecordedUri] = useState(null);
    const [duration, setDuration] = useState(0);
    const [sound, setSound] = useState(null);
    const [isPlaying, setIsPlaying] = useState(false);

    useEffect(() => {
        return () => {
            if (recording) {
                recording.stopAndUnloadAsync();
            }
            if (sound) {
                sound.unloadAsync();
            }
        };
    }, []);

    async function startRecording() {
        try {
            const permission = await Audio.requestPermissionsAsync();
            if (permission.status !== 'granted') {
                Alert.alert('Permission Denied', 'Microphone access is required to record audio.');
                return;
            }

            await Audio.setAudioModeAsync({
                allowsRecordingIOS: true,
                playsInSilentModeIOS: true,
            });

            const { recording } = await Audio.Recording.createAsync(
                Audio.RecordingOptionsPresets.HIGH_QUALITY
            );
            setRecording(recording);
            setIsRecording(true);
            setRecordedUri(null);
            setDuration(0);
        } catch (err) {
            console.error('Failed to start recording', err);
            Alert.alert('Error', 'Failed to start recording');
        }
    }

    async function stopRecording() {
        setIsRecording(false);
        try {
            await recording.stopAndUnloadAsync();
            const uri = recording.getURI();
            const status = await recording.getStatusAsync();
            setRecordedUri(uri);
            setDuration(status.durationMillis);
            setRecording(null);
        } catch (err) {
            console.error('Failed to stop recording', err);
        }
    }

    async function playSound() {
        if (recordedUri) {
            const { sound } = await Audio.Sound.createAsync({ uri: recordedUri });
            setSound(sound);
            setIsPlaying(true);
            await sound.playAsync();
            sound.setOnPlaybackStatusUpdate((status) => {
                if (status.didJustFinish) {
                    setIsPlaying(false);
                }
            });
        }
    }

    async function handleUpload() {
        if (!recordedUri) return;

        setUploading(true);
        try {
            await uploadAudio(recordedUri, user.uid, {
                duration: duration / 1000,
                device: 'Expo Device',
            });
            Alert.alert('Success', 'Recording uploaded successfully!');
            setRecordedUri(null);
            setDuration(0);
        } catch (err) {
            Alert.alert('Upload Failed', err.message);
        } finally {
            setUploading(false);
        }
    }

    return (
        <ScrollView contentContainerStyle={styles.container}>
            <Text style={styles.title}>Voice Collector</Text>
            <Text style={styles.instruction}>Press the button below to start recording your speech sample.</Text>

            <View style={styles.visualizerContainer}>
                {isRecording ? (
                    <ActivityIndicator size="large" color="#e74c3c" />
                ) : (
                    <Ionicons name="mic-outline" size={80} color="#bdc3c7" />
                )}
            </View>

            <View style={styles.timerContainer}>
                <Text style={styles.durationText}>
                    {isRecording ? 'RECORDING' : recordedUri ? 'SAVED' : 'READY'}
                </Text>
                <Text style={styles.timeText}>
                    {(duration / 1000).toFixed(1)}s
                </Text>
            </View>

            <TouchableOpacity
                style={[styles.recordButton, isRecording && styles.recordingActive]}
                onPress={isRecording ? stopRecording : startRecording}
                disabled={uploading}
            >
                <Ionicons
                    name={isRecording ? "stop" : "mic"}
                    size={40}
                    color="#fff"
                />
            </TouchableOpacity>

            {recordedUri && !isRecording && (
                <View style={styles.actionContainer}>
                    <TouchableOpacity
                        style={styles.playButton}
                        onPress={playSound}
                        disabled={isPlaying}
                    >
                        <Ionicons name={isPlaying ? "volume-high" : "play"} size={24} color="#3498db" />
                        <Text style={styles.playButtonText}>{isPlaying ? 'Playing...' : 'Preview'}</Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                        style={styles.uploadButton}
                        onPress={handleUpload}
                        disabled={uploading}
                    >
                        {uploading ? (
                            <ActivityIndicator color="#fff" />
                        ) : (
                            <>
                                <Ionicons name="cloud-upload" size={24} color="#fff" />
                                <Text style={styles.buttonText}>Upload Sample</Text>
                            </>
                        )}
                    </TouchableOpacity>
                </View>
            )}
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flexGrow: 1,
        padding: 30,
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#fff',
    },
    title: {
        fontSize: 32,
        fontWeight: 'bold',
        color: '#2c3e50',
        marginBottom: 10,
    },
    instruction: {
        fontSize: 16,
        color: '#7f8c8d',
        textAlign: 'center',
        marginBottom: 40,
    },
    visualizerContainer: {
        height: 150,
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 20,
    },
    timerContainer: {
        alignItems: 'center',
        marginBottom: 40,
    },
    durationText: {
        fontSize: 14,
        fontWeight: 'bold',
        color: '#95a5a6',
        letterSpacing: 2,
    },
    timeText: {
        fontSize: 64,
        fontWeight: '300',
        color: '#2c3e50',
    },
    recordButton: {
        width: 90,
        height: 90,
        borderRadius: 45,
        backgroundColor: '#e74c3c',
        alignItems: 'center',
        justifyContent: 'center',
        elevation: 5,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.3,
        shadowRadius: 5,
        marginBottom: 40,
    },
    recordingActive: {
        backgroundColor: '#c0392b',
        transform: [{ scale: 1.1 }],
    },
    actionContainer: {
        width: '100%',
        alignItems: 'center',
    },
    playButton: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 20,
        padding: 10,
    },
    playButtonText: {
        marginLeft: 8,
        color: '#3498db',
        fontSize: 18,
        fontWeight: '600',
    },
    uploadButton: {
        flexDirection: 'row',
        backgroundColor: '#2ecc71',
        paddingHorizontal: 30,
        paddingVertical: 18,
        borderRadius: 30,
        width: '100%',
        alignItems: 'center',
        justifyContent: 'center',
        elevation: 3,
    },
    buttonText: {
        color: '#fff',
        fontSize: 18,
        fontWeight: 'bold',
        marginLeft: 10,
    },
});
