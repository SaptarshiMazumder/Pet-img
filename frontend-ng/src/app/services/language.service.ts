import { Injectable, signal, computed } from '@angular/core';
import { TRANSLATIONS, Lang, T } from '../i18n/translations';

@Injectable({ providedIn: 'root' })
export class LanguageService {
  readonly lang = signal<Lang>((localStorage.getItem('pg_lang') as Lang) || 'en');
  readonly t = computed<T>(() => TRANSLATIONS[this.lang()]);

  toggle(): void {
    const next: Lang = this.lang() === 'en' ? 'ja' : 'en';
    this.lang.set(next);
    localStorage.setItem('pg_lang', next);
  }

  templateName(tpl: any): string {
    if (!tpl) return '';
    return this.lang() === 'ja' && tpl.name_ja ? tpl.name_ja : (tpl.name ?? '');
  }

  orderPortraits(n: number): string {
    if (this.lang() === 'ja') return `${n}点を注文`;
    return `Order ${n} portrait${n > 1 ? 's' : ''}`;
  }
}
