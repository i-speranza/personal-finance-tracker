<template>
  <div class="upload-page">
    <h2>Upload & Input Data</h2>
    
    <!-- Account Status Panel -->
    <section class="panel account-status-panel">
      <h3>Account Status</h3>
      <div v-if="loadingAccounts" class="loading">Loading accounts...</div>
      <div v-else-if="accountsError" class="error">{{ accountsError }}</div>
      <table v-else class="status-table">
        <thead>
          <tr>
            <th>Bank</th>
            <th>Account</th>
            <th>Last Transaction</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="account in accountsWithDates" :key="account.id">
            <td>{{ account.bank_name }}</td>
            <td>{{ account.account_name }}</td>
            <td :class="{ 'stale': isStale(account.last_transaction_date) }">
              {{ formatDate(account.last_transaction_date) }}
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- Transaction Upload Section -->
    <section class="panel upload-section">
      <h3>Upload Transactions</h3>
      
      <!-- Stepper -->
      <div class="stepper">
        <div 
          v-for="(step, index) in steps" 
          :key="index"
          class="step"
          :class="{ 
            'active': currentStep === index, 
            'completed': currentStep > index 
          }"
        >
          <div class="step-number">{{ index + 1 }}</div>
          <div class="step-label">{{ step }}</div>
        </div>
      </div>

      <!-- Step Content -->
      <div class="step-content">
        <!-- Step 1: Setup -->
        <div v-if="currentStep === 0" class="step-panel">
          <h4>Step 1: Select Bank, Account & Date</h4>
          
          <div class="form-group">
            <label for="upload-date">Date:</label>
            <input 
              type="date" 
              id="upload-date" 
              v-model="uploadForm.date"
            />
          </div>
          
          <div class="form-group">
            <label for="bank-select">Bank:</label>
            <select id="bank-select" v-model="uploadForm.bankName" @change="onBankChange">
              <option value="">Select a bank</option>
              <option v-for="bank in banks" :key="bank.id" :value="bank.name">
                {{ bank.display_name }}
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <label for="account-select">Account:</label>
            <select 
              id="account-select" 
              v-model="uploadForm.accountName"
              :disabled="!uploadForm.bankName"
            >
              <option value="">Select an account</option>
              <option 
                v-for="account in filteredAccounts" 
                :key="account.id" 
                :value="account.account_name"
              >
                {{ account.account_name }}
              </option>
            </select>
          </div>
          
          <div class="step-actions">
            <button 
              class="btn btn-primary" 
              @click="goToStep(1)"
              :disabled="!canProceedToStep1"
            >
              Next
            </button>
          </div>
        </div>

        <!-- Step 2: File Upload -->
        <div v-if="currentStep === 1" class="step-panel">
          <h4>Step 2: Upload File</h4>
          
          <div class="file-upload-area">
            <input 
              type="file" 
              id="file-input"
              ref="fileInput"
              accept=".xlsx,.xls,.csv"
              @change="onFileSelected"
            />
            <label for="file-input" class="file-label">
              <span v-if="uploadForm.file">{{ uploadForm.file.name }}</span>
              <span v-else>Click to select or drag a file (.xlsx, .xls, .csv)</span>
            </label>
          </div>
          
          <div v-if="uploadError" class="error">{{ uploadError }}</div>
          <div v-if="uploading" class="loading">Processing file...</div>
          
          <div class="step-actions">
            <button class="btn btn-secondary" @click="goToStep(0)">Back</button>
            <button 
              class="btn btn-primary" 
              @click="preprocessFile"
              :disabled="!uploadForm.file || uploading"
            >
              Upload & Process
            </button>
          </div>
        </div>

        <!-- Step 3: Pre-processing Review -->
        <div v-if="currentStep === 2" class="step-panel">
          <h4>Step 3: Pre-processing Review</h4>
          
          <div v-if="preprocessingResult">
            <div class="info-box">
              <p><strong>File saved as:</strong> {{ preprocessingResult.saved_filename }}</p>
              <p><strong>Date range:</strong> {{ preprocessingResult.date_range.first_date }} to {{ preprocessingResult.date_range.last_date }}</p>
              <p><strong>Transactions found:</strong> {{ preprocessingResult.transactions.length }}</p>
            </div>
            
            <div v-if="preprocessingResult.warnings.length > 0" class="warnings-section">
              <h5>Warnings ({{ preprocessingResult.warnings.length }})</h5>
              <ul class="warning-list">
                <li v-for="(warning, idx) in preprocessingResult.warnings" :key="idx" class="warning-item">
                  <span class="warning-type">{{ warning.type }}:</span> {{ warning.message }}
                </li>
              </ul>
            </div>
            
            <div v-else class="success-box">
              No warnings - file processed successfully!
            </div>
          </div>
          
          <div class="step-actions">
            <button class="btn btn-secondary" @click="resetUpload">Cancel</button>
            <button class="btn btn-primary" @click="harmonizeTransactions">
              Proceed to Harmonization
            </button>
          </div>
        </div>

        <!-- Step 4: Harmonization Review -->
        <div v-if="currentStep === 3" class="step-panel">
          <h4>Step 4: Harmonization Review</h4>
          
          <div v-if="harmonizing" class="loading">Checking for duplicates...</div>
          
          <div v-else-if="harmonizationResult">
            <!-- Duplicates Section -->
            <div class="collapsible-section">
              <div 
                class="section-header" 
                @click="toggleDuplicates"
                :class="{ 'collapsed': !showDuplicates }"
              >
                <span>Duplicates to Skip ({{ harmonizationResult.duplicate_transactions.length }})</span>
                <span class="toggle-icon">{{ showDuplicates ? '▼' : '▶' }}</span>
              </div>
              <div v-if="showDuplicates && harmonizationResult.duplicate_transactions.length > 0" class="section-content">
                <table class="transactions-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Amount</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(t, idx) in harmonizationResult.duplicate_transactions" :key="idx">
                      <td>{{ t.date }}</td>
                      <td :class="{ 'positive': t.amount > 0, 'negative': t.amount < 0 }">
                        {{ formatCurrency(t.amount) }}
                      </td>
                      <td>{{ t.description }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            
            <!-- New Transactions Section -->
            <div class="collapsible-section">
              <div 
                class="section-header" 
                @click="toggleNewTransactions"
                :class="{ 'collapsed': !showNewTransactions }"
              >
                <span>New Transactions to Add ({{ harmonizationResult.new_transactions.length }})</span>
                <span class="toggle-icon">{{ showNewTransactions ? '▼' : '▶' }}</span>
              </div>
              <div v-if="showNewTransactions && harmonizationResult.new_transactions.length > 0" class="section-content">
                <table class="transactions-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Amount</th>
                      <th>Description</th>
                      <th>Type</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(t, idx) in harmonizationResult.new_transactions" :key="idx">
                      <td>{{ t.date }}</td>
                      <td :class="{ 'positive': t.amount > 0, 'negative': t.amount < 0 }">
                        {{ formatCurrency(t.amount) }}
                      </td>
                      <td>{{ t.description }}</td>
                      <td>{{ t.transaction_type }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          
          <div class="step-actions">
            <button class="btn btn-secondary" @click="resetUpload">Cancel</button>
            <button 
              class="btn btn-primary" 
              @click="goToStep(4)"
              :disabled="!harmonizationResult || harmonizationResult.new_transactions.length === 0"
            >
              Proceed to Review
            </button>
          </div>
        </div>

        <!-- Step 5: Final Review & Commit -->
        <div v-if="currentStep === 4" class="step-panel">
          <h4>Step 5: Final Review & Commit</h4>
          
          <div v-if="committing" class="loading">Saving transactions...</div>
          <div v-if="commitError" class="error">{{ commitError }}</div>
          
          <div v-if="transactionsToCommit.length > 0" class="final-review">
            <p>Review transactions and mark any as "special" if needed:</p>
            
            <div class="transactions-review-table-wrapper">
              <table class="transactions-table review-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Amount</th>
                    <th>Description</th>
                    <th>Type</th>
                    <th>Special</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(t, idx) in transactionsToCommit" :key="idx">
                    <td>{{ t.date }}</td>
                    <td :class="{ 'positive': t.amount > 0, 'negative': t.amount < 0 }">
                      {{ formatCurrency(t.amount) }}
                    </td>
                    <td>{{ t.description }}</td>
                    <td>{{ t.transaction_type }}</td>
                    <td>
                      <input 
                        type="checkbox" 
                        v-model="t.is_special"
                        class="special-checkbox"
                      />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          
          <div class="step-actions">
            <button class="btn btn-secondary" @click="goToStep(3)">Back</button>
            <button 
              class="btn btn-success" 
              @click="commitTransactions"
              :disabled="committing || transactionsToCommit.length === 0"
            >
              Save All ({{ transactionsToCommit.length }})
            </button>
          </div>
        </div>

        <!-- Success State -->
        <div v-if="currentStep === 5" class="step-panel success-panel">
          <h4>Upload Complete!</h4>
          <div class="success-box">
            <p>{{ commitResult?.message }}</p>
            <p><strong>{{ commitResult?.inserted_count }}</strong> transactions have been added.</p>
          </div>
          <div class="step-actions">
            <button class="btn btn-primary" @click="resetUpload">Upload Another File</button>
          </div>
        </div>
      </div>
    </section>

    <!-- Asset Values Input Section -->
    <section class="panel assets-input-section">
      <h3>Input Asset Values</h3>
      
      <div class="form-row">
        <div class="form-group">
          <label for="asset-date">Date:</label>
          <input type="date" id="asset-date" v-model="assetForm.date" />
        </div>
      </div>
      
      <div v-if="loadingAllAccounts" class="loading">Loading accounts...</div>
      
      <div v-else class="asset-inputs">
        <div 
          v-for="account in allAccountsForAssets" 
          :key="account.id" 
          class="asset-input-row"
        >
          <label>
            {{ account.bank_name }} - {{ account.account_name }}
            <span class="asset-type-badge" :class="account.asset_type">
              {{ account.asset_type }}
            </span>
          </label>
          <input 
            type="text" 
            v-model="assetValues[account.id]"
            placeholder="0,00"
            @blur="formatAssetValue(account.id)"
          />
        </div>
      </div>
      
      <div v-if="assetSaveError" class="error">{{ assetSaveError }}</div>
      <div v-if="assetSaveSuccess" class="success-box">{{ assetSaveSuccess }}</div>
      
      <div class="step-actions">
        <button 
          class="btn btn-success" 
          @click="saveAssetValues"
          :disabled="savingAssets"
        >
          {{ savingAssets ? 'Saving...' : 'Save All Values' }}
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue';
import { api } from '@/api/client';
import type { 
  AccountWithLastDate, 
  Bank, 
  Account,
  PreprocessingResult,
  HarmonizationResult,
  ParsedTransaction,
  CommitResult,
  AssetType
} from '@/types';

// Account Status (CASH accounts for transaction tracking)
const accountsWithDates = ref<AccountWithLastDate[]>([]);
const loadingAccounts = ref(false);
const accountsError = ref<string | null>(null);

// All accounts for asset value input
const allAccountsForAssets = ref<Account[]>([]);
const loadingAllAccounts = ref(false);

// Banks and Accounts for upload
const banks = ref<Bank[]>([]);
const accounts = ref<Account[]>([]);

// Upload Form
const uploadForm = reactive({
  date: new Date().toISOString().split('T')[0],
  bankName: '',
  accountName: '',
  file: null as File | null
});

// Upload State
const currentStep = ref(0);
const steps = ['Setup', 'Upload', 'Pre-process', 'Harmonize', 'Commit'];
const uploading = ref(false);
const uploadError = ref<string | null>(null);
const preprocessingResult = ref<PreprocessingResult | null>(null);
const harmonizing = ref(false);
const harmonizationResult = ref<HarmonizationResult | null>(null);
const transactionsToCommit = ref<ParsedTransaction[]>([]);
const committing = ref(false);
const commitError = ref<string | null>(null);
const commitResult = ref<CommitResult | null>(null);

// Collapsible sections
const showDuplicates = ref(false);
const showNewTransactions = ref(true);

// Asset Form
const assetForm = reactive({
  date: new Date().toISOString().split('T')[0],
  assetType: 'cash' as AssetType
});
const assetValues = reactive<Record<number, string>>({});
const savingAssets = ref(false);
const assetSaveError = ref<string | null>(null);
const assetSaveSuccess = ref<string | null>(null);

// File input ref
const fileInput = ref<HTMLInputElement | null>(null);

// Computed
const filteredAccounts = computed(() => {
  if (!uploadForm.bankName) return [];
  return accounts.value.filter(a => a.bank_name === uploadForm.bankName && a.status);
});

const canProceedToStep1 = computed(() => {
  return uploadForm.bankName && uploadForm.accountName && uploadForm.date;
});

// Methods
async function loadAccountsWithDates() {
  loadingAccounts.value = true;
  accountsError.value = null;
  try {
    // Only load CASH accounts for transaction status
    accountsWithDates.value = await api.accounts.getLastTransactionDates(true, 'cash');
  } catch (e: any) {
    accountsError.value = e.message || 'Failed to load accounts';
  } finally {
    loadingAccounts.value = false;
  }
}

async function loadAllAccountsForAssets() {
  loadingAllAccounts.value = true;
  try {
    // Load ALL accounts for asset value input
    allAccountsForAssets.value = await api.accounts.getAll();
  } catch (e: any) {
    console.error('Failed to load all accounts:', e);
  } finally {
    loadingAllAccounts.value = false;
  }
}

async function loadBanks() {
  try {
    banks.value = await api.banks.getAll();
  } catch (e: any) {
    console.error('Failed to load banks:', e);
  }
}

async function loadAccounts() {
  try {
    // Only load CASH accounts for transaction uploads
    accounts.value = await api.accounts.getAll({ asset_type: 'cash' });
  } catch (e: any) {
    console.error('Failed to load accounts:', e);
  }
}

function onBankChange() {
  uploadForm.accountName = '';
  // Auto-select if only one account
  if (filteredAccounts.value.length === 1) {
    uploadForm.accountName = filteredAccounts.value[0].account_name;
  }
}

function onFileSelected(event: Event) {
  const input = event.target as HTMLInputElement;
  if (input.files && input.files.length > 0) {
    uploadForm.file = input.files[0];
    uploadError.value = null;
  }
}

function goToStep(step: number) {
  currentStep.value = step;
}

async function preprocessFile() {
  if (!uploadForm.file) return;
  
  uploading.value = true;
  uploadError.value = null;
  
  try {
    preprocessingResult.value = await api.upload.preprocess(
      uploadForm.file,
      uploadForm.bankName,
      uploadForm.accountName
    );
    currentStep.value = 2;
  } catch (e: any) {
    uploadError.value = e.message || 'Failed to process file';
  } finally {
    uploading.value = false;
  }
}

async function harmonizeTransactions() {
  if (!preprocessingResult.value) return;
  
  harmonizing.value = true;
  
  try {
    harmonizationResult.value = await api.upload.harmonize(
      preprocessingResult.value.transactions
    );
    currentStep.value = 3;
  } catch (e: any) {
    uploadError.value = e.message || 'Failed to harmonize transactions';
  } finally {
    harmonizing.value = false;
  }
}

function toggleDuplicates() {
  showDuplicates.value = !showDuplicates.value;
}

function toggleNewTransactions() {
  showNewTransactions.value = !showNewTransactions.value;
}

async function commitTransactions() {
  if (transactionsToCommit.value.length === 0) return;
  
  committing.value = true;
  commitError.value = null;
  
  try {
    commitResult.value = await api.upload.commit(transactionsToCommit.value);
    currentStep.value = 5;
    // Refresh account dates
    await loadAccountsWithDates();
  } catch (e: any) {
    commitError.value = e.message || 'Failed to save transactions';
  } finally {
    committing.value = false;
  }
}

function resetUpload() {
  currentStep.value = 0;
  uploadForm.file = null;
  uploadError.value = null;
  preprocessingResult.value = null;
  harmonizationResult.value = null;
  transactionsToCommit.value = [];
  commitError.value = null;
  commitResult.value = null;
  if (fileInput.value) {
    fileInput.value.value = '';
  }
}

// Watch for harmonization result to populate transactions to commit
import { watch } from 'vue';
watch(harmonizationResult, (result) => {
  if (result) {
    // Deep clone to allow editing is_special
    transactionsToCommit.value = result.new_transactions.map(t => ({ ...t }));
  }
});

// Asset Values Methods
function parseFlexibleNumber(value: string): number | null {
  if (!value || value.trim() === '') return null;
  
  const trimmed = value.trim();
  
  // Pattern: 1.000,50 (European with thousand separator)
  if (/^\d{1,3}(\.\d{3})*,\d+$/.test(trimmed)) {
    return parseFloat(trimmed.replace(/\./g, '').replace(',', '.'));
  }
  
  // Pattern: 1000,50 (comma as decimal)
  if (/^\d+,\d+$/.test(trimmed)) {
    return parseFloat(trimmed.replace(',', '.'));
  }
  
  // Pattern: 1000.50 or 1000 (dot as decimal or integer)
  const parsed = parseFloat(trimmed);
  return isNaN(parsed) ? null : parsed;
}

function formatAssetValue(accountId: number) {
  const value = assetValues[accountId];
  const parsed = parseFlexibleNumber(value);
  if (parsed !== null) {
    assetValues[accountId] = parsed.toLocaleString('it-IT', { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    });
  }
}

async function saveAssetValues() {
  const entries = [];
  
  for (const account of allAccountsForAssets.value) {
    const value = assetValues[account.id];
    const amount = parseFlexibleNumber(value);
    
    if (amount !== null && amount > 0) {
      entries.push({
        bank_name: account.bank_name,
        account_name: account.account_name,
        asset_type: account.asset_type || assetForm.assetType,  // Use account's asset_type
        date: assetForm.date,
        amount: amount
      });
    }
  }
  
  if (entries.length === 0) {
    assetSaveError.value = 'No values to save. Enter at least one amount.';
    return;
  }
  
  savingAssets.value = true;
  assetSaveError.value = null;
  assetSaveSuccess.value = null;
  
  try {
    const result = await api.assetsHistory.createBulk({ entries });
    assetSaveSuccess.value = `Successfully saved ${result.created_count} asset value(s).`;
    // Clear values after successful save
    for (const key in assetValues) {
      assetValues[key] = '';
    }
  } catch (e: any) {
    assetSaveError.value = e.message || 'Failed to save asset values';
  } finally {
    savingAssets.value = false;
  }
}

// Utility functions
function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'No transactions';
  return new Date(dateStr).toLocaleDateString('it-IT');
}

function formatCurrency(amount: number): string {
  return amount.toLocaleString('it-IT', { 
    style: 'currency', 
    currency: 'EUR' 
  });
}

function isStale(dateStr: string | null): boolean {
  if (!dateStr) return true;
  const date = new Date(dateStr);
  const now = new Date();
  const diffDays = (now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24);
  return diffDays > 30;
}

// Lifecycle
onMounted(async () => {
  await Promise.all([
    loadAccountsWithDates(),
    loadBanks(),
    loadAccounts(),
    loadAllAccountsForAssets()
  ]);
});
</script>

<style scoped>
.upload-page {
  max-width: 1200px;
  margin: 0 auto;
}

.panel {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}

.panel h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #333;
  border-bottom: 2px solid #007bff;
  padding-bottom: 10px;
}

/* Account Status Table */
.status-table {
  width: 100%;
  border-collapse: collapse;
}

.status-table th,
.status-table td {
  padding: 10px 15px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.status-table th {
  background-color: #f8f9fa;
  font-weight: 600;
}

.status-table tbody tr:hover {
  background-color: #f5f5f5;
}

.status-table .stale {
  color: #dc3545;
  font-weight: 500;
}

/* Stepper */
.stepper {
  display: flex;
  justify-content: space-between;
  margin-bottom: 30px;
  padding: 0 20px;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  position: relative;
}

.step:not(:last-child)::after {
  content: '';
  position: absolute;
  top: 15px;
  left: 50%;
  width: 100%;
  height: 2px;
  background-color: #ddd;
  z-index: 0;
}

.step.completed:not(:last-child)::after {
  background-color: #28a745;
}

.step-number {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: #ddd;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: #666;
  z-index: 1;
  transition: all 0.3s;
}

.step.active .step-number {
  background-color: #007bff;
  color: white;
}

.step.completed .step-number {
  background-color: #28a745;
  color: white;
}

.step-label {
  margin-top: 8px;
  font-size: 0.85em;
  color: #666;
}

.step.active .step-label {
  color: #007bff;
  font-weight: 500;
}

.step.completed .step-label {
  color: #28a745;
}

/* Step Content */
.step-content {
  min-height: 300px;
}

.step-panel {
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.step-panel h4 {
  margin-top: 0;
  margin-bottom: 20px;
}

/* Form Styles */
.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group select {
  width: 100%;
  max-width: 300px;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.1);
}

.form-row {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

/* File Upload */
.file-upload-area {
  margin-bottom: 20px;
}

.file-upload-area input[type="file"] {
  display: none;
}

.file-label {
  display: block;
  padding: 40px 20px;
  border: 2px dashed #ddd;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background-color: white;
}

.file-label:hover {
  border-color: #007bff;
  background-color: #f0f7ff;
}

/* Buttons */
.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #545b62;
}

.btn-success {
  background-color: #28a745;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background-color: #1e7e34;
}

.step-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
  justify-content: flex-end;
}

/* Info and Status Boxes */
.info-box {
  background-color: #e7f3ff;
  border: 1px solid #b6d4fe;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 20px;
}

.info-box p {
  margin: 5px 0;
}

.success-box {
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
  border-radius: 4px;
  padding: 15px;
  color: #155724;
}

.success-panel {
  text-align: center;
}

.success-panel .success-box {
  font-size: 1.1em;
}

/* Warnings */
.warnings-section {
  margin-bottom: 20px;
}

.warnings-section h5 {
  color: #856404;
  margin-bottom: 10px;
}

.warning-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.warning-item {
  background-color: #fff3cd;
  border: 1px solid #ffeeba;
  border-radius: 4px;
  padding: 10px;
  margin-bottom: 8px;
}

.warning-type {
  font-weight: 600;
  color: #856404;
}

/* Collapsible Sections */
.collapsible-section {
  margin-bottom: 15px;
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  background-color: #f8f9fa;
  cursor: pointer;
  font-weight: 500;
}

.section-header:hover {
  background-color: #e9ecef;
}

.section-content {
  padding: 15px;
  background-color: white;
  max-height: 300px;
  overflow-y: auto;
}

.toggle-icon {
  font-size: 0.8em;
  color: #666;
}

/* Transactions Table */
.transactions-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9em;
}

.transactions-table th,
.transactions-table td {
  padding: 8px 10px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.transactions-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  position: sticky;
  top: 0;
}

.transactions-table .positive {
  color: #28a745;
}

.transactions-table .negative {
  color: #dc3545;
}

.transactions-review-table-wrapper {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.review-table {
  margin: 0;
}

.special-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

/* Asset Inputs */
.asset-inputs {
  display: grid;
  gap: 15px;
  margin-bottom: 20px;
}

.asset-input-row {
  display: flex;
  align-items: center;
  gap: 15px;
}

.asset-input-row label {
  flex: 1;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.asset-type-badge {
  font-size: 0.7em;
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 600;
  text-transform: uppercase;
}

.asset-type-badge.cash {
  background-color: #d4edda;
  color: #155724;
}

.asset-type-badge.investment {
  background-color: #cce5ff;
  color: #004085;
}

.asset-input-row input {
  width: 150px;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  text-align: right;
}

.asset-input-row input:focus {
  outline: none;
  border-color: #007bff;
}

/* Loading and Error */
.loading {
  padding: 20px;
  text-align: center;
  color: #666;
}

.error {
  background-color: #f8d7da;
  border: 1px solid #f5c6cb;
  color: #721c24;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 15px;
}

/* Responsive */
@media (max-width: 768px) {
  .stepper {
    flex-wrap: wrap;
    gap: 10px;
  }
  
  .step {
    flex: 0 0 auto;
    min-width: 60px;
  }
  
  .step:not(:last-child)::after {
    display: none;
  }
  
  .form-row {
    flex-direction: column;
  }
  
  .form-group input,
  .form-group select {
    max-width: 100%;
  }
  
  .asset-input-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .asset-input-row input {
    width: 100%;
  }
}
</style>
