<template>
  <div class="user-management-page">
    <div class="page-header">
      <n-button type="primary" @click="showCreateModal = true">
        <template #icon>
          <n-icon><PersonAddOutline /></n-icon>
        </template>
        创建用户
      </n-button>
    </div>

    <n-data-table
      :columns="columns"
      :data="users"
      :loading="loading"
      :pagination="false"
      :bordered="false"
      :max-height="500"
    />

    <!-- 创建用户 Modal -->
    <n-modal v-model:show="showCreateModal">
      <n-card
        style="width: 600px"
        title="创建用户"
        :bordered="false"
        size="huge"
        role="dialog"
        aria-modal="true"
      >
        <n-form ref="createFormRef" :model="createForm" :rules="createRules">
          <n-form-item path="username" label="用户名">
            <n-input v-model:value="createForm.username" placeholder="请输入用户名" />
          </n-form-item>
          <n-form-item path="password" label="密码">
            <n-input
              v-model:value="createForm.password"
              type="password"
              show-password-on="click"
              placeholder="请输入密码（至少6位）"
            />
          </n-form-item>
          <n-form-item path="role" label="角色">
            <n-select
              v-model:value="createForm.role"
              :options="roleOptions"
              placeholder="请选择角色"
            />
          </n-form-item>
        </n-form>
        <template #footer>
          <n-button @click="showCreateModal = false">取消</n-button>
          <n-button type="primary" :loading="creating" @click="handleCreate" style="margin-left: 12px;">创建</n-button>
        </template>
      </n-card>
    </n-modal>

    <!-- 编辑用户 Modal -->
    <n-modal v-model:show="showEditModal">
      <n-card
        style="width: 600px"
        title="编辑用户"
        :bordered="false"
        size="huge"
        role="dialog"
        aria-modal="true"
      >
        <n-form ref="editFormRef" :model="editForm" :rules="editRules">
          <n-form-item label="用户名">
            <n-input :value="editingUser?.username" disabled />
          </n-form-item>
          <n-form-item path="password" label="新密码（可选）">
            <n-input
              v-model:value="editForm.password"
              type="password"
              show-password-on="click"
              placeholder="留空则不修改密码"
            />
          </n-form-item>
          <n-form-item path="role" label="角色">
            <n-select
              v-model:value="editForm.role"
              :options="roleOptions"
              placeholder="请选择角色"
            />
          </n-form-item>
          <n-form-item path="is_active" label="状态">
            <n-switch v-model:value="editForm.is_active">
              <template #checked>启用</template>
              <template #unchecked>禁用</template>
            </n-switch>
          </n-form-item>
        </n-form>
        <template #footer>
          <n-button @click="showEditModal = false">取消</n-button>
          <n-button type="primary" :loading="updating" @click="handleUpdate" style="margin-left: 12px;">保存</n-button>
        </template>
      </n-card>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted } from 'vue';
import {
  NButton,
  NIcon,
  NDataTable,
  NModal,
  NCard,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NSwitch,
  NTag,
  useMessage,
  useDialog,
  type DataTableColumns
} from 'naive-ui';
import { PersonAddOutline, CreateOutline, TrashOutline } from '@vicons/ionicons5';
import {
  getUsers,
  createUser,
  updateUser,
  deleteUser,
  type User,
  type UserCreate,
  type UserUpdate
} from '../services/api';
import { getCurrentUser as getLocalUser } from '../utils/auth';

const message = useMessage();
const dialog = useDialog();

const loading = ref(false);
const creating = ref(false);
const updating = ref(false);
const users = ref<User[]>([]);

const showCreateModal = ref(false);
const showEditModal = ref(false);
const editingUser = ref<User | null>(null);

const createFormRef = ref();
const editFormRef = ref();

const createForm = ref<UserCreate>({
  username: '',
  password: '',
  role: 'user'
});

const editForm = ref<UserUpdate>({
  password: '',
  role: 'user',
  is_active: true
});

const roleOptions = [
  { label: '管理员', value: 'admin' },
  { label: '普通用户', value: 'user' }
];

const createRules = {
  username: {
    required: true,
    message: '请输入用户名',
    trigger: 'blur'
  },
  password: {
    required: true,
    message: '请输入密码',
    trigger: 'blur',
    validator: (_rule: any, value: string) => {
      if (!value) return new Error('请输入密码');
      if (value.length < 6) return new Error('密码至少6位');
      return true;
    }
  },
  role: {
    required: true,
    message: '请选择角色',
    trigger: 'change'
  }
};

const editRules = {
  password: {
    validator: (_rule: any, value: string) => {
      if (value && value.length < 6) return new Error('密码至少6位');
      return true;
    },
    trigger: 'blur'
  }
};

// 表格列定义
const columns: DataTableColumns<User> = [
  {
    title: 'ID',
    key: 'id',
    width: 80
  },
  {
    title: '用户名',
    key: 'username',
    width: 150
  },
  {
    title: '角色',
    key: 'role',
    width: 120,
    render: (row) => {
      return h(
        NTag,
        {
          type: row.role === 'admin' ? 'error' : 'info',
          size: 'small'
        },
        { default: () => row.role === 'admin' ? '管理员' : '普通用户' }
      );
    }
  },
  {
    title: '状态',
    key: 'is_active',
    width: 100,
    render: (row) => {
      return h(
        NTag,
        {
          type: row.is_active ? 'success' : 'default',
          size: 'small'
        },
        { default: () => row.is_active ? '启用' : '禁用' }
      );
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render: (row) => new Date(row.created_at).toLocaleString('zh-CN')
  },
  {
    title: '最后登录',
    key: 'last_login_at',
    width: 180,
    render: (row) => row.last_login_at ? new Date(row.last_login_at).toLocaleString('zh-CN') : '-'
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row) => {
      return h('div', { style: { display: 'flex', gap: '8px' } }, [
        h(
          NButton,
          {
            size: 'small',
            onClick: () => handleEdit(row)
          },
          {
            default: () => '编辑',
            icon: () => h(NIcon, null, { default: () => h(CreateOutline) })
          }
        ),
        h(
          NButton,
          {
            size: 'small',
            type: 'error',
            onClick: () => handleDelete(row)
          },
          {
            default: () => '删除',
            icon: () => h(NIcon, null, { default: () => h(TrashOutline) })
          }
        )
      ]);
    }
  }
];

// 加载用户列表
async function loadUsers() {
  try {
    loading.value = true;
    const response = await getUsers();
    users.value = response.users;
  } catch (error: any) {
    message.error(error.message || '加载用户列表失败');
  } finally {
    loading.value = false;
  }
}

// 创建用户
async function handleCreate() {
  try {
    await createFormRef.value?.validate();
    creating.value = true;

    await createUser(createForm.value);
    message.success('用户创建成功');

    showCreateModal.value = false;
    createForm.value = {
      username: '',
      password: '',
      role: 'user'
    };

    await loadUsers();
  } catch (error: any) {
    message.error(error.message || '创建用户失败');
  } finally {
    creating.value = false;
  }
}

// 编辑用户
function handleEdit(user: User) {
  editingUser.value = user;
  editForm.value = {
    password: '',
    role: user.role,
    is_active: user.is_active
  };
  showEditModal.value = true;
}

// 更新用户
async function handleUpdate() {
  try {
    await editFormRef.value?.validate();
    if (!editingUser.value) return;

    updating.value = true;

    // 如果密码为空，不发送密码字段
    const updateData: UserUpdate = {
      role: editForm.value.role,
      is_active: editForm.value.is_active
    };
    if (editForm.value.password) {
      updateData.password = editForm.value.password;
    }

    await updateUser(editingUser.value.id, updateData);
    message.success('用户更新成功');

    showEditModal.value = false;
    editingUser.value = null;

    await loadUsers();
  } catch (error: any) {
    message.error(error.message || '更新用户失败');
  } finally {
    updating.value = false;
  }
}

// 删除用户
function handleDelete(user: User) {
  const currentUser = getLocalUser();

  // 不能删除自己
  if (currentUser?.id === user.id) {
    message.warning('不能删除当前登录的账户');
    return;
  }

  dialog.warning({
    title: '确认删除',
    content: `确定要删除用户 "${user.username}" 吗？此操作不可恢复。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await deleteUser(user.id);
        message.success('用户删除成功');
        await loadUsers();
      } catch (error: any) {
        message.error(error.message || '删除用户失败');
      }
    }
  });
}

onMounted(() => {
  loadUsers();
});
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
</style>
