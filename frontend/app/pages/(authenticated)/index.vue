<script setup lang="ts">
import * as v from "valibot";
import type { FormSubmitEvent } from "@nuxt/ui";

definePageMeta({
  layout: "auth",
  title: "Login",
});

const schema = v.object({
  email: v.pipe(
    v.string("Email is required"),
    v.nonEmpty("Email is required"),
    v.email("Enter a valid email address"),
  ),
  password: v.pipe(
    v.string("Password is required"),
    v.nonEmpty("Password is required"),
  ),
});

type Schema = v.InferOutput<typeof schema>;

const state = reactive<Partial<Schema>>({
  email: undefined,
  password: undefined,
});

const loading = ref(false);

async function onSubmit(event: FormSubmitEvent<Schema>) {
  loading.value = true;
  try {
    console.log("Validated login payload, ready for BFF:", event.data);
  } finally {
    loading.value = false;
  }
}

const inputUi = { base: "bg-white  text-black" };
</script>

<template>
  <UCard :ui="{ root: 'shadow-lg ring-0 max-w-sm w-full' }">
    <template #header>
      <div class="text-center">
        <h2 class="text-lg font-semibold text-white">Sign in</h2>
        <p class="text-sm text-muted">Enter your credentials to continue.</p>
      </div>
    </template>

    <UForm :schema="schema" :state="state" class="space-y-4" @submit="onSubmit">
      <UFormField class="text-black" label="Email" name="email" required>
        <UInput
          v-model="state.email"
          type="email"
          placeholder="you@example.com"
          class="w-full"
          :ui="inputUi"
        />
      </UFormField>

      <UFormField label="Password" name="password" required>
        <UInput
          v-model="state.password"
          type="password"
          placeholder="Enter your password"
          class="w-full"
          :ui="inputUi"
        />
      </UFormField>

      <UButton
        type="submit"
        label="Log in"
        color="primary"
        block
        :loading="loading"
      />
    </UForm>
  </UCard>
</template>
