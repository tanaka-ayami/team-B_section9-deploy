import { initializeApp, getApps, getApp } from "firebase/app";
import {
  getAuth,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  sendPasswordResetEmail,
  onIdTokenChanged,
  type User,
} from "firebase/auth";

const firebaseConfig = {
  apiKey:            process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain:        process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId:         process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket:     process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId:             process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

const app = getApps().length ? getApp() : initializeApp(firebaseConfig);
export const auth = getAuth(app);

export const loginWithEmail = (email: string, password: string) =>
  signInWithEmailAndPassword(auth, email, password);

export const registerWithEmail = (email: string, password: string) =>
  createUserWithEmailAndPassword(auth, email, password);

export const logout = () => signOut(auth);

export const resetPassword = (email: string) =>
  sendPasswordResetEmail(auth, email);

export const getIdToken = async (): Promise<string | null> => {
  const user = auth.currentUser;
  if (!user) return null;
  return user.getIdToken();
};

export const subscribeIdToken = (callback: (token: string | null) => void) =>
  onIdTokenChanged(auth, async (user: User | null) => {
    if (!user) { callback(null); return; }
    callback(await user.getIdToken());
  });

export default app;


// // 開発用モック（Firebase キー設定後に元に戻す）
// export const auth = {} as any;

// export const loginWithEmail = async (_email: string, _password: string) => {};
// export const registerWithEmail = async (_email: string, _password: string) => {};
// export const logout = async () => {};
// export const resetPassword = async (_email: string) => {};
// export const getIdToken = async (): Promise<string | null> => null;
// export const subscribeIdToken = (_callback: (token: string | null) => void) => () => {};

// export default {};