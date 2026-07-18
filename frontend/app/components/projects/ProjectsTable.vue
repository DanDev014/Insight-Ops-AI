<script setup lang="ts">
interface Project {
  id: number;
  name: string;
  budget: number;
  deadline: string;
  margin: number;
  status: string;
  hours_estimated: number;
  hours_logged: number;
}

const props = defineProps<{
  projects: Project[];
  loading?: boolean;
}>();

const search = ref("");
const status = ref("all");

const statusOptions = [
  { label: "All", value: "all" },
  { label: "Active", value: "active" },
  { label: "Paused", value: "paused" },
  { label: "Completed", value: "completed" },
];

const filteredProjects = computed(() => {
  return props.projects.filter((project) => {
    const matchesSearch = project.name
      .toLowerCase()
      .includes(search.value.toLowerCase());

    const matchesStatus =
      status.value === "all" || project.status === status.value;

    return matchesSearch && matchesStatus;
  });
});

const columns = [
  {
    accessorKey: "name",
    header: "Project",
  },
  {
    accessorKey: "budget",
    header: "Budget",
  },
  {
    accessorKey: "margin",
    header: "Margin",
  },
  {
    accessorKey: "progress",
    header: "Progress",
  },
  {
    accessorKey: "deadline",
    header: "Deadline",
  },
  {
    accessorKey: "status",
    header: "Status",
  },
];

const progress = (project: Project) =>
  Math.min(
    100,
    Math.round((project.hours_logged / project.hours_estimated) * 100),
  );

const currency = new Intl.NumberFormat("en-KE", {
  style: "currency",
  currency: "KES",
  maximumFractionDigits: 0,
});

const formatDate = (date: string) =>
  new Date(date).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

const badgeColor = (status: string) => {
  switch (status) {
    case "active":
      return "success";

    case "paused":
      return "warning";

    case "completed":
      return "primary";

    default:
      return "neutral";
  }
};
</script>

<template>
  <UCard :ui="{ root: 'bg-white shadow-lg ring-0' }">
    <template #header>
      <div
        class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between"
      >
        <div>
          <h2 class="text-lg font-semibold">Projects</h2>

          <p class="text-sm text-muted">
            Monitor project profitability and delivery.
          </p>
        </div>

        <div class="flex gap-3">
          <UInput
            v-model="search"
            icon="i-lucide-search"
            placeholder="Search projects..."
            variant="ghost"
            :highlight="true"
            class="w-72"
            :ui="{
              base: 'bg-white focus:bg-white border-2 border-violet-500 text-black',
            }"
          />

          <USelect
            v-model="status"
            :items="statusOptions"
            value-key="value"
            label-key="label"
            class="w-40"
            :ui="{
              base: 'bg-white border-2 border-violet-500',
              value: 'text-black',
            }"
          />
          <UButton
            icon="i-lucide-plus"
            label="New Project"
            class="text-white"
          />
        </div>
      </div>
    </template>

    <UTable
      :loading="loading"
      :data="filteredProjects"
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

      <template #budget-cell="{ row }">
        {{ currency.format(row.original.budget) }}
      </template>

      <template #margin-cell="{ row }">
        <UBadge
          :color="row.original.margin >= 20 ? 'success' : 'warning'"
          variant="soft"
        >
          {{ row.original.margin }}%
        </UBadge>
      </template>

      <template #progress-cell="{ row }">
        <div class="flex items-center gap-3 w-44">
          <UProgress :model-value="progress(row.original)" />

          <span class="text-sm font-medium whitespace-nowrap">
            {{ progress(row.original) }}%
          </span>
        </div>
      </template>

      <template #deadline-cell="{ row }">
        {{ formatDate(row.original.deadline) }}
      </template>

      <template #status-cell="{ row }">
        <UBadge :color="badgeColor(row.original.status)" variant="soft">
          {{ row.original.status }}
        </UBadge>
      </template>
    </UTable>
  </UCard>
</template>
