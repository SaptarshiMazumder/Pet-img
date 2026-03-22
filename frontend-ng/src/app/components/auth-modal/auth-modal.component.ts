import { Component, EventEmitter, Output, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth.service';
import { LanguageService } from '../../services/language.service';

@Component({
  selector: 'app-auth-modal',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './auth-modal.component.html',
  styleUrl: './auth-modal.component.css',
})
export class AuthModalComponent {
  @Output() closed = new EventEmitter<void>();

  protected readonly auth = inject(AuthService);
  protected readonly lang = inject(LanguageService);

  mode: 'signin' | 'signup' | 'reset' = 'signin';
  email = '';
  password = '';
  confirmPassword = '';
  submitting = false;
  error = '';
  resetSent = false;

  async submitEmail() {
    this.error = '';
    if (this.mode === 'signup' && this.password !== this.confirmPassword) {
      this.error = this.lang.t().auth.passwordMismatch;
      return;
    }
    this.submitting = true;
    try {
      if (this.mode === 'signin') {
        await this.auth.signInWithEmail(this.email, this.password);
      } else {
        await this.auth.signUpWithEmail(this.email, this.password);
      }
      this.closed.emit();
    } catch (e: any) {
      this.error = this.friendlyError(e?.code);
    } finally {
      this.submitting = false;
    }
  }

  async sendReset() {
    if (!this.email) { this.error = 'Enter your email address first.'; return; }
    this.error = '';
    this.submitting = true;
    try {
      await this.auth.sendPasswordReset(this.email);
      this.resetSent = true;
    } catch (e: any) {
      this.error = this.friendlyError(e?.code);
    } finally {
      this.submitting = false;
    }
  }

  async googleSignIn() {
    this.error = '';
    try {
      await this.auth.signInWithGoogle();
      this.closed.emit();
    } catch (e: any) {
      this.error = this.friendlyError(e?.code);
    }
  }

  private friendlyError(code: string): string {
    const map: Record<string, string> = {
      'auth/invalid-credential':    'Incorrect email or password.',
      'auth/user-not-found':        'No account found with this email.',
      'auth/wrong-password':        'Incorrect password.',
      'auth/email-already-in-use':  'An account with this email already exists.',
      'auth/weak-password':         'Password must be at least 6 characters.',
      'auth/invalid-email':         'Please enter a valid email address.',
      'auth/too-many-requests':     'Too many attempts. Please try again later.',
      'auth/popup-closed-by-user':  '',
    };
    return map[code] ?? 'Something went wrong. Please try again.';
  }
}
