<script setup lang="ts">
import * as v from "valibot";
import type { FormSubmitEvent } from "@nuxt/ui";

const industryOptions = [
  { label: "Fintech", value: "Fintech" },
  { label: "Retail", value: "Retail" },
  { label: "Healthcare", value: "Healthcare" },
  { label: "SaaS", value: "SaaS" },
  { label: "E-commerce", value: "E-commerce" },
  { label: "Logistics", value: "Logistics" },
  { label: "Energy", value: "Energy" },
  { label: "Real Estate", value: "Real Estate" },
  { label: "Entertainment", value: "Entertainment" },
];

// --- Validation schema ---
const schema = v.object({
  name: v.pipe(
    v.string("Client name is required"),
    v.nonEmpty("Client name is required"),
    v.maxLength(100, "Client name must be under 100 characters"),
  ),
  industry: v.pipe(
    v.string("Industry is required"),
    v.nonEmpty("Industry is required"),
  ),
  contract_value: v.pipe(
    v.number("Contract value is required"),
    v.minValue(0.01, "Contract value must be greater than 0"),
  ),
  payment_terms: v.pipe(
    v.number("Payment terms is required"),
    v.minValue(1, "Payment terms must be at least 1 day"),
  ),
  historical_payment_delay: v.pipe(
    v.number("Historical payment delay is required"),
    v.minValue(0, "Historical payment delay cannot be negative"),
  ),
  engagement_score: v.pipe(
    v.number("Engagement score is required"),
    v.minValue(0, "Engagement score must be between 0 and 1"),
    v.maxValue(1, "Engagement score must be between 0 and 1"),
  ),
});

type Schema = v.InferOutput<typeof schema>;

const open = defineModel<boolean>("open", { default: false });
const loading = ref(false);

const state = reactive<Partial<Schema>>({
  name: undefined,
  industry: undefined,
  contract_value: undefined,
  payment_terms: undefined,
  historical_payment_delay: undefined,
  engagement_score: undefined,
});

const emit = defineEmits<{
  created: [client: Record<string, any>];
}>();

const toast = useToast();

function resetForm() {
  state.name = undefined;
  state.industry = undefined;
  state.contract_value = undefined;
  state.payment_terms = undefined;
  state.historical_payment_delay = undefined;
  state.engagement_score = undefined;
}

async function onSubmit(event: FormSubmitEvent<Schema>) {
  loading.value = true;
  try {
    const client = await $fetch("/api/clients", {
      method: "POST",
      body: event.data,
    });

    toast.add({
      title: "Client created",
      description: `"${event.data.name}" was added successfully.`,
      color: "success",
    });

    emit("created", client as Record<string, any>);
    resetForm();
    open.value = false;
  } catch (error: any) {
    toast.add({
      title: "Could not create client",
      description:
        error?.data?.statusMessage ||
        error?.data?.error ||
        "Something went wrong. Please try again.",
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
    title="New Client"
    description="Add a new client to track engagement and payment behavior."
    :modal="true"
    :dismissible="false"
  >
    <template #body>
      <UForm
        ref="formRef"
        :schema="schema"
        :state="state"
        class="space-y-4"
        @submit="onSubmit"
      >
        <UFormField label="Client name" name="name" required>
          <UInput
            v-model="state.name"
            placeholder="e.g. Acme Corp"
            class="w-full"
            :ui="inputUi"
          />
        </UFormField>

        <UFormField label="Industry" name="industry" required>
          <USelect
            v-model="state.industry"
            :items="industryOptions"
            value-key="value"
            label-key="label"
            placeholder="Select an industry"
            class="w-full"
            :ui="selectUi"
          />
        </UFormField>

        <div class="grid grid-cols-2 gap-4">
          <UFormField label="Contract value ($)" name="contract_value" required>
            <UInput
              v-model.number="state.contract_value"
              type="number"
              step="0.01"
              placeholder="0.00"
              class="w-full"
              :ui="inputUi"
            />
          </UFormField>

          <UFormField
            label="Payment terms (days)"
            name="payment_terms"
            required
          >
            <UInput
              v-model.number="state.payment_terms"
              type="number"
              step="1"
              placeholder="30"
              class="w-full"
              :ui="inputUi"
            />
          </UFormField>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <UFormField
            label="Historical payment delay (days)"
            name="historical_payment_delay"
            required
          >
            <UInput
              v-model.number="state.historical_payment_delay"
              type="number"
              step="1"
              placeholder="0"
              class="w-full"
              :ui="inputUi"
            />
          </UFormField>

          <UFormField
            label="Engagement score (0–1)"
            name="engagement_score"
            required
          >
            <UInput
              v-model.number="state.engagement_score"
              type="number"
              step="0.01"
              min="0"
              max="1"
              placeholder="0.50"
              class="w-full"
              :ui="inputUi"
            />
          </UFormField>
        </div>
      </UForm>
    </template>

    <template #footer>
      <div class="flex justify-end gap-3 w-full">
        <UButton
          label="Create client"
          color="primary"
          :loading="loading"
          @click="submitForm"
        />
      </div>
    </template>
  </UModal>
</template>
