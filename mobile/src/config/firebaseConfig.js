import { initializeApp } from "firebase/app";
import { initializeAuth, getReactNativePersistence } from "firebase/auth";
import ReactNativeAsyncStorage from '@react-native-async-storage/async-storage';
import { getFirestore } from "firebase/firestore";
import { getStorage } from "firebase/storage";

// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyCKajFVnXfCuidE4dqYwlZN9iS5YHFRqMU",
    authDomain: "speechsense-d09a7.firebaseapp.com",
    projectId: "speechsense-d09a7",
    storageBucket: "speechsense-d09a7.firebasestorage.app",
    messagingSenderId: "39411718118",
    appId: "1:39411718118:web:bd534db58acf73eb29e827"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Auth with React Native persistence
const auth = initializeAuth(app, {
    persistence: getReactNativePersistence(ReactNativeAsyncStorage)
});

// Initialize and export services
const db = getFirestore(app);
const storage = getStorage(app);

// Prevent auto-refresh issues in dev
if (__DEV__) {
    // Optional: Log to confirm init
    console.log("Firebase Auth Initialized with Config");
}

export { auth, db, storage };
export default app;