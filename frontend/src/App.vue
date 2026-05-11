<template>
  <div id="app">
    <h1>Personal Finance Tracker</h1>
    <nav class="app-nav" aria-label="Main">
      <div class="nav-group" :class="{ 'nav-group--active': cashSectionActive }">
        <span class="nav-group-label">Cash flow</span>
        <div class="nav-group-links">
          <router-link to="/cash/dashboard">Dashboard</router-link>
          <router-link to="/cash/upload">Upload</router-link>
          <router-link to="/cash/data">Data</router-link>
        </div>
      </div>
      <div class="nav-group" :class="{ 'nav-group--active': investmentsSectionActive }">
        <span class="nav-group-label">Investments</span>
        <div class="nav-group-links">
          <router-link to="/investments/dashboard">Dashboard</router-link>
          <router-link to="/investments/upload">Upload</router-link>
          <router-link to="/investments/data">Data</router-link>
        </div>
      </div>
    </nav>
    <main>
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import './static/css/style.css';

const route = useRoute();
const cashSectionActive = computed(() => route.path.startsWith('/cash'));
const investmentsSectionActive = computed(() => route.path.startsWith('/investments'));
</script>

<style scoped>
#app {
  min-height: 100vh;
}

h1 {
  margin-top: 0;
}

.app-nav {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  gap: 28px 36px;
  margin-bottom: 20px;
}

.nav-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid transparent;
  transition: background 0.15s, border-color 0.15s;
}

.nav-group--active {
  background: #f0f7ff;
  border-color: #b6d4fe;
}

.nav-group-label {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #666;
}

.nav-group-links {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 14px;
}

.nav-group-links a {
  text-decoration: none;
  color: #007bff;
  font-size: 0.95rem;
}

.nav-group-links a:hover {
  text-decoration: underline;
}

.nav-group-links a.router-link-active {
  font-weight: bold;
  text-decoration: underline;
}

main {
  background-color: white;
  padding: 20px 28px;
  border-radius: 5px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style>
