import { supabase } from '../config/supabaseConfig';

export const signup = async (email, password, fullName, role = 'patient') => {
    try {
        // 1. Sign up/Create Auth User
        const { data, error } = await supabase.auth.signUp({
            email,
            password,
            options: {
                data: {
                    full_name: fullName,
                    role: role,
                }
            }
        });

        if (error) throw error;

        if (!data.user) {
            throw new Error("Signup successful but user not created");
        }

        // Profile creation is handled by Supabase Database Triggers (setup_triggers.sql)
        // This prevents RLS (Permission) errors on the client side.

        return data.user;
    } catch (error) {
        throw error;
    }
};

export const login = async (email, password) => {
    try {
        const { data, error } = await supabase.auth.signInWithPassword({
            email,
            password,
        });
        if (error) throw error;
        return data.user;
    } catch (error) {
        throw error;
    }
};

export const logout = async () => {
    try {
        const { error } = await supabase.auth.signOut();
        if (error) throw error;
    } catch (error) {
        throw error;
    }
};

export const getUserProfile = async (uid) => {
    try {
        const { data, error } = await supabase
            .from('profiles')
            .select('*')
            .eq('id', uid)
            .single();

        if (error) return null;
        return data;
    } catch (error) {
        throw error;
    }
};
