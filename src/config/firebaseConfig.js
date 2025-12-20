import { initializeApp } from "firebase/app";
import { initializeAuth, browserLocalPersistence } from "firebase/auth";
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

// Initialize Auth with browser persistence (works in Expo Go)
const auth = initializeAuth(app, {
    persistence: browserLocalPersistence
});

// Initialize and export services
const db = getFirestore(app);
const storage = getStorage(app);

export { auth, db, storage };
export default app;