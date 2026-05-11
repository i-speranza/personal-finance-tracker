import { createRouter, createWebHistory } from 'vue-router';
import CashflowDashboard from '@/views/cashflow/CashflowDashboard.vue';
import CashflowData from '@/views/cashflow/CashflowData.vue';
import CashflowUpload from '@/views/cashflow/CashflowUpload.vue';
import InvestmentsDashboard from '@/views/investments/InvestmentsDashboard.vue';
import InvestmentsUpload from '@/views/investments/InvestmentsUpload.vue';
import InvestmentsData from '@/views/investments/InvestmentsData.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/cash/dashboard' },
    { path: '/upload', redirect: '/cash/upload' },
    { path: '/edit', redirect: '/cash/data' },
    { path: '/investments', redirect: '/investments/data' },

    {
      path: '/cash/dashboard',
      name: 'CashDashboard',
      component: CashflowDashboard,
    },
    {
      path: '/cash/upload',
      name: 'CashUpload',
      component: CashflowUpload,
    },
    {
      path: '/cash/data',
      name: 'CashData',
      component: CashflowData,
    },

    {
      path: '/investments/dashboard',
      name: 'InvestmentsDashboard',
      component: InvestmentsDashboard,
    },
    {
      path: '/investments/upload',
      name: 'InvestmentsUpload',
      component: InvestmentsUpload,
    },
    {
      path: '/investments/data',
      name: 'InvestmentsData',
      component: InvestmentsData,
    },
  ],
});

export default router;
