<template>
  <n-message-provider>
    <n-dialog-provider>
      <n-layout has-sider style="height: 100vh">
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
            <div style="display: flex; align-items: center; padding: 0 24px; height: 60px;">
              <h2 style="margin: 0; font-size: 18px; font-weight: 600;">{{ currentRouteTitle }}</h2>
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
import {computed, h} from 'vue';
import {RouterLink, useRoute} from 'vue-router';
import type {MenuOption} from 'naive-ui';
import {
  NDialogProvider,
  NIcon,
  NLayout,
  NLayoutContent,
  NLayoutHeader,
  NLayoutSider,
  NMenu,
  NMessageProvider
} from 'naive-ui';
import {CubeOutline, HomeOutline, HardwareChipOutline, ServerOutline} from '@vicons/ionicons5';

// Import fonts
import 'vfonts/Lato.css';
import 'vfonts/FiraCode.css';

const route = useRoute();

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