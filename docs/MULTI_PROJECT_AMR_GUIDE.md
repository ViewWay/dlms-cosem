# 多项目实时抄表系统架构设计

## 系统概述

本系统基于 dlms-cosem 库，支持多项目、多电表、多安全级别的实时抄表系统。

## 需求分析

### 核心需求
1. **多项目管理**: 支持多个项目，每个项目有独立的电表群
2. **多种加密级别**: 
   - 无加密 (PUBLIC)
   - 低级安全 (LLS - 密码认证)
   - 高级安全 (HLS-GMAC - AES加密)
   - 证书认证 (HLS-CERT)
3. **实时抄表**: 支持实时数据读取和推送
4. **前后端分离**: REST API + WebSocket

### 业务场景
```
┌─────────────────────────────────────────────────────────────┐
│                      抄表系统主控台                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  居民小区    │  │  商业综合体  │  │  工业园区    │      │
│  │  (低加密)    │  │  (高加密)    │  │  (证书认证)  │      │
│  │  10个电表    │  │  5个电表     │  │  3个电表     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                   dlms-cosem 协议栈                          │
│  ┌─────────────────────────────────────────────────────┐  │
│  │   HDLC | TCP | UDP | TLS | NB-IoT | LoRaWAN      │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Vue3    │  │  React   │  │  移动端  │  │  大屏展示  │  │
│  │  管理界面  │  │  数据看板 │  │  APP     │  │          │  │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘  │
└────────┼───────────┼───────────┼───────────┼───────────┘
         │           │           │           │
┌────────▼───────────▼───────────▼───────────▼───────────┐
│                      API 网关层                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │            FastAPI / Flask + Celery              │   │
│  │  ┌───────────┐  ┌──────────┐  ┌──────────────┐  │   │
│  │  │ REST API  │  │ WebSocket│  │  任务队列     │  │   │
│  │  └─────┬─────┘  └─────┬────┘  └──────────────┘  │   │
│  └────────┼─────────────┼──────────────────────────┘   │
└───────────┼─────────────┼──────────────────────────────┘
            │             │
┌───────────▼─────────────▼──────────────────────────────┐
│                      业务逻辑层                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │          抄表引擎 (dlms-cosem-based)             │   │
│  │  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ 连接池管理    │  │  多加密支持  │              │   │
│  │  └──────────────┘  └──────────────┘              │   │
│  │  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ 实时抄读引擎  │  │  数据处理     │              │   │
│  │  └──────────────┘  └──────────────┘              │   │
│  └──────────────────────────────────────────────────┘   │
└───────────┬──────────────────────────────────────────────┘
            │
┌───────────▼──────────────────────────────────────────────┐
│                      数据层                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ PostgreSQL│  │  Redis   │  │ InfluxDB │  │  时序数据  │  │
│  │  元数据   │  │  缓存    │  │  电表数据 │  │           │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 数据库设计

### 项目表 (projects)
```sql
CREATE TABLE projects (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    security_level INT NOT NULL DEFAULT 1,  -- 0=PUBLIC, 1=LLS, 2=HLS, 3=CERT
    default_password VARCHAR(20),
    default_akey VARCHAR(40),
    default_ekey VARCHAR(40),
    default_client_title VARCHAR(20),
    realtime_enabled BOOLEAN DEFAULT TRUE,
    max_concurrent_reads INT DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 电表表 (meters)
```sql
CREATE TABLE meters (
    id VARCHAR(50) PRIMARY KEY,
    project_id VARCHAR(50) REFERENCES projects(id),
    name VARCHAR(100) NOT NULL,
    host VARCHAR(50) NOT NULL,
    port INT NOT NULL,
    client_address INT DEFAULT 16,
    server_address INT DEFAULT 1,
    security_level INT NOT NULL,
    password VARCHAR(20),
    akey VARCHAR(40),
    ekey VARCHAR(40),
    client_system_title VARCHAR(20),
    read_interval INT DEFAULT 300,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 电表数据表 (meter_data)
```sql
CREATE TABLE meter_data (
    id BIGSERIAL PRIMARY KEY,
    meter_id VARCHAR(50) REFERENCES meters(id),
    timestamp TIMESTAMP NOT NULL,
    voltage REAL,
    current REAL,
    active_power REAL,
    reactive_power REAL,
    power_factor REAL,
    total_energy REAL
);

CREATE INDEX idx_meter_data_timestamp ON meter_data(meter_id, timestamp);
```

## API 设计

### 1. 项目管理 API

```python
# GET /api/projects - 获取所有项目
# GET /api/projects/{id} - 获取项目详情
# POST /api/projects - 创建项目
# PUT /api/projects/{id} - 更新项目
# DELETE /api/projects/{id} - 删除项目
```

### 2. 电表管理 API

```python
# GET /api/projects/{project_id}/meters - 获取项目电表列表
# GET /api/meters/{meter_id} - 获取电表详情
# POST /api/meters - 添加电表
# PUT /api/meters/{meter_id} - 更新电表
# DELETE /api/meters/{meter_id} - 删除电表
```

### 3. 抄表 API

```python
# GET /api/meters/{meter_id}/read - 立即读取电表
# GET /api/projects/{project_id}/read - 读取项目所有电表
# POST /api/read/batch - 批量读取多个电表
# GET /api/read/status - 获取抄表状态
```

### 4. 实时数据 API

```python
# WS /api/realtime - WebSocket 实时数据推送
# GET /api/realtime/projects/{id}/latest - 获取最新数据
# GET /api/realtime/meters/{id}/latest - 获取电表最新数据
```

## 后端实现示例 (FastAPI)

```python
from fastapi import FastAPI, WebSocket, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio

app = FastAPI(title="多项目抄表系统")

# 全局抄表系统实例
meter_system = MultiProjectMeterSystem()

# Pydantic 模型
class ProjectCreate(BaseModel):
    project_id: str
    project_name: str
    security_level: int
    default_password: str = "00000000"

class MeterCreate(BaseModel):
    meter_id: str
    project_id: str
    name: str
    host: str
    port: int
    security_level: int
    read_interval: int = 300

# API 路由
@app.post("/api/projects")
async def create_project(project: ProjectCreate):
    """创建项目"""
    config = ProjectConfig(
        project_id=project.project_id,
        project_name=project.project_name,
        security_level=SecurityLevel(project.security_level),
        default_password=project.default_password,
    )
    meter_system.add_project(config)
    return {"status": "success", "project_id": project.project_id}

@app.post("/api/meters")
async def add_meter(meter: MeterCreate):
    """添加电表"""
    config = MeterConfig(
        meter_id=meter.meter_id,
        project_id=meter.project_id,
        name=meter.name,
        host=meter.host,
        port=meter.port,
        security_level=SecurityLevel(meter.security_level),
        read_interval=meter.read_interval,
    )
    meter_system.add_meter(config)
    return {"status": "success", "meter_id": meter.meter_id}

@app.get("/api/projects/{project_id}/meters")
async def get_project_meters(project_id: str):
    """获取项目电表列表"""
    meters = [m for m in meter_system.meters.values() 
               if m.project_id == project_id]
    return {
        "project_id": project_id,
        "meters": [
            {
                "meter_id": m.meter_id,
                "name": m.name,
                "host": m.host,
                "port": m.port,
                "security_level": m.security_level,
                "enabled": m.enabled,
            }
            for m in meters
        ]
    }

@app.get("/api/projects/{project_id}/read")
async def read_project_meters(project_id: str, realtime: bool = False):
    """读取项目所有电表"""
    results = await meter_system.read_project_meters(project_id, realtime)
    return {
        "project_id": project_id,
        "timestamp": datetime.now().isoformat(),
        "data": [
            {
                "meter_id": r.meter_id,
                "timestamp": r.timestamp.isoformat(),
                "voltage": r.voltage,
                "active_power": r.active_power,
                "total_energy": r.total_energy,
                "status": r.status.name,
            }
            for r in results
        ]
    }

@app.websocket("/api/realtime")
async def realtime_websocket(websocket: WebSocket, project_id: Optional[str] = None):
    """实时数据推送"""
    await websocket.accept()

    try:
        # 数据流
        async for data in meter_system._data_stream(project_id):
            await websocket.send_json({
                "meter_id": data.meter_id,
                "project_id": data.project_id,
                "timestamp": data.timestamp.isoformat(),
                "data": {
                    "voltage": data.voltage,
                    "current": data.current,
                    "active_power": data.active_power,
                    "total_energy": data.total_energy,
                },
                "status": data.status.name,
            })
    except WebSocketDisconnect:
        print(f"WebSocket 断开: {project_id}")

# 启动后台实时抄读
@app.on_event("startup")
async def startup_event():
    """启动时启动实时抄读"""
    asyncio.create_task(meter_system.start_realtime_reading())

@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    await meter_system.close()
```

## 前端实现 (Vue3 示例)

```vue
<template>
  <div class="amr-system">
    <!-- 项目列表 -->
    <div class="projects">
      <h2>项目列表</h2>
      <div v-for="project in projects" :key="project.id" 
           @click="selectProject(project.id)"
           :class="{ active: selectedProject === project.id }">
        {{ project.name }}
        <span class="security">{{ getSecurityName(project.security_level) }}</span>
      </div>
    </div>

    <!-- 电表列表 -->
    <div class="meters" v-if="selectedProject">
      <h2>{{ selectedProjectName }}</h2>
      <button @click="readAll">立即读取</button>
      <table>
        <thead>
          <tr>
            <th>电表</th>
            <th>电压 (V)</th>
            <th>电流 (A)</th>
            <th>功率 (W)</th>
            <th>电能 (kWh)</th>
            <th>状态</th>
            <th>更新时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="meter in meters" :key="meter.meter_id">
            <td>{{ meter.name }}</td>
            <td>{{ meter.voltage }}</td>
            <td>{{ meter.current }}</td>
            <td>{{ meter.active_power }}</td>
            <td>{{ meter.total_energy }}</td>
            <td>{{ getStatusName(meter.status) }}</td>
            <td>{{ meter.timestamp }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const projects = ref([])
const meters = ref([])
const selectedProject = ref(null)
const selectedProjectName = ref('')
let ws = null

// 加载项目
const loadProjects = async () => {
  const response = await fetch('/api/projects')
  projects.value = await response.json()
}

// 选择项目
const selectProject = async (projectId) => {
  selectedProject.value = projectId
  selectedProjectName.value = projects.value.find(p => p.id === projectId)?.name
  await loadMeters(projectId)
  
  // 连接 WebSocket
  connectWebSocket()
}

// 加载电表
const loadMeters = async (projectId) => {
  const response = await fetch(`/api/projects/${projectId}/meters`)
  const data = await response.json()
  meters.value = data.meters
}

// 读取所有电表
const readAll = async () => {
  const response = await fetch(`/api/projects/${selectedProject.value}/read?realtime=true`)
  const data = await response.json()
  
  // 更新电表数据
  data.data.forEach(item => {
    const meter = meters.value.find(m => m.meter_id === item.meter_id)
    if (meter) {
      Object.assign(meter, item)
    }
  })
}

// WebSocket 连接
const connectWebSocket = () => {
  if (ws) ws.close()
  
  ws = new WebSocket(`ws://localhost:8000/api/realtime?project_id=${selectedProject.value}`)
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    const meter = meters.value.find(m => m.meter_id === data.meter_id)
    if (meter) {
      Object.assign(meter, data.data)
      meter.timestamp = data.timestamp
      meter.status = data.status
    }
  }
}

// 辅助函数
const getSecurityName = (level) => {
  return ['无加密', '低级安全', '高级安全', '证书认证'][level]
}

const getStatusName = (status) => {
  return { 'ONLINE': '在线', 'OFFLINE': '离线', 'ERROR': '错误' }[status] || status
}

onMounted(() => {
  loadProjects()
})

onUnmounted(() => {
  if (ws) ws.close()
})
</script>
```

## 部署建议

### 1. 容器化部署
```dockerfile
# Dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Docker Compose
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/amr
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=amr
      - POSTGRES_USER=amr
      - POSTGRES_PASSWORD=amr123
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 3. 性能优化

1. **连接池**: 复用 TCP 连接，减少握手开销
2. **异步处理**: 使用 asyncio 处理并发抄表
3. **缓存**: Redis 缓存电表配置和最新数据
4. **消息队列**: Celery 处理定时任务
5. **数据库优化**: 时序数据库存储历史数据
