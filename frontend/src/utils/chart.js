export function calculateFromDate(timeframe, lastPointTimeStr, firstPointTimeStr) {
  const lastDate = new Date(lastPointTimeStr)
  let fromDate = new Date(lastDate)

  switch (timeframe) {
    case '1D':
      fromDate.setDate(fromDate.getDate() - 1)
      break
    case '5D':
      fromDate.setDate(fromDate.getDate() - 5)
      break
    case '1M':
      fromDate.setMonth(fromDate.getMonth() - 1)
      break
    case '3M':
      fromDate.setMonth(fromDate.getMonth() - 3)
      break
    case '6M':
      fromDate.setMonth(fromDate.getMonth() - 6)
      break
    case '1Y':
      fromDate.setFullYear(fromDate.getFullYear() - 1)
      break
    case 'YTD':
      fromDate = new Date(lastDate.getFullYear(), 0, 1)
      break
  }

  if (firstPointTimeStr) {
    const firstHist = new Date(firstPointTimeStr)
    if (fromDate < firstHist) {
      fromDate = firstHist
    }
  }

  return fromDate.toISOString().split('T')[0]
}

export function applyChartTimeframe(chartInstance, timeframe, dataAktual, showForecast, dataProyeksiLine) {
  if (!chartInstance || !dataAktual?.length) return

  if (timeframe === 'ALL') {
    chartInstance.timeScale().fitContent()
    return
  }

  let lastPointTime = dataAktual[dataAktual.length - 1].time
  if (showForecast && dataProyeksiLine?.length) {
    lastPointTime = dataProyeksiLine[dataProyeksiLine.length - 1].time
  }

  const lastHist = dataAktual[dataAktual.length - 1].time
  const firstHist = dataAktual[0].time
  const fromStr = calculateFromDate(timeframe, lastHist, firstHist)

  chartInstance.timeScale().setVisibleRange({
    from: fromStr,
    to: lastPointTime,
  })
}

export function applyIndicatorTimeframe(chartInstance, timeframe, dataArr) {
  if (!chartInstance || !dataArr?.length) return

  if (timeframe === 'ALL') {
    chartInstance.timeScale().fitContent()
    return
  }

  const lastPointTime = dataArr[dataArr.length - 1].time
  const firstPointTime = dataArr[0].time
  const fromStr = calculateFromDate(timeframe, lastPointTime, firstPointTime)

  chartInstance.timeScale().setVisibleRange({
    from: fromStr,
    to: lastPointTime,
  })
}
