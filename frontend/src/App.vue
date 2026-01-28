<template>
  <div id="app">
    <h1>Personal Finance Tracker</h1>
    <nav>
      <router-link to="/">Dashboard</router-link>
      <router-link to="/upload">Upload</router-link>
      <router-link to="/edit">Edit</router-link>
    </nav>
    <main>
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import './static/css/style.css';
</script>

<style scoped>
#app {
  min-height: 100vh;
}

h1 {
  margin-top: 0;
}

nav {
  margin-bottom: 20px;
}

nav a {
  margin-right: 15px;
  text-decoration: none;
  color: #007bff;
}

nav a:hover {
  text-decoration: underline;
}

nav a.router-link-active {
  font-weight: bold;
  text-decoration: underline;
}

main {
  background-color: white;
  padding: 20px;
  border-radius: 5px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
</style>
