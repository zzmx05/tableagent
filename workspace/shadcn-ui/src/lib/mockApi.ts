// Mock API 实现 - 模拟后端数据处理

import { DatasetMeta, DatasetProfile, TableProcessSpec, RunSummary, ColumnSchema } from '@/types/table';

// 生成模拟数据
function generateMockData(rows: number, columns: string[]): (string | number | null)[][] {
  const data: (string | number | null)[][] = [];
  for (let i = 0; i < rows; i++) {
    const row: (string | number | null)[] = [];
    columns.forEach((col) => {
      if (col.toLowerCase().includes('name')) {
        row.push(Math.random() > 0.1 ? `Name${i + 1}` : null);
      } else if (col.toLowerCase().includes('age')) {
        row.push(Math.random() > 0.1 ? Math.floor(Math.random() * 60) + 20 : null);
      } else if (col.toLowerCase().includes('email')) {
        row.push(Math.random() > 0.15 ? `user${i + 1}@example.com` : null);
      } else if (col.toLowerCase().includes('country')) {
        const countries: (string | null)[] = ['CN', 'US', 'UK', 'JP', null];
        row.push(countries[Math.floor(Math.random() * countries.length)] || null);
      } else if (col.toLowerCase().includes('score')) {
        row.push(Math.random() > 0.1 ? Math.floor(Math.random() * 100) : null);
      } else {
        row.push(Math.random() > 0.2 ? `Value${i + 1}` : null);
      }
    });
    data.push(row);
  }
  return data;
}

// 模拟上传
export async function mockUpload(
  file: File,
  options: { encoding: string; delimiter: string; hasHeader: boolean }
): Promise<{ datasetId: string; meta: DatasetMeta; profile: DatasetProfile }> {
  // 模拟延迟
  await new Promise((resolve) => setTimeout(resolve, 1500));

  const datasetId = `ds_${Date.now()}`;
  const columns = ['Name', 'Age', 'Email', 'Country', 'Score'];
  const rows = 1000;

  const schema: ColumnSchema[] = columns.map((col) => ({
    name: col,
    type: col.toLowerCase().includes('age') || col.toLowerCase().includes('score') ? 'number' : 'string',
    nullRate: Math.random() * 0.2,
    uniqueCount: Math.floor(Math.random() * rows),
    selected: true,
  }));

  const previewRows = generateMockData(50, columns);

  const meta: DatasetMeta = {
    datasetId,
    fileName: file.name,
    fileSize: file.size,
    rows,
    columns: columns.length,
    encoding: options.encoding,
    delimiter: options.delimiter,
    hasHeader: options.hasHeader,
    fingerprint: `fp_${Date.now()}`,
    uploadedAt: new Date().toISOString(),
  };

  const profile: DatasetProfile = {
    datasetId,
    schema,
    previewRows,
    statistics: {
      totalRows: rows,
      totalColumns: columns.length,
      memoryUsage: file.size,
    },
  };

  return { datasetId, meta, profile };
}

// 模拟处理
export async function mockProcess(
  datasetId: string,
  spec: TableProcessSpec
): Promise<{ runId: string }> {
  await new Promise((resolve) => setTimeout(resolve, 500));
  return { runId: `run_${Date.now()}` };
}

// 模拟获取运行状态
export async function mockGetRun(runId: string): Promise<RunSummary> {
  await new Promise((resolve) => setTimeout(resolve, 1000));

  // 10% 概率返回错误
  const hasError = Math.random() < 0.1;

  if (hasError) {
    return {
      runId,
      status: 'error',
      progress: 100,
      inputRows: 1000,
      outputRows: 0,
      affectedColumns: [],
      missingChanges: [],
      errorCode: 'ERR_INVALID_FILTER',
      errorMessage: 'Invalid filter expression: column "age" not found',
      startedAt: new Date().toISOString(),
      completedAt: new Date().toISOString(),
    };
  }

  return {
    runId,
    status: 'success',
    progress: 100,
    inputRows: 1000,
    outputRows: 850,
    affectedColumns: ['Name', 'Age', 'Email'],
    missingChanges: [
      { column: 'Name', before: 100, after: 0 },
      { column: 'Age', before: 120, after: 0 },
      { column: 'Email', before: 150, after: 0 },
    ],
    startedAt: new Date().toISOString(),
    completedAt: new Date().toISOString(),
  };
}

// 模拟导出
export async function mockExport(
  datasetId: string,
  spec: TableProcessSpec,
  options: { format: string; encoding: string }
): Promise<{ downloadUrl: string; fileName: string }> {
  await new Promise((resolve) => setTimeout(resolve, 1500));

  const fileName = `export_${Date.now()}.${options.format}`;
  const downloadUrl = `blob:${window.location.origin}/${fileName}`;

  return { downloadUrl, fileName };
}

// 生成处理后的预览数据
export function generateProcessedPreview(
  originalData: (string | number | null)[][],
  spec: TableProcessSpec,
  schema: ColumnSchema[]
): (string | number | null)[][] {
  let processed = [...originalData.map((row) => [...row])];

  // Apply select
  if (spec.select && spec.select.length > 0) {
    const selectedIndices = spec.select.map((col) => schema.findIndex((s) => s.name === col));
    processed = processed.map((row) => selectedIndices.map((i) => row[i]));
  }

  // Apply filter (简化实现)
  if (spec.filter) {
    processed = processed.filter(() => Math.random() > 0.15); // 模拟过滤掉15%的行
  }

  // Apply missing strategy
  if (spec.missing) {
    if (spec.missing.strategy === 'drop') {
      processed = processed.filter((row) => !row.some((cell) => cell === null));
    } else if (spec.missing.strategy === 'fill_const') {
      processed = processed.map((row) =>
        row.map((cell) => (cell === null ? spec.missing?.value || 'N/A' : cell))
      );
    }
  }

  return processed.slice(0, 20); // 只返回前20行
}