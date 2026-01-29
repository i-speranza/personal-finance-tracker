<template>
  <div class="data-management">
    <h2>Data Management</h2>
    
    <!-- Tab Navigation -->
    <div class="tabs">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        :class="['tab-btn', { active: activeTab === tab.id }]"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>
    
    <!-- Tab Content -->
    <div class="tab-content">
      <!-- Accounts Tab -->
      <div v-if="activeTab === 'accounts'" class="tab-panel">
        <div class="panel-header">
          <h3>Accounts</h3>
          <button class="btn btn-primary" @click="showAddAccountForm = !showAddAccountForm">
            {{ showAddAccountForm ? 'Cancel' : 'Add Account' }}
          </button>
        </div>
        
        <!-- Add Account Form -->
        <div v-if="showAddAccountForm" class="add-form">
          <div class="form-row">
            <div class="form-group">
              <label>Bank</label>
              <select v-model="newAccount.bank_name" @change="onBankSelectChange">
                <option value="">Select a bank...</option>
                <option v-for="bank in banks" :key="bank.id" :value="bank.name">
                  {{ bank.display_name }}
                </option>
                <option value="__new__">+ Add new bank...</option>
              </select>
            </div>
            <div class="form-group">
              <label>Account Name</label>
              <input type="text" v-model="newAccount.account_name" placeholder="e.g., Checking, Savings" />
            </div>
            <div class="form-group">
              <label>Asset Type</label>
              <select v-model="newAccount.asset_type">
                <option value="">Select type...</option>
                <option v-for="at in assetTypes" :key="at.id" :value="at.name">
                  {{ at.display_name }}
                </option>
              </select>
            </div>
            <button class="btn btn-success" @click="createAccount" :disabled="!canCreateAccount">
              Create Account
            </button>
          </div>
        </div>
        
        <!-- Add Bank Modal -->
        <div v-if="showAddBankModal" class="modal-overlay" @click.self="showAddBankModal = false">
          <div class="modal">
            <h4>Add New Bank</h4>
            <div class="form-group">
              <label>Bank ID (lowercase, no spaces)</label>
              <input type="text" v-model="newBank.name" placeholder="e.g., hsbc, revolut" />
            </div>
            <div class="form-group">
              <label>Display Name</label>
              <input type="text" v-model="newBank.display_name" placeholder="e.g., HSBC, Revolut" />
            </div>
            <div class="modal-actions">
              <button class="btn btn-secondary" @click="showAddBankModal = false">Cancel</button>
              <button class="btn btn-primary" @click="createBank" :disabled="!canCreateBank">Create Bank</button>
            </div>
          </div>
        </div>
        
        <!-- Accounts Table -->
        <div v-if="accountsLoading" class="loading">Loading accounts...</div>
        <div v-else-if="accountsError" class="error">{{ accountsError }}</div>
        <template v-else>
          <table class="data-table">
            <thead>
              <tr>
                <th>Bank</th>
                <th>Account Name</th>
                <th>Asset Type</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="account in sortedAccounts" 
                :key="account.id"
                :class="{ 'closed-row': !account.status }"
              >
                <td>{{ getBankDisplayName(account.bank_name) }}</td>
                <td>{{ account.account_name }}</td>
                <td>{{ getAssetTypeDisplayName(account.asset_type) }}</td>
                <td>
                  <button 
                    :class="['status-btn', account.status ? 'active' : 'closed']"
                    @click="toggleAccountStatus(account)"
                  >
                    {{ account.status ? 'Active' : 'Closed' }}
                  </button>
                </td>
              </tr>
              <tr v-if="sortedAccounts.length === 0">
                <td colspan="4" class="no-results">No accounts found</td>
              </tr>
            </tbody>
          </table>
        </template>
      </div>
      
      <!-- Asset Types Tab -->
      <div v-if="activeTab === 'assetTypes'" class="tab-panel">
        <div class="panel-header">
          <h3>Asset Types</h3>
        </div>
        
        <!-- Add Asset Type Form -->
        <div class="add-form">
          <div class="form-row">
            <div class="form-group">
              <label>Type ID (lowercase)</label>
              <input type="text" v-model="newAssetType.name" placeholder="e.g., crypto, real_estate" />
            </div>
            <div class="form-group">
              <label>Display Name</label>
              <input type="text" v-model="newAssetType.display_name" placeholder="e.g., Crypto, Real Estate" />
            </div>
            <button class="btn btn-success" @click="createAssetType" :disabled="!canCreateAssetType">
              Add Asset Type
            </button>
          </div>
        </div>
        
        <!-- Asset Types Table -->
        <div v-if="assetTypesLoading" class="loading">Loading asset types...</div>
        <div v-else-if="assetTypesError" class="error">{{ assetTypesError }}</div>
        <template v-else>
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Display Name</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="at in assetTypes" :key="at.id">
                <td>{{ at.id }}</td>
                <td>{{ at.name }}</td>
                <td>{{ at.display_name }}</td>
                <td>
                  <button 
                    class="btn btn-danger btn-sm"
                    @click="deleteAssetType(at)"
                    :disabled="isAssetTypeInUse(at.name)"
                    :title="isAssetTypeInUse(at.name) ? 'Cannot delete: type is in use' : 'Delete'"
                  >
                    Delete
                  </button>
                </td>
              </tr>
              <tr v-if="assetTypes.length === 0">
                <td colspan="4" class="no-results">No asset types found</td>
              </tr>
            </tbody>
          </table>
        </template>
      </div>
      
      <!-- Transactions Tab -->
      <div v-if="activeTab === 'transactions'" class="tab-panel">
        <div class="panel-header">
          <h3>Transactions</h3>
          <div class="header-actions">
            <button 
              class="btn btn-secondary btn-sm"
              @click="clearTransactionFilters"
              v-if="hasActiveTransactionFilters"
            >
              Clear Filters
            </button>
            <span v-if="pendingTransactionChanges.size > 0" class="pending-count">
              {{ pendingTransactionChanges.size }} pending change(s)
            </span>
            <button 
              class="btn btn-success"
              @click="showTransactionConfirmModal = true"
              :disabled="pendingTransactionChanges.size === 0"
            >
              Save Changes
            </button>
          </div>
        </div>
        
        <!-- Transactions Table -->
        <div v-if="transactionsLoading" class="loading">Loading transactions...</div>
        <div v-else-if="transactionsError" class="error">{{ transactionsError }}</div>
        <template v-else>
          <div class="table-info">
            <span>
              Showing {{ txTable.getRowModel().rows.length }} of {{ transactions.length }} transactions
              <template v-if="txTable.getFilteredRowModel().rows.length !== transactions.length">
                ({{ txTable.getFilteredRowModel().rows.length }} filtered)
              </template>
            </span>
          </div>
          
          <div class="table-container">
            <table class="data-table transactions-table">
              <thead>
                <tr>
                  <th 
                    v-for="header in txTable.getHeaderGroups()[0].headers" 
                    :key="header.id"
                    :class="{ sortable: header.column.getCanSort() }"
                    @click="header.column.getCanSort() ? header.column.toggleSorting() : null"
                  >
                    <div class="th-content">
                      <span>{{ header.column.columnDef.header }}</span>
                      <span v-if="header.column.getIsSorted()" class="sort-indicator">
                        {{ header.column.getIsSorted() === 'asc' ? '↑' : '↓' }}
                      </span>
                    </div>
                  </th>
                </tr>
                <tr class="filter-row">
                  <th v-for="header in txTable.getHeaderGroups()[0].headers" :key="header.id + '-filter'">
                    <!-- Date filter -->
                    <template v-if="header.column.id === 'date'">
                      <input 
                        type="date" 
                        :value="(header.column.getFilterValue() as string) ?? ''"
                        @input="header.column.setFilterValue(($event.target as HTMLInputElement).value || undefined)"
                        class="filter-input filter-date"
                        placeholder="Filter date..."
                      />
                    </template>
                    <!-- Select filters for Bank, Account, Type -->
                    <template v-else-if="['bank_name', 'account_name', 'transaction_type'].includes(header.column.id)">
                      <select 
                        :value="(header.column.getFilterValue() as string) ?? ''"
                        @change="header.column.setFilterValue(($event.target as HTMLSelectElement).value || undefined)"
                        class="filter-select"
                      >
                        <option value="">All</option>
                        <option 
                          v-for="option in getColumnUniqueValues(header.column.id)" 
                          :key="option" 
                          :value="option"
                        >
                          {{ header.column.id === 'bank_name' ? getBankDisplayName(option) : option || '(empty)' }}
                        </option>
                      </select>
                    </template>
                    <!-- Amount range filter -->
                    <template v-else-if="header.column.id === 'amount'">
                      <select 
                        :value="(header.column.getFilterValue() as string) ?? ''"
                        @change="header.column.setFilterValue(($event.target as HTMLSelectElement).value || undefined)"
                        class="filter-select"
                      >
                        <option value="">All</option>
                        <option value="positive">Positive</option>
                        <option value="negative">Negative</option>
                      </select>
                    </template>
                    <!-- Text filter for Description -->
                    <template v-else-if="header.column.id === 'description'">
                      <input 
                        type="text" 
                        :value="(header.column.getFilterValue() as string) ?? ''"
                        @input="header.column.setFilterValue(($event.target as HTMLInputElement).value || undefined)"
                        class="filter-input"
                        placeholder="Search..."
                      />
                    </template>
                    <!-- Special checkbox filter -->
                    <template v-else-if="header.column.id === 'is_special'">
                      <select 
                        :value="(header.column.getFilterValue() as string) ?? ''"
                        @change="header.column.setFilterValue(($event.target as HTMLSelectElement).value || undefined)"
                        class="filter-select"
                      >
                        <option value="">All</option>
                        <option value="true">Special</option>
                        <option value="false">Normal</option>
                      </select>
                    </template>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr 
                  v-for="row in txTable.getRowModel().rows" 
                  :key="row.original.id"
                  :class="{ 'modified-row': pendingTransactionChanges.has(row.original.id) }"
                >
                  <td>{{ row.original.date }}</td>
                  <td>{{ getBankDisplayName(row.original.bank_name) }}</td>
                  <td>{{ row.original.account_name }}</td>
                  <td :class="row.original.amount >= 0 ? 'positive' : 'negative'">
                    {{ formatAmount(row.original.amount) }}
                  </td>
                  <td class="description-cell" :title="row.original.description || ''">
                    {{ truncate(row.original.description || '-', 40) }}
                  </td>
                  <td>
                    <select 
                      :value="getTransactionFieldValue(row.original.id, 'transaction_type', row.original.transaction_type)"
                      @change="onTransactionTypeChange(row.original, $event)"
                      class="inline-select"
                    >
                      <option value="">None</option>
                      <option v-for="type in transactionTypes" :key="type" :value="type">
                        {{ type }}
                      </option>
                      <option value="__new__">+ Add new...</option>
                    </select>
                  </td>
                  <td>
                    <input 
                      type="checkbox"
                      :checked="getTransactionFieldValue(row.original.id, 'is_special', row.original.is_special)"
                      @change="onTransactionSpecialChange(row.original, $event)"
                    />
                  </td>
                </tr>
                <tr v-if="txTable.getRowModel().rows.length === 0">
                  <td colspan="7" class="no-results">No transactions found</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- Pagination -->
          <div class="pagination">
            <div class="pagination-info">
              <select 
                :value="txTable.getState().pagination.pageSize"
                @change="txTable.setPageSize(Number(($event.target as HTMLSelectElement).value))"
                class="page-size-select"
              >
                <option :value="25">25 per page</option>
                <option :value="50">50 per page</option>
                <option :value="100">100 per page</option>
                <option :value="250">250 per page</option>
              </select>
            </div>
            <div class="pagination-controls">
              <button 
                class="btn btn-secondary btn-sm"
                @click="txTable.setPageIndex(0)"
                :disabled="!txTable.getCanPreviousPage()"
              >
                First
              </button>
              <button 
                class="btn btn-secondary btn-sm"
                @click="txTable.previousPage()"
                :disabled="!txTable.getCanPreviousPage()"
              >
                Previous
              </button>
              <span class="page-info">
                Page {{ txTable.getState().pagination.pageIndex + 1 }} of {{ txTable.getPageCount() }}
              </span>
              <button 
                class="btn btn-secondary btn-sm"
                @click="txTable.nextPage()"
                :disabled="!txTable.getCanNextPage()"
              >
                Next
              </button>
              <button 
                class="btn btn-secondary btn-sm"
                @click="txTable.setPageIndex(txTable.getPageCount() - 1)"
                :disabled="!txTable.getCanNextPage()"
              >
                Last
              </button>
            </div>
          </div>
        </template>
        
        <!-- Add Transaction Type Modal -->
        <div v-if="showAddTransactionTypeModal" class="modal-overlay" @click.self="cancelAddTransactionType">
          <div class="modal">
            <h4>Add New Transaction Type</h4>
            <div class="form-group">
              <label>Type Name</label>
              <input type="text" v-model="newTransactionType" placeholder="e.g., Salary, Groceries" />
            </div>
            <div class="modal-actions">
              <button class="btn btn-secondary" @click="cancelAddTransactionType">Cancel</button>
              <button class="btn btn-primary" @click="confirmAddTransactionType" :disabled="!newTransactionType.trim()">Add</button>
            </div>
          </div>
        </div>
        
        <!-- Save Confirmation Modal -->
        <div v-if="showTransactionConfirmModal" class="modal-overlay" @click.self="showTransactionConfirmModal = false">
          <div class="modal">
            <h4>Confirm Changes</h4>
            <p>Save {{ pendingTransactionChanges.size }} transaction change(s)?</p>
            <div class="modal-actions">
              <button class="btn btn-secondary" @click="showTransactionConfirmModal = false">Cancel</button>
              <button class="btn btn-success" @click="saveTransactionChanges">Confirm</button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Assets History Tab -->
      <div v-if="activeTab === 'assetsHistory'" class="tab-panel">
        <div class="panel-header">
          <h3>Assets History</h3>
          <div class="header-actions">
            <button 
              class="btn btn-secondary btn-sm"
              @click="clearAssetsFilters"
              v-if="hasActiveAssetsFilters"
            >
              Clear Filters
            </button>
            <span v-if="pendingAssetsChanges.size > 0" class="pending-count">
              {{ pendingAssetsChanges.size }} pending change(s)
            </span>
            <button 
              class="btn btn-success"
              @click="showAssetsConfirmModal = true"
              :disabled="pendingAssetsChanges.size === 0"
            >
              Save Changes
            </button>
          </div>
        </div>
        
        <!-- Assets History Table -->
        <div v-if="assetsLoading" class="loading">Loading assets history...</div>
        <div v-else-if="assetsError" class="error">{{ assetsError }}</div>
        <template v-else>
          <div class="table-info">
            <span>
              Showing {{ assetsTable.getRowModel().rows.length }} of {{ assetsHistory.length }} assets
              <template v-if="assetsTable.getFilteredRowModel().rows.length !== assetsHistory.length">
                ({{ assetsTable.getFilteredRowModel().rows.length }} filtered)
              </template>
            </span>
          </div>
          
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th 
                    v-for="header in assetsTable.getHeaderGroups()[0].headers" 
                    :key="header.id"
                    :class="{ sortable: header.column.getCanSort() }"
                    @click="header.column.getCanSort() ? header.column.toggleSorting() : null"
                  >
                    <div class="th-content">
                      <span>{{ header.column.columnDef.header }}</span>
                      <span v-if="header.column.getIsSorted()" class="sort-indicator">
                        {{ header.column.getIsSorted() === 'asc' ? '↑' : '↓' }}
                      </span>
                    </div>
                  </th>
                </tr>
                <tr class="filter-row">
                  <th v-for="header in assetsTable.getHeaderGroups()[0].headers" :key="header.id + '-filter'">
                    <!-- Date filter -->
                    <template v-if="header.column.id === 'date'">
                      <input 
                        type="date" 
                        :value="(header.column.getFilterValue() as string) ?? ''"
                        @input="header.column.setFilterValue(($event.target as HTMLInputElement).value || undefined)"
                        class="filter-input filter-date"
                        placeholder="Filter date..."
                      />
                    </template>
                    <!-- Select filters for Bank, Account, Asset Type -->
                    <template v-else-if="['bank_name', 'account_name', 'asset_type'].includes(header.column.id)">
                      <select 
                        :value="(header.column.getFilterValue() as string) ?? ''"
                        @change="header.column.setFilterValue(($event.target as HTMLSelectElement).value || undefined)"
                        class="filter-select"
                      >
                        <option value="">All</option>
                        <option 
                          v-for="option in getAssetsColumnUniqueValues(header.column.id)" 
                          :key="option" 
                          :value="option"
                        >
                          {{ header.column.id === 'bank_name' 
                            ? getBankDisplayName(option) 
                            : header.column.id === 'asset_type' 
                              ? getAssetTypeDisplayName(option)
                              : option || '(empty)' 
                          }}
                        </option>
                      </select>
                    </template>
                    <!-- Amount - no filter, just placeholder -->
                    <template v-else-if="header.column.id === 'amount'">
                      <span class="filter-placeholder">-</span>
                    </template>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr 
                  v-for="row in assetsTable.getRowModel().rows" 
                  :key="row.original.id"
                  :class="{ 'modified-row': pendingAssetsChanges.has(row.original.id) }"
                >
                  <td>{{ row.original.date }}</td>
                  <td>{{ getBankDisplayName(row.original.bank_name) }}</td>
                  <td>{{ row.original.account_name }}</td>
                  <td>{{ getAssetTypeDisplayName(row.original.asset_type) }}</td>
                  <td>
                    <input 
                      type="number"
                      :value="getAssetFieldValue(row.original.id, 'amount', row.original.amount)"
                      @change="onAssetAmountChange(row.original, $event)"
                      class="inline-input"
                      step="0.01"
                    />
                  </td>
                </tr>
                <tr v-if="assetsTable.getRowModel().rows.length === 0">
                  <td colspan="5" class="no-results">No assets found</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- Pagination -->
          <div class="pagination">
            <div class="pagination-info">
              <select 
                :value="assetsTable.getState().pagination.pageSize"
                @change="assetsTable.setPageSize(Number(($event.target as HTMLSelectElement).value))"
                class="page-size-select"
              >
                <option :value="25">25 per page</option>
                <option :value="50">50 per page</option>
                <option :value="100">100 per page</option>
                <option :value="250">250 per page</option>
              </select>
            </div>
            <div class="pagination-controls">
              <button 
                class="btn btn-secondary btn-sm"
                @click="assetsTable.setPageIndex(0)"
                :disabled="!assetsTable.getCanPreviousPage()"
              >
                First
              </button>
              <button 
                class="btn btn-secondary btn-sm"
                @click="assetsTable.previousPage()"
                :disabled="!assetsTable.getCanPreviousPage()"
              >
                Previous
              </button>
              <span class="page-info">
                Page {{ assetsTable.getState().pagination.pageIndex + 1 }} of {{ assetsTable.getPageCount() }}
              </span>
              <button 
                class="btn btn-secondary btn-sm"
                @click="assetsTable.nextPage()"
                :disabled="!assetsTable.getCanNextPage()"
              >
                Next
              </button>
              <button 
                class="btn btn-secondary btn-sm"
                @click="assetsTable.setPageIndex(assetsTable.getPageCount() - 1)"
                :disabled="!assetsTable.getCanNextPage()"
              >
                Last
              </button>
            </div>
          </div>
        </template>
        
        <!-- Save Confirmation Modal -->
        <div v-if="showAssetsConfirmModal" class="modal-overlay" @click.self="showAssetsConfirmModal = false">
          <div class="modal">
            <h4>Confirm Changes</h4>
            <p>Save {{ pendingAssetsChanges.size }} assets history change(s)?</p>
            <div class="modal-actions">
              <button class="btn btn-secondary" @click="showAssetsConfirmModal = false">Cancel</button>
              <button class="btn btn-success" @click="saveAssetsChanges">Confirm</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { api } from '@/api/client';
import type { Account, Bank, Transaction, AssetsHistory, AssetTypeRef } from '@/types';
import {
  useVueTable,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  createColumnHelper,
  type ColumnFiltersState,
  type SortingState,
  type FilterFn,
} from '@tanstack/vue-table';

// Tab configuration
const tabs = [
  { id: 'accounts', label: 'Accounts' },
  { id: 'assetTypes', label: 'Asset Types' },
  { id: 'transactions', label: 'Transactions' },
  { id: 'assetsHistory', label: 'Assets History' },
];
const activeTab = ref('accounts');

// ============ ACCOUNTS TAB ============
const accounts = ref<Account[]>([]);
const banks = ref<Bank[]>([]);
const accountsLoading = ref(false);
const accountsError = ref<string | null>(null);
const showAddAccountForm = ref(false);
const showAddBankModal = ref(false);

const newAccount = ref({
  bank_name: '',
  account_name: '',
  asset_type: '',
});

const newBank = ref({
  name: '',
  display_name: '',
});

// Sorted accounts: active first, then by bank, then by account name
const sortedAccounts = computed(() => {
  return [...accounts.value].sort((a, b) => {
    if (a.status !== b.status) return a.status ? -1 : 1;
    const bankCompare = a.bank_name.localeCompare(b.bank_name);
    if (bankCompare !== 0) return bankCompare;
    return a.account_name.localeCompare(b.account_name);
  });
});

const canCreateAccount = computed(() => {
  return newAccount.value.bank_name && 
         newAccount.value.bank_name !== '__new__' &&
         newAccount.value.account_name.trim() && 
         newAccount.value.asset_type;
});

const canCreateBank = computed(() => {
  return newBank.value.name.trim() && newBank.value.display_name.trim();
});

function getBankDisplayName(bankName: string): string {
  const bank = banks.value.find(b => b.name === bankName);
  return bank?.display_name || bankName;
}

function onBankSelectChange() {
  if (newAccount.value.bank_name === '__new__') {
    showAddBankModal.value = true;
    newAccount.value.bank_name = '';
  }
}

async function fetchAccounts() {
  accountsLoading.value = true;
  accountsError.value = null;
  try {
    accounts.value = await api.accounts.getAll();
  } catch (err) {
    accountsError.value = err instanceof Error ? err.message : 'Failed to load accounts';
  } finally {
    accountsLoading.value = false;
  }
}

async function fetchBanks() {
  try {
    banks.value = await api.banks.getAll();
  } catch (err) {
    console.error('Failed to load banks:', err);
  }
}

async function createAccount() {
  if (!canCreateAccount.value) return;
  try {
    await api.accounts.create({
      bank_name: newAccount.value.bank_name,
      account_name: newAccount.value.account_name.trim(),
      asset_type: newAccount.value.asset_type as any,
      status: true,
    });
    newAccount.value = { bank_name: '', account_name: '', asset_type: '' };
    showAddAccountForm.value = false;
    await fetchAccounts();
  } catch (err) {
    alert(err instanceof Error ? err.message : 'Failed to create account');
  }
}

async function createBank() {
  if (!canCreateBank.value) return;
  try {
    const created = await api.banks.create({
      name: newBank.value.name.trim().toLowerCase(),
      display_name: newBank.value.display_name.trim(),
    });
    showAddBankModal.value = false;
    newBank.value = { name: '', display_name: '' };
    await fetchBanks();
    newAccount.value.bank_name = created.name;
  } catch (err) {
    alert(err instanceof Error ? err.message : 'Failed to create bank');
  }
}

async function toggleAccountStatus(account: Account) {
  const newStatus = !account.status;
  const action = newStatus ? 'reactivate' : 'close';
  if (!confirm(`Are you sure you want to ${action} this account?`)) return;
  
  try {
    await api.accounts.update(account.id, { status: newStatus });
    await fetchAccounts();
  } catch (err) {
    alert(err instanceof Error ? err.message : 'Failed to update account');
  }
}

// ============ ASSET TYPES TAB ============
const assetTypes = ref<AssetTypeRef[]>([]);
const assetTypesLoading = ref(false);
const assetTypesError = ref<string | null>(null);

const newAssetType = ref({
  name: '',
  display_name: '',
});

const canCreateAssetType = computed(() => {
  return newAssetType.value.name.trim() && newAssetType.value.display_name.trim();
});

function getAssetTypeDisplayName(assetType: string | null): string {
  if (!assetType) return '-';
  const at = assetTypes.value.find(a => a.name === assetType);
  return at?.display_name || assetType;
}

function isAssetTypeInUse(name: string): boolean {
  return accounts.value.some(a => a.asset_type === name) ||
         assetsHistory.value.some(ah => ah.asset_type === name);
}

async function fetchAssetTypes() {
  assetTypesLoading.value = true;
  assetTypesError.value = null;
  try {
    assetTypes.value = await api.assetTypes.getAll();
  } catch (err) {
    assetTypesError.value = err instanceof Error ? err.message : 'Failed to load asset types';
  } finally {
    assetTypesLoading.value = false;
  }
}

async function createAssetType() {
  if (!canCreateAssetType.value) return;
  try {
    await api.assetTypes.create({
      name: newAssetType.value.name.trim().toLowerCase(),
      display_name: newAssetType.value.display_name.trim(),
    });
    newAssetType.value = { name: '', display_name: '' };
    await fetchAssetTypes();
  } catch (err) {
    alert(err instanceof Error ? err.message : 'Failed to create asset type');
  }
}

async function deleteAssetType(assetType: AssetTypeRef) {
  if (!confirm(`Are you sure you want to delete "${assetType.display_name}"?`)) return;
  try {
    await api.assetTypes.delete(assetType.id);
    await fetchAssetTypes();
  } catch (err) {
    alert(err instanceof Error ? err.message : 'Failed to delete asset type');
  }
}

// ============ TRANSACTIONS TAB ============
const transactions = ref<Transaction[]>([]);
const transactionTypes = ref<string[]>([]);
const transactionsLoading = ref(false);
const transactionsError = ref<string | null>(null);
const pendingTransactionChanges = ref(new Map<number, Partial<Transaction>>());
const showTransactionConfirmModal = ref(false);
const showAddTransactionTypeModal = ref(false);
const newTransactionType = ref('');
const pendingTransactionTypeTarget = ref<{ tx: Transaction; event: Event } | null>(null);

// TanStack Table state for transactions
const txColumnFilters = ref<ColumnFiltersState>([]);
const txSorting = ref<SortingState>([{ id: 'date', desc: true }]);

// Custom filter functions
const amountFilterFn: FilterFn<Transaction> = (row, columnId, filterValue) => {
  const amount = row.getValue(columnId) as number;
  if (filterValue === 'positive') return amount >= 0;
  if (filterValue === 'negative') return amount < 0;
  return true;
};

const booleanFilterFn: FilterFn<Transaction> = (row, columnId, filterValue) => {
  const value = row.getValue(columnId) as boolean;
  if (filterValue === 'true') return value === true;
  if (filterValue === 'false') return value === false;
  return true;
};

const dateFilterFn: FilterFn<Transaction> = (row, columnId, filterValue) => {
  if (!filterValue) return true;
  const rowDate = row.getValue(columnId) as string;
  return rowDate.startsWith(filterValue);
};

// Column helper for transactions
const txColumnHelper = createColumnHelper<Transaction>();

const txColumns = [
  txColumnHelper.accessor('date', {
    header: 'Date',
    filterFn: dateFilterFn,
  }),
  txColumnHelper.accessor('bank_name', {
    header: 'Bank',
    filterFn: 'equals',
  }),
  txColumnHelper.accessor('account_name', {
    header: 'Account',
    filterFn: 'equals',
  }),
  txColumnHelper.accessor('amount', {
    header: 'Amount',
    filterFn: amountFilterFn,
  }),
  txColumnHelper.accessor('description', {
    header: 'Description',
    filterFn: 'includesString',
  }),
  txColumnHelper.accessor('transaction_type', {
    header: 'Type',
    filterFn: 'equals',
  }),
  txColumnHelper.accessor('is_special', {
    header: 'Special',
    filterFn: booleanFilterFn,
    enableSorting: false,
  }),
];

// TanStack Table for transactions
const txTable = useVueTable({
  get data() { return transactions.value; },
  columns: txColumns,
  state: {
    get columnFilters() { return txColumnFilters.value; },
    get sorting() { return txSorting.value; },
  },
  onColumnFiltersChange: (updater) => {
    txColumnFilters.value = typeof updater === 'function' 
      ? updater(txColumnFilters.value) 
      : updater;
  },
  onSortingChange: (updater) => {
    txSorting.value = typeof updater === 'function' 
      ? updater(txSorting.value) 
      : updater;
  },
  getCoreRowModel: getCoreRowModel(),
  getFilteredRowModel: getFilteredRowModel(),
  getSortedRowModel: getSortedRowModel(),
  getPaginationRowModel: getPaginationRowModel(),
  initialState: {
    pagination: { pageSize: 50 },
  },
});

// Get unique values for dropdown filters
function getColumnUniqueValues(columnId: string): string[] {
  const values = new Set<string>();
  transactions.value.forEach(tx => {
    const value = tx[columnId as keyof Transaction];
    if (value !== null && value !== undefined) {
      values.add(String(value));
    } else if (columnId === 'transaction_type') {
      values.add('');
    }
  });
  return Array.from(values).sort();
}

const hasActiveTransactionFilters = computed(() => {
  return txColumnFilters.value.length > 0;
});

function clearTransactionFilters() {
  txColumnFilters.value = [];
}

function formatAmount(amount: number): string {
  return amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function truncate(text: string, length: number): string {
  if (text.length <= length) return text;
  return text.substring(0, length) + '...';
}

function getTransactionFieldValue<K extends keyof Transaction>(
  txId: number, 
  field: K, 
  originalValue: Transaction[K]
): Transaction[K] {
  const pending = pendingTransactionChanges.value.get(txId);
  if (pending && field in pending) {
    return pending[field] as Transaction[K];
  }
  return originalValue;
}

function onTransactionTypeChange(tx: Transaction, event: Event) {
  const value = (event.target as HTMLSelectElement).value;
  if (value === '__new__') {
    pendingTransactionTypeTarget.value = { tx, event };
    showAddTransactionTypeModal.value = true;
    // Reset the select to previous value
    (event.target as HTMLSelectElement).value = tx.transaction_type || '';
    return;
  }
  updateTransactionField(tx, 'transaction_type', value || null);
}

function onTransactionSpecialChange(tx: Transaction, event: Event) {
  const value = (event.target as HTMLInputElement).checked;
  updateTransactionField(tx, 'is_special', value);
}

function updateTransactionField<K extends keyof Transaction>(tx: Transaction, field: K, value: Transaction[K]) {
  const pending = pendingTransactionChanges.value.get(tx.id) || {};
  const originalValue = tx[field];
  
  if (value === originalValue) {
    // Remove the field from pending if it matches original
    delete pending[field];
    if (Object.keys(pending).length === 0) {
      pendingTransactionChanges.value.delete(tx.id);
    } else {
      pendingTransactionChanges.value.set(tx.id, pending);
    }
  } else {
    pending[field] = value;
    pendingTransactionChanges.value.set(tx.id, pending);
  }
  // Trigger reactivity
  pendingTransactionChanges.value = new Map(pendingTransactionChanges.value);
}

function cancelAddTransactionType() {
  showAddTransactionTypeModal.value = false;
  newTransactionType.value = '';
  pendingTransactionTypeTarget.value = null;
}

function confirmAddTransactionType() {
  if (!newTransactionType.value.trim()) return;
  
  const typeName = newTransactionType.value.trim();
  if (!transactionTypes.value.includes(typeName)) {
    transactionTypes.value = [...transactionTypes.value, typeName].sort();
  }
  
  if (pendingTransactionTypeTarget.value) {
    updateTransactionField(pendingTransactionTypeTarget.value.tx, 'transaction_type', typeName);
  }
  
  cancelAddTransactionType();
}

async function fetchTransactions() {
  transactionsLoading.value = true;
  transactionsError.value = null;
  try {
    transactions.value = await api.transactions.getAll();
  } catch (err) {
    transactionsError.value = err instanceof Error ? err.message : 'Failed to load transactions';
  } finally {
    transactionsLoading.value = false;
  }
}

async function fetchTransactionTypes() {
  try {
    transactionTypes.value = await api.transactions.getTypes();
  } catch (err) {
    console.error('Failed to load transaction types:', err);
  }
}

async function saveTransactionChanges() {
  showTransactionConfirmModal.value = false;
  
  const changes = Array.from(pendingTransactionChanges.value.entries());
  let successCount = 0;
  let errorCount = 0;
  
  for (const [txId, update] of changes) {
    try {
      await api.transactions.update(txId, update);
      successCount++;
    } catch (err) {
      console.error(`Failed to update transaction ${txId}:`, err);
      errorCount++;
    }
  }
  
  pendingTransactionChanges.value = new Map();
  
  if (errorCount > 0) {
    alert(`Saved ${successCount} changes. ${errorCount} failed.`);
  }
  
  await fetchTransactions();
  await fetchTransactionTypes();
}

// ============ ASSETS HISTORY TAB ============
const assetsHistory = ref<AssetsHistory[]>([]);
const assetsLoading = ref(false);
const assetsError = ref<string | null>(null);
const pendingAssetsChanges = ref(new Map<number, { amount: number }>());
const showAssetsConfirmModal = ref(false);

// TanStack Table state for assets history
const assetsColumnFilters = ref<ColumnFiltersState>([]);
const assetsSorting = ref<SortingState>([{ id: 'date', desc: true }]);

// Custom filter functions for assets
const assetsDateFilterFn: FilterFn<AssetsHistory> = (row, columnId, filterValue) => {
  if (!filterValue) return true;
  const rowDate = row.getValue(columnId) as string;
  return rowDate.startsWith(filterValue);
};

// Column helper for assets history
const assetsColumnHelper = createColumnHelper<AssetsHistory>();

const assetsColumns = [
  assetsColumnHelper.accessor('date', {
    header: 'Date',
    filterFn: assetsDateFilterFn,
  }),
  assetsColumnHelper.accessor('bank_name', {
    header: 'Bank',
    filterFn: 'equals',
  }),
  assetsColumnHelper.accessor('account_name', {
    header: 'Account',
    filterFn: 'equals',
  }),
  assetsColumnHelper.accessor('asset_type', {
    header: 'Asset Type',
    filterFn: 'equals',
  }),
  assetsColumnHelper.accessor('amount', {
    header: 'Amount',
    enableColumnFilter: false,
  }),
];

// TanStack Table for assets history
const assetsTable = useVueTable({
  get data() { return assetsHistory.value; },
  columns: assetsColumns,
  state: {
    get columnFilters() { return assetsColumnFilters.value; },
    get sorting() { return assetsSorting.value; },
  },
  onColumnFiltersChange: (updater) => {
    assetsColumnFilters.value = typeof updater === 'function' 
      ? updater(assetsColumnFilters.value) 
      : updater;
  },
  onSortingChange: (updater) => {
    assetsSorting.value = typeof updater === 'function' 
      ? updater(assetsSorting.value) 
      : updater;
  },
  getCoreRowModel: getCoreRowModel(),
  getFilteredRowModel: getFilteredRowModel(),
  getSortedRowModel: getSortedRowModel(),
  getPaginationRowModel: getPaginationRowModel(),
  initialState: {
    pagination: { pageSize: 50 },
  },
});

// Get unique values for assets dropdown filters
function getAssetsColumnUniqueValues(columnId: string): string[] {
  const values = new Set<string>();
  assetsHistory.value.forEach(asset => {
    const value = asset[columnId as keyof AssetsHistory];
    if (value !== null && value !== undefined) {
      values.add(String(value));
    }
  });
  return Array.from(values).sort();
}

const hasActiveAssetsFilters = computed(() => {
  return assetsColumnFilters.value.length > 0;
});

function clearAssetsFilters() {
  assetsColumnFilters.value = [];
}

function getAssetFieldValue(assetId: number, field: 'amount', originalValue: number): number {
  const pending = pendingAssetsChanges.value.get(assetId);
  if (pending && field in pending) {
    return pending[field];
  }
  return originalValue;
}

function onAssetAmountChange(asset: AssetsHistory, event: Event) {
  const value = parseFloat((event.target as HTMLInputElement).value);
  if (isNaN(value)) return;
  
  if (value === asset.amount) {
    pendingAssetsChanges.value.delete(asset.id);
  } else {
    pendingAssetsChanges.value.set(asset.id, { amount: value });
  }
  // Trigger reactivity
  pendingAssetsChanges.value = new Map(pendingAssetsChanges.value);
}

async function fetchAssetsHistory() {
  assetsLoading.value = true;
  assetsError.value = null;
  try {
    assetsHistory.value = await api.assetsHistory.getAll();
  } catch (err) {
    assetsError.value = err instanceof Error ? err.message : 'Failed to load assets history';
  } finally {
    assetsLoading.value = false;
  }
}

async function saveAssetsChanges() {
  showAssetsConfirmModal.value = false;
  
  const changes = Array.from(pendingAssetsChanges.value.entries());
  let successCount = 0;
  let errorCount = 0;
  
  for (const [assetId, update] of changes) {
    try {
      await api.assetsHistory.update(assetId, update);
      successCount++;
    } catch (err) {
      console.error(`Failed to update asset ${assetId}:`, err);
      errorCount++;
    }
  }
  
  pendingAssetsChanges.value = new Map();
  
  if (errorCount > 0) {
    alert(`Saved ${successCount} changes. ${errorCount} failed.`);
  }
  
  await fetchAssetsHistory();
}

// ============ LIFECYCLE ============
onMounted(async () => {
  // Load initial data for all tabs
  await Promise.all([
    fetchAccounts(),
    fetchBanks(),
    fetchAssetTypes(),
    fetchTransactions(),
    fetchTransactionTypes(),
    fetchAssetsHistory(),
  ]);
});

// Watch for tab changes to refresh data
watch(activeTab, async (newTab) => {
  if (newTab === 'accounts') {
    await Promise.all([fetchAccounts(), fetchBanks()]);
  } else if (newTab === 'assetTypes') {
    await fetchAssetTypes();
  } else if (newTab === 'transactions') {
    await Promise.all([fetchTransactions(), fetchTransactionTypes()]);
  } else if (newTab === 'assetsHistory') {
    await fetchAssetsHistory();
  }
});
</script>

<style scoped>
.data-management {
  padding: 20px;
}

h2 {
  margin-top: 0;
  margin-bottom: 20px;
}

h3 {
  margin: 0;
}

h4 {
  margin-top: 0;
  margin-bottom: 15px;
}

/* Tabs */
.tabs {
  display: flex;
  gap: 5px;
  margin-bottom: 20px;
  border-bottom: 2px solid #e0e0e0;
  padding-bottom: 0;
}

.tab-btn {
  padding: 10px 20px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 1em;
  color: #666;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: #007bff;
}

.tab-btn.active {
  color: #007bff;
  border-bottom-color: #007bff;
  font-weight: 600;
}

/* Tab Content */
.tab-content {
  background: #fff;
}

.tab-panel {
  padding: 20px 0;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.pending-count {
  color: #856404;
  background: #fff3cd;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 0.9em;
}

/* Forms */
.add-form {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.form-row {
  display: flex;
  gap: 15px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 150px;
}

.form-group label {
  font-size: 0.9em;
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.95em;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

/* Buttons */
.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.95em;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #0056b3;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #545b62;
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #1e7e34;
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #c82333;
}

.btn-sm {
  padding: 5px 10px;
  font-size: 0.85em;
}

/* Status Button */
.status-btn {
  padding: 4px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85em;
  font-weight: 500;
}

.status-btn.active {
  background: #d4edda;
  color: #155724;
}

.status-btn.active:hover {
  background: #c3e6cb;
}

.status-btn.closed {
  background: #f8d7da;
  color: #721c24;
}

.status-btn.closed:hover {
  background: #f5c6cb;
}

/* Tables */
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95em;
}

.data-table th,
.data-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.data-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #333;
  position: sticky;
  top: 0;
}

.data-table tbody tr:hover {
  background: #f5f5f5;
}

.data-table .closed-row {
  background: #f0f0f0;
  color: #666;
}

.data-table .closed-row:hover {
  background: #e8e8e8;
}

.data-table .modified-row {
  background: #fff3cd;
}

.data-table .modified-row:hover {
  background: #ffe69c;
}

.data-table .positive {
  color: #28a745;
}

.data-table .negative {
  color: #dc3545;
}

.description-cell {
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Table Info */
.table-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 4px;
  font-size: 0.9em;
  color: #666;
}

/* No Results */
.no-results {
  text-align: center;
  color: #666;
  font-style: italic;
  padding: 20px !important;
}

/* Inline Edit Controls */
.inline-select {
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9em;
  min-width: 120px;
}

.inline-input {
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9em;
  width: 120px;
}

/* Pagination */
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  margin-top: 15px;
  padding: 10px 0;
}

.pagination-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-size-select {
  padding: 6px 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9em;
  background: white;
}

.page-info {
  color: #666;
  font-size: 0.9em;
  min-width: 120px;
  text-align: center;
}

/* Table container for horizontal scroll */
.table-container {
  overflow-x: auto;
  margin-bottom: 10px;
}

/* Filter row */
.filter-row th {
  background: #f0f4f8;
  padding: 8px;
  border-bottom: 2px solid #ddd;
}

.filter-input {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.85em;
  box-sizing: border-box;
}

.filter-input:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.15);
}

.filter-date {
  min-width: 130px;
}

.filter-select {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.85em;
  background: white;
  box-sizing: border-box;
}

.filter-select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.15);
}

.filter-placeholder {
  color: #999;
  font-size: 0.85em;
}

/* Sortable columns */
.sortable {
  cursor: pointer;
  user-select: none;
}

.sortable:hover {
  background: #e9ecef;
}

.th-content {
  display: flex;
  align-items: center;
  gap: 6px;
}

.sort-indicator {
  color: #007bff;
  font-weight: bold;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  padding: 25px;
  border-radius: 8px;
  min-width: 350px;
  max-width: 500px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal .form-group {
  margin-bottom: 15px;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
}

/* Loading and Error States */
.loading {
  padding: 40px;
  text-align: center;
  color: #0066cc;
  background: #e7f3ff;
  border-radius: 8px;
}

.error {
  padding: 20px;
  text-align: center;
  color: #721c24;
  background: #f8d7da;
  border-radius: 8px;
}

/* Responsive */
@media (max-width: 768px) {
  .tabs {
    flex-wrap: wrap;
  }
  
  .form-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .form-group {
    width: 100%;
  }
  
  .panel-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .data-table {
    display: block;
    overflow-x: auto;
  }
}
</style>
