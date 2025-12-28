<template>
  <n-message-provider>
    <n-dialog-provider>
      <!-- 登录页面：全屏显示，无导航 -->
      <div v-if="route.name === 'Login'" style="height: 100vh">
        <router-view />
      </div>

      <!-- 其他页面：带导航布局 -->
      <n-layout v-else has-sider style="height: 100vh">
        <n-layout-sider
            bordered
            width="240"
            content-style="padding: 12px;"
            collapsible
            :collapsed-width="20"
            :collapse-mode="'width'"
            show-trigger="arrow-circle"
        >
          <div style="display: flex; align-items: center; padding: 14px 20px; height: 60px; margin-bottom: 12px;">
            <img src="/logo.svg" alt="Synapse Logo" style="height: 32px; margin-right: 12px;"/>
            <h2 style="margin: 0; font-size: 20px; font-weight: 600;">Synapse</h2>
          </div>
          <n-menu
              :options="menuOptions"
              :value="activeMenuKey"
              :collapsed-width="64"
              :collapsed-icon-size="22"
          />
        </n-layout-sider>
        <n-layout>
          <n-layout-header bordered>
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 0 24px; height: 60px;">
              <h2 style="margin: 0; font-size: 18px; font-weight: 600;">{{ currentRouteTitle }}</h2>

              <!-- 用户信息和登出 -->
              <n-dropdown :options="userMenuOptions" placement="bottom-end" @select="handleUserMenuSelect">
                <n-button text>
                  <n-icon size="20" style="margin-right: 8px">
                    <PersonCircleOutline />
                  </n-icon>
                  {{ currentUser?.username || '用户' }}
                </n-button>
              </n-dropdown>
            </div>
          </n-layout-header>
          <n-layout-content content-style="padding: 24px;">
            <router-view/>
          </n-layout-content>
        </n-layout>
      </n-layout>
    </n-dialog-provider>
  </n-message-provider>
</template>

<script setup lang="ts">
import {computed, h, ref, onMounted} from 'vue';
import {RouterLink, useRoute, useRouter} from 'vue-router';
import type {MenuOption} from 'naive-ui';
import {
  NDialogProvider,
  NIcon,
  NLayout,
  NLayoutContent,
  NLayoutHeader,
  NLayoutSider,
  NMenu,
  NMessageProvider,
  NButton,
  NDropdown
} from 'naive-ui';
import {CubeOutline, HomeOutline, HardwareChipOutline, ServerOutline, PersonCircleOutline, LogOutOutline} from '@vicons/ionicons5';
import { getCurrentUser, logout as authLogout } from './utils/auth';
import type { User } from './services/api';

// Import fonts
import 'vfonts/Lato.css';
import 'vfonts/FiraCode.css';

const route = useRoute();
const router = useRouter();
const currentUser = ref<User | null>(null);

// 辅助函数：渲染图标
function renderIcon(icon: any) {
  return () => h(NIcon, null, { default: () => h(icon) });
}

// 加载当前用户信息
onMounted(() => {
  currentUser.value = getCurrentUser();
});

// 用户菜单选项
const userMenuOptions = [
  {
    label: '登出',
    key: 'logout',
    icon: renderIcon(LogOutOutline)
  }
];

// 处理用户菜单选择
function handleUserMenuSelect(key: string) {
  if (key === 'logout') {
    authLogout();
    router.push('/login');
  }
}

const menuOptions: MenuOption[] = [
  {
    label: () => h(RouterLink, {to: {name: 'Home'}}, {default: () => '首页'}),
    key: 'Home',
    icon: () => h(NIcon, null, {default: () => h(HomeOutline)})
  },
  {
    label: () => h(RouterLink, {to: {name: 'Services'}}, {default: () => '服务管理'}),
    key: 'Services',
    icon: () => h(NIcon, null, {default: () => h(CubeOutline)})
  },
  {
    label: 'MCP 管理',
    key: 'Mcp',
    icon: () => h(NIcon, null, {default: () => h(HardwareChipOutline)}),
    children: [
      {
        label: () => h(RouterLink, {to: {name: 'McpCombination'}}, {default: () => 'MCP 组合'}),
        key: 'McpCombination',
        icon: () => h(NIcon, null, {default: () => h(ServerOutline)})
      },
      {
        label: () => h(RouterLink, {to: {name: 'McpManagement'}}, {default: () => 'MCP 管理'}),
        key: 'McpManagement',
        icon: () => h(NIcon, null, {default: () => h(ServerOutline)})
      }
    ]
  }
];

// Computed property to determine the active menu key based on the current route
const activeMenuKey = computed(() => route.name as string);

const currentRouteTitle = computed(() => {
  switch (route.name) {
    case 'Home':
      return '首页';
    case 'Services':
      return '服务管理';
    case 'McpCombination':
      return 'MCP 组合';
    case 'McpManagement':
      return 'MCP 管理';
    default:
      return 'Dashboard';
  }
});
</script>

<style>
body {
  margin: 0;
  font-family: 'Lato', sans-serif;
}
</style>