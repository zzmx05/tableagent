import {
    processDataset,
    getDatasetVersions,
  } from '@/lib/api';
  
  import { useTableStore } from '@/store/tableStore';
  
  export async function executeCurrentProcess() {
    const state = useTableStore.getState();
  
    const {
      currentProfile,
      processSpec,
      setCurrentRun,
      applyProfile,
      setDatasetVersion,
      clearProcessSpec,
    } = state;
  
    if (!currentProfile) {
      throw new Error('当前没有数据集');
    }
  
    if (Object.keys(processSpec).length === 0) {
      throw new Error('当前没有待执行的处理方案');
    }
  
    try {
      const result = await processDataset(
        currentProfile.datasetId,
        processSpec
      );
  
      setCurrentRun({
        runId: result.runId,
        status: 'success',
        progress: 100,
        inputRows: result.inputRows,
        outputRows: result.outputRows,
        affectedColumns: result.affectedColumns || [],
        missingChanges: result.missingChanges || [],
        startedAt: new Date().toISOString(),
      });
  
      if (result.profile) {
        applyProfile(result.profile);
      }
  
      const versions = await getDatasetVersions(
        currentProfile.datasetId
      );
  
      setDatasetVersion(
        versions.currentVersion,
        versions.versions
      );
  
      clearProcessSpec();
  
      return {
        result,
        version: versions.currentVersion,
      };
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : '未知执行错误';
  
      setCurrentRun({
        runId: `failed_${Date.now()}`,
        status: 'error',
        progress: 0,
        inputRows:
          Number(currentProfile.statistics?.totalRows ?? 0),
        outputRows:
          Number(currentProfile.statistics?.totalRows ?? 0),
        affectedColumns: [],
        missingChanges: [],
        startedAt: new Date().toISOString(),
  
        errorCode: 'PROCESS_FAILED',
        errorMessage: message,
        
        failedSpec: { ...processSpec },
      });
  
      throw error;
    }
  }