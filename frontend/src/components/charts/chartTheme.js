// Shared ApexCharts styling so every chart reads as one system (navy dark).
export const COLORS = {
  brand: '#3aab9d',
  up: '#16c784',
  down: '#ef4757',
  info: '#3b82f6',
  purple: '#a78bfa',
  amber: '#f59e0b',
  line: '#e8eefb',
  grid: '#253272',
  text: '#8592ac',
}

export const baseChart = {
  fontFamily: 'Inter, system-ui, sans-serif',
  toolbar: { show: false },
  zoom: { enabled: false },
  animations: { easing: 'easeinout', speed: 400 },
}

export function axisStyle() {
  return {
    labels: { style: { colors: COLORS.text, fontSize: '11px' } },
    axisBorder: { show: false },
    axisTicks: { show: false },
  }
}

export const gridStyle = {
  borderColor: COLORS.grid,
  strokeDashArray: 4,
  padding: { left: 8, right: 8 },
}
