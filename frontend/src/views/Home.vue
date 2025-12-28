<!-- frontend/src/views/Home.vue -->
<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <n-grid :x-gap="16" :y-gap="16" :cols="4" style="margin-bottom: 24px;">
      <n-gi>
        <n-card :bordered="false" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
              <n-icon size="32">
                <cube-outline />
              </n-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">服务总数</div>
              <div class="stat-value">{{ stats.services.total }}</div>
              <div class="stat-detail">接口: {{ stats.endpoints.total }}</div>
            </div>
          </div>
        </n-card>
      </n-gi>

      <n-gi>
        <n-card :bordered="false" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
              <n-icon size="32">
                <file-tray-full-outline />
              </n-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">组合总数</div>
              <div class="stat-value">{{ stats.combinations.total }}</div>
              <div class="stat-detail">活跃: {{ stats.combinations.active }}</div>
            </div>
          </div>
        </n-card>
      </n-gi>

      <n-gi>
        <n-card :bordered="false" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
              <n-icon size="32">
                <server-outline />
              </n-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">MCP 服务</div>
              <div class="stat-value">{{ stats.mcp_servers.total }}</div>
              <div class="stat-detail">活跃: {{ stats.mcp_servers.active }}</div>
            </div>
          </div>
        </n-card>
      </n-gi>

      <n-gi>
        <n-card :bordered="false" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
              <n-icon size="32">
                <checkmark-circle-outline />
              </n-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">数据库</div>
              <div class="stat-value">SQLite</div>
              <div class="stat-detail">持久化存储</div>
            </div>
          </div>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 主内容区 -->
    <n-grid :x-gap="16" :y-gap="16" :cols="3">
      <!-- 左侧：最近项目 -->
      <n-gi :span="2">
        <n-card title="最近项目" :bordered="false" class="content-card">
          <template #header-extra>
            <n-tag :bordered="false" type="info" size="small">
              最近 5 条
            </n-tag>
          </template>

          <n-empty
            v-if="stats.recent_items.length === 0"
            description="暂无数据"
            style="margin: 40px 0;"
          />

          <n-timeline v-else>
            <n-timeline-item
              v-for="item in stats.recent_items"
              :key="`${item.type}-${item.id}`"
              :type="item.status === 'active' ? 'success' : 'default'"
            >
              <template #icon>
                <n-icon v-if="item.type === 'combination'">
                  <file-tray-full-outline />
                </n-icon>
                <n-icon v-else>
                  <server-outline />
                </n-icon>
              </template>

              <div class="timeline-content">
                <div class="timeline-header">
                  <span class="timeline-title">{{ item.name }}</span>
                  <n-tag
                    :type="item.type === 'combination' ? 'warning' : 'info'"
                    size="small"
                    :bordered="false"
                  >
                    {{ item.type === 'combination' ? '组合' : 'MCP服务' }}
                  </n-tag>
                </div>
                <div class="timeline-time">
                  {{ formatTime(item.created_at) }}
                </div>
              </div>
            </n-timeline-item>
          </n-timeline>
        </n-card>
      </n-gi>

      <!-- 右侧：快捷操作 + 系统信息 -->
      <n-gi :span="1">
        <!-- 快捷操作 -->
        <n-card title="快捷操作" :bordered="false" class="content-card" style="margin-bottom: 16px;">
          <n-space vertical :size="12">
            <n-button
              type="primary"
              block
              @click="router.push({ name: 'McpCombination' })"
              :render-icon="renderIcon(AddCircleOutline)"
            >
              创建组合
            </n-button>
            <n-button
              type="info"
              block
              @click="router.push({ name: 'McpManagement' })"
              :render-icon="renderIcon(AddCircleOutline)"
            >
              创建 MCP 服务
            </n-button>
          </n-space>
        </n-card>

        <!-- 状态分布 -->
        <n-card title="状态分布" :bordered="false" class="content-card">
          <div class="status-stats">
            <div class="status-item">
              <div class="status-label">
                <n-icon color="#18a058" size="18">
                  <checkmark-circle-outline />
                </n-icon>
                <span>活跃组合</span>
              </div>
              <div class="status-value">{{ stats.combinations.active }}</div>
            </div>
            <n-divider style="margin: 12px 0;" />
            <div class="status-item">
              <div class="status-label">
                <n-icon color="#d03050" size="18">
                  <close-circle-outline />
                </n-icon>
                <span>停用组合</span>
              </div>
              <div class="status-value">{{ stats.combinations.inactive }}</div>
            </div>
            <n-divider style="margin: 12px 0;" />
            <div class="status-item">
              <div class="status-label">
                <n-icon color="#18a058" size="18">
                  <checkmark-circle-outline />
                </n-icon>
                <span>活跃服务</span>
              </div>
              <div class="status-value">{{ stats.mcp_servers.active }}</div>
            </div>
            <n-divider style="margin: 12px 0;" />
            <div class="status-item">
              <div class="status-label">
                <n-icon color="#d03050" size="18">
                  <close-circle-outline />
                </n-icon>
                <span>停用服务</span>
              </div>
              <div class="status-value">{{ stats.mcp_servers.inactive }}</div>
            </div>
          </div>
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue';
import { useRouter } from 'vue-router';
import {
  NCard,
  NGrid,
  NGi,
  NIcon,
  NTag,
  NTimeline,
  NTimelineItem,
  NButton,
  NSpace,
  NDivider,
  NEmpty,
  useMessage
} from 'naive-ui';
import {
  CubeOutline,
  FileTrayFullOutline,
  ServerOutline,
  CheckmarkCircleOutline,
  CloseCircleOutline,
  AddCircleOutline
} from '@vicons/ionicons5';
import { getDashboardStats } from '../services/api';

const router = useRouter();
const message = useMessage();

interface DashboardStats {
  services: {
    total: number;
  };
  combinations: {
    total: number;
    active: number;
    inactive: number;
  };
  mcp_servers: {
    total: number;
    active: number;
    inactive: number;
  };
  endpoints: {
    total: number;
  };
  recent_items: Array<{
    id: number;
    name: string;
    type: 'combination' | 'mcp_server';
    status: string;
    created_at: string;
  }>;
}

const stats = ref<DashboardStats>({
  services: { total: 0 },
  combinations: { total: 0, active: 0, inactive: 0 },
  mcp_servers: { total: 0, active: 0, inactive: 0 },
  endpoints: { total: 0 },
  recent_items: []
});

const loadStats = async () => {
  try {
    const data = await getDashboardStats();
    stats.value = data;
  } catch (error) {
    console.error('Failed to load dashboard stats:', error);
    message.error('加载统计数据失败');
  }
};

const formatTime = (isoString: string) => {
  const date = new Date(isoString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return '刚刚';
  if (minutes < 60) return `${minutes} 分钟前`;
  if (hours < 24) return `${hours} 小时前`;
  if (days < 7) return `${days} 天前`;

  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
};

const renderIcon = (icon: any) => {
  return () => h(NIcon, null, { default: () => h(icon) });
};

onMounted(() => {
  loadStats();
});
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.stat-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
}

.stat-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  transform: translateY(-4px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-info {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #333;
  line-height: 1.2;
}

.stat-detail {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.content-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.timeline-content {
  padding: 4px 0;
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.timeline-title {
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.timeline-time {
  font-size: 12px;
  color: #999;
}

.status-stats {
  padding: 8px 0;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #666;
}

.status-value {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}
</style>
