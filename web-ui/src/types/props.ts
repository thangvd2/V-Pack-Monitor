import { User, Station } from './api';

export interface SetupModalProps {
  isOpen: boolean;
  onSaved: () => void;
  onCancel: () => void;
  currentStation?: any;
  isNewStation?: boolean;
  initialSettings?: any;
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
  storageInfo: any;
  currentUser: User;
  analytics: any;
}

export interface StationStatus {
  status: 'idle' | 'packing';
  waybill: string;
  processingCount: number;
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
}

export interface MtxFallbackProps {
  url: string;
  className?: string;
}
