<template>
  <div class="investments">
    <h2>Investments — Data</h2>
    <p class="intro">
      Portfolio assets and trades. For <strong>sells</strong>, enter <code>plus_minus</code> yourself: it is the
      taxable margin (loss or gain) used for tax logic. A suggested value (sell proceeds minus weighted-average buy
      cost) is available in the form only; only the number you save is stored. CSV import is on
      <router-link to="/investments/upload">Upload</router-link>.
      For <strong>bonds</strong>, cash flows and margin suggestions use <strong>quantity ÷ 100</strong> (Italian nominal
      convention); the grid still shows the stored quantity.
    </p>

    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        :class="['tab-btn', { active: activeTab === tab.id }]"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <div v-if="activeTab === 'assets'" class="tab-panel">
      <div class="panel-header">
        <h3>Assets</h3>
        <button type="button" class="btn btn-primary" @click="toggleAssetForm">
          {{ showAssetForm ? 'Cancel' : 'Add asset' }}
        </button>
      </div>

      <div v-if="showAssetForm" class="card form-card">
        <h4>{{ editingAssetId == null ? 'New asset' : 'Edit asset' }}</h4>
        <div class="form-grid">
          <label>asset_id <input v-model="assetForm.asset_id" type="text" placeholder="e.g. sp500" /></label>
          <label>asset_name <input v-model="assetForm.asset_name" type="text" /></label>
          <label>isin <input v-model="assetForm.isin" type="text" /></label>
          <label>ticker <input v-model="assetForm.ticker" type="text" /></label>
          <label>issuer <input v-model="assetForm.issuer" type="text" /></label>
          <label>broker <input v-model="assetForm.broker" type="text" /></label>
          <label>
            type
            <select v-model="assetForm.type" @change="onAssetTypeChange">
              <option value="fund">fund</option>
              <option value="bond">bond</option>
              <option value="share">share</option>
            </select>
          </label>
          <label>
            class
            <select v-model="assetForm.class">
              <option value="share">share</option>
              <option value="bond">bond</option>
              <option value="commodity">commodity</option>
            </select>
          </label>
          <label>market <input v-model="assetForm.market" type="text" /></label>
          <label>
            status
            <select v-model="assetForm.status">
              <option value="active">active</option>
              <option value="sold">sold</option>
              <option value="special">special</option>
            </select>
          </label>
          <label>currency <input v-model="assetForm.currency" type="text" /></label>
          <label>tax_rate <input v-model.number="assetForm.tax_rate" type="number" step="0.01" min="0" max="1" /></label>
          <label>
            default_exchange_rate
            <input v-model.number="assetForm.default_exchange_rate" type="number" step="0.0001" min="0" />
          </label>
          <label v-if="assetForm.type === 'bond'">
            expiration_date (required for bonds)
            <input v-model="assetForm.expiration_date" type="date" />
          </label>
          <label v-else>
            expiration_date (optional)
            <input v-model="assetForm.expiration_date" type="date" />
          </label>
        </div>
        <div class="geo-block">
          <span class="geo-title">Geographic % (must sum to 100)</span>
          <div class="form-grid geo-grid">
            <label>USA <input v-model.number="assetForm.perc_usa" type="number" step="0.1" min="0" max="100" /></label>
            <label>EU <input v-model.number="assetForm.perc_eu" type="number" step="0.1" min="0" max="100" /></label>
            <label>Other developed <input v-model.number="assetForm.perc_other_developed" type="number" step="0.1" min="0" max="100" /></label>
            <label>Emerging <input v-model.number="assetForm.perc_emerging" type="number" step="0.1" min="0" max="100" /></label>
            <label>Other <input v-model.number="assetForm.perc_other" type="number" step="0.1" min="0" max="100" /></label>
          </div>
          <p :class="['geo-sum', geoSumOk ? 'ok' : 'bad']">Sum: {{ geoSum.toFixed(2) }}%</p>
        </div>
        <p v-if="assetError" class="error">{{ assetError }}</p>
        <div class="actions">
          <button type="button" class="btn btn-success" :disabled="!canSaveAsset" @click="saveAsset">
            {{ editingAssetId == null ? 'Create' : 'Save' }}
          </button>
        </div>
      </div>

      <div v-if="assetsLoading" class="loading">Loading…</div>
      <p v-else-if="assetsLoadError" class="error">{{ assetsLoadError }}</p>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>asset_id</th>
            <th>name</th>
            <th>broker</th>
            <th>isin</th>
            <th>status</th>
            <th>expiry</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in assets" :key="a.id">
            <td>{{ a.asset_id }}</td>
            <td>{{ a.asset_name }}</td>
            <td>{{ a.broker ?? '—' }}</td>
            <td>{{ a.isin ?? '—' }}</td>
            <td>{{ a.status }}</td>
            <td>{{ a.expiration_date ?? '—' }}</td>
            <td class="row-actions">
              <button type="button" class="btn-link" @click="startEditAsset(a)">Edit</button>
              <button type="button" class="btn-link danger" @click="removeAsset(a)">Delete</button>
            </td>
          </tr>
          <tr v-if="assets.length === 0">
            <td colspan="7" class="muted">No assets yet</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="tab-panel">
      <div class="panel-header">
        <h3>Transactions</h3>
        <button type="button" class="btn btn-primary" @click="toggleTxForm">
          {{ showTxForm ? 'Cancel' : 'Add transaction' }}
        </button>
      </div>

      <div class="filter-row">
        <label>
          Filter by asset
          <select v-model.number="txFilterAssetPk">
            <option :value="0">All</option>
            <option v-for="a in assets" :key="a.id" :value="a.id">{{ a.asset_id }} — {{ a.asset_name }}</option>
          </select>
        </label>
        <button type="button" class="btn btn-secondary" @click="loadTransactions">Refresh</button>
      </div>

      <div v-if="showTxForm" class="card form-card">
        <h4>New transaction</h4>
        <p v-if="selectedTxAssetIsBond" class="muted bond-hint">
          Bond: euro amounts use quantity ÷ 100 (nominal units in the field below).
        </p>
        <div class="form-grid">
          <label>
            Asset
            <select v-model.number="txForm.asset_pk">
              <option v-for="a in assets" :key="a.id" :value="a.id">{{ a.asset_id }}</option>
            </select>
          </label>
          <label>date <input v-model="txForm.trade_date" type="date" /></label>
          <label>
            type
            <select v-model="txForm.transaction_type">
              <option value="purchase">purchase</option>
              <option value="sell">sell</option>
            </select>
          </label>
          <label>quantity <input v-model.number="txForm.quantity" type="number" step="0.0001" min="0" /></label>
          <label>unit_price <input v-model.number="txForm.unit_price" type="number" step="0.0001" /></label>
          <label>exchange_rate <input v-model.number="txForm.exchange_rate" type="number" step="0.0001" min="0" /></label>
          <label>fees (EUR) <input v-model.number="txForm.fees" type="number" step="0.01" min="0" /></label>
          <label v-if="txForm.transaction_type === 'sell'">
            plus_minus (required for sells — taxable margin)
            <input v-model="txForm.plus_minus_str" type="text" placeholder="e.g. 123.45" />
            <button type="button" class="btn btn-secondary btn-inline" @click="fillSuggestedPlusMinus">
              Suggest (proceeds − avg buy cost)
            </button>
          </label>
        </div>
        <p v-if="txError" class="error">{{ txError }}</p>
        <button type="button" class="btn btn-success" :disabled="!canSaveTx" @click="saveTx">Create</button>
      </div>

      <div v-if="txLoading" class="loading">Loading…</div>
      <p v-else-if="txLoadError" class="error">{{ txLoadError }}</p>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>date</th>
            <th>asset</th>
            <th>type</th>
            <th>qty</th>
            <th>price</th>
            <th>fees</th>
            <th title="Signed notional + fees (EUR): outflow on purchase, inflow on sell. Bonds: quantity ÷ 100.">
              Cash gross
            </th>
            <th title="Purchase = gross; sell = gross − taxable margin × asset tax rate. Bonds: quantity ÷ 100.">
              Cash net
            </th>
            <th>+/- (margin)</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in transactions" :key="t.id">
            <td>{{ t.trade_date }}</td>
            <td>{{ assetLabel(t.asset_pk) }}</td>
            <td>{{ t.transaction_type }}</td>
            <td>{{ t.quantity }}</td>
            <td>{{ t.unit_price }}</td>
            <td>{{ t.fees }}</td>
            <td>{{ formatMoney(txCashGross(t)) }}</td>
            <td>{{ formatMoney(txCashNet(t)) }}</td>
            <td>{{ t.plus_minus.toFixed(2) }}</td>
            <td>
              <button type="button" class="btn-link danger" @click="removeTx(t)">Delete</button>
            </td>
          </tr>
          <tr v-if="transactions.length === 0">
            <td colspan="10" class="muted">No transactions</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { api } from '@/api/client';
import type {
  InvestmentPortfolioAsset,
  InvestmentPortfolioTransaction,
  InvPortfolioKind,
  InvPortfolioClass,
  InvPortfolioStatus,
  InvPortfolioTxType,
} from '@/types';

const tabs = [
  { id: 'assets' as const, label: 'Assets' },
  { id: 'transactions' as const, label: 'Transactions' },
];

const activeTab = ref<(typeof tabs)[number]['id']>('assets');

const assets = ref<InvestmentPortfolioAsset[]>([]);
const assetsLoading = ref(false);
const assetsLoadError = ref<string | null>(null);

const transactions = ref<InvestmentPortfolioTransaction[]>([]);
const txLoading = ref(false);
const txLoadError = ref<string | null>(null);
const txFilterAssetPk = ref(0);

const showAssetForm = ref(false);
const editingAssetId = ref<number | null>(null);
const assetError = ref<string | null>(null);

const defaultAssetForm = () => ({
  asset_id: '',
  asset_name: '',
  isin: '',
  ticker: '',
  issuer: '',
  broker: '',
  type: 'fund' as InvPortfolioKind,
  class: 'share' as InvPortfolioClass,
  market: 'Borsa Italiana',
  status: 'active' as InvPortfolioStatus,
  currency: 'EUR',
  tax_rate: 0.26,
  default_exchange_rate: 1,
  perc_usa: 0,
  perc_eu: 0,
  perc_other_developed: 0,
  perc_emerging: 0,
  perc_other: 0,
  expiration_date: '' as string,
});

const assetForm = ref(defaultAssetForm());

const geoSum = computed(() => {
  const f = assetForm.value;
  return (
    f.perc_usa +
    f.perc_eu +
    f.perc_other_developed +
    f.perc_emerging +
    f.perc_other
  );
});

const geoSumOk = computed(() => Math.abs(geoSum.value - 100) <= 0.02);

const canSaveAsset = computed(() => {
  const f = assetForm.value;
  if (!f.asset_id.trim() || !f.asset_name.trim()) return false;
  if (!geoSumOk.value) return false;
  if (f.type === 'bond' && !f.expiration_date) return false;
  return true;
});

function onAssetTypeChange() {
  if (assetForm.value.type === 'bond' && assetForm.value.tax_rate === 0.26) {
    assetForm.value.tax_rate = 0.125;
  }
}

function toggleAssetForm() {
  showAssetForm.value = !showAssetForm.value;
  if (!showAssetForm.value) {
    editingAssetId.value = null;
    assetForm.value = defaultAssetForm();
    assetError.value = null;
  }
}

async function loadAssets() {
  assetsLoading.value = true;
  assetsLoadError.value = null;
  try {
    assets.value = await api.investmentPortfolioAssets.getAll();
  } catch (e: unknown) {
    assetsLoadError.value = e instanceof Error ? e.message : 'Failed to load assets';
  } finally {
    assetsLoading.value = false;
  }
}

function startEditAsset(a: InvestmentPortfolioAsset) {
  editingAssetId.value = a.id;
  showAssetForm.value = true;
  assetForm.value = {
    asset_id: a.asset_id,
    asset_name: a.asset_name,
    isin: a.isin ?? '',
    ticker: a.ticker ?? '',
    issuer: a.issuer ?? '',
    broker: a.broker ?? '',
    type: a.type,
    class: a['class'],
    market: a.market,
    status: a.status,
    currency: a.currency,
    tax_rate: a.tax_rate,
    default_exchange_rate: a.default_exchange_rate,
    perc_usa: a.perc_usa,
    perc_eu: a.perc_eu,
    perc_other_developed: a.perc_other_developed,
    perc_emerging: a.perc_emerging,
    perc_other: a.perc_other,
    expiration_date: a.expiration_date ?? '',
  };
  assetError.value = null;
}

async function saveAsset() {
  assetError.value = null;
  const f = assetForm.value;
  const payload = {
    asset_id: f.asset_id.trim(),
    asset_name: f.asset_name.trim(),
    isin: f.isin.trim() || null,
    ticker: f.ticker.trim() || null,
    issuer: f.issuer.trim() || null,
    broker: f.broker.trim() || null,
    type: f.type,
    class: f.class,
    market: f.market,
    status: f.status,
    currency: f.currency,
    tax_rate: f.tax_rate,
    default_exchange_rate: f.default_exchange_rate,
    perc_usa: f.perc_usa,
    perc_eu: f.perc_eu,
    perc_other_developed: f.perc_other_developed,
    perc_emerging: f.perc_emerging,
    perc_other: f.perc_other,
    expiration_date: f.expiration_date ? f.expiration_date : null,
  };
  try {
    if (editingAssetId.value == null) {
      await api.investmentPortfolioAssets.create(payload);
    } else {
      await api.investmentPortfolioAssets.update(editingAssetId.value, payload);
    }
    await loadAssets();
    toggleAssetForm();
  } catch (e: unknown) {
    assetError.value = e instanceof Error ? e.message : 'Save failed';
  }
}

async function removeAsset(a: InvestmentPortfolioAsset) {
  if (!confirm(`Delete asset ${a.asset_id} and all its transactions?`)) return;
  try {
    await api.investmentPortfolioAssets.delete(a.id);
    await loadAssets();
    await loadTransactions();
  } catch (e: unknown) {
    alert(e instanceof Error ? e.message : 'Delete failed');
  }
}

const showTxForm = ref(false);
const txError = ref<string | null>(null);
const txForm = ref({
  asset_pk: 0,
  trade_date: new Date().toISOString().slice(0, 10),
  transaction_type: 'purchase' as InvPortfolioTxType,
  quantity: 0,
  unit_price: 0,
  exchange_rate: 1,
  fees: 0,
  plus_minus_str: '',
});

const canSaveTx = computed(() => {
  const t = txForm.value;
  if (!(t.asset_pk > 0 && t.quantity > 0 && t.trade_date)) return false;
  if (t.transaction_type === 'purchase') return true;
  const s = t.plus_minus_str.trim();
  if (!s) return false;
  const n = Number(s.replace(',', '.'));
  return !Number.isNaN(n);
});

const selectedTxAssetIsBond = computed(() => {
  const a = assets.value.find((x) => x.id === txForm.value.asset_pk);
  return a?.type === 'bond';
});

function toggleTxForm() {
  showTxForm.value = !showTxForm.value;
  txError.value = null;
  if (showTxForm.value && assets.value.length && txForm.value.asset_pk === 0) {
    txForm.value.asset_pk = assets.value[0].id;
  }
  if (!showTxForm.value) {
    txForm.value.plus_minus_str = '';
  }
}

async function fillSuggestedPlusMinus() {
  const t = txForm.value;
  if (t.transaction_type !== 'sell') return;
  let txs: InvestmentPortfolioTransaction[];
  try {
    txs = await api.investmentPortfolioTransactions.getAll(t.asset_pk);
  } catch {
    txError.value = 'Could not load transactions for this asset.';
    return;
  }
  const buys = txs.filter((x) => x.transaction_type === 'purchase');
  if (!buys.length) {
    txError.value = 'No purchases for this asset yet — add buys first, or enter plus_minus manually.';
    return;
  }
  txError.value = null;
  const qtyForCalc = (raw: number) => quantityForMoneyComputations(t.asset_pk, raw);
  let totalQty = 0;
  let totalCost = 0;
  for (const p of buys) {
    const eq = qtyForCalc(p.quantity);
    totalQty += eq;
    totalCost += eq * p.unit_price * p.exchange_rate + p.fees;
  }
  if (totalQty <= 0) {
    txError.value = 'No valid purchase quantity for average cost.';
    return;
  }
  const avg = totalCost / totalQty;
  const sellEq = qtyForCalc(t.quantity);
  const proceeds = sellEq * t.unit_price * t.exchange_rate - t.fees;
  const margin = proceeds - sellEq * avg;
  txForm.value.plus_minus_str = String(Math.round(margin * 100) / 100);
}

function assetLabel(pk: number): string {
  const a = assets.value.find((x) => x.id === pk);
  return a ? a.asset_id : String(pk);
}

/** Italian bond listings: nominal is stored ×100 vs € flows — divide for money math. */
function quantityForMoneyComputations(assetPk: number, quantity: number): number {
  const a = assets.value.find((x) => x.id === assetPk);
  if (a?.type === 'bond') return quantity / 100;
  return quantity;
}

/** Notional trade amount in EUR (same convention as avg-cost suggestion). */
function txNotionalEur(t: InvestmentPortfolioTransaction): number {
  const q = quantityForMoneyComputations(t.asset_pk, t.quantity);
  return q * t.unit_price * t.exchange_rate;
}

/**
 * Signed cash impact: purchases −(notional + fees), sells +(notional + fees).
 */
function txCashGross(t: InvestmentPortfolioTransaction): number {
  const raw = txNotionalEur(t) + t.fees;
  return t.transaction_type === 'purchase' ? -raw : raw;
}

function assetTaxRate(assetPk: number): number {
  return assets.value.find((x) => x.id === assetPk)?.tax_rate ?? 0;
}

/** Purchase = gross; sell = notional + fees − margin × tax_rate (margin = plus_minus). */
function txCashNet(t: InvestmentPortfolioTransaction): number {
  if (t.transaction_type === 'purchase') return txCashGross(t);
  const tax = assetTaxRate(t.asset_pk);
  return txNotionalEur(t) + t.fees - t.plus_minus * tax;
}

function formatMoney(n: number): string {
  return n.toFixed(2);
}

async function loadTransactions() {
  txLoading.value = true;
  txLoadError.value = null;
  try {
    const pk = txFilterAssetPk.value > 0 ? txFilterAssetPk.value : undefined;
    transactions.value = await api.investmentPortfolioTransactions.getAll(pk);
  } catch (e: unknown) {
    txLoadError.value = e instanceof Error ? e.message : 'Failed to load transactions';
  } finally {
    txLoading.value = false;
  }
}

async function saveTx() {
  txError.value = null;
  const t = txForm.value;
  let plus_minus: number | null | undefined;
  if (t.transaction_type === 'purchase') {
    plus_minus = undefined;
  } else {
    const n = Number(t.plus_minus_str.replace(',', '.'));
    plus_minus = Number.isNaN(n) ? null : n;
  }

  try {
    await api.investmentPortfolioTransactions.create({
      asset_pk: t.asset_pk,
      trade_date: t.trade_date,
      transaction_type: t.transaction_type,
      quantity: t.quantity,
      unit_price: t.unit_price,
      exchange_rate: t.exchange_rate,
      fees: t.fees,
      plus_minus: plus_minus ?? null,
    });
    await loadTransactions();
    showTxForm.value = false;
    txForm.value.plus_minus_str = '';
  } catch (e: unknown) {
    txError.value = e instanceof Error ? e.message : 'Create failed';
  }
}

async function removeTx(t: InvestmentPortfolioTransaction) {
  if (!confirm('Delete this transaction?')) return;
  try {
    await api.investmentPortfolioTransactions.delete(t.id);
    await loadTransactions();
  } catch (e: unknown) {
    alert(e instanceof Error ? e.message : 'Delete failed');
  }
}

watch(txFilterAssetPk, () => {
  loadTransactions();
});

watch(
  () => [txForm.value.transaction_type, showTxForm.value] as const,
  ([ty, open]) => {
    if (!open || ty !== 'sell') return;
    if (txForm.value.plus_minus_str.trim() !== '') return;
    void fillSuggestedPlusMinus();
  },
);

onMounted(async () => {
  await loadAssets();
  await loadTransactions();
});
</script>

<style scoped>
.investments {
  max-width: 1100px;
}
.intro {
  color: #555;
  margin-bottom: 1rem;
}
.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.tab-btn {
  padding: 8px 14px;
  border: 1px solid #ccc;
  background: #f8f8f8;
  cursor: pointer;
  border-radius: 4px;
}
.tab-btn.active {
  background: #007bff;
  color: #fff;
  border-color: #007bff;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.btn {
  padding: 8px 14px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.btn-primary {
  background: #007bff;
  color: #fff;
}
.btn-secondary {
  background: #6c757d;
  color: #fff;
}
.btn-success {
  background: #28a745;
  color: #fff;
}
.btn-inline {
  margin-top: 8px;
  width: fit-content;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.card {
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 16px;
  background: #fafafa;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}
.form-grid label {
  display: flex;
  flex-direction: column;
  font-size: 0.85rem;
  gap: 4px;
}
.form-grid input,
.form-grid select {
  padding: 6px 8px;
}
.geo-block {
  margin-top: 8px;
}
.geo-title {
  font-weight: 600;
  font-size: 0.9rem;
}
.geo-sum.ok {
  color: #28a745;
}
.geo-sum.bad {
  color: #c00;
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
.row-actions {
  white-space: nowrap;
}
.btn-link {
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  margin-right: 8px;
  padding: 0;
}
.btn-link.danger {
  color: #c00;
}
.muted {
  color: #777;
}
.error {
  color: #c00;
}
.loading {
  padding: 12px;
}
.filter-row {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 12px;
}
.filter-row label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.85rem;
}
.bond-hint {
  margin: 0 0 10px;
  font-size: 0.85rem;
}
.actions {
  margin-top: 8px;
}
</style>
