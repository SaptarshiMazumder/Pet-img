import { Injectable, inject } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { firstValueFrom } from 'rxjs';
import { AuthService as Auth0Service, User } from '@auth0/auth0-angular';

export { User };

@Injectable({ providedIn: 'root' })
export class AuthService {
  readonly user$ = new BehaviorSubject<User | null>(null);

  private auth0 = inject(Auth0Service);

  constructor() {
    this.auth0.user$.subscribe(user => this.user$.next(user ?? null));
  }

  signInWithGoogle(): Promise<void> {
    return firstValueFrom(
      this.auth0.loginWithRedirect({ authorizationParams: { connection: 'google-oauth2' } })
    );
  }

  signInWithEmail(email: string, _password: string): Promise<void> {
    return firstValueFrom(
      this.auth0.loginWithRedirect({ authorizationParams: { login_hint: email } })
    );
  }

  signUpWithEmail(_email: string, _password: string): Promise<void> {
    return firstValueFrom(
      this.auth0.loginWithRedirect({ authorizationParams: { screen_hint: 'signup' } })
    );
  }

  sendPasswordReset(_email: string): Promise<void> {
    return firstValueFrom(this.auth0.loginWithRedirect());
  }

  signOut(): Promise<void> {
    this.auth0.logout({ logoutParams: { returnTo: window.location.origin } });
    return Promise.resolve();
  }

  async getIdToken(): Promise<string | null> {
    try {
      const claims = await firstValueFrom(this.auth0.idTokenClaims$);
      return (claims as any)?.__raw ?? null;
    } catch {
      return null;
    }
  }
}
