import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { AuthProvider, useAuth } from './src/components/AuthProvider';
import LoginScreen from './src/screens/LoginScreen';
import SignupScreen from './src/screens/SignupScreen';
import RecordScreen from './src/screens/RecordScreen';
import { ActivityIndicator, View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { logout } from './src/services/authService';

const Stack = createStackNavigator();

function DashboardScreen({ navigation }) {
    const { userProfile } = useAuth();

    return (
        <View style={styles.container}>
            <Text style={styles.welcomeText}>Welcome, {userProfile?.fullName || 'User'}!</Text>
            <Text style={styles.roleText}>Role: {userProfile?.role}</Text>

            <TouchableOpacity
                onPress={() => navigation.navigate('Record')}
                style={styles.recordButton}
            >
                <Text style={styles.buttonText}>Go to Recorder</Text>
            </TouchableOpacity>

            <TouchableOpacity
                onPress={logout}
                style={styles.logoutButton}
            >
                <Text style={styles.buttonText}>Logout</Text>
            </TouchableOpacity>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20, backgroundColor: '#f5f5f5' },
    welcomeText: { fontSize: 24, fontWeight: 'bold', color: '#2c3e50', marginBottom: 5 },
    roleText: { fontSize: 16, color: '#7f8c8d', marginBottom: 30 },
    recordButton: { backgroundColor: '#3498db', padding: 15, borderRadius: 10, width: '80%', alignItems: 'center', marginBottom: 15 },
    logoutButton: { backgroundColor: '#e74c3c', padding: 15, borderRadius: 10, width: '80%', alignItems: 'center' },
    buttonText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
});

function Navigation() {
    const { user, loading } = useAuth();

    if (loading) {
        return (
            <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
                <ActivityIndicator size="large" color="#3498db" />
            </View>
        );
    }

    return (
        <NavigationContainer>
            <Stack.Navigator>
                {user ? (
                    <>
                        <Stack.Screen name="Dashboard" component={DashboardScreen} options={{ title: 'SpeechSense' }} />
                        <Stack.Screen name="Record" component={RecordScreen} options={{ title: 'Record Speech' }} />
                    </>
                ) : (
                    <>
                        <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: false }} />
                        <Stack.Screen name="Signup" component={SignupScreen} options={{ headerShown: false }} />
                    </>
                )}
            </Stack.Navigator>
        </NavigationContainer>
    );
}

export default function App() {
    return (
        <AuthProvider>
            <Navigation />
        </AuthProvider>
    );
}
