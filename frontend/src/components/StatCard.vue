<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  sub: { type: String, default: '' },
  flag: { type: String, default: '' },
  flagTone: { type: String, default: 'muted' }, // 'up' | 'muted'
});
</script>

<template>
  <div class="card stat-card">
    <span v-if="flag" class="stat-flag" :class="flagTone === 'up' ? 'up-tone' : 'muted-tone'">{{ flag }}</span>
    <div class="stat-label">{{ label }}</div>
    <div class="stat-value">{{ value }}</div>
    <div v-if="sub" class="stat-sub">{{ sub }}</div>
  </div>
</template>

<style scoped>
.stat-card { padding: 14px 16px; position: relative; }
.stat-label { font-size: 11px; font-weight: 700; letter-spacing: .06em; color: var(--ink-muted); text-transform: uppercase; }
.stat-value { font-family: var(--font-mono); font-size: 21px; font-weight: 600; margin-top: 6px; }
.stat-sub { font-size: 11.5px; color: var(--ink-muted); margin-top: 4px; font-family: var(--font-mono); }
.stat-flag {
  display: inline-flex; align-items: center; gap: 5px; font-family: var(--font-mono); font-size: 11px;
  font-weight: 700; padding: 2px 8px; border-radius: 20px; position: absolute; top: 14px; right: 14px;
}
.up-tone { background: var(--up-bg); color: var(--up); }
.muted-tone { background: var(--surface-sunken); color: var(--ink-muted); }
</style>
