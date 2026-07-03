<script setup>
defineProps({
  label: String,
  value: [String, Number],
  sub: String,
  change: Number, // percent, optional
  icon: String, // svg path
  tone: { type: String, default: 'brand' },
})
</script>

<template>
  <div class="stat card">
    <div class="top">
      <span class="ic" :class="`ic--${tone}`" v-if="icon">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path :d="icon" /></svg>
      </span>
      <span
        v-if="change != null"
        class="pill"
        :class="change >= 0 ? 'pill--up' : 'pill--down'"
      >
        {{ change >= 0 ? '▲' : '▼' }} {{ Math.abs(change).toFixed(2) }}%
      </span>
    </div>
    <div class="value tabular">{{ value }}</div>
    <div class="label">{{ label }}</div>
    <div v-if="sub" class="sub">{{ sub }}</div>
  </div>
</template>

<style scoped>
.stat {
  display: flex;
  flex-direction: column;
}
.top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  min-height: 28px;
}
.ic {
  width: 38px;
  height: 38px;
  border-radius: 11px;
  display: grid;
  place-items: center;
}
.ic--brand {
  background: var(--surface-2);
  color: var(--brand);
}
.ic--up {
  background: var(--up-bg);
  color: var(--up);
}
.ic--down {
  background: var(--down-bg);
  color: var(--down);
}
.ic--info {
  background: #e0f2fe;
  color: #0369a1;
}
.value {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.label {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}
.sub {
  font-size: 12px;
  color: var(--text-faint);
  margin-top: 6px;
}
</style>
