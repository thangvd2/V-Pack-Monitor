export interface Station {
  id: number;
  name: string;
  ip_camera_1: string;
  camera_brand: string;
  camera_mode: string;
  ip_camera_2?: string;
  safety_code?: string;
  mac_address?: string;
  processing_count?: number;
}

export interface PackingRecord {
  id: number;
  waybill_code: string;
  status: 'READY' | 'RECORDING' | 'PROCESSING' | 'FAILED' | 'COMPLETED' | 'DELETED';
  station_id: number;
  recorded_at: string;
  video_paths: string[];
  record_mode?: string;
  duration?: number;
  station_name?: string;
}

export interface User {
  id: number;
  username: string;
  role: 'ADMIN' | 'OPERATOR';
  full_name?: string;
  is_active?: boolean;
  must_change_password?: number;
}

export interface Settings {
  RECORD_KEEP_DAYS?: number;
  RECORD_STREAM_TYPE?: string;
  CLOUD_PROVIDER?: string;
  GDRIVE_FOLDER_ID?: string;
  S3_ENDPOINT?: string;
  S3_ACCESS_KEY?: string;
  S3_SECRET_KEY?: string;
  S3_BUCKET_NAME?: string;
  TELEGRAM_BOT_TOKEN?: string;
  TELEGRAM_CHAT_ID?: string;
}

export interface StorageInfo {
  size_str: string;
  file_count: number;
}

export interface AnalyticsInfo {
  total_today: number;
  station_today: number;
}
