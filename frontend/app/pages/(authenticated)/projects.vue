<template>
  <div class="flex flex-col gap-2 w-full">
    <PageHeader
      title="Projects"
      description="Track project perfomance and profitability"
    />

    <ProjectsMetrics :projects="projects || []" :total="total" />

    <ProjectsTable
      v-model:search="search"
      v-model:status="status"
      v-model:page="page"
      :projects="projects || []"
      :loading="pending"
      :total="total"
      :per-page="perPage"
      @created="onProjectCreated"
    />

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

const search = ref("");
const status = ref("all");
const page = ref(1);
const perPage = ref(20);

// Debounce search input so we don't fire a request on every keystroke
const debouncedSearch = ref("");
let debounceTimer: ReturnType<typeof setTimeout>;
watch(search, (value) => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    debouncedSearch.value = value;
    page.value = 1;
  }, 300);
});

watch(status, () => {
  page.value = 1;
});

interface ProjectsResponse {
  projects: any[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

const { data, pending, error, refresh } = await useFetch<ProjectsResponse>(
  "/api/projects",
  {
    query: computed(() => ({
      page: page.value,
      per_page: perPage.value,
      search: debouncedSearch.value,
      status: status.value === "all" ? "" : status.value,
    })),
    watch: [page, perPage, debouncedSearch, status],
  },
);

const projects = computed(() => data.value?.projects ?? []);
const total = computed(() => data.value?.total ?? 0);

function onProjectCreated() {
  page.value = 1;
  refresh();
}
</script>
