import { DatasetMeta, DatasetProfile, TableProcessSpec, ColumnSchema } from '@/types/table';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8080';

async function readError(response: Response, fallback: string) {
  const payload = await response.json().catch(() => null);
  if (payload?.detail) {
    return typeof payload.detail === 'string' ? payload.detail : JSON.stringify(payload.detail);
  }
  return fallback;
}

export async function uploadDataset(
  file: File,
  options: { encoding: string; delimiter: string; hasHeader: boolean }
): Promise<{ datasetId: string; meta: DatasetMeta; profile: DatasetProfile }> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('encoding', options.encoding);
  formData.append('delimiter', options.delimiter);
  formData.append('has_header', String(options.hasHeader));

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(await readError(response, '文件上传失败'));
  }

  return response.json();
}

export async function processDataset(
  datasetId: string,
  spec: TableProcessSpec
) {
  const response = await fetch(`${API_BASE}/process`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      dataset_id: datasetId,
      process_spec: spec,
    }),
  });

  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.detail || '数据处理失败');
  }
  return result;
}

export async function chatWithAgent(payload: {
  sessionId: string;
  message: string;
  context?: Record<string, unknown>;
}) {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: payload.sessionId,
      message: payload.message,
      context: payload.context || {},
    }),
  });

  if (!response.ok) {
    throw new Error(await readError(response, '对话请求失败'));
  }

  return response.json();
}

export async function exportDataset(payload: {
  datasetId: string;
  format: string;
  encoding: string;
  delimiter: string;
  nullRepresentation: string;
}) {
  const response = await fetch(`${API_BASE}/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      dataset_id: payload.datasetId,
      format: payload.format,
      encoding: payload.encoding,
      delimiter: payload.delimiter,
      null_representation: payload.nullRepresentation,
    }),
  });

  if (!response.ok) {
    throw new Error(await readError(response, '导出失败'));
  }

  const blob = await response.blob();
  const ext = payload.format === 'xlsx' ? 'xlsx' : 'csv';
  return { blob, fileName: `${payload.datasetId}.${ext}` };
}

export function schemaForPreview(
  schema: ColumnSchema[],
  spec?: TableProcessSpec
): ColumnSchema[] {
  if (!spec?.select?.length) return schema;
  return spec.select
    .map((name) => schema.find((col) => col.name === name))
    .filter((col): col is ColumnSchema => Boolean(col));
}

export function previewFromSpec(
  rows: (string | number | null)[][],
  schema: ColumnSchema[],
  spec: TableProcessSpec
): { data: (string | number | null)[][]; schema: ColumnSchema[] } {
  const nextSchema = schemaForPreview(schema, spec);
  if (!spec.select?.length) {
    return { data: rows, schema: nextSchema };
  }

  const indices = spec.select
    .map((name) => schema.findIndex((col) => col.name === name))
    .filter((index) => index >= 0);

  return {
    data: rows.map((row) => indices.map((index) => row[index])),
    schema: nextSchema,
  };
}
