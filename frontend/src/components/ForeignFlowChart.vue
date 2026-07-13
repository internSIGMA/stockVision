<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import Chart from 'chart.js/auto';

const props = defineProps({
  rows: { type: Array, required: true }, // [{date, foreign_flow}, ...]
});

const canvasRef = ref(null);
let chartInstance = null;

function build() {
  if (!canvasRef.value) return;
  if (chartInstance) chartInstance.destroy();

  const styles = getComputedStyle(document.documentElement);
  const up = styles.getPropertyValue('--up').trim();
  const down = styles.getPropertyValue('--down').trim();
  const muted = styles.getPropertyValue('--ink-muted').trim();
  const border = styles.getPropertyValue('--border').trim();

  chartInstance = new Chart(canvasRef.value, {
    type: 'bar',
    data: {
      labels: props.rows.map((r) => r.date.slice(5)),
      datasets: [
        {
          data: props.rows.map((r) => r.foreign_flow / 1e9),
          backgroundColor: props.rows.map((r) => (r.foreign_flow >= 0 ? up : down)),
          borderWidth: 0,
          barPercentage: 0.7,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (ctx) => `${ctx.parsed.y.toFixed(1)}B` } },
      },
      scales: {
        x: { ticks: { color: muted, maxTicksLimit: 8, font: { family: "'Spline Sans Mono', monospace", size: 10 } }, grid: { display: false } },
        y: {
          ticks: { color: muted, font: { family: "'Spline Sans Mono', monospace", size: 10 }, callback: (v) => `${v.toFixed(1)}B` },
          grid: { color: border },
        },
      },
    },
  });
}

onMounted(build);
watch(() => props.rows, build);
onBeforeUnmount(() => chartInstance && chartInstance.destroy());
</script>

<template>
  <div class="flow-chart-wrap">
    <canvas ref="canvasRef"></canvas>
  </div>
</template>

<style scoped>
.flow-chart-wrap { height: 220px; }
</style>
