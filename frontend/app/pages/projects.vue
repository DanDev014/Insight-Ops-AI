<template>
  <div class="flex flex-col gap-2 w-full">
    <PageHeader
      title="Projects"
      description="Track project perfomance and profitability"
    />

    <ProjectsMetrics :projects="projects || []" />

    <ProjectsTable :projects="projects || []" :loading="pending" />

    <UAlert
      v-if="error"
      color="error"
      variant="soft"
      title="Unable to load projects."
    >
      <template #actions>
        <UButton label="Retry" @click="refresh" />
      </template>
    </UAlert>
  </div>
</template>
<script setup lang="ts">
import ProjectsMetrics from "~/components/projects/ProjectsMetrics.vue";
import ProjectsTable from "~/components/projects/ProjectsTable.vue";

const {
  data: projects,
  pending,
  error,
  refresh,
} = await useFetch("/api/projects");
</script>
