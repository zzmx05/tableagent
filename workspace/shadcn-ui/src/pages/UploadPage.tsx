// 上传页面

import { useState } from 'react';
import { useTableStore } from '@/store/tableStore';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Upload, FileText, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { mockUpload } from '@/lib/mockApi';
import { Alert, AlertDescription } from '@/components/ui/alert';

export default function UploadPage() {
  const { setCurrentDataset, currentDataset, currentProfile, setCurrentTab } = useTableStore();
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [encoding, setEncoding] = useState('UTF-8');
  const [delimiter, setDelimiter] = useState(',');
  const [hasHeader, setHasHeader] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);
    setUploading(true);
    setProgress(0);

    try {
      // 模拟进度
      const progressInterval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 10, 90));
      }, 150);

      const result = await mockUpload(file, { encoding, delimiter, hasHeader });

      clearInterval(progressInterval);
      setProgress(100);

      setCurrentDataset(result.meta, result.profile);
      toast.success('文件上传成功', {
        description: `已解析 ${result.meta.rows} 行数据`,
      });

      // 自动切换到处理页面
      setTimeout(() => {
        setCurrentTab('prepare');
      }, 1000);
    } catch (err) {
      setError('ERR_UPLOAD_FAILED: 文件解析失败，请检查文件格式和编码设置');
      toast.error('上传失败');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">上传数据</h1>
        <p className="text-muted-foreground mt-1">上传 CSV、TSV 或 Excel 文件开始数据处理</p>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error}
            <Button variant="link" size="sm" className="ml-2" onClick={() => setError(null)}>
              生成 fix 草案
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Upload Options */}
      <Card>
        <CardHeader>
          <CardTitle>上传设置</CardTitle>
          <CardDescription>配置文件解析选项</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
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
            <div className="space-y-2">
              <Label>表头</Label>
              <Select value={hasHeader ? 'yes' : 'no'} onValueChange={(v) => setHasHeader(v === 'yes')}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="yes">有表头</SelectItem>
                  <SelectItem value="no">无表头</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="border-2 border-dashed rounded-lg p-12 text-center hover:border-primary transition-colors cursor-pointer">
            <Input
              type="file"
              accept=".csv,.tsv,.xlsx,.xls"
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
              disabled={uploading}
            />
            <Label htmlFor="file-upload" className="cursor-pointer">
              <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-lg font-medium mb-2">点击或拖拽文件到此处</p>
              <p className="text-sm text-muted-foreground">支持 CSV、TSV、XLSX 格式，最大 100MB</p>
            </Label>
          </div>

          {uploading && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>解析中...</span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} />
            </div>
          )}
        </CardContent>
      </Card>

      {/* File Overview */}
      {currentDataset && currentProfile && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>文件概览</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">文件名</p>
                  <p className="font-medium">{currentDataset.fileName}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">文件大小</p>
                  <p className="font-medium">{(currentDataset.fileSize / 1024).toFixed(2)} KB</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">行数 × 列数</p>
                  <p className="font-medium">
                    {currentDataset.rows} × {currentDataset.columns}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">编码</p>
                  <p className="font-medium">{currentDataset.encoding}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Table Preview */}
          <Card>
            <CardHeader>
              <CardTitle>表格预览（前 50 行）</CardTitle>
              <CardDescription>每列显示类型推断、空值率与唯一值估计</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      {currentProfile.schema.map((col) => (
                        <TableHead key={col.name}>
                          <div className="space-y-1">
                            <p className="font-medium">{col.name}</p>
                            <div className="flex gap-1">
                              <Badge variant="outline" className="text-xs">
                                {col.type}
                              </Badge>
                              <Badge variant="secondary" className="text-xs">
                                空值 {(col.nullRate * 100).toFixed(1)}%
                              </Badge>
                            </div>
                          </div>
                        </TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {currentProfile.previewRows.slice(0, 10).map((row, i) => (
                      <TableRow key={i}>
                        {row.map((cell, j) => (
                          <TableCell key={j}>{cell === null ? <span className="text-muted-foreground italic">null</span> : String(cell)}</TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}