// Zustand 全局状态管理

import { create } from 'zustand';
import { AppState, Message, FlowData, TableProcessSpec, DatasetMeta, DatasetProfile, RunSummary } from '@/types/table';

interface TableStore extends AppState {
  // Actions
  setCurrentDataset: (meta: DatasetMeta, profile: DatasetProfile) => void;
  updateProcessSpec: (spec: Partial<TableProcessSpec>, source: string) => void;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  setCurrentRun: (run: RunSummary | null) => void;
  setProcessedPreview: (preview: (string | number | null)[][]) => void;
  applyProfile: (profile: DatasetProfile) => void;
  saveFlow: (flow: Omit<FlowData, 'flowId' | 'createdAt' | 'updatedAt'>) => void;
  loadFlow: (flowId: string) => void;
  deleteFlow: (flowId: string) => void;
  toggleAssistant: () => void;
  setCurrentTab: (tab: AppState['currentTab']) => void;
  setPrepareSubTab: (tab: AppState['prepareSubTab']) => void;
  toggleDiffOnly: () => void;
  undoLastSpec: () => void;
  clearDataset: () => void;
  toggleDataExternal: () => void;
  clearAllFlows: () => void;
}

// 从 localStorage 加载已保存的流程
function loadFlowsFromStorage(): FlowData[] {
  try {
    const stored = localStorage.getItem('table_agent_flows');
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

// 保存流程到 localStorage
function saveFlowsToStorage(flows: FlowData[]) {
  try {
    localStorage.setItem('table_agent_flows', JSON.stringify(flows));
  } catch (error) {
    console.error('Failed to save flows:', error);
  }
}

export const useTableStore = create<TableStore>((set, get) => ({
  // Initial state
  currentDataset: null,
  currentProfile: null,
  processSpec: {},
  specHistory: [],
  currentRun: null,
  runHistory: [],
  originalPreview: [],
  originalSchema: [],
  processedPreview: [],
  messages: [],
  savedFlows: loadFlowsFromStorage(),
  assistantCollapsed: false,
  currentTab: 'flows',
  prepareSubTab: 'params',
  showDiffOnly: false,
  dataExternalEnabled: false,

  // Actions
  setCurrentDataset: (meta, profile) => {
    set({
      currentDataset: meta,
      currentProfile: profile,
      originalPreview: profile.previewRows,
      originalSchema: profile.schema,
      processedPreview: profile.previewRows,
      processSpec: {},
      specHistory: [],
    });
  },

  updateProcessSpec: (spec, source) => {
    const current = get().processSpec;
    const newSpec = { ...current, ...spec };
    set({
      processSpec: newSpec,
      specHistory: [
        ...get().specHistory,
        { spec: newSpec, timestamp: new Date().toISOString(), source },
      ],
    });
  },

  addMessage: (message) => {
    const newMessage: Message = {
      ...message,
      id: `msg_${Date.now()}_${Math.random()}`,
      timestamp: new Date().toISOString(),
    };
    set({ messages: [...get().messages, newMessage] });
  },

  setCurrentRun: (run) => {
    set({ currentRun: run });
    if (run && run.status !== 'pending' && run.status !== 'running') {
      set({ runHistory: [...get().runHistory, run] });
    }
  },

  setProcessedPreview: (preview) => {
    set({ processedPreview: preview });
  },

  applyProfile: (profile) => {
    const current = get().currentDataset;
    set({
      currentProfile: profile,
      processedPreview: profile.previewRows,
      currentDataset: current
        ? {
            ...current,
            rows: Number(profile.statistics?.totalRows ?? current.rows),
            columns: Number(profile.statistics?.totalColumns ?? current.columns),
          }
        : current,
    });
  },

  saveFlow: (flow) => {
    const newFlow: FlowData = {
      ...flow,
      flowId: `flow_${Date.now()}`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    const updatedFlows = [...get().savedFlows, newFlow];
    set({ savedFlows: updatedFlows });
    saveFlowsToStorage(updatedFlows);
  },

  loadFlow: (flowId) => {
    const flow = get().savedFlows.find((f) => f.flowId === flowId);
    if (flow) {
      set({
        currentDataset: flow.datasetMeta,
        processSpec: flow.spec,
        originalPreview: flow.previewSample || [],
        originalSchema: [],
        processedPreview: flow.previewSample || [],
        currentTab: 'prepare',
      });
    }
  },

  deleteFlow: (flowId) => {
    const updatedFlows = get().savedFlows.filter((f) => f.flowId !== flowId);
    set({ savedFlows: updatedFlows });
    saveFlowsToStorage(updatedFlows);
  },

  toggleAssistant: () => {
    set({ assistantCollapsed: !get().assistantCollapsed });
  },

  setCurrentTab: (tab) => {
    set({ currentTab: tab });
  },

  setPrepareSubTab: (tab) => {
    set({ prepareSubTab: tab });
  },

  toggleDiffOnly: () => {
    set({ showDiffOnly: !get().showDiffOnly });
  },

  undoLastSpec: () => {
    const history = get().specHistory;
    if (history.length > 1) {
      const newHistory = history.slice(0, -1);
      const previousSpec = newHistory[newHistory.length - 1]?.spec || {};
      set({
        processSpec: previousSpec,
        specHistory: newHistory,
      });
    } else {
      set({
        processSpec: {},
        specHistory: [],
      });
    }
  },

  clearDataset: () => {
    set({
      currentDataset: null,
      currentProfile: null,
      processSpec: {},
      specHistory: [],
      currentRun: null,
      originalPreview: [],
      originalSchema: [],
      processedPreview: [],
    });
  },

  toggleDataExternal: () => {
    set({ dataExternalEnabled: !get().dataExternalEnabled });
  },

  clearAllFlows: () => {
    set({ savedFlows: [] });
    saveFlowsToStorage([]);
  },
}));