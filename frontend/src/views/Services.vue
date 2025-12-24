<!-- frontend/src/views/Services.vue -->
<template>
  <div class="services-page">
    <div class="page-header">
      <h1>服务管理</h1>
      <n-button type="primary" @click="showAddModal = true">
        添加服务
      </n-button>
    </div>

    <n-data-table
      :columns="columns"
      :data="services"
      :pagination="false"
      :bordered="false"
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
            <n-input v-model:value="newService.name" placeholder="例如：用户中心" />
          </n-form-item>
          <n-form-item path="url" label="Swagger/OpenAPI URL">
            <n-input v-model:value="newService.url" placeholder="http://.../v3/api-docs" />
          </n-form-item>
        </n-form>
        <template #footer>
          <n-button @click="showAddModal = false">取消</n-button>
          <n-button type="primary" @click="handleAddService" style="margin-left: 12px;">确定</n-button>
        </template>
      </n-card>
    </n-modal>

    <!-- View APIs Modal -->
    <n-modal v-model:show="showApisModal">
      <n-card
        style="width: 900px"
        :title="`'${selectedService?.name}' 的 API 列表`"
        :bordered="false"
        size="huge"
        role="dialog"
        aria-modal="true"
      >
        <n-spin :show="loadingApis">
          <n-data-table
            :columns="apiColumns"
            :data="mcpTools"
            :max-height="400"
          />
        </n-spin>
      </n-card>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { h, ref } from 'vue';
import { NButton, NDataTable, NModal, NCard, NForm, NFormItem, NInput, useMessage, NSpin } from 'naive-ui';
import type { DataTableColumns } from 'naive-ui';
import { getMcpTools } from '../services/api';

// --- Interfaces ---
interface Service {
  key: number;
  name: string;
  url: string;
  status: 'healthy' | 'unhealthy';
}
interface McpTool {
  name: string;
  description: string;
  input_schema: object;
  metadata: object;
}

// --- Data & State ---
const message = useMessage();
const formRef = ref(null);

// Service management state
const showAddModal = ref(false);
const services = ref<Service[]>([
  // Use a real public API for demonstration
  { key: 1, name: 'Petstore API', url: 'https://petstore3.swagger.io/api/v3/openapi.json', status: 'healthy' },
]);
const newService = ref({ name: '', url: '' });

// API viewing state
const showApisModal = ref(false);
const loadingApis = ref(false);
const selectedService = ref<Service | null>(null);
const mcpTools = ref<McpTool[]>([]);

// --- Form Rules ---
const rules = {
  name: { required: true, message: '请输入服务名称', trigger: 'blur' },
  url: { required: true, message: '请输入 OpenAPI URL', trigger: 'blur' },
};

// --- Table Columns ---
// Main services table
const serviceTableColumns = ({ viewApis, deleteService }): DataTableColumns<Service> => [
  { title: '服务名称', key: 'name' },
  { title: 'OpenAPI URL', key: 'url' },
  { title: '状态', key: 'status', render: (row) => h('span', { style: { color: row.status === 'healthy' ? '#63e2b7' : '#e88080' } }, row.status === 'healthy' ? '健康' : '异常') },
  { title: '操作', key: 'actions', render: (row) => h('div', { style: { display: 'flex', gap: '8px' } }, [
      h(NButton, { size: 'small', onClick: () => viewApis(row) }, { default: () => '查看 API' }),
      h(NButton, { size: 'small', type: 'error', ghost: true, onClick: () => deleteService(row) }, { default: () => '删除' }),
    ])
  },
];
// API details table (in modal)
const apiColumns: DataTableColumns<McpTool> = [
  { title: 'Tool Name', key: 'name' },
  { title: 'Description', key: 'description' },
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
  formRef.value?.validate((errors) => {
    if (!errors) {
      services.value.push({ key: Date.now(), name: newService.value.name, url: newService.value.url, status: 'healthy' });
      message.success('服务添加成功');
      showAddModal.value = false;
      newService.value = { name: '', url: '' };
    } else {
      message.error('请填写所有必填项');
    }
  });
};

const handleViewApis = async (url: string) => {
  loadingApis.value = true;
  mcpTools.value = [];
  try {
    const data = await getMcpTools(url);
    mcpTools.value = data.tools;
  } catch (error) {
    message.error(`获取 API 失败: ${error.message}`);
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
