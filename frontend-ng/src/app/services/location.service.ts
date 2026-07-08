import { Injectable, inject, signal, computed } from '@angular/core';
import { LanguageService } from './language.service';
import { ApiService } from './api.service';
import { Lang } from '../i18n/translations';

export type Region = 'IN' | 'JP' | 'GENERAL';
export type Currency = 'INR' | 'JPY' | 'USD';

export interface RegionConfig {
  region: Region;
  currency: Currency;
  currencySymbol: string;
  shippingSupported: boolean;
  defaultLang: Lang;
}

const REGION_MAP: Record<Region, RegionConfig> = {
  IN: { region: 'IN', currency: 'INR', currencySymbol: '₹', shippingSupported: true, defaultLang: 'en' },
  JP: { region: 'JP', currency: 'JPY', currencySymbol: '¥', shippingSupported: true, defaultLang: 'ja' },
  GENERAL: { region: 'GENERAL', currency: 'USD', currencySymbol: '$', shippingSupported: false, defaultLang: 'en' },
};

const STORAGE_KEY = 'pg_region';
const STORAGE_TS_KEY = 'pg_region_ts';
const CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours
const SUPPORTED_SHIPPING_COUNTRY_ALIASES = new Set([
  'IN',
  'IND',
  'INDIA',
  'JP',
  'JPN',
  'JAPAN',
  '日本',
  'インド',
]);

function countryToRegion(country: string): Region {
  switch (country) {
    case 'IN': return 'IN';
    case 'JP': return 'JP';
    default: return 'GENERAL';
  }
}

@Injectable({ providedIn: 'root' })
export class LocationService {
  private readonly langService = inject(LanguageService);
  private readonly api = inject(ApiService);

  readonly region = signal<Region>(this.loadCachedRegion());
  readonly config = computed<RegionConfig>(() => REGION_MAP[this.region()]);

  detect(): void {
    const cachedRaw = localStorage.getItem(STORAGE_KEY) as Region | null;
    const cached = cachedRaw === 'IN' || cachedRaw === 'JP' ? cachedRaw : null;
    const ts = Number(localStorage.getItem(STORAGE_TS_KEY) || '0');
    const isFresh = cached && (Date.now() - ts) < CACHE_TTL_MS;

    if (isFresh) {
      // Already loaded from cache in signal init — nothing to do
      return;
    }

    this.api.detectGeo().subscribe({
      next: (resp) => {
        const region = countryToRegion(resp.country);
        this.region.set(region);
        if (region === 'GENERAL') {
          localStorage.removeItem(STORAGE_KEY);
          localStorage.removeItem(STORAGE_TS_KEY);
        } else {
          localStorage.setItem(STORAGE_KEY, region);
          localStorage.setItem(STORAGE_TS_KEY, String(Date.now()));
        }

        // Auto-set language on first detection only (not when loading from cache)
        if (!cached) {
          this.langService.setLang(REGION_MAP[region].defaultLang);
        }
      },
      error: () => {
        // On failure, default to GENERAL (safest: USD, no shipping)
        this.region.set('GENERAL');
        localStorage.removeItem(STORAGE_KEY);
        localStorage.removeItem(STORAGE_TS_KEY);
      },
    });
  }

  formatPrice(amount: number): string {
    const c = this.config();
    return `${c.currencySymbol}${amount.toLocaleString()}`;
  }

  hasUnsupportedShippingCountry(country: string | null | undefined): boolean {
    const normalized = this.normalizeCountry(country);
    if (!normalized) {
      return false;
    }
    return !SUPPORTED_SHIPPING_COUNTRY_ALIASES.has(normalized);
  }

  private loadCachedRegion(): Region {
    const cached = localStorage.getItem(STORAGE_KEY) as Region | null;
    if (cached && (cached === 'IN' || cached === 'JP')) {
      return cached;
    }
    return 'GENERAL';
  }

  private normalizeCountry(country: string | null | undefined): string {
    return (country ?? '').trim().toUpperCase();
  }
}
