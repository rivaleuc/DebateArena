# DebateArena

**Staked, multi-round debates settled by AI consensus. Two debaters put up ETH, argue across rounds, and a GenLayer jury declares the winner.**

DebateArena runs structured head-to-head debates on a topic. Two participants join opposing sides, exchange arguments over up to three rounds, and then GenLayer validators judge the full transcript round-by-round and pick a winner by consensus. A companion EVM `StakePool` contract holds both debaters' stakes and pays the winner once the GenLayer verdict is readable — splitting the *judgment* (subjective, on GenLayer) from the *settlement* (deterministic, on the EVM).

- **Contract (Bradbury, chain 4221):** `0xB334B44C0C636b9259E10b07132638d7D1a92d7c`
- **Explorer:** https://explorer-bradbury.genlayer.com/contract/0xB334B44C0C636b9259E10b07132638d7D1a92d7c
- **Live app:** https://debatearena-cyan.vercel.app

## What it does

A debate moves through `open → active → judging → finished`, driven by four writes and three views on the `DebateArena` contract:

1. **`open_debate(topic, rounds)`** — validates the topic (≤500 chars) and clamps `rounds` to `1..ROUNDS_MAX` (3). Stores a JSON debate in `debates: TreeMap[str, str]` keyed by an incrementing `debate_count`, status `open`. Returns the key.
2. **`join(debate_key, side)`** — claims side `"a"` or `"b"` for the caller's address; once both sides are filled, status flips to `active` and `current_round` becomes `1`.
3. **`argue(debate_key, argument)`** — requires status `active` and an argument ≥`MIN_ARGUMENT_LEN` (50) chars; appends to the caller's side (≤2000 chars), one argument per side per round. When both sides have argued the current round, it either advances `current_round` or, at the last round, flips status to `judging`.
4. **`judge_debate(debate_key)`** — requires status `judging` and runs the AI jury. The leader function builds a round-by-round transcript and calls `gl.nondet.exec_prompt(prompt, response_format="json")`, returning `{"winner": "a"/"b", "round_scores": [...], "summary": "..."}`. Consensus is enforced by `gl.vm.run_nondet_unsafe(leader_fn, validator_fn)`, where `validator_fn` accepts a `gl.vm.Return` only if `winner` ∈ `{a, b}` and `round_scores` is a list. Status becomes `finished` and the winner/scores are stored.
5. **`get_debate(key)`** — view returning the full debate record (or `{"exists": False}`).
6. **`read_winner(key)`** — view returning `{"resolved": bool, "winner": "a"/"b", "winner_address": ...}` once finished — the hook the EVM `StakePool` reads to pay out.
7. **`stats()`** — view returning `{"total_debates": <int>, "finished": <int>}`.

On the EVM side, `StakePool.sol` implements `stakeA` / `stakeB` (both put up matching ETH) and `resolve(debateId, winnerAddr)`, callable only by the configured resolver, which transfers the full pot to the winner read from GenLayer.

## Why GenLayer

A deterministic VM cannot read two essays and decide which argument was stronger — that is precisely the subjective judgment a debate needs, and no oracle provides it. But money settlement *should* be deterministic and cheap.

GenLayer's Optimistic Democracy supplies the trustless verdict: the leader proposes a winner with per-round scoring, and independent validators each re-judge the transcript, finalising only if `validator_fn` passes. The EVM `StakePool` then does what EVMs are good at — holding stakes and paying out exactly, gated on `read_winner`.

Use GenLayer for the subjective call (who won) and a plain EVM/backend for the objective one (move the funds). DebateArena is the canonical example of that split.

## Architecture

| Contract | Frontend | EVM / off-chain |
| --- | --- | --- |
| `src/debate_arena.py` (GenLayer jury) | `app` (React + Vite) | `chain/contracts/StakePool.sol` — Hardhat-built EVM escrow that reads `read_winner` and pays the winner |

## Tech

- **GenVM Python**, pinned to `py-genlayer:1jb45aa8…jpz09h6` via the `Depends` header. Debates are JSON-encoded into a `TreeMap[str, str]` with a `u256` counter; `read_winner` exposes the slim verdict the EVM resolver consumes.
- **Solidity** `StakePool.sol` (`pragma ^0.8.24`) built with Hardhat (`hardhat.config.js`), holding native-ETH stakes with a resolver-gated `resolve`.
- **Frontend** reads with `genlayer-js` (`createClient({ chain: testnetBradbury })` → `readContract`) and writes via **MetaMask without the snap** — it calls `wallet_switchEthereumChain` / `wallet_addEthereumChain` to put the wallet on Bradbury (chain `4221`, hex `0x107d`) and signs with `writeContract`, awaiting a `FINALIZED` receipt.
- **UI:** React 19 + Vite + Tailwind v4 with `framer-motion` and `sonner`. The app is a debate room: open a topic, join a side, post arguments round-by-round, trigger judgment, and read the per-round winner and summary.

## Project structure

```
DebateArena/
├── src/
│   └── debate_arena.py       ← GenLayer contract (DebateArena jury)
├── chain/
│   └── contracts/
│       └── StakePool.sol     ← EVM stake/escrow (winner-takes-all)
├── lib/
│   └── utils.js
├── hardhat.config.js
├── package.json
├── app/                      ← production frontend
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig*.json
│   ├── public/               ← favicon.svg, icons.svg
│   └── src/
│       ├── App.tsx           ← UI
│       ├── genlayer.ts       ← client, wallet, read/write helpers
│       ├── main.tsx
│       └── index.css
└── README.md
```

## Develop

```bash
cd app
npm install
npm run dev      # local dev server (Vite)
npm run build    # type-check + production build to dist/
```

## Deploy the frontend

DebateArena's frontend is deployed on **Vercel** (not Cloudflare Pages):

- **Framework preset:** Vite
- **Root directory:** `app`
- **Build command:** `npm run build`
- **Output directory:** `dist`
- **Node version:** 20

## Why GenLayer (engineering notes)

- **Judgment and settlement are deliberately split.** GenLayer decides *who won* (subjective, needs consensus); `StakePool.sol` moves *the money* (deterministic, needs finality). `read_winner` is the narrow bridge: it returns `{"resolved": False}` until status is `finished`, so the resolver can't pay out early.
- **Turn order is enforced in storage.** `argue` checks `len(arguments_x) >= current_round` to block double-posting in a round, and only advances `current_round` (or moves to `judging`) once *both* sides have argued — the JSON record is the entire state machine across separate transactions.
- **`validator_fn` is lenient on shape, strict on outcome.** It requires `winner` ∈ `{a, b}` and `round_scores` to be a list, but doesn't over-constrain the reasoning text — enough to guarantee a usable verdict without rejecting valid stylistic variation between validators.
- **Transcript is truncated per round** (800 chars/side) before prompting, bounding the judge's input regardless of how long the arguments were.
- **TreeMap holds serialized JSON** — `json.loads` → mutate → `json.dumps` on every write; `stats()` even iterates all keys to count finished debates.

## License

MIT
