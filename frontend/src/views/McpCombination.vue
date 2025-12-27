<!-- frontend/src/views/McpCombination.vue -->
<template>
  <div class="mcp-combination-page">
    <div class="page-header">
      <n-button type="primary" @click="handleAddCombination">
        新增组合
      </n-button>
      <n-input
          v-model:value="searchQuery"
          placeholder="搜索组合名称或描述"
          clearable
          style="width: 300px;"
      />
    </div>

    <n-data-table
        :columns="columns"
        :data="filteredCombinations"
        :pagination="false"
        :bordered="false"
        :max-height="500"
    />

    <!-- 新增/编辑组合 Modal -->
    <n-modal v-model:show="showCombinationModal">
      <n-card
          style="width: 700px"
          :title="editingCombination ? '编辑组合' : '新增组合'"
          :bordered="false"
          size="huge"
          role="dialog"
          aria-modal="true"
      >
        <n-form ref="formRef" :model="combinationForm" :rules="rules">
          <n-form-item path="name" label="组合名称">
            <n-input v-model:value="combinationForm.name" placeholder="例如：用户服务组合"/>
          </n-form-item>
          <n-form-item path="description" label="组合描述">
            <n-input
                v-model:value="combinationForm.description"
                type="textarea"
                placeholder="描述这个组合的用途"
                :autosize="{minRows: 2, maxRows: 4}"
            />
          </n-form-item>
          <n-form-item label="已添加的接口">
            <div class="endpoints-list">
              <n-tag
                  v-for="endpoint in combinationForm.endpoints"
                  :key="`${endpoint.serviceName}-${endpoint.path}-${endpoint.method}`"
                  closable
                  @close="handleRemoveEndpoint(endpoint)"
                  style="margin: 4px;"
              >
                {{ endpoint.method }} {{ endpoint.path }} ({{ endpoint.serviceName }})
              </n-tag>
              <n-button
                  v-if="combinationForm.endpoints.length === 0"
                  text
                  type="primary"
                  @click="() => { endpointSelectorMode = 'combination'; showEndpointSelector = true; }"
              >
                + 点击添加接口
              </n-button>
            </div>
          </n-form-item>
          <n-button
              v-if="combinationForm.endpoints.length > 0"
              type="primary"
              dashed
              @click="() => { endpointSelectorMode = 'combination'; showEndpointSelector = true; }"
              style="margin-top: 8px; width: 100%;"
          >
            添加更多接口
          </n-button>
        </n-form>
        <template #footer>
          <n-button @click="showCombinationModal = false">取消</n-button>
          <n-button type="primary" @click="handleSaveCombination" style="margin-left: 12px;">保存</n-button>
        </template>
      </n-card>
    </n-modal>

    <!-- 管理接口 Modal -->
    <n-modal v-model:show="showManageEndpointsModal">
      <n-card
          style="width: 900px"
          :title="`管理「${editingCombination?.name}」的接口`"
          :bordered="false"
          size="huge"
          role="dialog"
          aria-modal="true"
      >
        <div class="manage-endpoints-header">
          <n-input
              v-model:value="manageEndpointsSearchQuery"
              placeholder="搜索接口路径或描述"
              clearable
              style="width: 300px;"
          />
          <n-button type="primary" @click="handleOpenEndpointSelector">
            添加接口
          </n-button>
        </div>

        <n-data-table
            :columns="manageEndpointsColumns"
            :data="filteredManageEndpoints"
            :max-height="400"
            style="margin-top: 16px;"
            :row-key="(row: CombinationEndpoint) => `${row.path}-${row.method}`"
        />

        <template #footer>
          <n-button @click="handleCloseManageEndpoints">取消</n-button>
          <n-button type="primary" @click="handleSaveManageEndpoints" style="margin-left: 12px;">
            保存
          </n-button>
        </template>
      </n-card>
    </n-modal>

    <!-- 接口选择器 Modal -->
    <n-modal v-model:show="showEndpointSelector">
      <n-card
          style="width: 1000px"
          title="选择接口"
          :bordered="false"
          size="huge"
          role="dialog"
          aria-modal="true"
      >
        <template #header-extra>
          <n-button @click="showEndpointSelector = false" text>
            <n-icon :size="20">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                <path
                    d="M18.3 5.71a.996.996 0 0 0-1.41 0L12 10.59L7.11 5.7A.996.996 0 1 0 5.7 7.11L10.59 12L5.7 16.89a.996.996 0 1 0 1.41 1.41L12 13.41l4.89 4.89a.996.996 0 1 0 1.41-1.41L13.41 12l4.89-4.89c.38-.38.38-1.02 0-1.4z"
                    fill="currentColor"></path>
              </svg>
            </n-icon>
          </n-button>
        </template>

        <n-steps :current="currentStep" style="margin-bottom: 24px;">
          <n-step title="选择服务"/>
          <n-step title="选择接口"/>
        </n-steps>

        <!-- 步骤 1: 选择服务 -->
        <div v-if="currentStep === 1">
          <n-input
              v-model:value="serviceSearchQuery"
              placeholder="搜索服务"
              clearable
              style="margin-bottom: 16px;"
          />
          <n-list bordered>
            <n-list-item
                v-for="service in filteredServices"
                :key="service.key"
                style="cursor: pointer;"
                @click="handleSelectService(service)"
            >
              <template #prefix>
                <n-icon :size="24">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
                    <path
                        d="M448 256L272 88v96C103.57 184 64 304.77 64 424c48.61-62.24 91.6-96 208-96v96z"
                        fill="none"
                        stroke="currentColor"
                        stroke-linejoin="round"
                        stroke-width="32"/>
                  </svg>
                </n-icon>
              </template>
              <n-thing :title="service.name" :description="service.url">
                <template #description>
                  <n-text depth="3">{{ service.type }} - {{ service.url }}</n-text>
                </template>
              </n-thing>
            </n-list-item>
          </n-list>
        </div>

        <!-- 步骤 2: 选择接口 -->
        <div v-if="currentStep === 2">
          <n-button @click="currentStep = 1" style="margin-bottom: 16px;">
            ← 返回选择服务
          </n-button>
          <n-alert
              type="info"
              :title="`当前服务：${selectedService?.name}`"
              style="margin-bottom: 16px;"
          />
          <n-input
              v-model:value="endpointSearchQuery"
              placeholder="搜索接口路径或描述"
              clearable
              style="margin-bottom: 16px;"
          />
          <n-spin :show="loadingEndpoints">
            <n-data-table
                :columns="endpointSelectorColumns"
                :data="filteredEndpoints"
                :max-height="400"
                :row-key="(row: ApiEndpoint) => `${row.path}-${row.method}`"
            />
          </n-spin>
        </div>

        <template #footer>
          <n-button @click="showEndpointSelector = false">关闭</n-button>
        </template>
      </n-card>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import {computed, h, onMounted, ref} from 'vue';
import type {DataTableColumns, FormInst, FormValidationError} from 'naive-ui';
import {
  NAlert,
  NButton,
  NCard,
  NDataTable,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NList,
  NListItem,
  NModal,
  NSpin,
  NStep,
  NSteps,
  NSwitch,
  NTag,
  NText,
  NThing,
  useMessage
} from 'naive-ui';
import {getApiEndpoints} from '../services/api';
import type {
  Combination,
  CombinationEndpoint
} from '../services/api';
import {
  getCombinations,
  createCombination,
  updateCombination,
  toggleCombinationStatus,
  deleteCombination
} from '../services/api';

// --- Interfaces ---
interface Service {
  key: number;
  name: string;
  url: string;
  type: string;
  status: 'healthy' | 'unhealthy';
}

interface ApiEndpoint {
  path: string;
  method: string;
  summary: string;
}

// --- Data & State ---
const message = useMessage();
const formRef = ref<FormInst | null>(null);

// 模拟服务列表（从 localStorage 或实际 API 获取）
const services = ref<Service[]>([
  {key: 1, name: 'Petstore API', url: 'https://petstore3.swagger.io/api/v3/openapi.json', type: 'OpenAPI 3.0', status: 'healthy'},
]);

// 组合管理状态
const combinations = ref<Combination[]>([]);
const loadingCombinations = ref(false);

const searchQuery = ref('');
const showCombinationModal = ref(false);
const editingCombination = ref<Combination | null>(null);
const combinationForm = ref({
  name: '',
  description: '',
  endpoints: [] as CombinationEndpoint[]
});

// 管理接口状态
const showManageEndpointsModal = ref(false);
const manageEndpointsSearchQuery = ref('');
const tempEndpoints = ref<CombinationEndpoint[]>([]); // 临时存储正在管理的接口列表

// 接口选择器状态
const showEndpointSelector = ref(false);
const currentStep = ref(1);
const selectedService = ref<Service | null>(null);
const loadingEndpoints = ref(false);
const availableEndpoints = ref<ApiEndpoint[]>([]);
const serviceSearchQuery = ref('');
const endpointSearchQuery = ref('');
const endpointSelectorMode = ref<'combination' | 'manage'>('combination'); // 区分接口选择器的使用场景

// --- Lifecycle ---
onMounted(async () => {
  await loadCombinations();
});

// --- Computed ---
const filteredCombinations = computed(() => {
  if (!searchQuery.value) {
    return combinations.value;
  }
  const query = searchQuery.value.toLowerCase();
  return combinations.value.filter(
      combo =>
          combo.name.toLowerCase().includes(query) ||
          combo.description.toLowerCase().includes(query)
  );
});

const filteredServices = computed(() => {
  if (!serviceSearchQuery.value) {
    return services.value;
  }
  const query = serviceSearchQuery.value.toLowerCase();
  return services.value.filter(
      service =>
          service.name.toLowerCase().includes(query) ||
          service.url.toLowerCase().includes(query)
  );
});

const filteredEndpoints = computed(() => {
  if (!endpointSearchQuery.value) {
    return availableEndpoints.value;
  }
  const query = endpointSearchQuery.value.toLowerCase();
  return availableEndpoints.value.filter(
      endpoint =>
          endpoint.path.toLowerCase().includes(query) ||
          endpoint.summary.toLowerCase().includes(query)
  );
});

const filteredManageEndpoints = computed(() => {
  if (!manageEndpointsSearchQuery.value) {
    return tempEndpoints.value;
  }
  const query = manageEndpointsSearchQuery.value.toLowerCase();
  return tempEndpoints.value.filter(
      endpoint =>
          endpoint.path.toLowerCase().includes(query) ||
          endpoint.summary.toLowerCase().includes(query) ||
          endpoint.serviceName.toLowerCase().includes(query)
  );
});

// --- Form Rules ---
const rules = {
  name: {required: true, message: '请输入组合名称', trigger: 'blur'},
  description: {required: false},
};

// --- Table Columns ---
const columns = computed<DataTableColumns<Combination>>(() => [
  {title: '组合名称', key: 'name'},
  {
    title: '描述',
    key: 'description',
    ellipsis: {tooltip: true}
  },
  {
    title: '接口数量',
    key: 'endpoints',
    render: (row) => h('span', {}, row.endpoints.length)
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
              {size: 'small', onClick: () => handleEditCombination(row)},
              {default: () => '编辑'}
          ),
          h(
              NButton,
              {size: 'small', onClick: () => handleManageEndpoints(row)},
              {default: () => '管理接口'}
          ),
          h(
              NButton,
              {
                size: 'small',
                type: 'error',
                ghost: true,
                onClick: () => handleDeleteCombination(row)
              },
              {default: () => '删除'}
          )
        ])
  }
]);

const endpointSelectorColumns = computed<DataTableColumns<ApiEndpoint>>(() => [
  {title: '路径', key: 'path'},
  {title: '方法', key: 'method'},
  {title: '描述', key: 'summary', ellipsis: {tooltip: true}},
  {
    title: '操作',
    key: 'actions',
    render: (row) => {
      // 根据模式判断是否已添加
      const isAdded = endpointSelectorMode.value === 'manage'
          ? tempEndpoints.value.some(ep => ep.path === row.path && ep.method === row.method)
          : combinationForm.value.endpoints.some(ep => ep.path === row.path && ep.method === row.method);

      return h(
          NButton,
          {
            size: 'small',
            type: isAdded ? 'default' : 'primary',
            disabled: isAdded,
            onClick: () => {
              if (endpointSelectorMode.value === 'manage') {
                handleAddEndpointToManage(row);
              } else {
                handleAddEndpoint(row);
              }
            }
          },
          {default: () => isAdded ? '已添加' : '添加'}
      );
    }
  }
]);

const manageEndpointsColumns = computed<DataTableColumns<CombinationEndpoint>>(() => [
  {title: '服务', key: 'serviceName'},
  {title: '路径', key: 'path'},
  {title: '方法', key: 'method', width: 80},
  {title: '描述', key: 'summary', ellipsis: {tooltip: true}},
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
              onClick: () => handleRemoveEndpointFromManage(row)
            },
            {default: () => '删除'}
        )
  }
]);

// --- Methods ---
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

const handleAddCombination = () => {
  editingCombination.value = null;
  combinationForm.value = {
    name: '',
    description: '',
    endpoints: []
  };
  showCombinationModal.value = true;
};

const handleEditCombination = (combination: Combination) => {
  editingCombination.value = combination;
  combinationForm.value = {
    name: combination.name,
    description: combination.description,
    endpoints: [...combination.endpoints]
  };
  showCombinationModal.value = true;
};

const handleManageEndpoints = (combination: Combination) => {
  editingCombination.value = combination;
  tempEndpoints.value = [...combination.endpoints];
  showManageEndpointsModal.value = true;
  manageEndpointsSearchQuery.value = '';
};

const handleOpenEndpointSelector = () => {
  endpointSelectorMode.value = 'manage';
  showEndpointSelector.value = true;
  currentStep.value = 1;
};

const handleCloseManageEndpoints = () => {
  showManageEndpointsModal.value = false;
  editingCombination.value = null;
  tempEndpoints.value = [];
};

const handleSaveManageEndpoints = async () => {
  if (!editingCombination.value) return;

  try {
    await updateCombination(editingCombination.value.id, {
      endpoints: tempEndpoints.value
    });
    message.success('接口管理保存成功');
    showManageEndpointsModal.value = false;
    await loadCombinations();
  } catch (error: unknown) {
    if (error instanceof Error) {
      message.error(`保存失败: ${error.message}`);
    } else {
      message.error('保存失败: 未知错误');
    }
  }
};

const handleRemoveEndpointFromManage = (endpoint: CombinationEndpoint) => {
  tempEndpoints.value = tempEndpoints.value.filter(
      ep => !(ep.path === endpoint.path && ep.method === endpoint.method && ep.serviceName === endpoint.serviceName)
  );
  message.success('接口已从列表中移除');
};

const handleAddEndpointToManage = (endpoint: ApiEndpoint) => {
  if (!selectedService.value) return;

  const newEndpoint: CombinationEndpoint = {
    serviceName: selectedService.value.name,
    serviceUrl: selectedService.value.url,
    path: endpoint.path,
    method: endpoint.method,
    summary: endpoint.summary
  };

  tempEndpoints.value.push(newEndpoint);
  message.success('接口已添加');
};

const handleSaveCombination = async () => {
  formRef.value?.validate(async (errors: Array<FormValidationError> | undefined) => {
    if (!errors) {
      try {
        if (editingCombination.value) {
          // 编辑模式
          await updateCombination(editingCombination.value.id, {
            name: combinationForm.value.name,
            description: combinationForm.value.description,
            endpoints: combinationForm.value.endpoints
          });
          message.success('组合更新成功');
        } else {
          // 新增模式
          await createCombination({
            name: combinationForm.value.name,
            description: combinationForm.value.description,
            endpoints: combinationForm.value.endpoints
          });
          message.success('组合创建成功');
        }
        showCombinationModal.value = false;
        await loadCombinations();
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

const handleDeleteCombination = async (combination: Combination) => {
  try {
    await deleteCombination(combination.id);
    message.success(`组合 "${combination.name}" 已删除`);
    await loadCombinations();
  } catch (error: unknown) {
    if (error instanceof Error) {
      message.error(`删除失败: ${error.message}`);
    } else {
      message.error('删除失败: 未知错误');
    }
  }
};

const handleToggleStatus = async (combination: Combination, value: boolean) => {
  try {
    await toggleCombinationStatus(combination.id, value ? 'active' : 'inactive');
    message.success(`组合已${value ? '启用' : '停用'}`);
    await loadCombinations();
  } catch (error: unknown) {
    if (error instanceof Error) {
      message.error(`状态切换失败: ${error.message}`);
    } else {
      message.error('状态切换失败: 未知错误');
    }
  }
};

const handleRemoveEndpoint = (endpoint: CombinationEndpoint) => {
  combinationForm.value.endpoints = combinationForm.value.endpoints.filter(
      ep => !(ep.path === endpoint.path && ep.method === endpoint.method)
  );
};

const handleSelectService = async (service: Service) => {
  selectedService.value = service;
  currentStep.value = 2;
  loadingEndpoints.value = true;
  availableEndpoints.value = [];

  try {
    availableEndpoints.value = await getApiEndpoints(service.url);
  } catch (error: unknown) {
    if (error instanceof Error) {
      message.error(`获取接口失败: ${error.message}`);
    } else {
      message.error('获取接口失败: 未知错误');
    }
    currentStep.value = 1;
  } finally {
    loadingEndpoints.value = false;
  }
};

const handleAddEndpoint = (endpoint: ApiEndpoint) => {
  if (!selectedService.value) return;

  const newEndpoint: CombinationEndpoint = {
    serviceName: selectedService.value.name,
    serviceUrl: selectedService.value.url,
    path: endpoint.path,
    method: endpoint.method,
    summary: endpoint.summary
  };

  combinationForm.value.endpoints.push(newEndpoint);
  message.success('接口已添加');
};
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.endpoints-list {
  min-height: 60px;
  padding: 12px;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}

.manage-endpoints-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
</style>
