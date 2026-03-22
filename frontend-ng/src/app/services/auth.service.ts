import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import {
  getAuth,
  GoogleAuthProvider,
  onAuthStateChanged,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  sendPasswordResetEmail,
  signOut,
  User,
} from 'firebase/auth';
import { firebaseApp } from '../firebase.config';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private auth = getAuth(firebaseApp);
  readonly user$ = new BehaviorSubject<User | null>(null);

  constructor() {
    onAuthStateChanged(this.auth, user => this.user$.next(user));
  }

  signInWithGoogle(): Promise<void> {
    return signInWithPopup(this.auth, new GoogleAuthProvider()).then(() => {});
  }

  signInWithEmail(email: string, password: string): Promise<void> {
    return signInWithEmailAndPassword(this.auth, email, password).then(() => {});
  }

  signUpWithEmail(email: string, password: string): Promise<void> {
    return createUserWithEmailAndPassword(this.auth, email, password).then(() => {});
  }

  sendPasswordReset(email: string): Promise<void> {
    return sendPasswordResetEmail(this.auth, email);
  }

  signOut(): Promise<void> {
    return signOut(this.auth);
  }

  async getIdToken(): Promise<string | null> {
    const user = this.auth.currentUser;
    return user ? user.getIdToken() : null;
  }
}
