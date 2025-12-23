import { supabase } from '../config/supabaseConfig';
import * as FileSystem from 'expo-file-system';
import { decode } from 'base64-arraybuffer';

export const uploadAudio = async (uri, userId, metadata) => {
    try {
        // 1. Read file as Base64 because Supabase react-native client needs ArrayBuffer or Blob
        // Expo doesn't support Blob perfectly yet without polyfills, but base64 to ArrayBuffer works reliable.
        const base64 = await FileSystem.readAsStringAsync(uri, {
            encoding: FileSystem.EncodingType.Base64,
        });

        const fileExt = uri.split('.').pop();
        const fileName = `${userId}/${Date.now()}.${fileExt}`;
        const filePath = fileName;

        // 2. Upload to 'audio_recordings' bucket
        const { data: uploadData, error: uploadError } = await supabase.storage
            .from('audio_recordings')
            .upload(filePath, decode(base64), {
                contentType: 'audio/wav', // Adjust if needed
                upsert: false
            });

        if (uploadError) {
            throw uploadError;
        }

        // 3. Get Public URL (if public) or just the path
        const { data: urlData } = supabase.storage
            .from('audio_recordings')
            .getPublicUrl(filePath);

        // 4. Create Record in DB 'recordings' table
        const { error: dbError } = await supabase
            .from('recordings')
            .insert({
                user_id: userId,
                audio_path: filePath,
                audio_url: urlData.publicUrl,
                duration_sec: metadata.duration,
                metadata: metadata, // store extra JSON
                created_at: new Date()
            });

        if (dbError) throw dbError;

        return { path: filePath, url: urlData.publicUrl };

    } catch (error) {
        console.error("Upload Error:", error);
        throw error;
    }
};
