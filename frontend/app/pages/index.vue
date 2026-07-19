<script setup lang="ts">
import * as v from "valibot";
import type { FormSubmitEvent } from "@nuxt/ui";

definePageMeta({
  layout: "auth",
  title: "Login",
});

// --- Validation schema ---
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
const authStore = useAuthStore();
const toast = useToast();

async function onSubmit(event: FormSubmitEvent<Schema>) {
  loading.value = true;
  try {
    await authStore.login(event.data.email, event.data.password);
    await navigateTo("/dashboard");
    toast.add({
      title: "Welcome back",
      description: "Login Successful",
      color: "success",
    });
  } catch (error: any) {
    toast.add({
      title: "Login failed",
      description:
        error?.data?.statusMessage ||
        error?.data?.message ||
        "Invalid email or password",
      color: "error",
    });
  } finally {
    loading.value = false;
  }
}

const inputUi = { base: "bg-white border-2 border-violet-500 text-black" };
const showPassword = ref(false);

const passwordFieldType = computed(() =>
  showPassword.value ? "text" : "password",
);
</script>

<template>
  <UCard :ui="{ root: 'shadow-lg ring-0 max-w-sm w-full' }">
    <template #header>
      <div>
        <h2 class="text-lg font-semibold text-white">Sign in</h2>
        <p class="text-sm text-muted">Enter your credentials to continue.</p>
      </div>
    </template>

    <UForm :schema="schema" :state="state" class="space-y-4" @submit="onSubmit">
      <UFormField label="Email" name="email" required>
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
          :type="passwordFieldType"
          placeholder="Enter your password"
          class="w-full"
          :ui="inputUi"
        >
          <template #trailing>
            <UButton
              :icon="showPassword ? 'i-lucide-eye-off' : 'i-lucide-eye'"
              color="neutral"
              variant="link"
              :padded="false"
              :aria-label="showPassword ? 'Hide password' : 'Show password'"
              @click="showPassword = !showPassword"
            />
          </template>
        </UInput>
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
