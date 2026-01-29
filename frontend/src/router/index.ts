import { createRouter, createWebHistory } from 'vue-router';
import Dashboard from '@/views/Dashboard.vue';
import DataManagement from '@/views/DataManagement.vue';
import Upload from '@/views/Upload.vue';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Dashboard',
      component: Dashboard,
    },
    {
      path: '/edit',
      name: 'DataManagement',
      component: DataManagement,
    },
    {
      path: '/upload',
      name: 'Upload',
      component: Upload,
    },
  ],
});

export default router;
