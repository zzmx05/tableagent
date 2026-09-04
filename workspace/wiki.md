# Project Summary
该项目致力于开发一款基于Web的智能对话数据处理平台，支持用户通过交互式界面进行数据上传、清洗、预览及导出，旨在提升数据处理的效率与准确性。用户可以处理多种数据格式，并通过直观的操作流程来管理和分析数据流。

# Project Module Description
- **AssistantPanel**: 提供对话助手界面，支持用户输入操作指令并显示处理结果。
- **FlowsPage**: 管理和展示已保存的数据处理流，支持导入、导出和编辑功能。
- **UploadPage**: 处理数据上传，支持CSV、TSV和Excel文件格式。
- **PreparePage**: 允许用户配置数据处理参数并预览处理结果。
- **ExportPage**: 负责导出处理后的数据和相关元数据。

# Directory Tree
```
shadcn-ui/
├── README.md               # 项目说明文件
├── components.json         # 组件配置文件
├── eslint.config.js        # ESLint 配置文件
├── index.html              # 项目入口 HTML 文件
├── package.json            # 项目依赖和脚本
├── postcss.config.js       # PostCSS 配置文件
├── public/                 # 公共资源
│   ├── favicon.svg         # 网站图标
│   └── robots.txt          # 搜索引擎爬虫协议
├── src/                    # 源代码
│   ├── App.css             # 样式文件
│   ├── App.tsx             # 主应用组件
│   ├── components/         # UI 组件
│   ├── hooks/              # 自定义 Hook
│   ├── lib/                # 工具函数和 API 模拟
│   ├── pages/              # 页面组件
│   ├── store/              # 状态管理
│   └── types/              # 类型定义
├── tailwind.config.ts      # Tailwind CSS 配置文件
├── template_config.json     # 模板配置文件
├── todo.md                 # 待办事项
├── tsconfig.app.json       # TypeScript 配置
├── tsconfig.json           # TypeScript 配置
├── tsconfig.node.json      # Node.js TypeScript 配置
└── vite.config.ts          # Vite 配置文件
```

# File Description Inventory
- `src/types/table.ts`: 定义项目中使用的类型，包括数据处理规范、数据集元数据等。
- `src/lib/mockApi.ts`: 模拟后端 API，用于数据上传、处理和导出。
- `src/store/tableStore.ts`: Zustand 状态管理，管理应用状态和数据流。
- `src/components/AssistantPanel.tsx`: 对话助手组件，处理用户输入和展示处理结果。
- `src/pages/FlowsPage.tsx`: 流程管理页面，展示和操作已保存的数据处理流。
- `src/pages/UploadPage.tsx`: 数据上传页面，处理文件上传和参数设置。
- `src/pages/PreparePage.tsx`: 数据处理参数配置页面，预览处理结果。
- `src/pages/ExportPage.tsx`: 数据导出页面，设置导出选项并下载处理后的数据。

# Technology Stack
- **React**: 用于构建用户界面。
- **TypeScript**: 提供类型安全的开发体验。
- **Zustand**: 状态管理库。
- **shadcn/ui**: UI 组件库。
- **Tailwind CSS**: 用于样式设计。

# Usage
1. 安装依赖:
   ```bash
   cd /workspace/shadcn-ui
   pnpm install
   ```
2. 构建项目:
   ```bash
   pnpm run build
   ```
3. 运行项目:
   ```bash
   pnpm run start
   ```
