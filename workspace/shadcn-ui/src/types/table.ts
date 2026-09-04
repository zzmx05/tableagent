// 核心类型定义

export interface TableProcessSpec {
  select?: string[];
  rename?: Record<string, string>;
  cast?: Record<string, string>;
  missing?: {
    strategy: 'drop' | 'fill_const' | 'fill_mean' | 'fill_median' | 'fill_mode';
    value?: string | number;
  };
  filter?: string;
}

export interface ColumnSchema {
  name: string;
  type: string;
  nullRate: number;
  uniqueCount: number;
  selected: boolean;
}

export interface DatasetMeta {
  datasetId: string;
  fileName: string;
  fileSize: number;
  rows: number;
  columns: number;
  sheets?: string[];
  encoding: string;
  delimiter?: string;
  hasHeader: boolean;
  fingerprint: string;
  uploadedAt: string;
}

export interface DatasetProfile {
  datasetId: string;
  schema: ColumnSchema[];
  previewRows: (string | number | null)[][];
  statistics: Record<string, string | number>;
}

export interface RunSummary {
  runId: string;
  status: 'pending' | 'running' | 'success' | 'error';
  progress: number;
  inputRows: number;
  outputRows: number;
  affectedColumns: string[];
  missingChanges: Array<{ column: string; before: number; after: number }>;
  errorCode?: string;
  errorMessage?: string;
  startedAt: string;
  completedAt?: string;
}

export interface FlowData {
  flowId: string;
  name: string;
  spec: TableProcessSpec;
  datasetMeta: DatasetMeta;
  previewSample?: (string | number | null)[][];
  conversationSummary?: string;
  createdAt: string;
  updatedAt: string;
}

export type MessageType = 'chat' | 'execute' | 'fix';

export interface Message {
  id: string;
  type: MessageType;
  content: string;
  timestamp: string;
  
  // For execute messages
  spec?: TableProcessSpec;
  impact?: {
    affectedColumns?: number;
    estimatedRowsDeleted?: number;
    description?: string;
  };
  
  // For fix messages
  targetError?: string;
  patch?: Partial<TableProcessSpec>;
  diff?: Array<{ path: string; before: string | number | null; after: string | number | null }>;
  
  // For chat messages
  statistics?: Record<string, string | number | Record<string, number>>;
  suggestions?: string[];
  
  // Metadata
  source?: string; // 'manual' | 'execute #N' | 'fix #M'
  starred?: boolean;
}

export interface AppState {
  // Current dataset
  currentDataset: DatasetMeta | null;
  currentProfile: DatasetProfile | null;
  
  // Process parameters
  processSpec: TableProcessSpec;
  specHistory: Array<{ spec: TableProcessSpec; timestamp: string; source: string }>;
  
  // Run state
  currentRun: RunSummary | null;
  runHistory: RunSummary[];
  
  // Preview data
  originalPreview: (string | number | null)[][];
  processedPreview: (string | number | null)[][];
  
  // Messages
  messages: Message[];
  
  // Flows
  savedFlows: FlowData[];
  
  // UI state
  assistantCollapsed: boolean;
  currentTab: 'flows' | 'upload' | 'prepare' | 'export';
  prepareSubTab: 'params' | 'preview';
  showDiffOnly: boolean;
  
  // Settings
  dataExternalEnabled: boolean;
}

export interface UploadOptions {
  encoding: string;
  delimiter: string;
  hasHeader: boolean;
}

export interface ExportOptions {
  format: 'csv' | 'xlsx';
  encoding: string;
  delimiter: string;
  dateFormat: string;
  nullRepresentation: string;
}