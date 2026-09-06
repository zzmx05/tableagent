// 右侧对话助手面板

import { useState } from 'react';
import { useTableStore } from '@/store/tableStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageType, Message, TableProcessSpec } from '@/types/table';
import { ChevronLeft, ChevronRight, Send, Copy, Star } from 'lucide-react';
import { toast } from 'sonner';
import { generateProcessedPreview } from '@/lib/mockApi';

export function AssistantPanel() {
  const { assistantCollapsed, toggleAssistant, messages, addMessage, updateProcessSpec, processSpec, currentProfile, setProcessedPreview } = useTableStore();
  const [inputMode, setInputMode] = useState<MessageType>('chat');
  const [inputValue, setInputValue] = useState('');
  const [messageFilter, setMessageFilter] = useState<MessageType | 'all'>('all');

  const placeholders = {
    chat: '询问数据统计、建议或解释...',
    execute: '描述要执行的数据处理操作...',
    fix: '描述遇到的错误或需要修复的问题...',
  };

  const handleSend = async() => {
    if (!inputValue.trim()) return;

    if (inputMode === 'chat') {
      // 用户消息显示
      addMessage({
        type: 'chat',
        content: inputValue,
      });


      try {

        const response = await fetch(
          "http://localhost:8080/chat",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body:JSON.stringify({
              session_id:"user_001",        
              message:inputValue,          
              history:[],          
              context:{}          
          }),
          }
        );


        if (!response.ok) {
          throw new Error("Backend request failed");
        }


        const data = await response.json();


        addMessage({
          type: 'chat',
          content: data.reply,
        });


      } catch(error) {


        console.error(error);


        addMessage({
          type:'chat',
          content:
            "连接后端失败，请确认 FastAPI 已启动",
        });

      }
    } else if (inputMode === 'execute') {
      // 生成 execute 方案
      const mockSpec: TableProcessSpec = {
        select: ['Name', 'Age', 'Email', 'Country'],
        missing: {
          strategy: 'fill_const',
          value: 'N/A',
        },
        filter: 'age >= 18',
      };

      addMessage({
        type: 'execute',
        content: `执行方案: ${inputValue}`,
        spec: mockSpec,
        impact: {
          affectedColumns: 4,
          estimatedRowsDeleted: 150,
          description: '将填充缺失值并过滤年龄小于18的记录',
        },
      });
    } else if (inputMode === 'fix') {
      // 生成 fix 补丁
      addMessage({
        type: 'fix',
        content: `修复建议: ${inputValue}`,
        targetError: 'ERR_INVALID_FILTER',
        patch: {
          filter: 'Age >= 18',
        },
        diff: [
          { path: 'filter', before: 'age >= 18', after: 'Age >= 18' },
        ],
      });
    }

    setInputValue('');
  };

  const handleApplySpec = (message: Message) => {
    if (message.spec) {
      updateProcessSpec(message.spec, `execute #${message.id}`);
      
      // 生成处理后的预览
      if (currentProfile) {
        const processed = generateProcessedPreview(
          currentProfile.previewRows,
          { ...processSpec, ...message.spec },
          currentProfile.schema
        );
        setProcessedPreview(processed);
      }
      
      toast.success('已应用到参数', {
        description: '查看差异',
        action: {
          label: '撤销',
          onClick: () => {
            useTableStore.getState().undoLastSpec();
            toast.info('已撤销');
          },
        },
        duration: 15000,
      });
    }
  };

  const handleApplyPatch = (message: Message) => {
    if (message.patch) {
      updateProcessSpec(message.patch, `fix #${message.id}`);
      toast.success('已应用补丁', {
        description: '参数已更新',
        duration: 5000,
      });
    }
  };

  const filteredMessages = messages.filter(
    (msg) => messageFilter === 'all' || msg.type === messageFilter
  );

  if (assistantCollapsed) {
    return (
      <div className="fixed right-0 top-0 h-full w-12 bg-background border-l flex items-center justify-center">
        <Button variant="ghost" size="icon" onClick={toggleAssistant}>
          <ChevronLeft className="h-4 w-4" />
        </Button>
      </div>
    );
  }

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-background border-l flex flex-col">
      {/* Header */}
      <div className="p-4 border-b flex items-center justify-between">
        <h2 className="font-semibold">对话助手</h2>
        <Button variant="ghost" size="icon" onClick={toggleAssistant}>
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Filter */}
      <div className="p-4 border-b">
        <Tabs value={messageFilter} onValueChange={(v) => setMessageFilter(v as MessageType | 'all')}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="all">全部</TabsTrigger>
            <TabsTrigger value="chat">Chat</TabsTrigger>
            <TabsTrigger value="execute">Execute</TabsTrigger>
            <TabsTrigger value="fix">Fix</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {filteredMessages.length === 0 && (
            <div className="text-center text-muted-foreground py-8">
              <p>暂无消息</p>
              <p className="text-sm mt-2">开始对话以获取帮助</p>
            </div>
          )}
          {filteredMessages.map((msg) => (
            <MessageCard key={msg.id} message={msg} onApplySpec={handleApplySpec} onApplyPatch={handleApplyPatch} />
          ))}
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="p-4 border-t space-y-2">
        <Tabs value={inputMode} onValueChange={(v) => setInputMode(v as MessageType)}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="chat">Chat</TabsTrigger>
            <TabsTrigger value="execute">Execute</TabsTrigger>
            <TabsTrigger value="fix">Fix</TabsTrigger>
          </TabsList>
        </Tabs>
        <div className="flex gap-2">
          <Input
            placeholder={placeholders[inputMode]}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
          />
          <Button onClick={handleSend} size="icon">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

function MessageCard({
  message,
  onApplySpec,
  onApplyPatch,
}: {
  message: Message;
  onApplySpec: (msg: Message) => void;
  onApplyPatch: (msg: Message) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Badge variant={message.type === 'execute' ? 'default' : message.type === 'fix' ? 'destructive' : 'secondary'}>
              {message.type}
            </Badge>
            {message.starred && <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />}
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={() => {
              navigator.clipboard.writeText(JSON.stringify(message.spec || message.patch, null, 2));
              toast.success('已复制到剪贴板');
            }}
          >
            <Copy className="h-3 w-3" />
          </Button>
        </div>
        <CardTitle className="text-sm">{message.content}</CardTitle>
        <CardDescription className="text-xs">{new Date(message.timestamp).toLocaleString('zh-CN')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {message.type === 'execute' && message.spec && (
          <>
            {message.impact && (
              <div className="text-sm text-muted-foreground">
                <p>影响预估: {message.impact.description}</p>
                <p className="text-xs mt-1">
                  影响列数: {message.impact.affectedColumns} | 预计删除行数: {message.impact.estimatedRowsDeleted}
                </p>
              </div>
            )}
            <Button size="sm" variant="outline" onClick={() => setExpanded(!expanded)}>
              {expanded ? '收起' : '查看'} JSON 方案
            </Button>
            {expanded && (
              <pre className="text-xs bg-muted p-2 rounded overflow-x-auto">
                {JSON.stringify(message.spec, null, 2)}
              </pre>
            )}
            <div className="flex gap-2">
              <Button size="sm" onClick={() => onApplySpec(message)}>
                应用到参数
              </Button>
              <Button size="sm" variant="outline">
                预览差异
              </Button>
            </div>
          </>
        )}

        {message.type === 'fix' && message.patch && (
          <>
            <div className="text-sm">
              <p className="font-medium">目标错误: {message.targetError}</p>
              {message.diff && (
                <div className="mt-2 space-y-1">
                  {message.diff.map((d, i) => (
                    <div key={i} className="text-xs">
                      <span className="text-red-500">- {d.path}: {JSON.stringify(d.before)}</span>
                      <br />
                      <span className="text-green-500">+ {d.path}: {JSON.stringify(d.after)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={() => onApplyPatch(message)}>
                应用补丁并重试
              </Button>
              <Button size="sm" variant="outline" onClick={() => onApplyPatch(message)}>
                只应用补丁
              </Button>
            </div>
          </>
        )}

        {message.type === 'chat' && (
          <>
            {message.statistics && (
              <div className="text-sm space-y-1">
                {Object.entries(message.statistics).map(([key, value]) => (
                  <p key={key} className="text-muted-foreground">
                    {key}: {JSON.stringify(value)}
                  </p>
                ))}
              </div>
            )}
            {message.suggestions && message.suggestions.length > 0 && (
              <div className="space-y-1">
                <p className="text-sm font-medium">建议:</p>
                {message.suggestions.map((s, i) => (
                  <Badge key={i} variant="outline" className="mr-1">
                    {s}
                  </Badge>
                ))}
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}