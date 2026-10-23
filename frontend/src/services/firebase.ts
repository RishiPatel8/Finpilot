import { initializeApp, getApps, getApp } from 'firebase/app';
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  signOut as fbSignOut,
  UserCredential
} from 'firebase/auth';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || '',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || '',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || '',
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || '',
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || '',
};

export const isFirebaseConfigured = (): boolean => {
  return Boolean(
    firebaseConfig.apiKey &&
    firebaseConfig.projectId &&
    firebaseConfig.authDomain
  );
};

// Initialize Firebase only if config is present or on demand
export const app = getApps().length > 0
  ? getApp()
  : isFirebaseConfigured()
    ? initializeApp(firebaseConfig)
    : null;

export const auth = app ? getAuth(app) : null;
export const googleProvider = new GoogleAuthProvider();

export const signInWithGoogle = async (): Promise<string> => {
  if (!auth) {
    // Development fallback when Firebase credentials are not yet configured in .env
    // Returns a safe test mock token supported by backend
    const mockEmail = `google_user_${Math.floor(Math.random() * 900 + 100)}@gmail.com`;
    return `mock-firebase:g_${Date.now()}:${mockEmail}:Google Explorer`;
  }

  const result: UserCredential = await signInWithPopup(auth, googleProvider);
  const idToken = await result.user.getIdToken();
  return idToken;
};

export const signOutFirebase = async (): Promise<void> => {
  if (auth) {
    await fbSignOut(auth);
  }
};
