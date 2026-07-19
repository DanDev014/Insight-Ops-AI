<template>
  <div class="flex flex-col gap-2 w-full">
    <PageHeader
      title="Clients"
      description="Monitor client relationships and payment risk"
    />

    <ClientsMetrics :clients="clients || []" :total="total" />

    <ClientsTable
      v-model:search="search"
      v-model:risk="riskFilter"
      v-model:page="page"
      :clients="clients || []"
      :loading="pending"
      :total="total"
      :per-page="perPage"
      @created="onClientCreated"
    />

    <UAlert
      v-if="error"
      color="error"
      variant="soft"
      title="Unable to load clients."
    >
      <template #actions>
        <UButton label="Retry" @click="refresh" />
      </template>
    </UAlert>
  </div>
</template>
<script setup lang="ts">
import ClientsMetrics from "~/components/clients/ClientsMetrics.vue";
import ClientsTable from "~/components/clients/ClientsTable.vue";

const search = ref("");
const riskFilter = ref("all");
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

watch(riskFilter, () => {
  page.value = 1;
});

interface ClientsResponse {
  clients: any[];
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}

const { data, pending, error, refresh } = await useFetch<ClientsResponse>(
  "/api/clients",
  {
    query: computed(() => ({
      page: page.value,
      per_page: perPage.value,
      search: debouncedSearch.value,
      // Sent for forward-compatibility; Flask doesn't filter on this yet
      // since risk classification isn't computed server-side.
      risk: riskFilter.value === "all" ? "" : riskFilter.value,
    })),
    watch: [page, perPage, debouncedSearch, riskFilter],
  },
);

const clients = computed(() => data.value?.clients ?? []);
const total = computed(() => data.value?.total ?? 0);

function onClientCreated() {
  page.value = 1;
  refresh();
}
</script>
