import { User, Station, Settings, StorageInfo, AnalyticsInfo } from './api';

export interface SetupModalProps {
  isOpen: boolean;
  onSaved: () => void;
  onCancel: () => void;
  currentStation?: Station | null;
  isNewStation?: boolean;
  initialSettings?: Settings | null;
}

export interface UserManagementModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: User | null;
  showConfirmDialog: (message: string, onConfirm: () => void) => void;
}

export interface VideoPlayerModalProps {
  isOpen: boolean;
  onClose: () => void;
  videoUrl: string;
  waybillCode: string;
}

export interface DashboardProps {
  stations: Station[];
  activeStationId: number | null | 'orphaned';
  storageInfo: StorageInfo | null;
  currentUser: User;
  analytics: AnalyticsInfo | null;
}

export interface StationStatus {
  status: 'idle' | 'packing';
  waybill: string;
  processingCount: number;
  station_id?: number;
  occupied?: boolean;
  occupied_by?: string;
  occupied_by_name?: string;
}

export interface ReconnectInfo {
  station_id: number;
  status: 'searching' | 'found';
  new_ip?: string;
}

export interface AdminDashboardProps {
  stations: Station[];
  stationStatuses: Record<number, StationStatus>;
  reconnectInfo: ReconnectInfo | null;
  mtxAvailable: boolean;
  isDualCamStation: (station: Station) => boolean;
  MTX_HOST: string;
  onStationClick: (stationId: number) => void;
}

export interface SystemHealthProps {
  currentUser: User;
  stations: Station[];
}

