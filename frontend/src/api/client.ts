import type {
  Transaction,
  TransactionCreate,
  TransactionUpdate,
  InvestmentProduct,
  InvestmentProductCreate,
  InvestmentProductUpdate,
  SIPPlan,
  SIPPlanCreate,
  SIPPlanUpdate,
  InvestmentObservation,
  InvestmentObservationCreate,
  InvestmentObservationUpdate,
  InvestmentWithdrawal,
  InvestmentWithdrawalCreate,
  AssetsHistory,
  AssetsHistoryCreate,
  AssetsHistoryUpdate,
  IntesaRawTransaction,
  IntesaRawTransactionCreate,
  AllianzRawTransaction,
  AllianzRawTransactionCreate,
  Bank,
  BankCreate,
  Account,
  AccountCreate,
  AccountUpdate,
  AssetTypeRef,
  AssetTypeRefCreate,
  ApiError as ApiErrorType,
  PaginatedResponse,
  // Upload workflow types
  PreprocessingResult,
  HarmonizationResult,
  ParsedTransaction,
  CommitResult,
  AccountWithLastDate,
  BulkAssetsHistoryCreate,
  BulkAssetsHistoryResult,
  SyncAccountsResult,
} from '@/types';

const API_BASE_URL = import.meta.env.DEV ? '/api' : '/api';

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = 'ApiError';
  }
}

async function request<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error: ApiErrorType = await response.json().catch(() => ({
      detail: response.statusText,
    }));
    throw new ApiError(response.status, error.detail);
  }

  // Handle empty responses
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return response.json();
  }
  return {} as T;
}

// Transactions API
export const transactionsApi = {
  getAll: (params?: {
    skip?: number;
    limit?: number;
    bank_name?: string;
    account_name?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<Transaction[]> => {
    const searchParams = new URLSearchParams();
    if (params?.skip !== undefined) searchParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) searchParams.append('limit', params.limit.toString());
    if (params?.bank_name) searchParams.append('bank_name', params.bank_name);
    if (params?.account_name) searchParams.append('account_name', params.account_name);
    if (params?.start_date) searchParams.append('start_date', params.start_date);
    if (params?.end_date) searchParams.append('end_date', params.end_date);
    
    const query = searchParams.toString();
    return request<Transaction[]>(`/transactions${query ? `?${query}` : ''}`);
  },

  getById: (id: number): Promise<Transaction> => {
    return request<Transaction>(`/transactions/${id}`);
  },

  create: (data: TransactionCreate): Promise<Transaction> => {
    return request<Transaction>('/transactions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: (id: number, data: TransactionUpdate): Promise<Transaction> => {
    return request<Transaction>(`/transactions/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  delete: (id: number): Promise<void> => {
    return request<void>(`/transactions/${id}`, {
      method: 'DELETE',
    });
  },

  getTypes: (): Promise<string[]> => {
    return request<string[]>('/transactions/types');
  },
};

// Investment Products API
export const investmentProductsApi = {
  getAll: (): Promise<InvestmentProduct[]> => {
    return request<InvestmentProduct[]>('/investment-products');
  },

  getById: (id: number): Promise<InvestmentProduct> => {
    return request<InvestmentProduct>(`/investment-products/${id}`);
  },

  create: (data: InvestmentProductCreate): Promise<InvestmentProduct> => {
    return request<InvestmentProduct>('/investment-products', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: (id: number, data: InvestmentProductUpdate): Promise<InvestmentProduct> => {
    return request<InvestmentProduct>(`/investment-products/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  delete: (id: number): Promise<void> => {
    return request<void>(`/investment-products/${id}`, {
      method: 'DELETE',
    });
  },
};

// SIP Plans API
export const sipPlansApi = {
  getAll: (): Promise<SIPPlan[]> => {
    return request<SIPPlan[]>('/sip-plans');
  },

  getById: (id: number): Promise<SIPPlan> => {
    return request<SIPPlan>(`/sip-plans/${id}`);
  },

  create: (data: SIPPlanCreate): Promise<SIPPlan> => {
    return request<SIPPlan>('/sip-plans', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: (id: number, data: SIPPlanUpdate): Promise<SIPPlan> => {
    return request<SIPPlan>(`/sip-plans/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  delete: (id: number): Promise<void> => {
    return request<void>(`/sip-plans/${id}`, {
      method: 'DELETE',
    });
  },
};

// Investment Observations API
export const investmentObservationsApi = {
  getAll: (productId?: number): Promise<InvestmentObservation[]> => {
    const query = productId ? `?product_id=${productId}` : '';
    return request<InvestmentObservation[]>(`/investment-observations${query}`);
  },

  getById: (id: number): Promise<InvestmentObservation> => {
    return request<InvestmentObservation>(`/investment-observations/${id}`);
  },

  create: (data: InvestmentObservationCreate): Promise<InvestmentObservation> => {
    return request<InvestmentObservation>('/investment-observations', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: (id: number, data: InvestmentObservationUpdate): Promise<InvestmentObservation> => {
    return request<InvestmentObservation>(`/investment-observations/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  delete: (id: number): Promise<void> => {
    return request<void>(`/investment-observations/${id}`, {
      method: 'DELETE',
    });
  },
};

// Investment Withdrawals API
export const investmentWithdrawalsApi = {
  getAll: (): Promise<InvestmentWithdrawal[]> => {
    return request<InvestmentWithdrawal[]>('/investment-withdrawals');
  },

  getById: (id: number): Promise<InvestmentWithdrawal> => {
    return request<InvestmentWithdrawal>(`/investment-withdrawals/${id}`);
  },

  create: (data: InvestmentWithdrawalCreate): Promise<InvestmentWithdrawal> => {
    return request<InvestmentWithdrawal>('/investment-withdrawals', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  delete: (id: number): Promise<void> => {
    return request<void>(`/investment-withdrawals/${id}`, {
      method: 'DELETE',
    });
  },
};

// Assets History API
export const assetsHistoryApi = {
  getAll: (params?: {
    bank_name?: string;
    account_name?: string;
    asset_type?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<AssetsHistory[]> => {
    const searchParams = new URLSearchParams();
    if (params?.bank_name) searchParams.append('bank_name', params.bank_name);
    if (params?.account_name) searchParams.append('account_name', params.account_name);
    if (params?.asset_type) searchParams.append('asset_type', params.asset_type);
    if (params?.start_date) searchParams.append('start_date', params.start_date);
    if (params?.end_date) searchParams.append('end_date', params.end_date);
    
    const query = searchParams.toString();
    return request<AssetsHistory[]>(`/assets-history${query ? `?${query}` : ''}`);
  },

  getById: (id: number): Promise<AssetsHistory> => {
    return request<AssetsHistory>(`/assets-history/${id}`);
  },

  create: (data: AssetsHistoryCreate): Promise<AssetsHistory> => {
    return request<AssetsHistory>('/assets-history', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  createBulk: (data: BulkAssetsHistoryCreate): Promise<BulkAssetsHistoryResult> => {
    return request<BulkAssetsHistoryResult>('/assets-history/bulk', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: (id: number, data: AssetsHistoryUpdate): Promise<AssetsHistory> => {
    return request<AssetsHistory>(`/assets-history/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  delete: (id: number): Promise<void> => {
    return request<void>(`/assets-history/${id}`, {
      method: 'DELETE',
    });
  },
};

// Banks API
export const banksApi = {
  getAll: (): Promise<Bank[]> => {
    return request<Bank[]>('/banks');
  },

  getById: (id: number): Promise<Bank> => {
    return request<Bank>(`/banks/${id}`);
  },

  create: (data: BankCreate): Promise<Bank> => {
    return request<Bank>('/banks', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
};

// Accounts API
export const accountsApi = {
  getAll: (params?: { bank_name?: string; asset_type?: string }): Promise<Account[]> => {
    const searchParams = new URLSearchParams();
    if (params?.bank_name) searchParams.append('bank_name', params.bank_name);
    if (params?.asset_type) searchParams.append('asset_type', params.asset_type);
    const query = searchParams.toString();
    return request<Account[]>(`/accounts${query ? `?${query}` : ''}`);
  },

  getById: (id: number): Promise<Account> => {
    return request<Account>(`/accounts/${id}`);
  },

  getLastTransactionDates: (activeOnly: boolean = true, assetType?: string): Promise<AccountWithLastDate[]> => {
    const searchParams = new URLSearchParams();
    searchParams.append('active_only', activeOnly.toString());
    if (assetType) searchParams.append('asset_type', assetType);
    return request<AccountWithLastDate[]>(`/accounts/last-transaction-dates?${searchParams.toString()}`);
  },

  syncFromAssetsHistory: (): Promise<SyncAccountsResult> => {
    return request<SyncAccountsResult>('/accounts/sync-from-assets-history', {
      method: 'POST',
    });
  },

  create: (data: AccountCreate): Promise<Account> => {
    return request<Account>('/accounts', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: (id: number, data: AccountUpdate): Promise<Account> => {
    return request<Account>(`/accounts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },
};

// Asset Types API
export const assetTypesApi = {
  getAll: (): Promise<AssetTypeRef[]> => {
    return request<AssetTypeRef[]>('/asset-types');
  },

  create: (data: AssetTypeRefCreate): Promise<AssetTypeRef> => {
    return request<AssetTypeRef>('/asset-types', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  delete: (id: number): Promise<void> => {
    return request<void>(`/asset-types/${id}`, {
      method: 'DELETE',
    });
  },
};

// Upload API
export const uploadApi = {
  preprocess: async (
    file: File,
    bankName: string,
    accountName: string
  ): Promise<PreprocessingResult> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('bank_name', bankName);
    formData.append('account_name', accountName);

    const url = `${API_BASE_URL}/upload/preprocess`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      // Note: Don't set Content-Type header - browser will set it with boundary for FormData
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: response.statusText,
      }));
      throw new ApiError(response.status, error.detail);
    }

    return response.json();
  },

  harmonize: (transactions: ParsedTransaction[]): Promise<HarmonizationResult> => {
    return request<HarmonizationResult>('/upload/harmonize', {
      method: 'POST',
      body: JSON.stringify(transactions),
    });
  },

  commit: (transactions: ParsedTransaction[]): Promise<CommitResult> => {
    return request<CommitResult>('/upload/commit', {
      method: 'POST',
      body: JSON.stringify({ transactions }),
    });
  },
};

// Export all APIs
export const api = {
  transactions: transactionsApi,
  investmentProducts: investmentProductsApi,
  sipPlans: sipPlansApi,
  investmentObservations: investmentObservationsApi,
  investmentWithdrawals: investmentWithdrawalsApi,
  assetsHistory: assetsHistoryApi,
  banks: banksApi,
  accounts: accountsApi,
  assetTypes: assetTypesApi,
  upload: uploadApi,
};
