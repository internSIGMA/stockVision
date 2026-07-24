<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: null },
  /** Komponen ikon Lucide, opsional. */
  icon: { type: [Object, Function], default: null },
})
</script>

<template>
  <div
    class="flex flex-col items-center justify-center gap-2 px-6 py-10 text-center"
    role="status"
  >
    <component
      :is="icon"
      v-if="icon"
      class="size-5 text-muted-foreground/60"
      aria-hidden="true"
    />
    <p class="text-[13px] font-medium">{{ title }}</p>
    <p v-if="description" class="max-w-[42ch] text-[12px] leading-relaxed text-muted-foreground">
      {{ description }}
    </p>
    <div v-if="$slots.action" class="mt-1">
      <slot name="action" />
    </div>
  </div>
</template>
