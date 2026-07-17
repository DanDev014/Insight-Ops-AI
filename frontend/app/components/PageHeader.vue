<template>
  <div class="flex flex-col items-start gap-2">
    <h3 class="font-bold">{{ props.title }}</h3>
    <p class="text-gray-500 text-sm">{{ props.description }}</p>
  </div>
</template>
<script setup lang="ts">
const props = defineProps<{
  title: string;
  description: string;
}>();
</script>
