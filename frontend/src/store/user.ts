import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const userInfo = ref<{ username: string; role: string; name: string } | null>(null)
  const isAuthenticated = ref(false)

  function login(userData: { username: string; role: string; name: string }) {
    userInfo.value = userData
    isAuthenticated.value = true
    // In real app, you would also save token to localStorage here
  }

  function logout() {
    userInfo.value = null
    isAuthenticated.value = false
  }

  return {
    userInfo,
    isAuthenticated,
    login,
    logout
  }
})
