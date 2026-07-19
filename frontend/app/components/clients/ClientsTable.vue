<script setup lang="ts">
import ClientModal from "./ClientModal.vue";

interface Client {
  id: number;
  name: string;
  industry: string | null;
  contract_value: number | null;
  payment_terms: number | null;
  historical_payment_delay: number | null;
  engagement_score: number | null;
}

defineProps<{
  clients: Client[];
  loading?: boolean;
  total?: number;
  perPage?: number;
}>();

const emit = defineEmits<{
  created: [client: Record<string, any>];
}>();

const search = defineModel<string>("search", { default: "" });
// NOTE: risk classification isn't computed by the backend yet, so this filter
// currently has no effect on the returned data — it's wired up client-side
// (sent as a `risk` query param) so it's ready to go once the backend
// supports it, but it's a no-op for now.
const riskFilter = defineModel<string>("risk", { default: "all" });
const page = defineModel<number>("page", { default: 1 });

const showModal = ref(false);

const riskOptions = [
  { label: "All", value: "all" },
  { label: "High Risk", value: "high" },
  { label: "Medium Risk", value: "medium" },
  { label: "Low Risk", value: "low" },
];

function riskButtonClass(value: string) {
  return riskFilter.value === value
    ? "text-white"
    : "bg-white border-2 border-violet-500 text-violet-500";
}

function riskButtonColor(value: string) {
  return riskFilter.value === value ? "primary" : "neutral";
}

function onClientCreated(client: Record<string, any>) {
  emit("created", client);
}

const columns = [
  {
    accessorKey: "name",
    header: "Client",
  },
  {
    accessorKey: "industry",
    header: "Industry",
  },
  {
    accessorKey: "contract_value",
    header: "Contract Value",
  },
  {
    accessorKey: "payment_terms",
    header: "Payment Terms",
  },
  {
    accessorKey: "historical_payment_delay",
    header: "Avg Delay",
  },
  {
    accessorKey: "engagement_score",
    header: "Engagement",
  },
  {
    accessorKey: "risk_level",
    header: "Risk Level",
  },
  {
    accessorKey: "confidence",
    header: "Confidence",
  },
];

const currency = new Intl.NumberFormat("en-KE", {
  style: "currency",
  currency: "KES",
  maximumFractionDigits: 0,
});
</script>

<template>
  <UCard :ui="{ root: 'bg-white shadow-lg ring-0' }">
    <template #header>
      <div
        class="flex flex-col gap-4 w-full md:flex-row md:items-center md:justify-between"
      >
        <div class="flex flex-wrap gap-3 w-full justify-between">
          <UInput
            v-model="search"
            icon="i-lucide-search"
            placeholder="Search clients..."
            variant="ghost"
            :highlight="true"
            class="w-72"
            :ui="{
              base: 'bg-white focus:bg-white border-2 border-violet-500 text-black',
            }"
          />

          <div class="flex gap-2">
            <UButton
              v-for="option in riskOptions"
              :key="option.value"
              :label="option.label"
              :color="riskButtonColor(option.value)"
              :class="riskButtonClass(option.value)"
              @click="riskFilter = option.value"
            />
          </div>

          <UButton
            icon="i-lucide-plus"
            label="Add Client"
            class="text-white"
            @click="showModal = true"
          />
        </div>
      </div>
      <ClientModal v-model:open="showModal" @created="onClientCreated" />
    </template>

    <UTable
      :loading="loading"
      :data="clients"
      :columns="columns"
      :ui="{ th: 'text-black' }"
    >
      <template #name-cell="{ row }">
        <div>
          <p class="font-medium">
            {{ row.original.name }}
          </p>

          <p class="text-xs text-muted">#{{ row.original.id }}</p>
        </div>
      </template>

      <template #industry-cell="{ row }">
        {{ row.original.industry ?? "—" }}
      </template>

      <template #contract_value-cell="{ row }">
        {{
          row.original.contract_value != null
            ? currency.format(row.original.contract_value)
            : "—"
        }}
      </template>

      <template #payment_terms-cell="{ row }">
        {{
          row.original.payment_terms != null
            ? `${row.original.payment_terms}d`
            : "—"
        }}
      </template>

      <template #historical_payment_delay-cell="{ row }">
        {{
          row.original.historical_payment_delay != null
            ? `${row.original.historical_payment_delay}d`
            : "—"
        }}
      </template>

      <template #engagement_score-cell="{ row }">
        {{
          row.original.engagement_score != null
            ? row.original.engagement_score.toFixed(2)
            : "—"
        }}
      </template>

      <template #risk_level-cell>
        <span class="text-muted">—</span>
      </template>

      <template #confidence-cell>
        <span class="text-muted">—</span>
      </template>
    </UTable>

    <template #footer>
      <div class="flex justify-center items-center">
        <UPagination
          v-model:page="page"
          :total="total ?? 0"
          :items-per-page="perPage ?? 20"
        />
      </div>
    </template>
  </UCard>
</template>
