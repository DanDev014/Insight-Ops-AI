<script setup lang="ts">
import type { NavigationMenuItem } from "@nuxt/ui";

const items: NavigationMenuItem[][] = [
  [
    {
      label: "Dashboard",
      icon: "i-lucide-layout-dashboard",
      to: "/dashboard",
    },
    {
      label: "AI Briefing",
      icon: "i-lucide-sparkles",
      to: "/briefing",
    },
    {
      label: "Clients",
      icon: "i-lucide-users",
      to: "/clients",
    },
    {
      label: "Projects",
      icon: "i-lucide-folder-kanban",
      to: "/projects",
    },
    {
      label: "Team",
      icon: "i-lucide-users-round",
      to: "/team",
    },
    {
      label: "AI Actions",
      icon: "i-lucide-bot",
      to: "/actions",
    },
    {
      label: "Reports",
      icon: "i-lucide-chart-column",
      to: "/reports",
    },
    {
      label: "History",
      icon: "i-lucide-history",
      to: "/history",
    },
  ],
  [
    {
      label: "Settings",
      icon: "i-lucide-settings",
      to: "/settings",
    },
  ],
];

const authStore = useAuthStore();
const user = authStore.user;
</script>

<template>
  <UDashboardSidebar
    collapsible
    resizable
    class="bg-[#0B1020] border-r border-white/10 text-white"
    :ui="{
      root: 'bg-[#0B1020]',
      body: 'bg-[#0B1020]',
      header: 'bg-[#0B1020]',
      footer: 'bg-[#0B1020] border-t border-white/10',
    }"
  >
    <!-- Header -->
    <template #header="{ collapsed }">
      <div class="flex items-center gap-3 px-1 py-2">
        <div
          class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-violet-600 shadow-lg"
        >
          <UIcon name="i-lucide-sparkles" class="size-5 text-white" />
        </div>

        <div v-if="!collapsed" class="min-w-0">
          <h1 class="truncate text-sm font-semibold text-white">Kora AI</h1>

          <p class="text-xs text-gray-400">AI Chief Operating Officer</p>
        </div>
      </div>
    </template>

    <!-- Sidebar -->
    <template #default="{ collapsed }">
      <UButton
        :label="collapsed ? undefined : 'Ask Kora..'"
        icon="i-lucide-search"
        color="neutral"
        variant="soft"
        block
        :square="collapsed"
        class="mb-6 bg-white/5 text-white ring-1 ring-white/10 hover:bg-white/10"
      >
        <template #trailing>
          <div v-if="!collapsed" class="flex items-center gap-1">
            <UKbd value="⌘" />
            <UKbd value="K" />
          </div>
        </template>
      </UButton>

      <UNavigationMenu
        :items="items[0]"
        :collapsed="collapsed"
        orientation="vertical"
        :ui="{
          list: 'space-y-2',
          link: 'rounded-xl px-3 py-2 transition-all',
          linkLeadingIcon: 'size-5',
          linkLabel: 'font-medium',
          linkInactive: 'text-gray-400 hover:bg-white/5 hover:text-white',
          linkActive: 'bg-violet-600 text-white shadow',
        }"
      />

      <UNavigationMenu
        :items="items[1]"
        :collapsed="collapsed"
        orientation="vertical"
        class="mt-auto"
        :ui="{
          list: 'space-y-2',
          link: 'rounded-xl px-3 py-2 transition-all',
          linkLeadingIcon: 'size-5',
          linkLabel: 'font-medium',
          linkInactive: 'text-gray-400 hover:bg-white/5 hover:text-white',
          linkActive: 'bg-violet-600 text-white shadow',
        }"
      />
    </template>

    <!-- Footer -->
    <template #footer="{ collapsed }">
      <button
        class="flex w-full items-center gap-3 rounded-xl p-2 transition hover:bg-white/5"
      >
        <UAvatar src="https://i.pravatar.cc/100?img=12" size="md" />

        <div v-if="!collapsed" class="flex flex-1 items-center justify-between">
          <div class="text-left">
            <p class="text-sm font-medium text-white">{{ user.email }}</p>

            <p class="text-xs text-gray-400">Agency Owner</p>
          </div>
        </div>
      </button>
    </template>
  </UDashboardSidebar>
</template>
