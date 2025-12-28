<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <img src="/logo.svg" alt="Synapse Logo" class="logo" />
        <h1 class="title">Synapse</h1>
        <p class="subtitle">企业级 API 聚合与 MCP 服务平台</p>
      </div>

      <n-form
        ref="formRef"
        :model="formValue"
        :rules="rules"
        size="large"
        :show-label="false"
      >
        <n-form-item path="username">
          <n-input
            v-model:value="formValue.username"
            placeholder="用户名"
            @keydown.enter="handleLogin"
          >
            <template #prefix>
              <n-icon :component="PersonOutline" />
            </template>
          </n-input>
        </n-form-item>

        <n-form-item path="password">
          <n-input
            v-model:value="formValue.password"
            type="password"
            show-password-on="click"
            placeholder="密码"
            @keydown.enter="handleLogin"
          >
            <template #prefix>
              <n-icon :component="LockClosedOutline" />
            </template>
          </n-input>
        </n-form-item>

        <n-alert v-if="errorMessage" type="error" style="margin-bottom: 16px" closable @close="errorMessage = ''">
          {{ errorMessage }}
        </n-alert>

        <n-button
          type="primary"
          block
          size="large"
          :loading="loading"
          @click="handleLogin"
          strong
        >
          登录
        </n-button>
      </n-form>

      <n-divider style="margin: 24px 0" />

      <div class="login-footer">
        <n-text depth="3" style="font-size: 13px">
          <n-icon :component="InformationCircleOutline" style="vertical-align: middle; margin-right: 4px" />
          默认管理员账户：<n-text code>admin</n-text> / <n-text code>admin123</n-text>
        </n-text>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { NForm, NFormItem, NInput, NButton, NAlert, NDivider, NText, NIcon } from 'naive-ui';
import { PersonOutline, LockClosedOutline, InformationCircleOutline } from '@vicons/ionicons5';
import { login } from '../services/api';
import { setToken, setCurrentUser } from '../utils/auth';

const router = useRouter();

const formRef = ref();
const loading = ref(false);
const errorMessage = ref('');

const formValue = ref({
  username: '',
  password: '',
});

const rules = {
  username: {
    required: true,
    message: '请输入用户名',
    trigger: 'blur',
  },
  password: {
    required: true,
    message: '请输入密码',
    trigger: 'blur',
  },
};

async function handleLogin() {
  try {
    await formRef.value?.validate();
    loading.value = true;
    errorMessage.value = '';

    const response = await login({
      username: formValue.value.username,
      password: formValue.value.password,
    });

    // 保存 Token 和用户信息
    setToken(response.access_token);
    setCurrentUser(response.user);

    // 跳转到首页
    router.push('/');
  } catch (error: any) {
    console.error('Login error:', error);
    errorMessage.value = error.message || '登录失败，请检查用户名和密码';
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-box {
  width: 100%;
  max-width: 420px;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 16px;
  padding: 48px 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.logo {
  height: 56px;
  margin-bottom: 16px;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.title {
  margin: 0 0 8px 0;
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  margin: 0;
  font-size: 14px;
  color: #666;
  font-weight: 400;
}

.login-footer {
  text-align: center;
}

/* Form styling */
:deep(.n-form-item) {
  margin-bottom: 20px;
}

:deep(.n-input) {
  border-radius: 8px;
}

:deep(.n-button) {
  border-radius: 8px;
  height: 44px;
  font-size: 16px;
  font-weight: 600;
}
</style>
