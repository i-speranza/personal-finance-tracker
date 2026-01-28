import { createRouter, createWebHistory } from 'vue-router';
import Dashboard from '@/views/Dashboard.vue';
import Edit from '@/views/Edit.vue';
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
      name: 'Edit',
      component: Edit,
    },
    {
      path: '/upload',
      name: 'Upload',
      component: Upload,
    },
  ],
});

export default router;
