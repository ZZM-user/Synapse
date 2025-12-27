<!-- frontend/src/views/Services.vue -->
<template>
  <div class="services-page">
    <div class="page-header">
      <n-button type="primary" @click="showAddModal = true">
        添加服务
      </n-button>
    </div>

    <n-data-table
        :columns="columns"
        :data="services"
        :pagination="false"
        :bordered="false"
        :max-height="400"
    />

    <!-- Add Service Modal -->
    <n-modal v-model:show="showAddModal">
      <n-card
          style="width: 600px"
          title="添加新服务"
          :bordered="false"
          size="huge"
          role="dialog"
          aria-modal="true"
      >
        <n-form ref="formRef" :model="newService" :rules="rules">
          <n-form-item path="name" label="服务名称">
            <n-input v-model:value="newService.name" placeholder="例如：用户中心"/>
          </n-form-item>
          <n-form-item path="type" label="文档类型">
            <n-select v-model:value="newService.type" :options="docTypeOptions" placeholder="选择文档类型"/>
          </n-form-item>
          <n-form-item path="url" label="文档地址">
            <n-input v-model:value="newService.url" placeholder="http://.../openapi.json 或 http://.../swagger.yaml"/>
          </n-form-item>
        </n-form>
        <template #footer>
          <n-button @click="showAddModal = false">取消</n-button>
          <n-button type="primary" @click="handleAddService" style="margin-left: 12px;">确定</n-button>
        </template>
      </n-card>
    </n-modal>

    <n-modal v-model:show="showApisModal">
      <n-card
          style="width: 900px"
          :title="`'${selectedService?.name}' 的 API 列表`"
          :bordered="false"
          size="huge"
          role="dialog"
          aria-modal="true"
      >
        <template #header-extra>
          <n-button-group>
            <n-input v-model:value="searchQuery" placeholder="搜索 API/描述" clearable style="margin-right: 12px;"/>
            <n-button @click="showApisModal = false" text>
              <n-icon :size="20">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M18.3 5.71a.996.996 0 0 0-1.41 0L12 10.59L7.11 5.7A.996.996 0 1 0 5.7 7.11L10.59 12L5.7 16.89a.996.996 0 1 0 1.41 1.41L12 13.41l4.89 4.89a.996.996 0 1 0 1.41-1.41L13.41 12l4.89-4.89c.38-.38.38-1.02 0-1.4z" fill="currentColor"></path></svg>
              </n-icon>
            </n-button>
          </n-button-group>
        </template>
        <n-spin :show="loadingApis">
          <n-data-table
              :columns="apiColumns"
              :data="filteredApiEndpoints"
              :max-height="400"
          />
        </n-spin>
      </n-card>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import {computed, h, ref} from 'vue';
import type {DataTableColumns, FormInst, FormValidationError} from 'naive-ui';
import {
  NButton,
  NButtonGroup,
  NCard,
  NDataTable,
  NForm,
  NFormItem,
  NIcon,
  NInput,
  NModal,
  NSelect,
  NSpin,
  useMessage
} from 'naive-ui';
import {getApiEndpoints} from '../services/api';

// --- Interfaces ---
interface Service {
  key: number;
  name: string;
  url: string;
  type: string; // Add type property
  status: 'healthy' | 'unhealthy';
}

interface ApiEndpoint {
  path: string;
  method: string;
  summary: string;
}

interface ServiceActions {
  viewApis: (row: Service) => void;
  deleteService: (row: Service) => void;
}

// --- Data & State ---
const message = useMessage();
const formRef = ref<FormInst | null>(null);

// Service management state
const showAddModal = ref(false);
const services = ref<Service[]>([
  // Use a real public API for demonstration
  {key: 1, name: 'Petstore API', url: 'https://petstore3.swagger.io/api/v3/openapi.json', type: 'OpenAPI 3.0', status: 'healthy'},
]);
const newService = ref({name: '', url: '', type: null}); // Initialize type to null

// API viewing state
const showApisModal = ref(false);
const loadingApis = ref(false);
const selectedService = ref<Service | null>(null);
const apiEndpoints = ref<ApiEndpoint[]>([]);
const searchQuery = ref('');

const filteredApiEndpoints = computed(() => {
  if (!searchQuery.value) {
    return apiEndpoints.value;
  }
  return apiEndpoints.value.filter(api =>
      api.path.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      api.summary.toLowerCase().includes(searchQuery.value.toLowerCase())
  );
});

// Document Type Options
const docTypeOptions = [
  {label: 'OpenAPI 3.0', value: 'OpenAPI 3.0'},
  {label: 'Swagger 2.0', value: 'Swagger 2.0'},
  {label: 'AsyncAPI', value: 'AsyncAPI'},
];

// --- Form Rules ---
const rules = {
  name: {required: true, message: '请输入服务名称', trigger: 'blur'},
  type: {required: true, message: '请选择文档类型', trigger: ['blur', 'change']},
  url: {required: true, message: '请输入文档地址', trigger: 'blur'},
};

// --- Table Columns ---
// Main services table
const serviceTableColumns = ({viewApis, deleteService}: ServiceActions): DataTableColumns<Service> => [
  {title: '服务名称', key: 'name'},
  {title: '文档类型', key: 'type'},
  {title: 'OpenAPI URL', key: 'url'},
  {
    title: '状态',
    key: 'status',
    render: (row) => h('span', {style: {color: row.status === 'healthy' ? '#63e2b7' : '#e88080'}}, row.status === 'healthy' ? '健康' : '异常')
  },
  {
    title: '操作', key: 'actions', render: (row) => h('div', {style: {display: 'flex', gap: '8px'}}, [
      h(NButton, {size: 'small', onClick: () => viewApis(row)}, {default: () => '查看 API'}),
      h(NButton, {
        size: 'small',
        type: 'error',
        ghost: true,
        onClick: () => deleteService(row)
      }, {default: () => '删除'}),
    ])
  },
];
// API details table (in modal)
const apiColumns: DataTableColumns<ApiEndpoint> = [
  {title: '路径', key: 'path'},
  {title: '方法', key: 'method'},
  {title: '描述', key: 'summary'},
];

const columns = serviceTableColumns({
  viewApis: (row: Service) => {
    selectedService.value = row;
    showApisModal.value = true;
    handleViewApis(row.url);
  },
  deleteService: (row: Service) => {
    services.value = services.value.filter((service) => service.key !== row.key);
    message.success(`服务 "${row.name}" 已删除`);
  }
});

// --- Methods ---
const handleAddService = () => {
  formRef.value?.validate((errors: Array<FormValidationError> | undefined) => {
    if (!errors) {
      services.value.push({
        key: Date.now(),
        name: newService.value.name,
        url: newService.value.url,
        type: newService.value.type as string, // Cast to string as it's validated as required
        status: 'healthy'
      });
      message.success('服务添加成功');
      showAddModal.value = false;
      newService.value = {name: '', url: '', type: null};
    } else {
      message.error('请填写所有必填项');
    }
  });
};

const handleViewApis = async (url: string) => {
  loadingApis.value = true;
  apiEndpoints.value = [];
  try {
    apiEndpoints.value = await getApiEndpoints(url);
  } catch (error: unknown) {
    if (error instanceof Error) {
      message.error(`获取 API 失败: ${error.message}`);
    } else {
      message.error('获取 API 失败: 未知错误');
    }
    showApisModal.value = false; // Close modal on error
  } finally {
    loadingApis.value = false;
  }
};
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

h1 {
  margin: 0;
}
</style>

