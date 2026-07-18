<script setup lang="ts">
import * as v from "valibot";
import type { FormSubmitEvent } from "@nuxt/ui";

// --- Hardcoded options (backend routes for clients not implemented yet) ---
const clientOptions = [
  { label: "Acme Corp", value: 1 },
  { label: "Northwind Traders", value: 2 },
  { label: "Globex Inc", value: 3 },
  { label: "Initech", value: 4 },
];

const statusOptions = [
  { label: "Active", value: "active" },
  { label: "On Hold", value: "on_hold" },
  { label: "Completed", value: "completed" },
  { label: "Cancelled", value: "cancelled" },
];

// --- Validation schema ---
const schema = v.object({
  name: v.pipe(
    v.string("Project name is required"),
    v.nonEmpty("Project name is required"),
    v.maxLength(100, "Project name must be under 100 characters"),
  ),
  client_id: v.pipe(
    v.number("Client is required"),
    v.minValue(1, "Client is required"),
  ),
  budget: v.pipe(
    v.number("Budget is required"),
    v.minValue(0.01, "Budget must be greater than 0"),
  ),
  hours_estimated: v.pipe(
    v.number("Estimated hours is required"),
    v.minValue(1, "Estimated hours must be at least 1"),
  ),
  deadline: v.pipe(
    v.string("Deadline is required"),
    v.nonEmpty("Deadline is required"),
  ),
  status: v.pipe(
    v.string("Status is required"),
    v.nonEmpty("Status is required"),
  ),
});

type Schema = v.InferOutput<typeof schema>;

const open = ref(false);
const loading = ref(false);

const state = reactive<Partial<Schema>>({
  name: undefined,
  client_id: undefined,
  budget: undefined,
  hours_estimated: undefined,
  deadline: undefined,
  status: undefined,
});

const emit = defineEmits<{
  created: [project: Record<string, any>];
}>();

const toast = useToast();

function resetForm() {
  state.name = undefined;
  state.client_id = undefined;
  state.budget = undefined;
  state.hours_estimated = undefined;
  state.deadline = undefined;
  state.status = undefined;
}

async function onSubmit(event: FormSubmitEvent<Schema>) {
  loading.value = true;
  try {
    const project = await $fetch("/api/projects", {
      method: "POST",
      body: event.data,
    });

    toast.add({
      title: "Project created",
      description: `"${event.data.name}" was added successfully.`,
      color: "success",
    });

    emit("created", project as Record<string, any>);
    resetForm();
    open.value = false;
  } catch (error: any) {
    toast.add({
      title: "Could not create project",
      description:
        error?.data?.error || "Something went wrong. Please try again.",
      color: "error",
    });
  } finally {
    loading.value = false;
  }
}

const inputUi = { base: "bg-white border-2 border-violet-500 text-black" };
const selectUi = {
  base: "bg-white border-2 border-violet-500",
  value: "text-black",
};

const formRef = ref();

function submitForm() {
  formRef.value?.submit();
}
</script>

<template>
  <UModal
    v-model:open="open"
    title="New Project"
    description="Add a new project to track budget, hours, and progress."
  >
    <UButton
      label="New Project"
      icon="i-lucide-plus"
      color="primary"
      @click="open = true"
    />

    <template #body>
      <UForm
        ref="formRef"
        :schema="schema"
        :state="state"
        class="space-y-4"
        @submit="onSubmit"
      >
        <UFormField label="Project name" name="name" required>
          <UInput
            v-model="state.name"
            placeholder="e.g. Website Redesign"
            class="w-full"
            :ui="inputUi"
          />
        </UFormField>

        <UFormField label="Client" name="client_id" required>
          <USelect
            v-model="state.client_id"
            :items="clientOptions"
            value-key="value"
            label-key="label"
            placeholder="Select a client"
            class="w-full"
            :ui="selectUi"
          />
        </UFormField>

        <div class="grid grid-cols-2 gap-4">
          <UFormField label="Budget ($)" name="budget" required>
            <UInput
              v-model.number="state.budget"
              type="number"
              step="0.01"
              placeholder="0.00"
              class="w-full"
              :ui="inputUi"
            />
          </UFormField>

          <UFormField label="Estimated hours" name="hours_estimated" required>
            <UInput
              v-model.number="state.hours_estimated"
              type="number"
              step="1"
              placeholder="0"
              class="w-full"
              :ui="inputUi"
            />
          </UFormField>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <UFormField label="Deadline" name="deadline" required>
            <UInput
              v-model="state.deadline"
              type="date"
              class="w-full"
              :ui="inputUi"
            />
          </UFormField>

          <UFormField label="Status" name="status" required>
            <USelect
              v-model="state.status"
              :items="statusOptions"
              value-key="value"
              label-key="label"
              placeholder="Select status"
              class="w-full"
              :ui="selectUi"
            />
          </UFormField>
        </div>
      </UForm>
    </template>

    <template #footer>
      <div class="flex justify-end gap-3 w-full">
        <UButton
          label="Cancel"
          color="neutral"
          variant="ghost"
          @click="open = false"
        />
        <UButton
          label="Create project"
          color="primary"
          :loading="loading"
          @click="submitForm"
        />
      </div>
    </template>
  </UModal>
</template>
