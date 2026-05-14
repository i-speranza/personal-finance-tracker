<template>
  <div class="investments-upload">
    <h2>Investments — Upload</h2>
    <p class="intro">
      Import portfolio instruments and trades from CSV. For <strong>sells</strong>, CSV rows must include
      <code>plus_minus</code> (taxable margin). See <router-link to="/investments/data">Data</router-link> for manual
      entry and edits.
    </p>

    <section class="panel">
      <h3>CSV import</h3>
      <div class="upload-row">
        <label class="file-label">
          Assets CSV
          <input type="file" accept=".csv,text/csv" @change="onAssetsFile" />
        </label>
        <button type="button" class="btn btn-primary" :disabled="!assetsFile" @click="uploadAssetsCsv">
          Upload assets
        </button>
      </div>
      <div class="upload-row">
        <label class="file-label">
          Transactions CSV
          <input type="file" accept=".csv,text/csv" @change="onTxFile" />
        </label>
        <button type="button" class="btn btn-primary" :disabled="!txFile" @click="uploadTxCsv">
          Upload transactions
        </button>
      </div>
      <pre v-if="importMessage" class="import-result">{{ importMessage }}</pre>
    </section>

    <section class="panel valuation-panel">
      <h3>Mark-to-market snapshot</h3>
      <p class="valuation-intro">
        Enter the <strong>market unit price</strong> per instrument (as quoted on the as-of date). Only rows with a
        price are saved. <strong>Average acquisition cost</strong> is computed from your purchase history (portfolio
        currency), using <strong>full cost per unit including fees</strong>:
        <span class="valuation-formula">(quantity × unit_price × exchange_rate + fees) / quantity</span>; it does not
        change when you sell.
      </p>
      <div class="valuation-toolbar">
        <label class="date-field">
          As-of date
          <input v-model="valuationAsOfDate" type="date" />
        </label>
        <button type="button" class="btn btn-primary" :disabled="valuationSubmitting" @click="submitValuations">
          Save valuations
        </button>
      </div>
      <p v-if="valuationLoadError" class="valuation-error">{{ valuationLoadError }}</p>
      <p v-else-if="!valuationRows.length" class="valuation-note">No active assets to value.</p>
      <div v-else class="valuation-table-wrap">
        <table class="valuation-table">
          <thead>
            <tr>
              <th scope="col">asset_id</th>
              <th scope="col">isin</th>
              <th scope="col">asset_name</th>
              <th scope="col">bank</th>
              <th scope="col">avg. acquisition / unit</th>
              <th scope="col">market unit price</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in valuationRows" :key="a.id">
              <td><code>{{ a.asset_id }}</code></td>
              <td>{{ a.isin ?? '—' }}</td>
              <td>{{ a.asset_name }}</td>
              <td>{{ a.broker ?? '—' }}</td>
              <td class="num">{{ formatCost(a.current_average_unit_cost) }}</td>
              <td>
                <input
                  v-model="marketPriceByAssetPk[a.id]"
                  class="price-input"
                  type="text"
                  inputmode="decimal"
                  autocomplete="off"
                  placeholder="—"
                  :aria-label="`Market unit price for ${a.asset_id}`"
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <pre v-if="valuationMessage" class="import-result valuation-result">{{ valuationMessage }}</pre>
    </section>

    <aside class="helper-panel" aria-labelledby="csv-columns-heading">
      <h3 id="csv-columns-heading">CSV column reference</h3>
      <p class="helper-note">
        First row must be the header with these exact column names (UTF-8; comma-separated is typical). Numbers may use
        a comma as decimal separator.
      </p>

      <h4 class="helper-sub">Assets CSV</h4>
      <table class="col-help">
        <thead>
          <tr>
            <th scope="col">Column</th>
            <th scope="col">Meaning</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>asset_id</code> *</td>
            <td>Stable unique key for the instrument; must match <code>asset_id</code> in the transactions file.</td>
          </tr>
          <tr>
            <td><code>asset_name</code> *</td>
            <td>Human-readable name (defaults to <code>asset_id</code> if empty).</td>
          </tr>
          <tr>
            <td><code>type</code> *</td>
            <td>Instrument kind: <code>fund</code>, <code>bond</code>, or <code>share</code>.</td>
          </tr>
          <tr>
            <td><code>class</code> *</td>
            <td>Asset class: <code>share</code>, <code>bond</code>, or <code>commodity</code>.</td>
          </tr>
          <tr>
            <td><code>isin</code></td>
            <td>Optional ISIN.</td>
          </tr>
          <tr>
            <td><code>ticker</code></td>
            <td>Optional ticker symbol.</td>
          </tr>
          <tr>
            <td><code>issuer</code></td>
            <td>Optional issuer name.</td>
          </tr>
          <tr>
            <td><code>broker</code></td>
            <td>Optional broker or custodian name.</td>
          </tr>
          <tr>
            <td><code>market</code></td>
            <td>Optional trading venue; default <code>Borsa Italiana</code>.</td>
          </tr>
          <tr>
            <td><code>status</code></td>
            <td>Optional: <code>active</code> (default), <code>sold</code>, or <code>special</code>.</td>
          </tr>
          <tr>
            <td><code>currency</code></td>
            <td>Optional ISO currency code; default <code>EUR</code>.</td>
          </tr>
          <tr>
            <td><code>tax_rate</code></td>
            <td>Optional withholding rate 0–1; default <code>0.26</code>.</td>
          </tr>
          <tr>
            <td><code>default_exchange_rate</code></td>
            <td>Optional FX rate to portfolio currency; default <code>1</code>.</td>
          </tr>
          <tr>
            <td>
              <code>perc_usa</code>, <code>perc_eu</code>, <code>perc_other_developed</code>,
              <code>perc_emerging</code>, <code>perc_other</code>
            </td>
            <td>
              Optional geographic weights 0–100. If you set them, all five should be present and sum to 100 (within a
              small tolerance).
            </td>
          </tr>
          <tr>
            <td><code>expiration_date</code></td>
            <td>ISO date <code>YYYY-MM-DD</code>; required when <code>type</code> is <code>bond</code>.</td>
          </tr>
        </tbody>
      </table>
      <p class="helper-foot">* Required column (header must be present).</p>

      <h4 class="helper-sub">Transactions CSV</h4>
      <table class="col-help">
        <thead>
          <tr>
            <th scope="col">Column</th>
            <th scope="col">Meaning</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><code>asset_id</code> *</td>
            <td>Must match an asset already in the app (import assets first).</td>
          </tr>
          <tr>
            <td><code>date</code> *</td>
            <td>Trade date as ISO <code>YYYY-MM-DD</code> (first 10 characters are used).</td>
          </tr>
          <tr>
            <td><code>transaction_type</code> *</td>
            <td><code>purchase</code> or <code>sell</code>.</td>
          </tr>
          <tr>
            <td><code>quantity</code> *</td>
            <td>
              Number of units (decimals allowed). For assets with type <code>bond</code>, store nominal as listed
              (Italian convention); euro amounts in the app use quantity ÷ 100.
            </td>
          </tr>
          <tr>
            <td><code>unit_price</code> *</td>
            <td>Price per unit in the trade currency.</td>
          </tr>
          <tr>
            <td><code>exchange_rate</code></td>
            <td>Optional FX to portfolio currency; default <code>1</code>.</td>
          </tr>
          <tr>
            <td><code>fees</code></td>
            <td>Optional fees amount; default <code>0</code>.</td>
          </tr>
          <tr>
            <td><code>plus_minus</code></td>
            <td>
              <strong>Required for <code>sell</code></strong>: taxable margin (same meaning as on the Data page).
              Omit or leave empty for purchases.
            </td>
          </tr>
        </tbody>
      </table>
      <p class="helper-foot">
        * Required headers. You may omit optional columns entirely; for every <code>sell</code> row, include a
        <code>plus_minus</code> value (add that column to the header when you have sells).
      </p>

      <h4 class="helper-sub">Mark-to-market snapshot</h4>
      <p class="helper-note">
        Use the form above to store one <strong>market unit price</strong> per active asset for a chosen
        <strong>as-of date</strong>. The backend table is <code>investment_portfolio_market_quotes</code> (unique per
        date and asset). The <strong>bank</strong> column shows each asset’s <code>broker</code> (custodian) from the
        assets CSV. Purchase rows in <code>investment_portfolio_transactions</code> may include
        <code>average_unit_cost_after_trade</code>: weighted average after each buy in portfolio currency, using per
        purchase <strong>(quantity × unit_price × exchange_rate + fees) / quantity</strong> as the unit acquisition
        price.
      </p>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { api } from '@/api/client';
import type { InvestmentPortfolioAsset } from '@/types';

const assetsFile = ref<File | null>(null);
const txFile = ref<File | null>(null);
const importMessage = ref('');

const valuationRows = ref<InvestmentPortfolioAsset[]>([]);
const valuationLoadError = ref('');
const valuationAsOfDate = ref(isoToday());
const marketPriceByAssetPk = reactive<Record<number, string>>({});
const valuationMessage = ref('');
const valuationSubmitting = ref(false);

function isoToday(): string {
  const d = new Date();
  const z = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
  return z.toISOString().slice(0, 10);
}

function formatCost(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) {
    return '—';
  }
  return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 });
}

function parsePriceInput(s: string): number | null {
  const t = s.trim().replace(',', '.');
  if (t === '') {
    return null;
  }
  const v = Number(t);
  if (!Number.isFinite(v) || v < 0) {
    return null;
  }
  return v;
}

/** Mark-to-market table: bank (broker) first, then name, then asset_id. */
function sortValuationAssets(rows: InvestmentPortfolioAsset[]): InvestmentPortfolioAsset[] {
  return [...rows].sort((a, b) => {
    const bankA = (a.broker ?? '').trim();
    const bankB = (b.broker ?? '').trim();
    const missA = bankA === '' ? 1 : 0;
    const missB = bankB === '' ? 1 : 0;
    if (missA !== missB) {
      return missA - missB;
    }
    const byBank = bankA.localeCompare(bankB, undefined, { sensitivity: 'base' });
    if (byBank !== 0) {
      return byBank;
    }
    const byName = a.asset_name.localeCompare(b.asset_name, undefined, { sensitivity: 'base' });
    if (byName !== 0) {
      return byName;
    }
    return a.asset_id.localeCompare(b.asset_id, undefined, { sensitivity: 'base' });
  });
}

onMounted(async () => {
  try {
    valuationLoadError.value = '';
    const loaded = await api.investmentPortfolioAssets.getAll({
      status: 'active',
      include_position: true,
    });
    valuationRows.value = sortValuationAssets(loaded);
  } catch (e: unknown) {
    valuationLoadError.value = e instanceof Error ? e.message : 'Failed to load assets';
  }
});

function onAssetsFile(ev: Event) {
  const input = ev.target as HTMLInputElement;
  assetsFile.value = input.files?.[0] ?? null;
}

function onTxFile(ev: Event) {
  const input = ev.target as HTMLInputElement;
  txFile.value = input.files?.[0] ?? null;
}

async function uploadAssetsCsv() {
  if (!assetsFile.value) return;
  importMessage.value = '';
  try {
    const r = await api.investmentPortfolioAssets.importCsv(assetsFile.value);
    importMessage.value = JSON.stringify(r, null, 2);
  } catch (e: unknown) {
    importMessage.value = e instanceof Error ? e.message : 'Upload failed';
  }
}

async function uploadTxCsv() {
  if (!txFile.value) return;
  importMessage.value = '';
  try {
    const r = await api.investmentPortfolioTransactions.importCsv(txFile.value);
    importMessage.value = JSON.stringify(r, null, 2);
  } catch (e: unknown) {
    importMessage.value = e instanceof Error ? e.message : 'Upload failed';
  }
}

async function submitValuations() {
  valuationMessage.value = '';
  if (!valuationAsOfDate.value) {
    valuationMessage.value = 'Choose an as-of date.';
    return;
  }
  const quotes: { asset_pk: number; market_unit_price: number }[] = [];
  for (const a of valuationRows.value) {
    const raw = marketPriceByAssetPk[a.id];
    const v = parsePriceInput(raw ?? '');
    if (v !== null) {
      quotes.push({ asset_pk: a.id, market_unit_price: v });
    }
  }
  if (!quotes.length) {
    valuationMessage.value = 'Enter at least one market unit price.';
    return;
  }
  valuationSubmitting.value = true;
  try {
    const r = await api.investmentPortfolioValuations.bulkUpsert({
      as_of_date: valuationAsOfDate.value,
      quotes,
    });
    valuationMessage.value = JSON.stringify(r, null, 2);
  } catch (e: unknown) {
    valuationMessage.value = e instanceof Error ? e.message : 'Save failed';
  } finally {
    valuationSubmitting.value = false;
  }
}
</script>

<style scoped>
.investments-upload {
  max-width: 900px;
}
.intro {
  color: #555;
  margin-bottom: 1.25rem;
}
.helper-panel {
  margin-bottom: 1.25rem;
  padding: 1rem 1.25rem;
  background: #f5f9ff;
  border: 1px solid #cfe2fc;
  border-radius: 8px;
  border-left: 4px solid #007bff;
}
.helper-panel h3 {
  margin: 0 0 0.5rem;
  font-size: 1.05rem;
}
.helper-note {
  margin: 0 0 0.75rem;
  font-size: 0.875rem;
  color: #555;
  line-height: 1.45;
}
.helper-sub {
  margin: 1rem 0 0.5rem;
  font-size: 0.95rem;
  color: #333;
}
.helper-sub:first-of-type {
  margin-top: 0;
}
.col-help {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
  line-height: 1.4;
}
.col-help th,
.col-help td {
  text-align: left;
  vertical-align: top;
  padding: 0.45rem 0.5rem;
  border-bottom: 1px solid #dee8f5;
}
.col-help thead th {
  font-weight: 600;
  color: #333;
  background: rgba(0, 123, 255, 0.06);
}
.col-help tbody tr:last-child td {
  border-bottom: none;
}
.col-help code {
  font-size: 0.8125rem;
}
.helper-foot {
  margin: 0.5rem 0 0;
  font-size: 0.8rem;
  color: #666;
  line-height: 1.4;
}
.panel {
  background: #fafafa;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.25rem;
}
.panel h3 {
  margin-top: 0;
}
.upload-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.file-label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.9rem;
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
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.import-result {
  background: #f4f4f4;
  padding: 12px;
  border-radius: 4px;
  overflow: auto;
  max-height: 320px;
}
.valuation-panel {
  margin-top: 1.25rem;
}
.valuation-intro {
  color: #555;
  font-size: 0.9rem;
  line-height: 1.45;
  margin: 0 0 1rem;
}
.valuation-intro .valuation-formula {
  font-family: ui-monospace, monospace;
  font-size: 0.84em;
  white-space: nowrap;
}
.valuation-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 12px;
  margin-bottom: 12px;
}
.date-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.9rem;
}
.valuation-error {
  color: #b00020;
  font-size: 0.9rem;
  margin: 0 0 8px;
}
.valuation-note {
  color: #666;
  font-size: 0.9rem;
  margin: 0;
}
.valuation-table-wrap {
  overflow: auto;
  max-height: 420px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
}
.valuation-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}
.valuation-table th,
.valuation-table td {
  text-align: left;
  padding: 0.5rem 0.6rem;
  border-bottom: 1px solid #eee;
  vertical-align: middle;
}
.valuation-table thead th {
  background: #f0f4f8;
  font-weight: 600;
  position: sticky;
  top: 0;
  z-index: 1;
}
.valuation-table tbody tr:last-child td {
  border-bottom: none;
}
.valuation-table .num {
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}
.price-input {
  width: 100%;
  min-width: 7rem;
  max-width: 12rem;
  padding: 6px 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 0.875rem;
}
.valuation-result {
  margin-top: 12px;
  max-height: 160px;
}
</style>
