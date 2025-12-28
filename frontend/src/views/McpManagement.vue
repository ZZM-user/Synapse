<!-- frontend/src/views/McpManagement.vue -->
<template>
  <div class="mcp-management-page">
    <div class="page-header">
      <n-button type="primary" @click="handleAddServer">
        新增 MCP 服务
      </n-button>
      <n-input
          v-model:value="searchQuery"
          placeholder="搜索 MCP 服务名称、前缀或描述"
          clearable
          style="width: 350px;"
      />
    </div>

    <n-spin :show="loadingServers">
      <n-data-table
          :columns="columns"
          :data="filteredServers"
          :pagination="false"
          :bordered="false"
          :max-height="500"
      />
    </n-spin>

    <!-- 新增/编辑 MCP 服务 Modal -->
    <n-modal v-model:show="showServerModal">
      <n-card
          style="width: 700px"
          :title="editingServer ? '编辑 MCP 服务' : '新增 MCP 服务'"
          :bordered="false"
          size="huge"
          role="dialog"
          aria-modal="true"
      >
        <n-form ref="formRef" :model="serverForm" :rules="rules">
          <n-form-item path="name" label="服务名称">
            <n-input v-model:value="serverForm.name" placeholder="例如：用户管理服务"/>
          </n-form-item>
          <n-form-item path="prefix" label="MCP 前缀">
            <n-input
                v-model:value="serverForm.prefix"
                placeholder="例如：user-service（唯一标识，只能包含字母、数字、下划线和连字符）"
                :disabled="!!editingServer"
            />
            <template #feedback>
              <span style="color: #999;">MCP 前缀创建后不可修改，将用于生成 MCP 端点</span>
            </template>
          </n-form-item>
          <n-form-item path="description" label="服务描述">
            <n-input
                v-model:value="serverForm.description"
                type="textarea"
                placeholder="描述这个 MCP 服务的用途"
                :autosize="{minRows: 2, maxRows: 4}"
            />
          </n-form-item>
          <n-form-item label="已选择的组合">
            <div class="combinations-list">
              <n-tag
                  v-for="combId in serverForm.combination_ids"
                  :key="combId"
                  closable
                  @close="handleRemoveCombination(combId)"
                  style="margin: 4px;"
                  type="info"
              >
                {{ getCombinationName(combId) }}
              </n-tag>
              <n-button
                  v-if="serverForm.combination_ids.length === 0"
                  text
                  type="primary"
                  @click="() => { combinationSelectorMode = 'server'; showCombinationSelector = true; }"
              >
                + 点击选择组合
              </n-button>
            </div>
          </n-form-item>
          <n-button
              v-if="serverForm.combination_ids.length > 0"
              type="primary"
              dashed
              @click="() => { combinationSelectorMode = 'server'; showCombinationSelector = true; }"
              style="margin-top: 8px; width: 100%;"
          >
            添加更多组合
          </n-button>
        </n-form>
        <template #footer>
          <n-button @click="showServerModal = false">取消</n-button>
          <n-button type="primary" @click="handleSaveServer" style="margin-left: 12px;">保存</n-button>
        </template>
      </n-card>
    </n-modal>

    <!-- 组合选择器 Modal -->
    <n-modal v-model:show="showCombinationSelector">
      <n-card
          style="width: 900px"
          title="选择组合"
          :bordered="false"
          size="huge"
          role="dialog"
          aria-modal="true"
      >
        <template #header-extra>
          <n-button @click="showCombinationSelector = false" text>
            <n-icon :size="20">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                <path
                    d="M18.3 5.71a.996.996 0 0 0-1.41 0L12 10.59L7.11 5.7A.996.996 0 1 0 5.7 7.11L10.59 12L5.7 16.89a.996.996 0 1 0 1.41 1.41L12 13.41l4.89 4.89a.996.996 0 1 0 1.41-1.41L13.41 12l4.89-4.89c.38-.38.38-1.02 0-1.4z"
                    fill="currentColor"></path>
              </svg>
            </n-icon>
          </n-button>
        </template>

        <n-input
            v-model:value="combinationSearchQuery"
            placeholder="搜索组合名称或描述"
            clearable
            style="margin-bottom: 16px;"
        />

        <n-spin :show="loadingCombinations">
          <n-data-table
              :columns="combinationSelectorColumns"
              :data="filteredCombinations"
              :max-height="400"
              :row-key="(row: Combination) => row.id"
          />
        </n-spin>

        <template #footer>
          <n-button @click="showCombinationSelector = false">关闭</n-button>
        </template>
      </n-card>
    </n-modal>

    <!-- 管理组合 Modal -->
    <n-modal v-model:show="showManageCombinationsModal">
      <n-card
          style="width: 900px"
          :title="`管理「${editingServer?.name}」的组合`"
          :bordered="false"
          size="huge"
          role="dialog"
          aria-modal="true"
      >
        <div class="manage-combinations-header">
          <n-input
              v-model:value="manageCombinationsSearchQuery"
              placeholder="搜索组合名称或描述"
              clearable
              style="width: 300px;"
          />
          <n-button type="primary" @click="handleOpenCombinationSelector">
            添加组合
          </n-button>
        </div>

        <n-data-table
            :columns="manageCombinationsColumns"
            :data="filteredManageCombinations"
            :max-height="400"
            style="margin-top: 16px;"
            :row-key="(row: any) => row.id"
        />

        <template #footer>
          <n-button @click="handleCloseManageCombinations">取消</n-button>
          <n-button type="primary" @click="handleSaveManageCombinations" style="margin-left: 12px;">
            保存
          </n-button>
        </template>
      </n-card>
    </n-modal>

    <!-- MCP 配置查看 Modal -->
    <n-modal v-model:show="showConfigModal">
      <n-card
          style="width: 800px"
          title="MCP Server 配置"
          :bordered="false"
          size="huge"
          role="dialog"
          aria-modal="true"
      >
        <n-spin :show="loadingConfig">
          <div v-if="currentMcpConfig" class="config-container">
            <div class="config-info">
              <h3>{{ currentMcpConfig.note }}</h3>
              <p>{{ currentMcpConfig.usage }}</p>
            </div>

            <div class="config-code">
              <div class="code-header">
                <span>配置文件（claude_desktop_config.json）</span>
                <n-button size="small" type="primary" @click="handleCopyConfig">
                  复制配置
                </n-button>
              </div>
              <pre><code>{{ JSON.stringify(currentMcpConfig.example, null, 2) }}</code></pre>
            </div>

            <div class="config-details">
              <h3>服务端点</h3>
              <n-descriptions bordered :column="1">
                <n-descriptions-item label="服务名称">
                  {{ Object.keys(currentMcpConfig.config)[0] }}
                </n-descriptions-item>
                <n-descriptions-item label="MCP 端点">
                  <n-tag type="success">{{ currentMcpConfig.endpoint }}</n-tag>
                  <p style="margin: 4px 0 0 0; font-size: 12px; color: #666;">
                    此端点同时支持 GET（SSE流）和 POST（JSON-RPC请求）
                  </p>
                </n-descriptions-item>
              </n-descriptions>
            </div>

            <div class="config-help">
              <h3>使用说明</h3>
              <n-descriptions bordered :column="1">
                <n-descriptions-item label="Claude Desktop">
                  {{ currentMcpConfig.instructions.claude_desktop }}
                </n-descriptions-item>
                <n-descriptions-item label="Cursor">
                  {{ currentMcpConfig.instructions.cursor }}
                </n-descriptions-item>
                <n-descriptions-item label="通用步骤">
                  {{ currentMcpConfig.instructions.general }}
                </n-descriptions-item>
              </n-descriptions>

              <div style="margin-top: 16px; padding: 12px; background: #f0f9ff; border-radius: 6px; border-left: 4px solid #0ea5e9;">
                <p style="margin: 0; color: #0369a1; font-weight: 500;">💡 重要提示</p>
                <ul style="margin: 8px 0 0 0; padding-left: 20px; color: #075985;">
                  <li v-for="(tip, index) in currentMcpConfig.important" :key="index">{{ tip }}</li>
                </ul>
              </div>
            </div>
          </div>
        </n-spin>

        <template #footer>
          <n-button @click="showConfigModal = false">关闭</n-button>
        </template>
      </n-card>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import {computed, h, onMounted, ref} from 'vue';
import type {DataTableColumns, FormInst, FormValidationError} from 'naive-ui';
import {
  NButton,
  NCard,
  NDataTable,
  NDescriptions,
  NDescriptionsItem,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NModal,
  NSpin,
  NSwitch,
  NTag,
  useMessage
} from 'naive-ui';
import type {
  McpServer,
  Combination
} from '../services/api';
import {
  getMcpServers,
  createMcpServer,
  updateMcpServer,
  toggleMcpServerStatus,
  deleteMcpServer,
  getCombinations,
  getMcpServerConfig
} from '../services/api';

// --- Data & State ---
const message = useMessage();
const formRef = ref<FormInst | null>(null);

// MCP 服务管理状态
const mcpServers = ref<McpServer[]>([]);
const loadingServers = ref(false);
const searchQuery = ref('');
const showServerModal = ref(false);
const editingServer = ref<McpServer | null>(null);
const serverForm = ref({
  name: '',
  prefix: '',
  description: '',
  combination_ids: [] as number[]
});

// 组合数据
const combinations = ref<Combination[]>([]);
const loadingCombinations = ref(false);

// 组合选择器状态
const showCombinationSelector = ref(false);
const combinationSearchQuery = ref('');
const combinationSelectorMode = ref<'server' | 'manage'>('server');

// 管理组合状态
const showManageCombinationsModal = ref(false);
const manageCombinationsSearchQuery = ref('');
const tempCombinationIds = ref<number[]>([]);

// MCP 配置查看状态
const showConfigModal = ref(false);
const currentMcpConfig = ref<any>(null);
const loadingConfig = ref(false);

// --- Lifecycle ---
onMounted(async () => {
  await Promise.all([loadServers(), loadCombinations()]);
});

// --- Computed ---
const filteredServers = computed(() => {
  if (!searchQuery.value) {
    return mcpServers.value;
  }
  const query = searchQuery.value.toLowerCase();
  return mcpServers.value.filter(
      server =>
          server.name.toLowerCase().includes(query) ||
          server.prefix.toLowerCase().includes(query) ||
          server.description.toLowerCase().includes(query)
  );
});

const filteredCombinations = computed(() => {
  if (!combinationSearchQuery.value) {
    return combinations.value;
  }
  const query = combinationSearchQuery.value.toLowerCase();
  return combinations.value.filter(
      combination =>
          combination.name.toLowerCase().includes(query) ||
          combination.description.toLowerCase().includes(query)
  );
});

const filteredManageCombinations = computed(() => {
  const managedCombinations = combinations.value.filter(c => tempCombinationIds.value.includes(c.id));

  if (!manageCombinationsSearchQuery.value) {
    return managedCombinations;
  }
  const query = manageCombinationsSearchQuery.value.toLowerCase();
  return managedCombinations.filter(
      combination =>
          combination.name.toLowerCase().includes(query) ||
          combination.description.toLowerCase().includes(query)
  );
});

// --- Form Rules ---
const rules = {
  name: {required: true, message: '请输入服务名称', trigger: 'blur'},
  prefix: {
    required: true,
    message: '请输入 MCP 前缀',
    trigger: 'blur',
    validator: (_rule: any, value: string) => {
      if (!value) {
        return new Error('请输入 MCP 前缀');
      }
      if (!/^[a-zA-Z0-9_-]+$/.test(value)) {
        return new Error('MCP 前缀只能包含字母、数字、下划线和连字符');
      }
      return true;
    }
  },
  description: {required: false},
};

// --- Table Columns ---
const columns = computed<DataTableColumns<McpServer>>(() => [
  {title: '服务名称', key: 'name'},
  {title: 'MCP 前缀', key: 'prefix'},
  {
    title: '描述',
    key: 'description',
    ellipsis: {tooltip: true}
  },
  {
    title: '组合数量',
    key: 'combination_ids',
    render: (row) => h('span', {}, row.combination_ids.length)
  },
  {
    title: '状态',
    key: 'status',
    render: (row) =>
        h(NSwitch, {
          value: row.status === 'active',
          onUpdateValue: (value: boolean) => handleToggleStatus(row, value)
        })
  },
  {
    title: '更新时间',
    key: 'updatedAt',
    render: (row) => h('span', {}, new Date(row.updatedAt).toLocaleDateString())
  },
  {
    title: '操作',
    key: 'actions',
    render: (row) =>
        h('div', {style: {display: 'flex', gap: '8px'}}, [
          h(
              NButton,
              {size: 'small', onClick: () => handleViewConfig(row)},
              {default: () => '查看配置'}
          ),
          h(
              NButton,
              {size: 'small', onClick: () => handleEditServer(row)},
              {default: () => '编辑'}
          ),
          h(
              NButton,
              {size: 'small', onClick: () => handleManageCombinations(row)},
              {default: () => '管理组合'}
          ),
          h(
              NButton,
              {
                size: 'small',
                type: 'error',
                ghost: true,
                onClick: () => handleDeleteServer(row)
              },
              {default: () => '删除'}
          )
        ])
  }
]);

const combinationSelectorColumns = computed<DataTableColumns<Combination>>(() => [
  {title: '组合名称', key: 'name'},
  {title: '描述', key: 'description', ellipsis: {tooltip: true}},
  {
    title: '接口数量',
    key: 'endpoints',
    render: (row) => h('span', {}, row.endpoints.length)
  },
  {
    title: '操作',
    key: 'actions',
    render: (row) => {
      const isAdded = combinationSelectorMode.value === 'manage'
          ? tempCombinationIds.value.includes(row.id)
          : serverForm.value.combination_ids.includes(row.id);

      return h(
          NButton,
          {
            size: 'small',
            type: isAdded ? 'default' : 'primary',
            disabled: isAdded,
            onClick: () => {
              if (combinationSelectorMode.value === 'manage') {
                handleAddCombinationToManage(row.id);
              } else {
                handleAddCombination(row.id);
              }
            }
          },
          {default: () => isAdded ? '已添加' : '添加'}
      );
    }
  }
]);

const manageCombinationsColumns = computed<DataTableColumns<Combination>>(() => [
  {title: '组合名称', key: 'name'},
  {title: '描述', key: 'description', ellipsis: {tooltip: true}},
  {
    title: '接口数量',
    key: 'endpoints',
    render: (row) => h('span', {}, row.endpoints.length)
  },
  {
    title: '操作',
    key: 'actions',
    width: 80,
    render: (row) =>
        h(
            NButton,
            {
              size: 'small',
              type: 'error',
              ghost: true,
              onClick: () => handleRemoveCombinationFromManage(row.id)
            },
            {default: () => '删除'}
        )
  }
]);

// --- Methods ---
const loadServers = async () => {
  loadingServers.value = true;
  try {
    mcpServers.value = await getMcpServers();
  } catch (error: unknown) {
    if (error instanceof Error) {
      message.error(`加载 MCP 服务列表失败: ${error.message}`);
    } else {
      message.error('加载 MCP 服务列表失败: 未知错误');
    }
  } finally {
    loadingServers.value = false;
  }
};

const loadCombinations = async () => {
  loadingCombinations.value = true;
  try {
    combinations.value = await getCombinations();
  } catch (error: unknown) {
    if (error instanceof Error) {
      message.error(`加载组合列表失败: ${error.message}`);
    } else {
      message.error('加载组合列表失败: 未知错误');
    }
  } finally {
    loadingCombinations.value = false;
  }
};

const getCombinationName = (id: number): string => {
  const combination = combinations.value.find(c => c.id === id);
  return combination ? combination.name : `组合 #${id}`;
};

const handleAddServer = () => {
  editingServer.value = null;
  serverForm.value = {
    name: '',
    prefix: '',
    description: '',
    combination_ids: []
  };
  showServerModal.value = true;
};

const handleEditServer = (server: McpServer) => {
  editingServer.value = server;
  serverForm.value = {
    name: server.name,
    prefix: server.prefix,
    description: server.description,
    combination_ids: [...server.combination_ids]
  };
  showServerModal.value = true;
};

const handleSaveServer = async () => {
  formRef.value?.validate(async (errors: Array<FormValidationError> | undefined) => {
    if (!errors) {
      try {
        if (editingServer.value) {
          // 编辑模式
          await updateMcpServer(editingServer.value.id, {
            name: serverForm.value.name,
            description: serverForm.value.description,
            combination_ids: serverForm.value.combination_ids
          });
          message.success('MCP 服务更新成功');
        } else {
          // 新增模式
          await createMcpServer({
            name: serverForm.value.name,
            prefix: serverForm.value.prefix,
            description: serverForm.value.description,
            combination_ids: serverForm.value.combination_ids
          });
          message.success('MCP 服务创建成功');
        }
        showServerModal.value = false;
        await loadServers();
      } catch (error: unknown) {
        if (error instanceof Error) {
          message.error(`保存失败: ${error.message}`);
        } else {
          message.error('保存失败: 未知错误');
        }
      }
    } else {
      message.error('请填写所有必填项');
    }
  });
};

const handleDeleteServer = async (server: McpServer) => {
  try {
    await deleteMcpServer(server.id);
    message.success(`MCP 服务 "${server.name}" 已删除`);
    await loadServers();
  } catch (error: unknown) {
    if (error instanceof Error) {
      message.error(`删除失败: ${error.message}`);
    } else {
      message.error('删除失败: 未知错误');
    }
  }
};

const handleToggleStatus = async (server: McpServer, value: boolean) => {
  try {
    await toggleMcpServerStatus(server.id, value ? 'active' : 'inactive');
    message.success(`MCP 服务已${value ? '启用' : '停用'}`);
    await loadServers();
  } catch (error: unknown) {
    if (error instanceof Error) {
      message.error(`状态切换失败: ${error.message}`);
    } else {
      message.error('状态切换失败: 未知错误');
    }
  }
};

const handleAddCombination = (combinationId: number) => {
  if (!serverForm.value.combination_ids.includes(combinationId)) {
    serverForm.value.combination_ids.push(combinationId);
    message.success('组合已添加');
  }
};

const handleRemoveCombination = (combinationId: number) => {
  serverForm.value.combination_ids = serverForm.value.combination_ids.filter(id => id !== combinationId);
};

const handleManageCombinations = (server: McpServer) => {
  editingServer.value = server;
  tempCombinationIds.value = [...server.combination_ids];
  showManageCombinationsModal.value = true;
  manageCombinationsSearchQuery.value = '';
};

const handleOpenCombinationSelector = () => {
  combinationSelectorMode.value = 'manage';
  showCombinationSelector.value = true;
};

const handleCloseManageCombinations = () => {
  showManageCombinationsModal.value = false;
  editingServer.value = null;
  tempCombinationIds.value = [];
};

const handleSaveManageCombinations = async () => {
  if (!editingServer.value) return;

  try {
    await updateMcpServer(editingServer.value.id, {
      combination_ids: tempCombinationIds.value
    });
    message.success('组合管理保存成功');
    showManageCombinationsModal.value = false;
    await loadServers();
  } catch (error: unknown) {
    if (error instanceof Error) {
      message.error(`保存失败: ${error.message}`);
    } else {
      message.error('保存失败: 未知错误');
    }
  }
};

const handleAddCombinationToManage = (combinationId: number) => {
  if (!tempCombinationIds.value.includes(combinationId)) {
    tempCombinationIds.value.push(combinationId);
    message.success('组合已添加');
  }
};

const handleRemoveCombinationFromManage = (combinationId: number) => {
  tempCombinationIds.value = tempCombinationIds.value.filter(id => id !== combinationId);
  message.success('组合已从列表中移除');
};

const handleViewConfig = async (server: McpServer) => {
  loadingConfig.value = true;
  try {
    const config = await getMcpServerConfig(server.prefix);
    currentMcpConfig.value = config;
    showConfigModal.value = true;
  } catch (error: unknown) {
    if (error instanceof Error) {
      message.error(`获取配置失败: ${error.message}`);
    } else {
      message.error('获取配置失败: 未知错误');
    }
  } finally {
    loadingConfig.value = false;
  }
};

const handleCopyConfig = () => {
  if (!currentMcpConfig.value) return;

  const configText = JSON.stringify(currentMcpConfig.value.example, null, 2);
  navigator.clipboard.writeText(configText).then(() => {
    message.success('配置已复制到剪贴板');
  }).catch(() => {
    message.error('复制失败，请手动复制');
  });
};
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.combinations-list {
  min-height: 60px;
  padding: 12px;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}

.manage-combinations-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.config-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.config-info h3,
.config-details h3,
.config-help h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
}

.config-info p {
  margin: 0;
  color: #666;
}

.config-code {
  background: #f5f5f5;
  border-radius: 6px;
  padding: 16px;
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 600;
}

.config-code pre {
  margin: 0;
  background: #fff;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}

.config-code code {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.config-help ol {
  margin: 0;
  padding-left: 20px;
}

.config-help li {
  margin-bottom: 8px;
  color: #666;
}

</style>
