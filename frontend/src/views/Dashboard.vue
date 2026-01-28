<template>
  <div class="dashboard">
    <h2>Dashboard</h2>
    
    <!-- Filters Section -->
    <div class="filters">
      <div class="filter-group">
        <label>
          <input 
            type="checkbox" 
            v-model="filters.excludeSpecial"
            @change="applyClientFilters"
          />
          Exclude Special Transactions
        </label>
      </div>
      
      <div class="filter-group">
        <label for="bank-filter">Bank:</label>
        <v-select
          id="bank-filter"
          v-model="filters.bankNames"
          :options="availableBanks"
          multiple
          @update:modelValue="onBankChange"
        />
        <div class="multiselect-info">
          {{ filters.bankNames.length }} of {{ availableBanks.length }} selected
        </div>
      </div>
      
      <div class="filter-group">
        <label for="account-filter">Account:</label>
        <v-select
          id="account-filter"
          v-model="filters.accountNames"
          :options="availableAccounts"
          multiple
          @update:modelValue="applyClientFilters"
        />
        <div class="multiselect-info">
          {{ filters.accountNames.length }} of {{ availableAccounts.length }} selected
        </div>
      </div>
      
      <div class="filter-group">
        <label for="start-date">Start Date:</label>
        <input 
          type="date" 
          id="start-date"
          v-model="filters.startDate"
          @change="applyFilters"
        />
      </div>
      
      <div class="filter-group">
        <label for="end-date">End Date:</label>
        <input 
          type="date" 
          id="end-date"
          v-model="filters.endDate"
          @change="applyFilters"
        />
      </div>
      
      <div class="filter-group">
        <label for="min-amount">Min Amount:</label>
        <input 
          type="number" 
          id="min-amount"
          v-model.number="filters.minAmount"
          @input="applyClientFilters"
          placeholder="Min"
        />
      </div>
      
      <div class="filter-group">
        <label for="max-amount">Max Amount:</label>
        <input 
          type="number" 
          id="max-amount"
          v-model.number="filters.maxAmount"
          @input="applyClientFilters"
          placeholder="Max"
        />
      </div>
    </div>
    
    <!-- Loading State -->
    <div v-if="loading" class="loading">
      Loading transactions...
    </div>
    
    <!-- Error State -->
    <div v-if="error" class="error">
      {{ error }}
    </div>
    
    <!-- Charts Section -->
    <div v-if="!loading && !error" class="charts">
      <div class="chart-container">
        <h3>Transactions Over Time</h3>
        <canvas ref="scatterChartRef"></canvas>
      </div>
      
      <div class="chart-container">
        <h3>Monthly Income, Expenses, and Balance</h3>
        <canvas ref="monthlyChartRef"></canvas>
      </div>
      
      <div class="chart-container">
        <h3>Cumulative Balance Over Time</h3>
        <canvas ref="cumulativeChartRef"></canvas>
      </div>
      
      <div class="chart-container">
        <h3>Assets History</h3>
        <canvas ref="assetsHistoryChartRef"></canvas>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import { Chart, registerables } from 'chart.js';
import zoomPlugin from 'chartjs-plugin-zoom';
import { format, parseISO, startOfMonth } from 'date-fns';
import type { Transaction, AssetsHistory } from '@/types';
import { api } from '@/api/client';

// Register Chart.js components
Chart.register(...registerables);
Chart.register(zoomPlugin);

// Refs for chart canvases
const assetsHistoryChartRef = ref<HTMLCanvasElement | null>(null);
const scatterChartRef = ref<HTMLCanvasElement | null>(null);
const monthlyChartRef = ref<HTMLCanvasElement | null>(null);
const cumulativeChartRef = ref<HTMLCanvasElement | null>(null);

// Chart instances
let assetsHistoryChart: Chart | null = null;
let scatterChart: Chart | null = null;
let monthlyChart: Chart | null = null;
let cumulativeChart: Chart | null = null;

// Double-click handlers for cleanup
let assetsHistoryDblClickHandler: ((e: MouseEvent) => void) | null = null;
let scatterDblClickHandler: ((e: MouseEvent) => void) | null = null;
let monthlyDblClickHandler: ((e: MouseEvent) => void) | null = null;
let cumulativeDblClickHandler: ((e: MouseEvent) => void) | null = null;

// State
const loading = ref(false);
const error = ref<string | null>(null);
const allTransactions = ref<Transaction[]>([]);
const filteredTransactions = ref<Transaction[]>([]);
const assetsHistory = ref<AssetsHistory[]>([]);

// Filters
const filters = ref({
  excludeSpecial: true,
  bankNames: [] as string[],
  accountNames: [] as string[],
  startDate: '',
  endDate: '',
  minAmount: null as number | null,
  maxAmount: null as number | null,
});

// Available options for dropdowns
const availableBanks = ref<string[]>([]);
const availableAccounts = ref<string[]>([]);

// Fetch transactions from API
async function fetchTransactions() {
  loading.value = true;
  error.value = null;
  
  try {
    const params: {
      start_date?: string;
      end_date?: string;
    } = {};
    
    // Only use date filters for API call
    // Bank and account filters will be applied client-side for multiselect support
    if (filters.value.startDate) {
      params.start_date = filters.value.startDate;
    }
    if (filters.value.endDate) {
      params.end_date = filters.value.endDate;
    }
    
    const transactions = await api.transactions.getAll(params);
    allTransactions.value = transactions;
    
    // Extract unique banks and accounts
    const banks = new Set<string>();
    const accounts = new Set<string>();
    
    transactions.forEach(t => {
      banks.add(t.bank_name);
      accounts.add(t.account_name);
    });
    
    const sortedBanks = Array.from(banks).sort();
    const sortedAccounts = Array.from(accounts).sort();
    
    // Update available options
    const banksChanged = JSON.stringify(availableBanks.value) !== JSON.stringify(sortedBanks);
    const accountsChanged = JSON.stringify(availableAccounts.value) !== JSON.stringify(sortedAccounts);
    
    availableBanks.value = sortedBanks;
    availableAccounts.value = sortedAccounts;
    
    // Set default selections to all if this is the first load or if options changed
    if (filters.value.bankNames.length === 0 || banksChanged) {
      filters.value.bankNames = [...availableBanks.value];
    } else {
      // Keep only valid selections
      filters.value.bankNames = filters.value.bankNames.filter(b => availableBanks.value.includes(b));
      // If no valid selections, select all
      if (filters.value.bankNames.length === 0) {
        filters.value.bankNames = [...availableBanks.value];
      }
    }
    
    if (filters.value.accountNames.length === 0 || accountsChanged) {
      filters.value.accountNames = [...availableAccounts.value];
    } else {
      // Keep only valid selections
      filters.value.accountNames = filters.value.accountNames.filter(a => availableAccounts.value.includes(a));
      // If no valid selections, select all
      if (filters.value.accountNames.length === 0) {
        filters.value.accountNames = [...availableAccounts.value];
      }
    }
    
    applyClientFilters();
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load transactions';
    console.error('Error fetching transactions:', err);
  } finally {
    loading.value = false;
  }
}

// Apply client-side filters
function applyClientFilters() {
  let filtered = [...allTransactions.value];
  
  // Filter by bank names (multiselect)
  if (filters.value.bankNames.length > 0 && filters.value.bankNames.length < availableBanks.value.length) {
    filtered = filtered.filter(t => filters.value.bankNames.includes(t.bank_name));
  }
  
  // Filter by account names (multiselect)
  if (filters.value.accountNames.length > 0 && filters.value.accountNames.length < availableAccounts.value.length) {
    filtered = filtered.filter(t => filters.value.accountNames.includes(t.account_name));
  }
  
  // Filter by is_special
  if (filters.value.excludeSpecial) {
    filtered = filtered.filter(t => !t.is_special);
  }
  
  // Filter by amount range
  if (filters.value.minAmount !== null) {
    filtered = filtered.filter(t => t.amount >= filters.value.minAmount!);
  }
  if (filters.value.maxAmount !== null) {
    filtered = filtered.filter(t => t.amount <= filters.value.maxAmount!);
  }
  
  filteredTransactions.value = filtered;
  updateCharts();
}

// Handle bank filter change - update available accounts
function onBankChange() {
  // Update available accounts based on selected banks
  if (filters.value.bankNames.length > 0 && filters.value.bankNames.length < availableBanks.value.length) {
    const accounts = new Set<string>();
    allTransactions.value
      .filter(t => filters.value.bankNames.includes(t.bank_name))
      .forEach(t => accounts.add(t.account_name));
    const newAvailableAccounts = Array.from(accounts).sort();
    
    // Update available accounts
    availableAccounts.value = newAvailableAccounts;
    
    // Keep only valid account selections
    filters.value.accountNames = filters.value.accountNames.filter(a => newAvailableAccounts.includes(a));
    // If no valid selections remain, select all available
    if (filters.value.accountNames.length === 0 && newAvailableAccounts.length > 0) {
      filters.value.accountNames = [...newAvailableAccounts];
    }
  } else {
    // Show all accounts if all banks are selected
    const accounts = new Set<string>();
    allTransactions.value.forEach(t => accounts.add(t.account_name));
    const allAccounts = Array.from(accounts).sort();
    availableAccounts.value = allAccounts;
    
    // If account filter is empty or has invalid selections, select all
    const invalidAccounts = filters.value.accountNames.filter(a => !allAccounts.includes(a));
    if (invalidAccounts.length > 0 || filters.value.accountNames.length === 0) {
      filters.value.accountNames = [...allAccounts];
    }
  }
  
  applyClientFilters();
}

// Apply all filters
function applyFilters() {
  fetchTransactions();
  fetchAssetsHistory();
}

// Group transactions by month
function groupByMonth(transactions: Transaction[]): Map<string, Transaction[]> {
  const grouped = new Map<string, Transaction[]>();
  
  transactions.forEach(transaction => {
    const date = parseISO(transaction.date);
    const monthKey = format(startOfMonth(date), 'yyyy-MM');
    
    if (!grouped.has(monthKey)) {
      grouped.set(monthKey, []);
    }
    grouped.get(monthKey)!.push(transaction);
  });
  
  return grouped;
}

// Calculate monthly aggregates (exclude current/incomplete month)
function calculateMonthlyAggregates(transactions: Transaction[]) {
  const grouped = groupByMonth(transactions);
  const months = Array.from(grouped.keys()).sort().slice(0, -1);
  
  const data = months.map(month => {
    const monthTransactions = grouped.get(month)!;
    const income = monthTransactions
      .filter(t => t.amount > 0)
      .reduce((sum, t) => sum + t.amount, 0);
    const expenses = monthTransactions
      .filter(t => t.amount < 0)
      .reduce((sum, t) => sum + Math.abs(t.amount), 0);
    const balance = income - expenses;
    
    return {
      month,
      income,
      expenses: -expenses, // Keep as negative for chart
      balance,
    };
  });
  
  return data;
}

// Calculate cumulative balance (exclude current/incomplete month)
function calculateCumulative(transactions: Transaction[]) {
  const grouped = groupByMonth(transactions);
  const months = Array.from(grouped.keys()).sort().slice(0, -1);
  
  let cumulative = 0;
  const data = months.map(month => {
    const monthTransactions = grouped.get(month)!;
    const monthTotal = monthTransactions.reduce((sum, t) => sum + t.amount, 0);
    cumulative += monthTotal;
    
    return {
      month,
      cumulative,
    };
  });
  
  return data;
}

// Fetch assets history from API
async function fetchAssetsHistory() {
  try {
    const params: {
      start_date?: string;
      end_date?: string;
    } = {};
    
    if (filters.value.startDate) {
      params.start_date = filters.value.startDate;
    }
    if (filters.value.endDate) {
      params.end_date = filters.value.endDate;
    }
    
    const history = await api.assetsHistory.getAll(params);
    assetsHistory.value = history;
    console.log('Fetched assets history:', history.length, 'entries');
    updateAssetsHistoryChart();
  } catch (err) {
    console.error('Error fetching assets history:', err);
    // Show error in UI if it's a significant error
    if (err instanceof Error && !err.message.includes('404')) {
      error.value = `Failed to load assets history: ${err.message}`;
    }
  }
}

// Update assets history chart
function updateAssetsHistoryChart() {
  if (!assetsHistoryChartRef.value) return;
  
  // Handle empty data
  if (!assetsHistory.value || assetsHistory.value.length === 0) {
    console.log('No assets history data available');
    // Destroy existing chart if it exists
    if (assetsHistoryChart) {
      assetsHistoryChart.destroy();
      assetsHistoryChart = null;
    }
    return;
  }
  
  // Group assets by account_name (or bank_name + account_name for uniqueness)
  const assetMap = new Map<string, { date: number; amount: number }[]>();
  
  assetsHistory.value.forEach(asset => {
    // Create a unique key for each asset (bank + account)
    const assetKey = `${asset.bank_name} - ${asset.account_name}`;
    
    if (!assetMap.has(assetKey)) {
      assetMap.set(assetKey, []);
    }
    
    assetMap.get(assetKey)!.push({
      date: parseISO(asset.date).getTime(),
      amount: asset.amount,
    });
  });
  
  // Sort each asset's data by date
  assetMap.forEach((data) => {
    data.sort((a, b) => a.date - b.date);
  });
  
  // If no assets after grouping, don't create chart
  if (assetMap.size === 0) {
    if (assetsHistoryChart) {
      assetsHistoryChart.destroy();
      assetsHistoryChart = null;
    }
    return;
  }
  
  // Remove old double-click handler
  if (assetsHistoryChartRef.value && assetsHistoryDblClickHandler) {
    assetsHistoryChartRef.value.removeEventListener('dblclick', assetsHistoryDblClickHandler);
    assetsHistoryDblClickHandler = null;
  }

  // Destroy existing chart
  if (assetsHistoryChart) {
    assetsHistoryChart.destroy();
  }
  
  // Generate colors for each asset
  const colors = [
    'rgba(75, 192, 192, 1)',
    'rgba(255, 99, 132, 1)',
    'rgba(54, 162, 235, 1)',
    'rgba(255, 206, 86, 1)',
    'rgba(153, 102, 255, 1)',
    'rgba(255, 159, 64, 1)',
    'rgba(199, 199, 199, 1)',
    'rgba(83, 102, 255, 1)',
    'rgba(255, 99, 255, 1)',
    'rgba(99, 255, 132, 1)',
  ];
  
  // Create datasets for each asset
  const datasets = Array.from(assetMap.entries()).map(([assetKey, data], index) => {
    const colorIndex = index % colors.length;
    return {
      label: assetKey,
      data: data.map(d => ({ x: d.date, y: d.amount })),
      borderColor: colors[colorIndex],
      backgroundColor: colors[colorIndex].replace('1)', '0.2)'),
      tension: 0.1,
      fill: false,
      borderWidth: 1,
    };
  });
  
  // Calculate sum of all assets by date
  const sumByDate = new Map<number, number>();
  assetsHistory.value.forEach(asset => {
    const dateTime = parseISO(asset.date).getTime();
    const currentSum = sumByDate.get(dateTime) || 0;
    sumByDate.set(dateTime, currentSum + asset.amount);
  });
  
  // Convert to sorted array
  const sumData = Array.from(sumByDate.entries())
    .map(([date, amount]) => ({ x: date, y: amount }))
    .sort((a, b) => a.x - b.x);
  
  // Add sum dataset as the first dataset (so it appears on top)
  datasets.unshift({
    label: 'Total Assets',
    data: sumData,
    borderColor: 'rgba(0, 100, 0, 1)', // Dark green
    backgroundColor: 'rgba(0, 100, 0, 0.1)',
    tension: 0.1,
    fill: false,
    borderWidth: 3, // Thicker line
    pointRadius: 4, // Show dots on the line
    pointBackgroundColor: 'rgba(0, 100, 0, 1)', // Dark green dots
    pointBorderColor: 'rgba(0, 100, 0, 1)',
  });
  
  // Create new chart
  assetsHistoryChart = new Chart(assetsHistoryChartRef.value, {
    type: 'line',
    data: {
      datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        x: {
          type: 'linear',
          position: 'bottom',
          title: {
            display: true,
            text: 'Date',
          },
          ticks: {
            callback: function(value) {
              return format(new Date(value as number), 'yyyy-MM-dd');
            },
          },
        },
        y: {
          title: {
            display: true,
            text: 'Amount',
          },
          grid: {
            color: function(context) {
              if (context.tick.value === 0) {
                return 'rgba(0, 0, 0, 0.5)';
              }
              return 'rgba(0, 0, 0, 0.1)';
            },
          },
        },
      },
      plugins: {
        legend: {
          display: true,
        },
        tooltip: {
          callbacks: {
            label: (context) => {
              const raw = context.raw as { x?: number; y?: number };
              if (!raw || raw.x === undefined || raw.y === undefined) {
                return [];
              }
              const date = format(new Date(raw.x), 'yyyy-MM-dd');
              const amount = raw.y.toFixed(2);
              return [`Date: ${date}`, `Amount: ${amount}`];
            },
          },
        },
        zoom: {
          zoom: {
            wheel: {
              enabled: true,
            },
            pinch: {
              enabled: true,
            },
            mode: 'xy',
            drag: {
              enabled: true,
              modifierKey: undefined,
            },
          },
          pan: {
            enabled: true,
            mode: 'xy',
            modifierKey: 'shift',
          },
          limits: {
            x: { min: 'original', max: 'original' },
            y: { min: 'original', max: 'original' },
          },
        },
      },
      onHover: (event, activeElements) => {
        const canvas = event.native?.target as HTMLCanvasElement;
        if (canvas) {
          canvas.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
        }
      },
    },
  });

  // Add double-click handler to reset zoom
  if (assetsHistoryChartRef.value) {
    assetsHistoryDblClickHandler = () => {
      if (assetsHistoryChart) {
        assetsHistoryChart.resetZoom();
      }
    };
    assetsHistoryChartRef.value.addEventListener('dblclick', assetsHistoryDblClickHandler);
  }
}

// Update all charts
function updateCharts() {
  nextTick(() => {
    updateAssetsHistoryChart();
    updateScatterChart();
    updateMonthlyChart();
    updateCumulativeChart();
  });
}

// Update scatterplot chart
function updateScatterChart() {
  if (!scatterChartRef.value) return;
  
  const transactions = filteredTransactions.value;
  
  // Prepare data (include date, description for tooltip)
  const incomeData = transactions
    .filter(t => t.amount > 0)
    .map(t => ({
      x: parseISO(t.date).getTime(),
      y: t.amount,
      dateLabel: format(parseISO(t.date), 'yyyy-MM-dd'),
      description: t.description ?? '-',
    }));
  
  const expenseData = transactions
    .filter(t => t.amount < 0)
    .map(t => ({
      x: parseISO(t.date).getTime(),
      y: t.amount,
      dateLabel: format(parseISO(t.date), 'yyyy-MM-dd'),
      description: t.description ?? '-',
    }));
  
  // Remove old double-click handler
  if (scatterChartRef.value && scatterDblClickHandler) {
    scatterChartRef.value.removeEventListener('dblclick', scatterDblClickHandler);
    scatterDblClickHandler = null;
  }

  // Destroy existing chart
  if (scatterChart) {
    scatterChart.destroy();
  }
  
  // Create new chart
  scatterChart = new Chart(scatterChartRef.value, {
    type: 'scatter',
    data: {
      datasets: [
        {
          label: 'Income',
          data: incomeData,
          backgroundColor: 'rgba(75, 192, 192, 0.6)',
          borderColor: 'rgba(75, 192, 192, 1)',
          pointRadius: 4,
        },
        {
          label: 'Expenses',
          data: expenseData,
          backgroundColor: 'rgba(255, 99, 132, 0.6)',
          borderColor: 'rgba(255, 99, 132, 1)',
          pointRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        x: {
          type: 'linear',
          position: 'bottom',
          title: {
            display: true,
            text: 'Date',
          },
          ticks: {
            callback: function(value) {
              return format(new Date(value as number), 'yyyy-MM-dd');
            },
          },
        },
        y: {
          title: {
            display: true,
            text: 'Amount',
          },
          grid: {
            color: function(context) {
              if (context.tick.value === 0) {
                return 'rgba(0, 0, 0, 0.5)';
              }
              return 'rgba(0, 0, 0, 0.1)';
            },
          },
        },
      },
      plugins: {
        legend: {
          display: true,
        },
        tooltip: {
          callbacks: {
            label: (context) => {
              const raw = context.raw as { dateLabel?: string; description?: string };
              if (!raw || context.parsed.x === null || context.parsed.y === null) {
                return [];
              }
              const date = raw.dateLabel ?? format(new Date(context.parsed.x), 'yyyy-MM-dd');
              const amount = context.parsed.y.toFixed(2);
              const desc = raw.description ?? '-';
              return [`Date: ${date}`, `Amount: ${amount}`, `Description: ${desc}`];
            },
          },
        },
        zoom: {
          zoom: {
            wheel: {
              enabled: true,
            },
            pinch: {
              enabled: true,
            },
            mode: 'xy',
            drag: {
              enabled: true,
              modifierKey: undefined,
            },
          },
          pan: {
            enabled: true,
            mode: 'xy',
            modifierKey: 'shift',
          },
          limits: {
            x: { min: 'original', max: 'original' },
            y: { min: 'original', max: 'original' },
          },
        },
      },
      onHover: (event, activeElements) => {
        const canvas = event.native?.target as HTMLCanvasElement;
        if (canvas) {
          canvas.style.cursor = activeElements.length > 0 ? 'pointer' : 'default';
        }
      },
    },
  });

  // Add double-click handler to reset zoom
  if (scatterChartRef.value) {
    scatterDblClickHandler = () => {
      if (scatterChart) {
        scatterChart.resetZoom();
      }
    };
    scatterChartRef.value.addEventListener('dblclick', scatterDblClickHandler);
  }
}

// Update monthly chart
function updateMonthlyChart() {
  if (!monthlyChartRef.value) return;
  
  const aggregates = calculateMonthlyAggregates(filteredTransactions.value);
  
  // Remove old double-click handler
  if (monthlyChartRef.value && monthlyDblClickHandler) {
    monthlyChartRef.value.removeEventListener('dblclick', monthlyDblClickHandler);
    monthlyDblClickHandler = null;
  }

  // Destroy existing chart
  if (monthlyChart) {
    monthlyChart.destroy();
  }
  
  // Create new chart
  monthlyChart = new Chart(monthlyChartRef.value, {
    type: 'line',
    data: {
      labels: aggregates.map(a => a.month),
      datasets: [
        {
          label: 'Income',
          data: aggregates.map(a => a.income),
          borderColor: 'rgba(75, 192, 192, 1)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          tension: 0.1,
        },
        {
          label: 'Expenses',
          data: aggregates.map(a => a.expenses),
          borderColor: 'rgba(255, 99, 132, 1)',
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          tension: 0.1,
        },
        {
          label: 'Balance',
          data: aggregates.map(a => a.balance),
          borderColor: 'rgba(54, 162, 235, 1)',
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          tension: 0.1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        y: {
          title: {
            display: true,
            text: 'Amount',
          },
          grid: {
            color: (context: { tick: { value: number } }) => {
              if (context.tick.value === 0) {
                return 'rgba(0, 0, 0, 0.5)';
              }
              return 'rgba(0, 0, 0, 0.1)';
            },
          },
        },
      },
      plugins: {
        legend: {
          display: true,
        },
        zoom: {
          zoom: {
            wheel: {
              enabled: true,
            },
            pinch: {
              enabled: true,
            },
            mode: 'xy',
            drag: {
              enabled: true,
              modifierKey: undefined,
            },
          },
          pan: {
            enabled: true,
            mode: 'xy',
            modifierKey: 'shift',
          },
          limits: {
            x: { min: 'original', max: 'original' },
            y: { min: 'original', max: 'original' },
          },
        },
      },
    },
  });

  // Add double-click handler to reset zoom
  if (monthlyChartRef.value) {
    monthlyDblClickHandler = () => {
      if (monthlyChart) {
        monthlyChart.resetZoom();
      }
    };
    monthlyChartRef.value.addEventListener('dblclick', monthlyDblClickHandler);
  }
}

// Update cumulative chart
function updateCumulativeChart() {
  if (!cumulativeChartRef.value) return;
  
  const cumulative = calculateCumulative(filteredTransactions.value);
  
  // Remove old double-click handler
  if (cumulativeChartRef.value && cumulativeDblClickHandler) {
    cumulativeChartRef.value.removeEventListener('dblclick', cumulativeDblClickHandler);
    cumulativeDblClickHandler = null;
  }

  // Destroy existing chart
  if (cumulativeChart) {
    cumulativeChart.destroy();
  }
  
  // Create new chart
  cumulativeChart = new Chart(cumulativeChartRef.value, {
    type: 'line',
    data: {
      labels: cumulative.map(c => c.month),
      datasets: [
        {
          label: 'Cumulative Balance',
          data: cumulative.map(c => c.cumulative),
          borderColor: 'rgba(153, 102, 255, 1)',
          backgroundColor: 'rgba(153, 102, 255, 0.2)',
          tension: 0.1,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        y: {
          title: {
            display: true,
            text: 'Cumulative Balance',
          },
        },
      },
      plugins: {
        legend: {
          display: true,
        },
        zoom: {
          zoom: {
            wheel: {
              enabled: true,
            },
            pinch: {
              enabled: true,
            },
            mode: 'xy',
            drag: {
              enabled: true,
              modifierKey: undefined,
            },
          },
          pan: {
            enabled: true,
            mode: 'xy',
            modifierKey: 'shift',
          },
          limits: {
            x: { min: 'original', max: 'original' },
            y: { min: 'original', max: 'original' },
          },
        },
      },
    },
  });

  // Add double-click handler to reset zoom
  if (cumulativeChartRef.value) {
    cumulativeDblClickHandler = () => {
      if (cumulativeChart) {
        cumulativeChart.resetZoom();
      }
    };
    cumulativeChartRef.value.addEventListener('dblclick', cumulativeDblClickHandler);
  }
}

// Cleanup charts on unmount
function cleanupCharts() {
  // Remove double-click handlers
  if (assetsHistoryChartRef.value && assetsHistoryDblClickHandler) {
    assetsHistoryChartRef.value.removeEventListener('dblclick', assetsHistoryDblClickHandler);
    assetsHistoryDblClickHandler = null;
  }
  if (scatterChartRef.value && scatterDblClickHandler) {
    scatterChartRef.value.removeEventListener('dblclick', scatterDblClickHandler);
    scatterDblClickHandler = null;
  }
  if (monthlyChartRef.value && monthlyDblClickHandler) {
    monthlyChartRef.value.removeEventListener('dblclick', monthlyDblClickHandler);
    monthlyDblClickHandler = null;
  }
  if (cumulativeChartRef.value && cumulativeDblClickHandler) {
    cumulativeChartRef.value.removeEventListener('dblclick', cumulativeDblClickHandler);
    cumulativeDblClickHandler = null;
  }

  // Destroy charts
  if (assetsHistoryChart) {
    assetsHistoryChart.destroy();
    assetsHistoryChart = null;
  }
  if (scatterChart) {
    scatterChart.destroy();
    scatterChart = null;
  }
  if (monthlyChart) {
    monthlyChart.destroy();
    monthlyChart = null;
  }
  if (cumulativeChart) {
    cumulativeChart.destroy();
    cumulativeChart = null;
  }
}

// Initialize on mount
onMounted(() => {
  fetchTransactions();
  fetchAssetsHistory();
});

// Cleanup on unmount
onUnmounted(() => {
  cleanupCharts();
});
</script>

<style scoped>
.dashboard {
  padding: 20px 100px;
}

h2 {
  margin-top: 0;
  margin-bottom: 20px;
}

h3 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 1.2em;
}

.filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 30px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.filter-group label {
  font-weight: 500;
  font-size: 0.9em;
  color: #333;
}

.filter-group input[type="checkbox"] {
  margin-right: 5px;
}

.filter-group input[type="date"],
.filter-group input[type="number"],
.filter-group select {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9em;
}

.filter-group select[multiple] {
  min-height: 80px;
  max-height: 120px;
  overflow-y: auto;
}

.filter-group :deep(.v-select) {
  min-height: 80px;
}

.filter-group :deep(.v-select .vs__dropdown-toggle) {
  min-height: 80px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9em;
}

.filter-group :deep(.v-select.vs--open .vs__dropdown-toggle),
.filter-group :deep(.v-select .vs__dropdown-toggle:focus-within) {
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
  outline: none;
}

.multiselect-info {
  font-size: 0.8em;
  color: #666;
  margin-top: 4px;
}

.filter-group input[type="date"]:focus,
.filter-group input[type="number"]:focus,
.filter-group select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.loading,
.error {
  padding: 20px;
  text-align: center;
  margin-bottom: 20px;
  border-radius: 4px;
}

.loading {
  background-color: #e7f3ff;
  color: #0066cc;
}

.error {
  background-color: #ffe7e7;
  color: #cc0000;
}

.charts {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.chart-container {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  min-height: 400px;
}

.chart-container canvas {
  max-height: 400px;
}

@media (max-width: 768px) {
  .filters {
    grid-template-columns: 1fr;
  }
  
  .chart-container {
    min-height: 300px;
  }
  
  .chart-container canvas {
    max-height: 300px;
  }
}
</style>