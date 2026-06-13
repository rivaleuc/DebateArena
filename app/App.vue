<template>
  <div class="min-h-screen bg-black text-white font-mono">
    <header class="p-4 border-b border-zinc-800 flex justify-between">
      <span class="text-xl">⚔️ DEBATE ARENA</span>
      <span class="text-zinc-600 text-sm">stake · argue · win</span>
    </header>

    <div class="max-w-5xl mx-auto p-6">
      <!-- Create debate -->
      <section v-if="view === 'create'" class="space-y-4">
        <h2 class="text-2xl text-red-500">NEW DEBATE</h2>
        <input v-model="topic" placeholder="Topic to debate..."
          class="w-full bg-zinc-900 border border-zinc-700 p-3 rounded text-white" />
        <select v-model="rounds" class="bg-zinc-900 border border-zinc-700 p-3 rounded text-white">
          <option value="1">1 round</option>
          <option value="2">2 rounds</option>
          <option value="3">3 rounds</option>
        </select>
        <button @click="create" class="bg-red-600 hover:bg-red-700 px-6 py-3 rounded font-bold">
          CREATE
        </button>
      </section>

      <!-- Argue -->
      <section v-if="view === 'argue'" class="space-y-4">
        <h2 class="text-2xl text-blue-500">MAKE YOUR ARGUMENT</h2>
        <input v-model="debateKey" placeholder="Debate #" class="w-full bg-zinc-900 border border-zinc-700 p-3 rounded text-white" />
        <textarea v-model="argument" rows="6" placeholder="Your argument (min 50 chars)..."
          class="w-full bg-zinc-900 border border-zinc-700 p-3 rounded text-white resize-none"></textarea>
        <button @click="argue" class="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded font-bold">
          SUBMIT ARGUMENT
        </button>
      </section>

      <!-- Nav -->
      <nav class="fixed bottom-0 left-0 right-0 bg-zinc-900 border-t border-zinc-800 p-3 flex justify-center gap-4">
        <button @click="view = 'create'" :class="view === 'create' ? 'text-red-500' : 'text-zinc-500'">CREATE</button>
        <button @click="view = 'argue'" :class="view === 'argue' ? 'text-blue-500' : 'text-zinc-500'">ARGUE</button>
        <button @click="view = 'judge'" :class="view === 'judge' ? 'text-yellow-500' : 'text-zinc-500'">JUDGE</button>
      </nav>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
const view = ref("create");
const topic = ref("");
const rounds = ref("2");
const debateKey = ref("");
const argument = ref("");

function create() { /* GenLayer write call */ }
function argue() { /* GenLayer write call */ }
</script>
