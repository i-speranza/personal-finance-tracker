<template>
  <div class="inv-dashboard">
    <h2>Investments — Dashboard</h2>
    <p class="intro muted">
      Snapshot uses <strong>active</strong> assets only.<br>
      IRR uses buy/sell cash flows in portfolio currency (fees included);<br>
      <code>plus_minus</code> is not used for IRR. (TBC after first sell.)<br>
      <strong>Bonds</strong> use stored nominal ÷ 100 for shares and euro amounts (Italian listing convention), matching
      <router-link to="/investments/data">Data</router-link>.
    </p>

    <div v-if="loading" class="loading">Loading dashboard…</div>
    <p v-else-if="loadError" class="error">{{ loadError }}</p>

    <template v-else>
      <p v-if="dashboard?.empty_detail" class="empty-banner">
        {{ emptyMessage(dashboard.empty_detail) }}
        <router-link to="/investments/upload">Upload</router-link>
        valuations or add trades in
        <router-link to="/investments/data">Data</router-link>.
      </p>

      <template v-if="dashboard?.as_of_date">
        <section class="summary-row">
          <div class="summary-card">
            <span class="label">Last observation date</span>
            <span class="value">{{ dashboard.as_of_date }}</span>
          </div>
          <div class="summary-card">
            <span class="label">Portfolio IRR (annualized)</span>
            <span class="value">{{ formatIrr(dashboard.portfolio_irr) }}</span>
          </div>
        </section>

        <section class="panel">
          <h3>Total controvalore by bank (broker)</h3>
          <p class="muted small">As of {{ dashboard.as_of_date }}; after-tax uses each asset’s <code>tax_rate</code> on unrealized gains only.</p>
          <table class="data-table compact">
            <thead>
              <tr>
                <th>Bank / Broker</th>
                <th class="num">Total controvalore</th>
                <th class="num">After tax</th>
                <th class="num">% after tax</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="b in dashboard.totals_by_broker" :key="b.broker">
                <td>{{ b.broker }}</td>
                <td class="num">{{ fmtMoney(b.total_controvalore, dashboard.currency) }}</td>
                <td class="num">{{ fmtMoney(b.total_controvalore_after_tax, dashboard.currency) }}</td>
                <td class="num">{{ fmtBrokerAfterTaxShare(b.total_controvalore_after_tax) }}</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section class="panel wide-panel">
          <h3>Positions (as of {{ dashboard.as_of_date }})</h3>
          <div class="scroll-x force-wide">
            <table class="data-table positions-table wide-positions-table">
              <thead>
                <tr>
                  <th scope="col" class="sortable" @click="togglePositionSort('asset_id')">
                    asset_id<span class="sort-ind" aria-hidden="true">{{ positionSortIndicator('asset_id') }}</span>
                  </th>
                  <th scope="col" class="sortable" @click="togglePositionSort('asset_name')">
                    asset_name<span class="sort-ind" aria-hidden="true">{{ positionSortIndicator('asset_name') }}</span>
                  </th>
                  <th scope="col" class="sortable" @click="togglePositionSort('broker')">
                    Bank<span class="sort-ind" aria-hidden="true">{{ positionSortIndicator('broker') }}</span>
                  </th>
                  <th scope="col" class="num sortable" @click="togglePositionSort('shares')">
                    Shares<span class="sort-ind" aria-hidden="true">{{ positionSortIndicator('shares') }}</span>
                  </th>
                  <th scope="col" class="num sortable" @click="togglePositionSort('total_valore_with_fees')">
                    Total valore<br>(incl. fees)<span class="sort-ind" aria-hidden="true">{{
                      positionSortIndicator('total_valore_with_fees')
                    }}</span>
                  </th>
                  <th scope="col" class="num sortable" @click="togglePositionSort('total_valore_no_fees')">
                    Total valore<br>(excl. fees)<span class="sort-ind" aria-hidden="true">{{
                      positionSortIndicator('total_valore_no_fees')
                    }}</span>
                  </th>
                  <th scope="col" class="num sortable" @click="togglePositionSort('total_controvalore')">
                    Total controvalore<span class="sort-ind" aria-hidden="true">{{
                      positionSortIndicator('total_controvalore')
                    }}</span>
                  </th>
                  <th scope="col" class="num sortable" @click="togglePositionSort('total_controvalore_after_tax')">
                    Controvalore after tax<span class="sort-ind" aria-hidden="true">{{
                      positionSortIndicator('total_controvalore_after_tax')
                    }}</span>
                  </th>
                  <th scope="col" class="num sortable" @click="togglePositionSort('pct_gain_loss_real')">
                    % gain/loss<br>(real)<span class="sort-ind" aria-hidden="true">{{
                      positionSortIndicator('pct_gain_loss_real')
                    }}</span>
                  </th>
                  <th scope="col" class="num sortable" @click="togglePositionSort('pct_gain_loss_no_fees')">
                    % gain/loss<br>(no fees)<span class="sort-ind" aria-hidden="true">{{
                      positionSortIndicator('pct_gain_loss_no_fees')
                    }}</span>
                  </th>
                  <th scope="col" class="num sortable" @click="togglePositionSort('irr')">
                    IRR<span class="sort-ind" aria-hidden="true">{{ positionSortIndicator('irr') }}</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="p in sortedPositions"
                  :key="p.asset_pk"
                  :class="{
                    'position-row-loss': isNegativeRealPct(p.pct_gain_loss_real),
                    'position-row-gain': isNonNegativeRealPct(p.pct_gain_loss_real),
                  }"
                >
                  <td>{{ p.asset_id }}</td>
                  <td>{{ p.asset_name }}</td>
                  <td>{{ p.broker ?? '—' }}</td>
                  <td class="num">{{ fmtShares(p.shares) }}</td>
                  <td class="num">{{ p.total_valore_with_fees != null ? fmtMoney(p.total_valore_with_fees, dashboard.currency) : '—' }}</td>
                  <td class="num">{{ p.total_valore_no_fees != null ? fmtMoney(p.total_valore_no_fees, dashboard.currency) : '—' }}</td>
                  <td class="num">{{ p.total_controvalore != null ? fmtMoney(p.total_controvalore, dashboard.currency) : '—' }}</td>
                  <td class="num">{{ p.total_controvalore_after_tax != null ? fmtMoney(p.total_controvalore_after_tax, dashboard.currency) : '—' }}</td>
                  <td class="num">{{ formatPctCol(p.pct_gain_loss_real) }}</td>
                  <td class="num">{{ formatPctCol(p.pct_gain_loss_no_fees) }}</td>
                  <td class="num">{{ formatIrr(p.irr) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="panel">
          <h3>Class mix (% of portfolio)</h3>
          <p class="muted small">
            Share of total valore (cost, fees incl.) and total controvalore in each asset class, as of {{ dashboard.as_of_date }}.
          </p>
          <div v-if="classMixColumns.length" class="scroll-x">
            <table class="data-table compact">
              <thead>
                <tr>
                  <th></th>
                  <th v-for="col in classMixColumns" :key="col.class" class="num">{{ classGeoTitle(col.class) }}</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <th scope="row">Valore</th>
                  <td v-for="col in classMixColumns" :key="'mix-v-' + col.class" class="num">
                    {{ fmtGeoMixPct(col.valore_pct) }}
                  </td>
                </tr>
                <tr>
                  <th scope="row">Controvalore</th>
                  <td v-for="col in classMixColumns" :key="'mix-c-' + col.class" class="num">
                    {{ fmtGeoMixPct(col.controvalore_pct) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="muted small">No class mix for this snapshot.</p>
        </section>

        <section class="panel">
          <h3>Geographic mix (% of portfolio)</h3>

          <template v-for="block in geoByClassRows" :key="block.class">
            <h4 class="geo-subhead">{{ classGeoTitle(block.class) }}</h4>
            <div class="scroll-x">
              <table class="data-table compact">
                <thead>
                  <tr>
                    <th></th>
                    <th v-for="gk in geoKeys" :key="gk" class="num">{{ geoLabels[gk] }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <th scope="row">Valore (cost, fees incl.)</th>
                    <td v-for="gk in geoKeys" :key="'v-' + block.class + '-' + gk" class="num">
                      {{ fmtGeoMixPct(geoMixPctByClass(block, gk, 'valore')) }}
                    </td>
                  </tr>
                  <tr>
                    <th scope="row">Controvalore</th>
                    <td v-for="gk in geoKeys" :key="'c-' + block.class + '-' + gk" class="num">
                      {{ fmtGeoMixPct(geoMixPctByClass(block, gk, 'controvalore')) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </section>

        <section class="panel chart-panel">
          <h3>Portfolio — total valore vs total controvalore</h3>
          <p class="muted small">Per observation date: sum over open positions (with a quote that day) of shares × average cost and × market unit price.</p>
          <div class="chart-wrap">
            <canvas ref="portfolioChartRef"></canvas>
          </div>
        </section>

        <section class="panel chart-panel">
          <h3>Per asset — unit valore vs unit controvalore</h3>
          <p class="muted small">
            All open positions with quotes: <strong>valore/unit</strong> (avg. cost, fees incl.) as a solid line;
            <strong>controvalore/unit</strong> as a dotted line. One color per asset.
          </p>
          <div class="chart-wrap chart-wrap--unit">
            <canvas ref="unitChartRef"></canvas>
          </div>
        </section>
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import { format, parseISO } from 'date-fns';
import { Chart, registerables } from 'chart.js';
import type {
  InvestmentDashboardResponse,
  InvestmentDashboardGeoByClassRow,
  InvestmentDashboardClassMixRow,
  InvestmentDashboardPositionRow,
  InvestmentDashboardUnitAssetSeries,
} from '@/types';
import { api } from '@/api/client';

Chart.register(...registerables);

const GEO_KEYS = ['usa', 'eu', 'other_developed', 'emerging', 'other'] as const;
const geoKeys = GEO_KEYS;
const geoLabels: Record<(typeof GEO_KEYS)[number], string> = {
  usa: 'USA',
  eu: 'EU',
  other_developed: 'Other developed',
  emerging: 'Emerging',
  other: 'Other',
};

const loading = ref(true);
const loadError = ref<string | null>(null);
const dashboard = ref<InvestmentDashboardResponse | null>(null);

const portfolioChartRef = ref<HTMLCanvasElement | null>(null);
const unitChartRef = ref<HTMLCanvasElement | null>(null);
let portfolioChart: Chart | null = null;
let unitChart: Chart | null = null;

const brokerAfterTaxSum = computed(() => {
  const rows = dashboard.value?.totals_by_broker ?? [];
  return rows.reduce((s, b) => s + b.total_controvalore_after_tax, 0);
});

type PositionSortKey = keyof Pick<
  InvestmentDashboardPositionRow,
  | 'asset_id'
  | 'asset_name'
  | 'broker'
  | 'shares'
  | 'total_valore_with_fees'
  | 'total_valore_no_fees'
  | 'total_controvalore'
  | 'total_controvalore_after_tax'
  | 'pct_gain_loss_real'
  | 'pct_gain_loss_no_fees'
  | 'irr'
>;

const positionSortKey = ref<PositionSortKey>('asset_name');
const positionSortDir = ref<'asc' | 'desc'>('asc');

function togglePositionSort(key: PositionSortKey) {
  if (positionSortKey.value === key) {
    positionSortDir.value = positionSortDir.value === 'asc' ? 'desc' : 'asc';
  } else {
    positionSortKey.value = key;
    positionSortDir.value = 'asc';
  }
}

function positionSortIndicator(key: PositionSortKey): string {
  if (positionSortKey.value !== key) return '';
  return positionSortDir.value === 'asc' ? ' \u25B2' : ' \u25BC';
}

function cmpNullableNum(
  a: number | null | undefined,
  b: number | null | undefined,
  asc: boolean,
): number {
  const na = a == null || Number.isNaN(a);
  const nb = b == null || Number.isNaN(b);
  if (na && nb) return 0;
  if (na) return 1;
  if (nb) return -1;
  const diff = a - b;
  return asc ? diff : -diff;
}

function cmpStr(a: string, b: string, asc: boolean): number {
  const diff = a.localeCompare(b, undefined, { sensitivity: 'base' });
  return asc ? diff : -diff;
}

const sortedPositions = computed(() => {
  const rows = dashboard.value?.positions ?? [];
  const key = positionSortKey.value;
  const asc = positionSortDir.value === 'asc';
  return [...rows].sort((a, b) => {
    switch (key) {
      case 'asset_id':
        return cmpStr(a.asset_id, b.asset_id, asc);
      case 'asset_name':
        return cmpStr(a.asset_name, b.asset_name, asc);
      case 'broker':
        return cmpStr(a.broker ?? '', b.broker ?? '', asc);
      case 'shares':
        return cmpNullableNum(a.shares, b.shares, asc);
      case 'total_valore_with_fees':
        return cmpNullableNum(a.total_valore_with_fees, b.total_valore_with_fees, asc);
      case 'total_valore_no_fees':
        return cmpNullableNum(a.total_valore_no_fees, b.total_valore_no_fees, asc);
      case 'total_controvalore':
        return cmpNullableNum(a.total_controvalore, b.total_controvalore, asc);
      case 'total_controvalore_after_tax':
        return cmpNullableNum(a.total_controvalore_after_tax, b.total_controvalore_after_tax, asc);
      case 'pct_gain_loss_real':
        return cmpNullableNum(a.pct_gain_loss_real, b.pct_gain_loss_real, asc);
      case 'pct_gain_loss_no_fees':
        return cmpNullableNum(a.pct_gain_loss_no_fees, b.pct_gain_loss_no_fees, asc);
      case 'irr':
        return cmpNullableNum(a.irr, b.irr, asc);
      default:
        return 0;
    }
  });
});

const geoByClassRows = computed(() => dashboard.value?.geo_allocation_by_class ?? []);

const classMixColumns = computed((): InvestmentDashboardClassMixRow[] => dashboard.value?.class_mix ?? []);

const CLASS_GEO_LABELS: Record<string, string> = {
  share: 'Shares',
  bond: 'Bonds',
  commodity: 'Commodities',
};

/** Distinct colors per asset (valore + controvalore share the same hue). */
const UNIT_PER_ASSET_COLORS = [
  '#7c3aed',
  '#ea580c',
  '#2563eb',
  '#059669',
  '#dc2626',
  '#ca8a04',
  '#db2777',
  '#0891b2',
  '#4f46e5',
  '#65a30d',
  '#c026d3',
  '#0d9488',
];

function geoMixPctByClass(
  block: InvestmentDashboardGeoByClassRow,
  key: string,
  row: 'valore' | 'controvalore',
): number {
  const src = row === 'valore' ? block.valore_pct : block.controvalore_pct;
  return src[key] ?? 0;
}

function classGeoTitle(cls: string): string {
  return CLASS_GEO_LABELS[cls] ?? cls;
}

function emptyMessage(code: string): string {
  if (code === 'no_active_assets') return 'There are no active portfolio assets.';
  if (code === 'no_market_quotes_for_open_positions') return 'Open positions have no market quotes yet.';
  return 'Dashboard data is not available yet.';
}

function fmtMoney(n: number, currency: string): string {
  return new Intl.NumberFormat(undefined, { style: 'currency', currency, maximumFractionDigits: 2 }).format(n);
}

function fmtBrokerAfterTaxShare(amount: number): string {
  const total = brokerAfterTaxSum.value;
  if (total <= 0) return '—';
  return `${Math.round((amount / total) * 100)}%`;
}

function fmtShares(n: number): string {
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 4 }).format(n);
}

function fmtGeoMixPct(n: number): string {
  return `${Math.round(n)}%`;
}

function formatPctCol(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return '—';
  const sign = v > 0 ? '+' : '';
  return `${sign}${v.toFixed(2)}%`;
}

function isNegativeRealPct(v: number | null | undefined): boolean {
  return v != null && !Number.isNaN(v) && v < 0;
}

function isNonNegativeRealPct(v: number | null | undefined): boolean {
  return v != null && !Number.isNaN(v) && v >= 0;
}

function formatIrr(r: number | null | undefined): string {
  if (r == null || Number.isNaN(r)) return '—';
  return `${(r * 100).toFixed(2)}%`;
}

async function loadDashboard() {
  loading.value = true;
  loadError.value = null;
  try {
    const data = await api.investmentDashboard.get();
    dashboard.value = data;
  } catch (e: unknown) {
    loadError.value = e instanceof Error ? e.message : 'Failed to load dashboard';
    dashboard.value = null;
  } finally {
    loading.value = false;
  }
}

function destroyCharts() {
  portfolioChart?.destroy();
  portfolioChart = null;
  unitChart?.destroy();
  unitChart = null;
}

function formatChartDate(iso: string): string {
  try {
    return format(parseISO(iso), 'MMM d, yyyy');
  } catch {
    return iso;
  }
}

function updatePortfolioChart() {
  const d = dashboard.value;
  if (!d?.timeseries?.length || !portfolioChartRef.value) {
    portfolioChart?.destroy();
    portfolioChart = null;
    return;
  }
  const labels = d.timeseries.map((p) => formatChartDate(p.date));
  const cur = d.currency;
  portfolioChart?.destroy();
  portfolioChart = new Chart(portfolioChartRef.value, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Total valore (fees incl.)',
          data: d.timeseries.map((p) => p.total_valore_with_fees),
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.1)',
          tension: 0.15,
          fill: false,
        },
        {
          label: 'Total controvalore',
          data: d.timeseries.map((p) => p.total_controvalore),
          borderColor: '#059669',
          backgroundColor: 'rgba(5, 150, 105, 0.1)',
          tension: 0.15,
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { position: 'bottom' },
        tooltip: {
          callbacks: {
            label(ctx) {
              const v = ctx.parsed.y;
              if (v == null) return `${ctx.dataset.label}: —`;
              return `${ctx.dataset.label}: ${fmtMoney(v, cur)}`;
            },
          },
        },
      },
      scales: {
        x: { ticks: { maxRotation: 45, minRotation: 0 } },
        y: {
          ticks: {
            callback(v) {
              return typeof v === 'number' ? v.toLocaleString() : String(v);
            },
          },
        },
      },
    },
  });
}

function updateUnitChart() {
  const d = dashboard.value;
  const byAsset = d?.unit_timeseries_by_asset;
  if (!byAsset?.length || !unitChartRef.value) {
    unitChart?.destroy();
    unitChart = null;
    return;
  }
  const dateSet = new Set<string>();
  for (const s of byAsset) {
    for (const p of s.points) dateSet.add(p.date);
  }
  const sortedIsoDates = [...dateSet].sort((a, b) => a.localeCompare(b));
  const labels = sortedIsoDates.map((iso) => formatChartDate(iso));
  const cur = d?.currency ?? 'EUR';

  const datasets = byAsset.flatMap((s: InvestmentDashboardUnitAssetSeries, i: number) => {
    const col = UNIT_PER_ASSET_COLORS[i % UNIT_PER_ASSET_COLORS.length];
    const byDate = new Map(s.points.map((p) => [p.date, p]));
    const vData = sortedIsoDates.map((dt) => byDate.get(dt)?.unit_valore_with_fees ?? null);
    const cData = sortedIsoDates.map((dt) => {
      const pt = byDate.get(dt);
      return pt != null ? pt.unit_controvalore : null;
    });
    return [
      {
        label: `${s.asset_id} — valore/unit`,
        data: vData,
        borderColor: col,
        backgroundColor: `${col}14`,
        tension: 0.15,
        spanGaps: true,
        fill: false,
      },
      {
        label: `${s.asset_id} — controvalore/unit`,
        data: cData,
        borderColor: col,
        backgroundColor: 'transparent',
        borderDash: [6, 4],
        tension: 0.15,
        spanGaps: true,
        fill: false,
      },
    ];
  });

  unitChart?.destroy();
  unitChart = new Chart(unitChartRef.value, {
    type: 'line',
    data: {
      labels,
      datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { position: 'bottom' },
        tooltip: {
          callbacks: {
            label(ctx) {
              const v = ctx.parsed.y;
              if (v == null) return `${ctx.dataset.label}: —`;
              return `${ctx.dataset.label}: ${fmtMoney(v, cur)}`;
            },
          },
        },
      },
      scales: {
        x: { ticks: { maxRotation: 45, minRotation: 0 } },
        y: {
          ticks: {
            callback(v) {
              return typeof v === 'number' ? v.toLocaleString(undefined, { maximumFractionDigits: 4 }) : String(v);
            },
          },
        },
      },
    },
  });
}

watch(
  () => dashboard.value?.timeseries,
  async () => {
    await nextTick();
    updatePortfolioChart();
  },
  { deep: true },
);

watch(
  () => dashboard.value?.unit_timeseries_by_asset,
  async () => {
    await nextTick();
    updateUnitChart();
  },
  { deep: true },
);

onMounted(async () => {
  await loadDashboard();
  await nextTick();
  updatePortfolioChart();
  updateUnitChart();
});

onUnmounted(() => {
  destroyCharts();
});
</script>

<style scoped>
.inv-dashboard {
  max-width: min(100vw - 2rem, 1920px);
}
.intro {
  line-height: 1.5;
  margin-bottom: 1rem;
}
.muted {
  color: #555;
}
.small {
  font-size: 0.85rem;
  margin: 0 0 8px;
}
.error {
  color: #c00;
}
.loading {
  padding: 12px;
}
.empty-banner {
  background: #fff8e6;
  border: 1px solid #f0d78c;
  padding: 12px 14px;
  border-radius: 6px;
  margin-bottom: 16px;
}
.summary-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
}
.summary-card {
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 12px 16px;
  min-width: 180px;
  background: #fafafa;
}
.summary-card .label {
  display: block;
  font-size: 0.8rem;
  color: #666;
  margin-bottom: 4px;
}
.summary-card .value {
  font-size: 1.15rem;
  font-weight: 600;
}
.panel {
  margin-bottom: 24px;
}
.panel h3 {
  margin: 0 0 8px;
  font-size: 1.05rem;
}
.geo-subhead {
  margin: 16px 0 6px;
  font-size: 0.95rem;
  font-weight: 600;
  color: #333;
}
.geo-subhead:first-of-type {
  margin-top: 4px;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}
.data-table th,
.data-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}
.data-table th {
  background: #f0f0f0;
}
.data-table th.sortable {
  cursor: pointer;
  user-select: none;
}
.data-table th.sortable:hover {
  background: #e4e4e4;
}
.data-table th.sortable .sort-ind {
  font-size: 0.7em;
  opacity: 0.75;
  white-space: nowrap;
}
.data-table.compact {
  width: max-content;
  max-width: 100%;
}
.data-table.compact th,
.data-table.compact td {
  padding: 6px 8px;
}
.data-table .num {
  text-align: right;
  white-space: nowrap;
}
.scroll-x {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
.positions-table {
  width: max-content;
  min-width: 1680px;
}
.positions-table tbody tr.position-row-loss td {
  color: #b91c1c;
}
.positions-table tbody tr.position-row-gain td {
  color: #14532d;
}
.chart-panel .chart-wrap {
  height: 320px;
  position: relative;
}
.chart-toolbar {
  margin-bottom: 10px;
}
.chart-toolbar label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.85rem;
  max-width: 420px;
}
.chart-toolbar select {
  padding: 6px 8px;
}
</style>
