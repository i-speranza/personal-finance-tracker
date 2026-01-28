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
  IntesaRawTransaction,
  IntesaRawTransactionCreate,
  AllianzRawTransaction,
  AllianzRawTransactionCreate,
  Bank,
  BankCreate,
  Account,
  AccountCreate,
  AccountUpdate,
  ApiError as ApiErrorType,
  PaginatedResponse,
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

  update: (id: number, data: Partial<AssetsHistoryCreate>): Promise<AssetsHistory> => {
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
  getAll: (): Promise<Account[]> => {
    return request<Account[]>('/accounts');
  },

  getById: (id: number): Promise<Account> => {
    return request<Account>(`/accounts/${id}`);
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
};
