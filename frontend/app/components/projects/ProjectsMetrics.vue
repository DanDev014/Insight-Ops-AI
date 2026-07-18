<script setup lang="ts">
interface Project {
  id: number;
  name: string;
  budget: number;
  deadline: string;
  margin: number;
  status: "active" | "paused" | "completed";
  hours_estimated: number;
  hours_logged: number;
}

const props = defineProps<{
  projects: Project[];
}>();

const metrics = computed(() => {
  const projects = props.projects;

  const totalProjects = projects.length;

  const activeProjects = projects.filter(
    (project) => project.status === "active",
  ).length;

  const atRiskProjects = projects.filter((project) => {
    const progress = (project.hours_logged / project.hours_estimated) * 100;

    return progress >= 90 || project.margin < 15;
  }).length;

  const averageMargin =
    projects.length === 0
      ? 0
      : projects.reduce((sum, project) => sum + project.margin, 0) /
        projects.length;

  const averageProgress =
    projects.length === 0
      ? 0
      : projects.reduce(
          (sum, project) =>
            sum + (project.hours_logged / project.hours_estimated) * 100,
          0,
        ) / projects.length;

  return {
    totalProjects,
    activeProjects,
    atRiskProjects,
    averageMargin,
    averageProgress,
  };
});

const cards = computed(() => [
  {
    title: "Projects",
    value: metrics.value.totalProjects,
    icon: "i-lucide-folder-kanban",
  },
  {
    title: "Active",
    value: metrics.value.activeProjects,
    icon: "i-lucide-activity",
  },
  {
    title: "At Risk",
    value: metrics.value.atRiskProjects,
    icon: "i-lucide-triangle-alert",
  },
  {
    title: "Avg Margin",
    value: `${metrics.value.averageMargin.toFixed(1)}%`,
    icon: "i-lucide-badge-dollar-sign",
  },
  {
    title: "Avg Progress",
    value: `${metrics.value.averageProgress.toFixed(0)}%`,
    icon: "i-lucide-chart-column",
  },
]);
</script>

<template>
  <div class="grid gap-4 mb-5 sm:grid-cols-2 xl:grid-cols-5">
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
