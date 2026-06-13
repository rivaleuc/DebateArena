# DebateArena

Structured on-chain debates where two sides stake ETH, argue in rounds, and AI validators judge the winner. The winning side takes the entire pool.

## How it works

1. Someone opens a debate topic (e.g. "Is Bitcoin a better store of value than gold?")
2. Two players join (side A and side B), each staking the same amount of ETH
3. They argue in rounds (1-3 rounds, configured at creation)
4. When all rounds are done, anyone can trigger AI judgment
5. GenLayer validators score each round independently, declare a winner
6. StakePool pays the winner 2x their stake

## Deployed

**GenLayer (Bradbury):** `0xB334B44C0C636b9259E10b07132638d7D1a92d7c`

## Project structure

```
DebateArena/
├── src/
│   └── debate_arena.py          ← GenLayer intelligent contract
├── chain/
│   └── contracts/
│       └── StakePool.sol        ← ETH staking + winner payout
├── app/
│   ├── index.html
│   ├── main.js
│   ├── style.css
│   └── App.vue                  ← Vue 3 frontend
├── lib/
│   └── utils.js                 ← Shared utilities (ABI, formatters)
├── hardhat.config.js
└── package.json                 ← Flat, no monorepo
```

No monorepo. No `packages/`. No `pnpm-workspace`. Just flat directories:
- `src/` for the intelligent contract
- `chain/` for Solidity (Hardhat, not Foundry)
- `app/` for the Vue frontend (Vite)
- `lib/` for shared code

## Key differences from other repos

- **Vue 3** — not Next.js, SvelteKit, or Astro
- **Hardhat** — not Foundry
- **ETH staking** — no ERC-20 token, just native ETH
- **Multi-round game** — not a single-shot judgment
- **Flat structure** — no monorepo, no workspace
- **Winner-takes-all** — not proportional settlement

## Quick start

```bash
npm install
npm run dev           # Vue frontend
npm run compile       # Hardhat compile
npm run deploy:genlayer  # Deploy to GenLayer
```
