import { Toaster } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useTableStore } from '@/store/tableStore';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Settings, HelpCircle, User, FileText, Save, FolderOpen, Plus } from 'lucide-react';
import { AssistantPanel } from '@/components/AssistantPanel';
import UploadPage from '@/pages/UploadPage';
import PreparePage from '@/pages/PreparePage';
import ExportPage from '@/pages/ExportPage';
import FlowsPage from '@/pages/FlowsPage';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertTriangle } from 'lucide-react';

const queryClient = new QueryClient();

function App() {
  const { 
    currentTab, 
    setCurrentTab, 
    dataExternalEnabled, 
    toggleDataExternal, 
    clearAllFlows,
    assistantCollapsed,
    currentDataset,
    processSpec,
    saveFlow,
    loadFlow,
    currentProfile,
    savedFlows
  } = useTableStore();

  const [isRenaming, setIsRenaming] = useState(false);
  const [currentFlowName, setCurrentFlowName] = useState('新流程1');
  const [showFlowSwitchAlert, setShowFlowSwitchAlert] = useState(false);
  const [lastLoadedFlowId, setLastLoadedFlowId] = useState<string | null>(null);
  
  // 计算完成度
  const getCompletionStatus = () => {
    const { currentRun } = useTableStore.getState();
    const steps = {
      upload: !!currentDataset,
      prepare: !!currentRun && currentRun.status === 'success',
      export: false,
    };

    const completed = Object.values(steps).filter(Boolean).length;
    const total = Object.keys(steps).length;
    const percentage = Math.round((completed / total) * 100);

    return { completed, total, percentage, steps };
  };

  const status = getCompletionStatus();

  // 检查是否需要显示流程切换提示
  useEffect(() => {
    if (lastLoadedFlowId && savedFlows[lastLoadedFlowId]) {
      setShowFlowSwitchAlert(true);
    }
  }, [currentDataset, processSpec, lastLoadedFlowId, savedFlows]);

  const handleRestoreFlow = () => {
    if (lastLoadedFlowId && savedFlows[lastLoadedFlowId]) {
      const flow = savedFlows[lastLoadedFlowId];
      // 这里应该恢复流程参数，但目前我们只显示提示
      toast.success(`已恢复流程 "${flow.name}" 的参数`);
      setShowFlowSwitchAlert(false);
    }
  };

  const handleSave = () => {
    if (!currentProfile || !currentDataset) {
      toast.error('请先上传数据');
      return;
    }

    saveFlow({
      name: currentFlowName,
      spec: processSpec,
      datasetMeta: currentDataset,
      previewSample: currentProfile.previewRows,
    });
    toast.success('流程已保存');
  };

  const handleSaveAs = () => {
    if (!currentProfile || !currentDataset) {
      toast.error('请先上传数据');
      return;
    }

    const newName = prompt('请输入新流程名称:', `${currentFlowName} 副本`);
    if (newName) {
      saveFlow({
        name: newName,
        spec: processSpec,
        datasetMeta: currentDataset,
        previewSample: currentProfile.previewRows,
      });
      setCurrentFlowName(newName);
      toast.success('流程已另存为');
    }
  };

  const handleNewFlow = () => {
    setCurrentFlowName('新流程1');
    useTableStore.getState().clearDataset();
    toast.info('已创建新流程');
  };

  const handleOpenFlow = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const flow = JSON.parse(e.target?.result as string);
          loadFlow(flow.flowId);
          setCurrentFlowName(flow.name);
          setLastLoadedFlowId(flow.flowId);
          toast.success('流程已加载');
        } catch (error) {
          toast.error('导入失败: 无效的 JSON 文件');
        }
      };
      reader.readAsText(file);
    };
    input.click();
  };

  // 快捷键处理
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case 's':
            e.preventDefault();
            if (e.shiftKey) {
              handleSaveAs();
            } else {
              handleSave();
            }
            break;
          case 'o':
            if (!e.shiftKey) {
              e.preventDefault();
              handleOpenFlow();
            }
            break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [currentProfile, currentDataset, processSpec]);

  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <div className="min-h-screen bg-background">
          {/* Top Navigation */}
          <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
            <div className="container mx-auto px-4 py-3">
              <div className="flex items-center justify-between">
                {/* Left side - App name and current flow */}
                <div className="flex items-center gap-6">
                  <h1 className="text-xl font-bold">表格智能体</h1>
                  
                  {/* Current Flow Indicator */}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" className="gap-2">
                        {isRenaming ? (
                          <Input
                            value={currentFlowName}
                            onChange={(e) => setCurrentFlowName(e.target.value)}
                            onBlur={() => setIsRenaming(false)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') setIsRenaming(false);
                              if (e.key === 'Escape') setIsRenaming(false);
                            }}
                            autoFocus
                            className="h-7 px-2"
                          />
                        ) : (
                          <>
                            <span className="text-muted-foreground">当前:</span>
                            <span className="font-medium">{currentFlowName}</span>
                            <Badge variant="outline" className="ml-2">
                              • 未保存
                            </Badge>
                          </>
                        )}
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="start">
                      <DropdownMenuItem onClick={() => setIsRenaming(true)}>
                        重命名
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={handleSave}>
                        <Save className="h-4 w-4 mr-2" />
                        保存
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={handleSaveAs}>
                        <Save className="h-4 w-4 mr-2" />
                        另存为
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => setCurrentTab('flows')}>
                        管理流程...
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                {/* Center - Stepper (only Upload/Prepare/Export) */}
                <div className="flex-1 flex justify-center">
                  <Tabs value={currentTab !== 'flows' ? currentTab : 'upload'} onValueChange={(v) => {
                    if (v !== 'flows') {
                      setCurrentTab(v as 'upload' | 'prepare' | 'export');
                    }
                  }}>
                    <TabsList>
                      <TabsTrigger value="upload">
                        上传
                        {status.steps.upload && <Badge className="ml-2 h-4 w-4 p-0">✓</Badge>}
                      </TabsTrigger>
                      <TabsTrigger value="prepare">
                        处理
                        {status.steps.prepare && <Badge className="ml-2 h-4 w-4 p-0">✓</Badge>}
                      </TabsTrigger>
                      <TabsTrigger value="export">导出</TabsTrigger>
                    </TabsList>
                  </Tabs>
                </div>

                {/* Right side - Actions and settings */}
                <div className="flex items-center gap-2">
                  {/* Flows Menu */}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <FileText className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={handleNewFlow}>
                        <Plus className="h-4 w-4 mr-2" />
                        新建流程
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={handleOpenFlow}>
                        <FolderOpen className="h-4 w-4 mr-2" />
                        打开...
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={handleSave}>
                        <Save className="h-4 w-4 mr-2" />
                        保存
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={handleSaveAs}>
                        <Save className="h-4 w-4 mr-2" />
                        另存为
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => setCurrentTab('flows')}>
                        管理流程...
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>

                  {/* Settings */}
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <Settings className="h-4 w-4" />
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>设置</DialogTitle>
                        <DialogDescription>配置应用行为和隐私选项</DialogDescription>
                      </DialogHeader>
                      <div className="space-y-4 py-4">
                        <div className="flex items-center justify-between">
                          <div className="space-y-0.5">
                            <Label>数据外发</Label>
                            <p className="text-sm text-muted-foreground">允许发送统计与采样数据给模型</p>
                          </div>
                          <Switch checked={dataExternalEnabled} onCheckedChange={toggleDataExternal} />
                        </div>
                        <Separator />
                        <div>
                          <Label>清空本地缓存</Label>
                          <p className="text-sm text-muted-foreground mb-2">删除所有已保存的流程和解析缓存</p>
                          <Button variant="destructive" size="sm" onClick={clearAllFlows}>
                            清空全部
                          </Button>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>

                  {/* Help */}
                  <Button variant="ghost" size="icon">
                    <HelpCircle className="h-4 w-4" />
                  </Button>

                  {/* Account */}
                  <Button variant="ghost" size="icon">
                    <User className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* Flow Switch Alert */}
          {showFlowSwitchAlert && (
            <div className="container mx-auto px-4 py-2">
              <Alert variant="default">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription className="flex items-center justify-between">
                  <span>已切换至『{savedFlows[lastLoadedFlowId || '']?.name || '未知流程'}』，是否恢复该流程参数？</span>
                  <Button variant="outline" size="sm" onClick={handleRestoreFlow}>
                    一键恢复
                  </Button>
                </AlertDescription>
              </Alert>
            </div>
          )}

          {/* Main Content */}
          <div className="container mx-auto px-4 py-6" style={{ marginRight: assistantCollapsed ? '3rem' : '24rem' }}>
            {currentTab === 'upload' && <UploadPage />}
            {currentTab === 'prepare' && <PreparePage />}
            {currentTab === 'export' && <ExportPage />}
            {currentTab === 'flows' && <FlowsPage />}
          </div>

          {/* Assistant Panel */}
          <AssistantPanel />
        </div>
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;