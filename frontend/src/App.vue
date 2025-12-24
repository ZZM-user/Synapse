<!-- frontend/src/App.vue -->
<template>
  <n-message-provider>
    <n-dialog-provider>
      <n-layout style="height: 100vh">
        <n-layout-header bordered>
          <div style="display: flex; align-items: center; padding: 0 20px; height: 60px;">
            <img src="/logo.svg" alt="Prism Logo" style="height: 32px; margin-right: 12px;"/>
            <h2 style="margin: 0; font-size: 20px; font-weight: 600;">Prism Gateway</h2>
          </div>
        </n-layout-header>
        <n-layout has-sider>
          <n-layout-sider bordered content-style="padding: 12px;">
            <n-menu
              :options="menuOptions"
              :value="activeMenuKey"
            />
          </n-layout-sider>
          <n-layout-content content-style="padding: 24px;">
            <router-view />
          </n-layout-content>
        </n-layout>
      </n-layout>
    </n-dialog-provider>
  </n-message-provider>
</template>

<script setup lang="ts">
import { h, ref, computed, onMounted } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
import { NLayout, NLayoutSider, NLayoutContent, NLayoutHeader, NMenu, NMessageProvider, NDialogProvider } from 'naive-ui';
import type { MenuOption } from 'naive-ui';

// Import fonts
import 'vfonts/Lato.css';
import 'vfonts/FiraCode.css';

const route = useRoute();

const menuOptions: MenuOption[] = [
  {
    label: () => h(RouterLink, { to: { name: 'Home' } }, { default: () => '首页' }),
    key: 'Home',
  },
  {
    label: () => h(RouterLink, { to: { name: 'Services' } }, { default: () => '服务管理' }),
    key: 'Services',
  },
];

// Computed property to determine the active menu key based on the current route
const activeMenuKey = computed(() => route.name);

// Simple logo SVG - will be created in public/logo.svg
onMounted(() => {
  const logoSvg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
      <defs>
        <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#42d392;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#647eff;stop-opacity:1" />
        </linearGradient>
      </defs>
      <polygon points="50,5 95,27.5 95,72.5 50,95 5,72.5 5,27.5" fill="url(#grad1)" />
      <polygon points="50,5 95,27.5 50,50 5,27.5" fill="rgba(255,255,255,0.5)" />
      <polygon points="95,27.5 95,72.5 50,95 50,50" fill="rgba(0,0,0,0.2)" />
    </svg>
  `;
  const blob = new Blob([logoSvg], { type: 'image/svg+xml' });
  const url = URL.createObjectURL(blob);
  const img = new Image();
  img.src = url;
  
  const link = document.createElement('link');
  link.rel = 'icon';
  link.href = url;
  document.head.appendChild(link);

  // This is a simplified way to make the logo available. In a real app,
  // the logo would be a static file. I will create public/logo.svg next.
});
</script>

<style>
body {
  margin: 0;
  font-family: 'Lato', sans-serif;
}
</style>