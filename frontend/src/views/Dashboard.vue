<template>
  <div>
    <h2>Dashboard</h2>
    <div id="dashboard-content">
      <p>Dashboard content will be loaded here...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { api } from '@/api/client';

onMounted(() => {
  console.log('Dashboard module initialized');
  
  // Dashboard content will be loaded here
  const dashboardContent = document.getElementById('dashboard-content');
  if (dashboardContent) {
    dashboardContent.innerHTML = '<p>Dashboard content will be loaded here...</p>';
  }
  
  // Example: Load transactions for dashboard
  // api.transactions.getAll().then(transactions => {
  //   console.log('Transactions loaded:', transactions);
  // }).catch(error => {
  //   console.error('Error loading transactions:', error);
  // });
});
</script>
