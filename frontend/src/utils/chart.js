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
