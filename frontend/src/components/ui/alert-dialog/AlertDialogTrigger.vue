<script setup>
import { AlertDialogTrigger } from "reka-ui";

const props = defineProps({
  asChild: { type: Boolean, required: false },
  as: { type: null, required: false },
});
</script>

<template>
  <AlertDialogTrigger
    data-slot="alert-dialog-trigger"
    :as="as"
    :as-child="asChild"
  >
    <slot />
  </AlertDialogTrigger>
</template>
