import { Routes } from '@angular/router';
import { App } from './app';

export const routes: Routes = [
  { path: '', component: App },
  {
    path: 'support',
    loadComponent: () => import('./pages/support/support-page.component').then(m => m.SupportPageComponent),
  },
  {
    path: 'privacy',
    loadComponent: () => import('./pages/privacy/privacy-page.component').then(m => m.PrivacyPageComponent),
  },
  {
    path: 'terms',
    loadComponent: () => import('./pages/terms/terms-page.component').then(m => m.TermsPageComponent),
  },
  {
    path: 'scta',
    loadComponent: () => import('./pages/scta/scta-page.component').then(m => m.SctaPageComponent),
  },
  { path: '**', redirectTo: '' },
];
