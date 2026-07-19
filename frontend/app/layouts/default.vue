<template>
  <UDashboardGroup>
    <LayoutAppSidebar />
    <div
      class="p-4 text-black flex flex-col w-full min-h-screen overflow-y-scroll"
    >
      <UButton
        label="Logout"
        class="text-white self-end w-[10%] flex items-center justify-center"
        color="primary"
        @click="onLogoutClick()"
        :loading="loading"
      />
      <slot />
    </div>
  </UDashboardGroup>
</template>
<script setup lang="ts">
const authStore = useAuthStore();
const loading = ref(false);
const toast = useToast();
const onLogoutClick = async () => {
  loading.value = true;
  try {
    await authStore.logout();
    await navigateTo("/");
    toast.add({
      title: "Logout Successful",
      color: "success",
    });
  } catch {
    toast.add({
      title: "Logout failed",
      description: "Something went wrong. Please try again.",
      color: "error",
    });
  } finally {
    loading.value = false;
  }
};
</script>
