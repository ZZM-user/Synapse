<template>
  <div class="login-container">
    <n-card class="login-card" title="Synapse 登录">
      <n-form
        ref="formRef"
        :model="formValue"
        :rules="rules"
        size="large"
      >
        <n-form-item path="username" label="用户名">
          <n-input
            v-model:value="formValue.username"
            placeholder="请输入用户名"
            @keydown.enter="handleLogin"
          />
        </n-form-item>

        <n-form-item path="password" label="密码">
          <n-input
            v-model:value="formValue.password"
            type="password"
            show-password-on="click"
            placeholder="请输入密码"
            @keydown.enter="handleLogin"
          />
        </n-form-item>

        <n-space vertical>
          <n-button
            type="primary"
            block
            size="large"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </n-button>
        </n-space>
      </n-form>

      <n-alert v-if="errorMessage" type="error" style="margin-top: 16px">
        {{ errorMessage }}
      </n-alert>

      <n-divider />

      <n-text depth="3" style="font-size: 12px">
        默认账户: admin / admin123
      </n-text>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { NCard, NForm, NFormItem, NInput, NButton, NSpace, NAlert, NDivider, NText, useMessage } from 'naive-ui';
import { login } from '../services/api';
import { setToken, setCurrentUser } from '../utils/auth';

const router = useRouter();
const message = useMessage();

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

    message.success('登录成功！');

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
}

.login-card {
  width: 100%;
  max-width: 400px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}
</style>
