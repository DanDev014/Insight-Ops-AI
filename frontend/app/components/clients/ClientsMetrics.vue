<script setup lang="ts">
interface Client {
  id: number;
  name: string;
  industry: string | null;
  contract_value: number | null;
  payment_terms: number | null;
  historical_payment_delay: number | null;
  engagement_score: number | null;
}

const props = defineProps<{
  clients: Client[];
  total?: number;
}>();

const metrics = computed(() => {
  const clients = props.clients;

  // Real total count across all pages, from the API's pagination metadata.
  const totalClients = props.total ?? clients.length;

  const withContractValue = clients.filter((c) => c.contract_value != null);
  const totalContractValue = withContractValue.reduce(
    (sum, c) => sum + (c.contract_value ?? 0),
    0,
  );

  const withEngagement = clients.filter((c) => c.engagement_score != null);
  const averageEngagement =
    withEngagement.length === 0
      ? 0
      : withEngagement.reduce((sum, c) => sum + (c.engagement_score ?? 0), 0) /
        withEngagement.length;

  const withDelay = clients.filter((c) => c.historical_payment_delay != null);
  const averageDelay =
    withDelay.length === 0
      ? 0
      : withDelay.reduce(
          (sum, c) => sum + (c.historical_payment_delay ?? 0),
          0,
        ) / withDelay.length;

  return {
    totalClients,
    totalContractValue,
    averageEngagement,
    averageDelay,
  };
});

const currency = new Intl.NumberFormat("en-KE", {
  style: "currency",
  currency: "KES",
  maximumFractionDigits: 0,
  notation: "compact",
});

const cards = computed(() => [
  {
    title: "Clients",
    value: metrics.value.totalClients,
    icon: "i-lucide-users",
  },
  {
    title: "Total Contract Value",
    value: currency.format(metrics.value.totalContractValue),
    icon: "i-lucide-badge-dollar-sign",
  },
  {
    title: "Avg Engagement",
    value: metrics.value.averageEngagement.toFixed(2),
    icon: "i-lucide-heart-handshake",
  },
  {
    title: "Avg Payment Delay",
    value: `${metrics.value.averageDelay.toFixed(0)}d`,
    icon: "i-lucide-clock-alert",
  },
]);
</script>

<template>
  <div class="grid gap-4 mb-5 sm:grid-cols-2 xl:grid-cols-4">
    <UCard
      v-for="card in cards"
      :key="card.title"
      :ui="{ root: 'bg-white shadow-lg ring-0' }"
    >
      <div class="flex items-start justify-between">
        <div>
          <p class="text-sm text-muted">
            {{ card.title }}
          </p>

          <p class="mt-2 text-3xl font-semibold">
            {{ card.value }}
          </p>
        </div>

        <div
          class="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10"
        >
          <UIcon :name="card.icon" class="size-5 text-primary" />
        </div>
      </div>
    </UCard>
  </div>
</template>
