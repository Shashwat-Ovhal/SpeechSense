import { ref, uploadBytes, getDownloadURL } from "firebase/storage";
import { collection, addDoc, serverTimestamp } from "firebase/firestore";
import { storage, db } from "../config/firebaseConfig";

export const uploadAudio = async (uri, userId, metadata) => {
    try {
        // 1. Create a reference to the file in Firebase Storage
        const response = await fetch(uri);
        const blob = await response.blob();
        const filename = `recordings/${userId}/${Date.now()}.m4a`;
        const storageRef = ref(storage, filename);

        // 2. Upload the file
        await uploadBytes(storageRef, blob);

        // 3. Get the download URL
        const downloadURL = await getDownloadURL(storageRef);

        // 4. Save metadata to Firestore
        const docRef = await addDoc(collection(db, "speech_records"), {
            userId,
            audioUrl: downloadURL,
            storagePath: filename,
            duration: metadata.duration,
            timestamp: serverTimestamp(),
            metadata: {
                device: metadata.device || "unknown",
                ...metadata
            }
        });

        return { id: docRef.id, url: downloadURL };
    } catch (error) {
        console.error("Error uploading audio:", error);
        throw error;
    }
};
