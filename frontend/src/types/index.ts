// Type definitions matching FastAPI schemas

export enum InvestmentType {
  ONE_TIME = 'one_time',
  SIP = 'sip',
}

export enum WithdrawalType {
  IN = 'in',
  OUT = 'out',
}

export enum AssetType {
  CASH = 'cash',
  INVESTMENT = 'investment',
}

// Transaction Types
export interface Transaction {
  id: number;
  bank_name: string;
  account_name: string;
  date: string; // ISO date string
  amount: number;
  description: string | null;
  details: string | null;
  category: string | null;
  transaction_type: string | null;
  is_special: boolean;
  created_at: string; // ISO datetime string
  updated_at: string; // ISO datetime string
}

export interface TransactionCreate {
  bank_name: string;
  account_name: string;
  date: string;
  amount: number;
  description?: string | null;
  details?: string | null;
  category?: string | null;
  transaction_type?: string | null;
  is_special?: boolean;
}

export interface TransactionUpdate {
  bank_name?: string;
  account_name?: string;
  date?: string;
  amount?: number;
  description?: string | null;
  category?: string | null;
  details?: string | null;
  transaction_type?: string | null;
  is_special?: boolean;
}

// Investment Product Types
export interface InvestmentProduct {
  id: number;
  product_name: string;
  bank_name: string;
  start_date: string;
  end_date: string | null;
  investment_type: InvestmentType;
  created_at: string;
  updated_at: string;
}

export interface InvestmentProductCreate {
  product_name: string;
  bank_name: string;
  start_date: string;
  end_date?: string | null;
  investment_type: InvestmentType;
}

export interface InvestmentProductUpdate {
  product_name?: string;
  bank_name?: string;
  start_date?: string;
  end_date?: string | null;
  investment_type?: InvestmentType;
}

// SIP Plan Types
export interface SIPPlan {
  id: number;
  product_id: number;
  start_date: string;
  end_date: string | null;
  monthly_contribution: number;
  created_at: string;
  updated_at: string;
}

export interface SIPPlanCreate {
  product_id: number;
  start_date: string;
  end_date?: string | null;
  monthly_contribution: number;
}

export interface SIPPlanUpdate {
  start_date?: string;
  end_date?: string | null;
  monthly_contribution?: number;
}

// Investment Observation Types
export interface InvestmentObservation {
  id: number;
  product_id: number;
  observation_date: string;
  num_shares: number;
  total_invested: number;
  current_value: number;
  created_at: string;
}

export interface InvestmentObservationCreate {
  product_id: number;
  observation_date: string;
  num_shares: number;
  total_invested: number;
  current_value: number;
}

export interface InvestmentObservationUpdate {
  observation_date?: string;
  num_shares?: number;
  total_invested?: number;
  current_value?: number;
}

// Investment Withdrawal Types
export interface InvestmentWithdrawal {
  id: number;
  bank_name: string;
  date: string;
  type: WithdrawalType;
  amount: number;
  description: string | null;
  created_at: string;
}

export interface InvestmentWithdrawalCreate {
  bank_name: string;
  date: string;
  type: WithdrawalType;
  amount: number;
  description?: string | null;
}

// Assets History Types
export interface AssetsHistory {
  id: number;
  account_name: string;
  bank_name: string;
  asset_type: AssetType;
  date: string;
  amount: number;
  created_at: string;
  updated_at: string;
}

export interface AssetsHistoryCreate {
  account_name: string;
  bank_name: string;
  asset_type: AssetType;
  date: string;
  amount: number;
}

// Raw Transaction Types
export interface IntesaRawTransaction {
  id: number;
  transaction_id: number | null;
  data: string;
  operazione: string | null;
  dettagli: string | null;
  conto_o_carta: string | null;
  contabilizzazione: string | null;
  categoria: string | null;
  valuta: string | null;
  importo: number;
  created_at: string;
}

export interface IntesaRawTransactionCreate {
  data: string;
  operazione?: string | null;
  dettagli?: string | null;
  conto_o_carta?: string | null;
  contabilizzazione?: string | null;
  categoria?: string | null;
  valuta?: string | null;
  importo: number;
  transaction_id?: number | null;
}

export interface AllianzRawTransaction {
  id: number;
  transaction_id: number | null;
  data_contabile: string;
  data_valuta: string | null;
  descrizione: string | null;
  importo: number;
  created_at: string;
}

export interface AllianzRawTransactionCreate {
  data_contabile: string;
  data_valuta?: string | null;
  descrizione?: string | null;
  importo: number;
  transaction_id?: number | null;
}

// Bank Types
export interface Bank {
  id: number;
  name: string;
  display_name: string;
  created_at: string;
  updated_at: string;
}

export interface BankCreate {
  name: string;
  display_name: string;
}

// Account Types
export interface Account {
  id: number;
  bank_name: string;
  account_name: string;
  asset_type: AssetType | null;
  status: boolean;
  created_at: string;
  updated_at: string;
}

export interface AccountCreate {
  bank_name: string;
  account_name: string;
  asset_type?: AssetType | null;
  status?: boolean;
}

export interface AccountUpdate {
  bank_name?: string;
  account_name?: string;
  asset_type?: AssetType | null;
  status?: boolean;
}

// API Response Types
export interface ApiError {
  detail: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Upload Workflow Types
export interface UploadWarning {
  type: 'filtered_row' | 'duplicate' | 'parsing_error';
  message: string;
  details?: Record<string, unknown>;
}

export interface ParsedTransaction {
  bank_name: string;
  account_name: string;
  date: string;
  amount: number;
  description: string | null;
  details: string | null;
  category: string | null;
  transaction_type: string | null;
  is_special: boolean;
}

export interface PreprocessingResult {
  transactions: ParsedTransaction[];
  warnings: UploadWarning[];
  date_range: {
    first_date: string;
    last_date: string;
  };
  saved_filename: string;
}

export interface HarmonizationResult {
  new_transactions: ParsedTransaction[];
  duplicate_transactions: ParsedTransaction[];
}

export interface CommitRequest {
  transactions: ParsedTransaction[];
}

export interface CommitResult {
  inserted_count: number;
  message: string;
}

export interface AccountWithLastDate {
  id: number;
  bank_name: string;
  account_name: string;
  asset_type: AssetType | null;
  status: boolean;
  last_transaction_date: string | null;
}

export interface SyncAccountsResult {
  created_count: number;
  updated_count: number;
  accounts: Account[];
}

export interface BulkAssetsHistoryCreate {
  entries: AssetsHistoryCreate[];
}

export interface BulkAssetsHistoryResult {
  created_count: number;
  entries: AssetsHistory[];
}
