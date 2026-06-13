// Debate-specific utilities — not a separate package, just a shared file.

export const STAKE_POOL_ABI = [
  "function stakeA(uint256 debateId) payable",
  "function stakeB(uint256 debateId) payable",
  "function resolve(uint256 debateId, address winner)",
  "function getMatch(uint256) view returns (address,address,uint256,uint8,address)",
  "event Staked(uint256 indexed debateId, address indexed player, string side)",
  "event Resolved(uint256 indexed debateId, address indexed winner, uint256 payout)",
];

export function formatRoundScore(scores) {
  return scores
    .map((s, i) => `R${i + 1}: ${s.winner.toUpperCase()} — ${s.reason}`)
    .join("\n");
}

export function debateStatus(debate) {
  const map = { open: "⏳ Waiting", active: "⚔️ Live", judging: "🧠 Judging", finished: "🏆 Done" };
  return map[debate.status] || debate.status;
}

export function canArgue(debate, address) {
  if (debate.status !== "active") return false;
  const side = address === debate.side_a ? "a" : address === debate.side_b ? "b" : null;
  if (!side) return false;
  const args = side === "a" ? debate.arguments_a : debate.arguments_b;
  return args.length < debate.current_round;
}
