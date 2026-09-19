// 处理页面 - 参数编辑和预览对比

import { useState } from 'react';
import { useTableStore } from '@/store/tableStore';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Play, RotateCcw, AlertCircle, Info } from 'lucide-react';
import { toast } from 'sonner';
// import { mockProcess, mockGetRun, generateProcessedPreview } from '@/lib/mockApi';
import { ColumnSchema } from '@/types/table';
import {processDataset,schemaForPreview,rollbackDataset,getDatasetVersions,} from '@/lib/api';
export default function PreparePage() {
  const {
    currentProfile,
    processSpec,
    updateProcessSpec,
    currentRun,
    setCurrentRun,
    originalPreview,
    originalSchema,
    processedPreview,
    setProcessedPreview,
    applyProfile,
    prepareSubTab,
    setPrepareSubTab,
    showDiffOnly,
    toggleDiffOnly,
    undoLastSpec,
    specHistory,
  
    // 版本管理
    currentVersion,
    versionHistory,
    setDatasetVersion,
    clearProcessSpec,
  } = useTableStore();

  const [running, setRunning] = useState(false);

  if (!currentProfile) {
    return (
      <div className="flex items-center justify-center h-full">
        <Card className="w-96">
          <CardContent className="py-12 text-center">
            <AlertCircle className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">未上传数据</h3>
            <p className="text-muted-foreground">请先上传数据文件</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const handleRun = async () => {
    if (!currentProfile) return;
  
    // 没有参数变化时不创建空版本
    if (Object.keys(processSpec).length === 0) {
      toast.info('没有需要运行的参数修改');
      return;
    }
  
    setRunning(true);
  
    try {
      // 1. 执行本轮数据处理
      const result = await processDataset(
        currentProfile.datasetId,
        processSpec
      );
  
      // 2. 保存运行结果
      setCurrentRun({
        runId: result.runId,
        status: result.status,
        progress: 100,
        inputRows: result.inputRows,
        outputRows: result.outputRows,
        affectedColumns: result.affectedColumns || [],
        missingChanges: result.missingChanges || [],
        startedAt: new Date().toISOString(),
      });
  
      // 3. 用后端返回的新 profile 更新页面
      if (result.profile) {
        applyProfile(result.profile);
      }
  
      // 4. 重新向后端查询版本状态
      const versions = await getDatasetVersions(
        currentProfile.datasetId
      );
  
      setDatasetVersion(
        versions.currentVersion,
        versions.versions
      );
  
      // 5. 本轮操作已经写入新版本，不应该重复执行
      clearProcessSpec();
  
      toast.success('运行成功', {
        description: `已生成 ${versions.currentVersion}，输出 ${result.outputRows} 行数据`,
      });
    } catch (error) {
      console.error('运行失败:', error);
  
      toast.error('运行失败', {
        description:
          error instanceof Error
            ? error.message
            : '未知错误',
      });
    } finally {
      setRunning(false);
    }
  };

  const handleUndoSpec = () => {
    undoLastSpec();
    toast.info('已撤销上次参数修改');
  };

  const handleRollback = async () => {
    if (!currentProfile) return;
  
    // 找到当前版本的位置
    const currentIndex = versionHistory.indexOf(currentVersion);
  
    if (currentIndex <= 0) {
      toast.info('已经是原始版本 v000');
      return;
    }
  
    // 当前版本的上一个版本
    const targetVersion = versionHistory[currentIndex - 1];
  
    setRunning(true);
  
    try {
      // 1. 通知后端移动 current_version
      const result = await rollbackDataset(
        currentProfile.datasetId,
        targetVersion
      );
  
      // 2. 更新页面上的数据
      if (result.profile) {
        applyProfile(result.profile);
      }
  
      // 3. 再从后端获取真实版本状态
      const versions = await getDatasetVersions(
        currentProfile.datasetId
      );
  
      setDatasetVersion(
        versions.currentVersion,
        versions.versions
      );
  
      // 防止撤销后还残留旧参数
      clearProcessSpec();
  
      toast.success('撤销成功', {
        description: `已恢复到 ${targetVersion}`,
      });
    } catch (error) {
      console.error('撤销运行失败:', error);
  
      toast.error('撤销运行失败', {
        description:
          error instanceof Error
            ? error.message
            : '未知错误',
      });
    } finally {
      setRunning(false);
    }
  };
  const hasChanges = specHistory.length > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">数据处理</h1>
          <p className="text-muted-foreground mt-1">配置参数并预览处理结果</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline">
            当前版本：{currentVersion}
          </Badge>

          <Button
            variant="outline"
            onClick={handleUndoSpec}
            disabled={!hasChanges || running}
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            撤销参数
          </Button>

          <Button
            variant="outline"
            onClick={handleRollback}
            disabled={currentVersion === 'v000' || running}
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            撤销运行
          </Button>

          <Button
            onClick={handleRun}
            disabled={running || !hasChanges}
          >
            <Play className="h-4 w-4 mr-2" />
            {running ? '处理中...' : '运行一次'}
          </Button>
        </div>
      </div>

      {/* Changes Alert */}
      {hasChanges && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            检测到 {specHistory.length} 处参数变更
            <Button
              variant="link"
              size="sm"
              className="ml-2"
              onClick={handleUndoSpec}
            >
              撤销参数修改
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Running Progress */}
      {currentRun && (currentRun.status === 'pending' || currentRun.status === 'running') && (
        <Card>
          <CardContent className="py-6">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>运行中...</span>
                <span>{currentRun.progress}%</span>
              </div>
              <Progress value={currentRun.progress} />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Run Summary */}
      {currentRun && currentRun.status === 'success' && (
        <Card>
          <CardHeader>
            <CardTitle>运行结果</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">输入行数</p>
                <p className="text-2xl font-bold">{currentRun.inputRows}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">输出行数</p>
                <p className="text-2xl font-bold">{currentRun.outputRows}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">受影响列</p>
                <p className="text-2xl font-bold">{currentRun.affectedColumns.length}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">删除行数</p>
                <p className="text-2xl font-bold">{currentRun.inputRows - currentRun.outputRows}</p>
              </div>
            </div>
            {currentRun.missingChanges.length > 0 && (
              <div className="mt-4">
                <p className="text-sm font-medium mb-2">缺失值变化 Top 3:</p>
                <div className="space-y-1">
                  {currentRun.missingChanges.slice(0, 3).map((change) => (
                    <p key={change.column} className="text-sm text-muted-foreground">
                      {change.column}: {change.before} → {change.after}
                    </p>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Error Alert */}
      {currentRun && currentRun.status === 'error' && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {currentRun.errorCode}: {currentRun.errorMessage}
            <Button variant="link" size="sm" className="ml-2">
              生成 fix 草案
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Main Tabs */}
      <Tabs value={prepareSubTab} onValueChange={(v) => setPrepareSubTab(v as 'params' | 'preview')}>
        <TabsList>
          <TabsTrigger value="params">参数</TabsTrigger>
          <TabsTrigger value="preview">预览/对比</TabsTrigger>
        </TabsList>

        <TabsContent value="params" className="space-y-4">
          <ParametersPanel />
        </TabsContent>

        <TabsContent value="preview" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>数据预览对比</CardTitle>
                <div className="flex items-center gap-2">
                  <Checkbox checked={showDiffOnly} onCheckedChange={toggleDiffOnly} id="diff-only" />
                  <Label htmlFor="diff-only">仅看变化列</Label>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="font-semibold mb-2">原始数据</h3>
                  <PreviewTable data={originalPreview} schema={originalSchema.length ? originalSchema : currentProfile.schema} />
                </div>
                <div>
                  <h3 className="font-semibold mb-2">应用参数后</h3>
                  <PreviewTable
                    data={processedPreview}
                    schema={schemaForPreview(currentProfile.schema, processSpec)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function ParametersPanel() {
  const { currentProfile, processSpec, updateProcessSpec } = useTableStore();

  if (!currentProfile) return null;

  const handleColumnToggle = (columnName: string, checked: boolean) => {
    const currentSelect = processSpec.select || currentProfile.schema.map((s) => s.name);
    const newSelect = checked ? [...currentSelect, columnName] : currentSelect.filter((c) => c !== columnName);
    updateProcessSpec({ select: newSelect }, 'manual');
  };

  const handleMissingStrategyChange = (strategy: string) => {
    updateProcessSpec(
      {
        missing: {
          strategy: strategy as 'drop' | 'fill_const' | 'fill_mean' | 'fill_median' | 'fill_mode',
          value: strategy === 'fill_const' ? 'N/A' : undefined,
        },
      },
      'manual'
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>处理参数</CardTitle>
        <CardDescription>配置列选择、类型转换、缺失值处理和筛选条件</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Column Selection */}
        <div>
          <Label className="text-base font-semibold">列选择</Label>
          <div className="mt-2 space-y-2">
            {currentProfile.schema.map((col) => {
              const isSelected = !processSpec.select || processSpec.select.includes(col.name);
              return (
                <div key={col.name} className="flex items-center justify-between p-2 border rounded">
                  <div className="flex items-center gap-2">
                    <Checkbox checked={isSelected} onCheckedChange={(checked) => handleColumnToggle(col.name, checked as boolean)} id={col.name} />
                    <Label htmlFor={col.name} className="cursor-pointer">
                      {col.name}
                    </Label>
                    <Badge variant="outline">{col.type}</Badge>
                    <Badge variant="secondary" className="text-xs">
                      空值 {(col.nullRate * 100).toFixed(1)}%
                    </Badge>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Missing Value Strategy */}
        <div>
          <Label className="text-base font-semibold">缺失值处理</Label>
          <Select value={processSpec.missing?.strategy || 'drop'} onValueChange={handleMissingStrategyChange}>
            <SelectTrigger className="mt-2">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="drop">删除包含空值的行</SelectItem>
              <SelectItem value="fill_const">填充常量</SelectItem>
              <SelectItem value="fill_mean">填充均值</SelectItem>
              <SelectItem value="fill_median">填充中位数</SelectItem>
              <SelectItem value="fill_mode">填充众数</SelectItem>
            </SelectContent>
          </Select>
          {processSpec.missing?.strategy === 'fill_const' && (
            <Input
              className="mt-2"
              placeholder="填充值"
              value={String(processSpec.missing.value || '')}
              onChange={(e) =>
                updateProcessSpec(
                  {
                    missing: { strategy: 'fill_const', value: e.target.value },
                  },
                  'manual'
                )
              }
            />
          )}
        </div>

        {/* Filter Expression */}
        <div>
          <Label className="text-base font-semibold">筛选表达式</Label>
          <Input
            className="mt-2"
            placeholder="例如: Age >= 18 and Country in ['CN','US']"
            value={processSpec.filter || ''}
            onChange={(e) => updateProcessSpec({ filter: e.target.value }, 'manual')}
          />
          <p className="text-xs text-muted-foreground mt-1">使用列名和 Python 表达式语法</p>
        </div>
      </CardContent>
    </Card>
  );
}

function PreviewTable({ data, schema }: { data: (string | number | null)[][]; schema: ColumnSchema[] }) {
  return (
    <div className="rounded-md border overflow-x-auto max-h-96">
      <Table>
        <TableHeader>
          <TableRow>
            {schema.map((col) => (
              <TableHead key={col.name}>{col.name}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.slice(0, 20).map((row, i) => (
            <TableRow key={i}>
              {row.map((cell, j) => (
                <TableCell key={j}>{cell === null ? <span className="text-muted-foreground italic">null</span> : String(cell)}</TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}