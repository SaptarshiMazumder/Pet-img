import { Component, EventEmitter, Output, inject } from '@angular/core';
import { AuthService } from '../../services/auth.service';
import { LanguageService } from '../../services/language.service';

@Component({
  selector: 'app-auth-modal',
  standalone: true,
  imports: [],
  templateUrl: './auth-modal.component.html',
  styleUrl: './auth-modal.component.css',
})
export class AuthModalComponent {
  @Output() closed = new EventEmitter<void>();

  protected readonly auth = inject(AuthService);
  protected readonly lang = inject(LanguageService);

  signIn() {
    this.auth.signInWithEmail('', '');
  }

  signUp() {
    this.auth.signUpWithEmail('', '');
  }

  googleSignIn() {
    this.auth.signInWithGoogle();
  }
}
