export interface Station {
  id: number;
  name: string;
  ip: string;
  brand: string;
  camera_mode: string;
  rtsp_url_1?: string;
  rtsp_url_2?: string;
  is_active?: boolean;
}

export interface Record {
  id: number;
  waybill_code: string;
  status: 'READY' | 'RECORDING' | 'PROCESSING' | 'FAILED' | 'COMPLETED';
  station_id: number;
  created_at: string;
  file_path_1?: string;
  file_path_2?: string;
}

export interface User {
  id: number;
  username: string;
  role: 'ADMIN' | 'OPERATOR';
  full_name?: string;
}
