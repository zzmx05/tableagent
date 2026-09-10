// 导出页面

import { useState } from 'react';
import { useTableStore } from '@/store/tableStore';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Download, FileText, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { exportDataset, schemaForPreview } from '@/lib/api';

export default function ExportPage() {
  const { currentProfile, processSpec, processedPreview, currentDataset } = useTableStore();
  const [format, setFormat] = useState<'csv' | 'xlsx'>('csv');
  const [encoding, setEncoding] = useState('UTF-8');
  const [delimiter, setDelimiter] = useState(',');
  const [dateFormat, setDateFormat] = useState('YYYY-MM-DD');
  const [nullRepresentation, setNullRepresentation] = useState('');
  const [exporting, setExporting] = useState(false);

  if (!currentProfile) {
    return (
      <div className="flex items-center justify-center h-full">
        <Card className="w-96">
          <CardContent className="py-12 text-center">
            <AlertCircle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">未上传数据</h3>
            <p className="text-muted-foreground">请先上传并处理数据</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const handleExport = async () => {
    if (!currentProfile || !currentDataset) return;

    setExporting(true);

    try {
      const result = await exportDataset({
        datasetId: currentProfile.datasetId,
        format,
        encoding,
        delimiter,
        nullRepresentation,
      });

      const url = URL.createObjectURL(result.blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = result.fileName;
      a.click();
      URL.revokeObjectURL(url);

      toast.success('导出成功', {
        description: result.fileName,
      });
    } catch (error) {
      toast.error('导出失败');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">导出数据</h1>
          <p className="text-muted-foreground mt-1">配置导出选项并下载处理后的数据</p>
        </div>
        <Button onClick={handleExport} disabled={exporting}>
          <Download className="h-4 w-4 mr-2" />
          {exporting ? '导出中...' : '导出'}
        </Button>
      </div>

      {/* Export Options */}
      <Card>
        <CardHeader>
          <CardTitle>导出选项</CardTitle>
          <CardDescription>配置输出格式和编码</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>格式</Label>
              <Select value={format} onValueChange={(v) => setFormat(v as 'csv' | 'xlsx')}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="csv">CSV</SelectItem>
                  <SelectItem value="xlsx">Excel (XLSX)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>编码</Label>
              <Select value={encoding} onValueChange={setEncoding}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="UTF-8">UTF-8</SelectItem>
                  <SelectItem value="GBK">GBK</SelectItem>
                  <SelectItem value="ISO-8859-1">ISO-8859-1</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {format === 'csv' && (
              <div className="space-y-2">
                <Label>分隔符</Label>
                <Select value={delimiter} onValueChange={setDelimiter}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value=",">,（逗号）</SelectItem>
                    <SelectItem value="\t">\t（制表符）</SelectItem>
                    <SelectItem value="|">|（竖线）</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
            <div className="space-y-2">
              <Label>日期格式</Label>
              <Input value={dateFormat} onChange={(e) => setDateFormat(e.target.value)} placeholder="YYYY-MM-DD" />
            </div>
            <div className="space-y-2">
              <Label>空值表示</Label>
              <Input value={nullRepresentation} onChange={(e) => setNullRepresentation(e.target.value)} placeholder="留空或输入自定义值" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Export Preview */}
      <Card>
        <CardHeader>
          <CardTitle>导出前预览（前 100 行）</CardTitle>
          <CardDescription>确认数据格式正确后可下载</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border overflow-x-auto max-h-96">
            <Table>
              <TableHeader>
                <TableRow>
                  {schemaForPreview(currentProfile.schema, processSpec).map((col) => (
                    <TableHead key={col.name}>{col.name}</TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {processedPreview.slice(0, 20).map((row, i) => (
                  <TableRow key={i}>
                    {row.map((cell, j) => (
                      <TableCell key={j}>
                        {cell === null ? <span className="text-muted-foreground italic">{nullRepresentation || 'null'}</span> : String(cell)}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Export Package Info */}
      <Card>
        <CardHeader>
          <CardTitle>导出包内容</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">数据文件 (data.{format})</span>
            </div>
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">处理方案 (process_spec.json)</span>
            </div>
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">运行摘要 (run_summary.json)</span>
            </div>
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">数据集元信息 (dataset_meta.json)</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}