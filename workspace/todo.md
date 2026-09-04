# 表格智能体 MVP - 开发计划

## 项目概述
构建一个桌面端（≥1280px）对话驱动的表格数据处理 Web 应用，支持上传、清洗、预览与导出。

## 核心文件列表（共8个文件）

### 1. 类型定义与工具 (2个文件)
- `src/types/table.ts` - 核心类型定义（TableProcessSpec, DatasetMeta, Message等）
- `src/lib/mockApi.ts` - Mock API 实现（上传、处理、导出）

### 2. 状态管理 (1个文件)
- `src/store/tableStore.ts` - Zustand 全局状态管理（数据集、流程、消息、参数）

### 3. 右侧助手组件 (1个文件)
- `src/components/AssistantPanel.tsx` - 右侧对话助手（chat/execute/fix 三种卡片）

### 4. 四个主工作区页面 (4个文件)
- `src/pages/FlowsPage.tsx` - 流程管理（显示已保存流程，加载/导出/删除）
- `src/pages/UploadPage.tsx` - 上传页面（文件上传、预览、概览）
- `src/pages/PreparePage.tsx` - 处理页面（参数编辑、预览对比、运行）
- `src/pages/ExportPage.tsx` - 导出页面（格式选项、预览、下载）

## 技术栈
- React + TypeScript
- Zustand (状态管理)
- shadcn/ui (UI组件)
- Tailwind CSS (样式)

## 实现策略
1. 先定义完整的类型系统和 Mock API
2. 实现全局状态管理
3. 构建右侧助手面板（核心交互）
4. 依次实现四个工作区页面
5. 集成顶部导航和布局

## 关键功能
- ✅ 对话驱动（chat/execute/fix）
- ✅ JSON 方案校验（TableProcessSpec）
- ✅ 参数应用与撤销
- ✅ 预览差异对比
- ✅ 流程保存/加载（localStorage）
- ✅ 错误处理与修复
- ✅ 导出包（数据+元数据）

## 文件关系
```
App.tsx (主布局 + 顶部导航)
├── AssistantPanel.tsx (右侧助手，常驻)
└── 工作区路由
    ├── FlowsPage.tsx
    ├── UploadPage.tsx
    ├── PreparePage.tsx
    └── ExportPage.tsx

状态层: tableStore.ts (全局状态)
工具层: mockApi.ts (模拟后端)
类型层: table.ts (类型定义)
```