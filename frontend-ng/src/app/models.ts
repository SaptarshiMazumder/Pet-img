export interface GalleryEntry {
  job_id: string;
  template_key: string;
  style_key: string;
  presigned_url: string | null;
  source_url: string | null;
  seed: number | null;
  created_at: string | null;
  orientation?: 'portrait' | 'landscape';
  unlocked?: boolean;
}

export interface CreditPack {
  pack_id: string;
  credits: number;
  price_usd: number;
  label: string;
}

export interface OrderForm {
  firstName: string;
  lastName: string;
  addressLine1: string;
  addressLine2: string;
  city: string;
  postCode: string;
  country: string;
  email: string;
  phone: string;
  product_uid: string;
  quantity: number;
  order_type: 'draft' | 'order';
}

export interface JobEntry {
  job_id: string;
  template_key: string;
  style_key: string;
  status: 'pending' | 'processing' | 'fixing' | 'completed' | 'failed';
  presigned_url?: string;
  positive_prompt?: string;
  seed?: number;
  error?: string;
  duration_seconds?: number;
  submitted_at: Date;
  orientation?: 'portrait' | 'landscape';
  unlocked?: boolean;
}

export interface ExpandedItem {
  job_id: string;
  presigned_url: string;
  positive_prompt?: string;
  template_key: string;
  style_key: string;
  isSample?: boolean;
  orientation?: 'portrait' | 'landscape';
  unlocked?: boolean;
}

export interface SampleEntry {
  sample_id: string;
  presigned_url: string | null;
}

export interface OrderItem {
  job_id: string;
  presigned_url: string | null;
  template_key: string;
  category?: string;
  size: string;
  color?: string;
  orientation?: string;
  quantity: number;
}

export interface ShippingAddress {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  addressLine1: string;
  addressLine2: string;
  city: string;
  postCode: string;
  country: string;
}

export interface Order {
  id: string;
  items: OrderItem[];
  shipping: ShippingAddress;
  notes: string;
  status: 'draft' | 'submitted';
  created_at: string | null;
  submitted_at: string | null;
}
