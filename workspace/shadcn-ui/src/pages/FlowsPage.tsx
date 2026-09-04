import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useTableStore } from '@/store/tableStore';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { Save, FolderOpen, Plus, Edit, Trash2, Download } from 'lucide-react';
import { toast } from 'sonner';

interface FlowItem {
  id: string;
  name: string;
  updatedAt: Date;
  datasetMeta: any;
  spec: any;
}

export default function FlowsPage() {
  const { savedFlows, loadFlow, deleteFlow, currentDataset, processSpec, saveFlow } = useTableStore();
  const [flows, setFlows] = useState<FlowItem[]>([]);
  const [editingFlow, setEditingFlow] = useState<FlowItem | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    // Convert savedFlows to FlowItem array
    const flowItems: FlowItem[] = Object.entries(savedFlows).map(([id, flow]) => ({
      id,
      name: flow.name,
      updatedAt: new Date(flow.updatedAt),
      datasetMeta: flow.datasetMeta,
      spec: flow.spec,
    }));
    setFlows(flowItems);
  }, [savedFlows]);

  const handleLoadFlow = (flowId: string) => {
    loadFlow(flowId);
    toast.success('流程已加载');
  };

  const handleDeleteFlow = (flowId: string) => {
    deleteFlow(flowId);
    toast.success('流程已删除');
  };

  const handleEditFlow = (flow: FlowItem) => {
    setEditingFlow(flow);
    setIsEditing(true);
  };

  const handleSaveEdit = () => {
    if (editingFlow) {
      // Update the flow in the store
      saveFlow({
        name: editingFlow.name,
        spec: editingFlow.spec,
        datasetMeta: editingFlow.datasetMeta,
        previewSample: 10, // Default value
      });
      setIsEditing(false);
      setEditingFlow(null);
      toast.success('流程已更新');
    }
  };

  const handleExportFlow = (flow: FlowItem) => {
    const dataStr = JSON.stringify({ 
      flowId: flow.id,
      name: flow.name,
      updatedAt: flow.updatedAt,
      datasetMeta: flow.datasetMeta,
      spec: flow.spec
    }, null, 2);
    
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${flow.name}.flow.json`;
    link.click();
    URL.revokeObjectURL(url);
    toast.success('流程已导出');
  };

  const formatDate = (date: Date) => {
    return format(date, 'yyyy年MM月dd日 HH:mm', { locale: zhCN });
  };

  return (
    <div className="container mx-auto py-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>流程管理</span>
            <div className="flex gap-2">
              <Button onClick={() => {
                useTableStore.getState().clearDataset();
                toast.info('已创建新流程');
              }}>
                <Plus className="h-4 w-4 mr-2" />
                新建流程
              </Button>
              <Button variant="outline" onClick={() => {
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
                      toast.success('流程已加载');
                    } catch (error) {
                      toast.error('导入失败: 无效的 JSON 文件');
                    }
                  };
                  reader.readAsText(file);
                };
                input.click();
              }}>
                <FolderOpen className="h-4 w-4 mr-2" />
                打开流程
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {flows.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-muted-foreground">暂无保存的流程</p>
              <p className="text-sm text-muted-foreground mt-2">
                您可以创建新流程或从文件导入现有流程
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>名称</TableHead>
                  <TableHead>更新时间</TableHead>
                  <TableHead>数据集摘要</TableHead>
                  <TableHead>来源</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {flows.map((flow) => (
                  <TableRow key={flow.id}>
                    <TableCell className="font-medium">{flow.name}</TableCell>
                    <TableCell>{formatDate(flow.updatedAt)}</TableCell>
                    <TableCell>
                      {flow.datasetMeta ? (
                        <Badge variant="outline">
                          {flow.datasetMeta.name} ({flow.datasetMeta.rows}行)
                        </Badge>
                      ) : (
                        <Badge variant="outline">无数据集</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">本地</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleLoadFlow(flow.id)}
                        >
                          <FolderOpen className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleEditFlow(flow)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleExportFlow(flow)}
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDeleteFlow(flow.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={isEditing} onOpenChange={setIsEditing}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>编辑流程</DialogTitle>
          </DialogHeader>
          {editingFlow && (
            <div className="space-y-4">
              <div>
                <Label htmlFor="flowName">流程名称</Label>
                <Input
                  id="flowName"
                  value={editingFlow.name}
                  onChange={(e) => setEditingFlow({...editingFlow, name: e.target.value})}
                />
              </div>
              <div>
                <Label>流程参数</Label>
                <Textarea
                  value={JSON.stringify(editingFlow.spec, null, 2)}
                  onChange={(e) => setEditingFlow({...editingFlow, spec: JSON.parse(e.target.value)})}
                  rows={10}
                />
              </div>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => setIsEditing(false)}>
                  取消
                </Button>
                <Button onClick={handleSaveEdit}>
                  <Save className="h-4 w-4 mr-2" />
                  保存
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}