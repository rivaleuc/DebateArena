import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Toaster, toast } from "sonner";

const CONTRACT = "0xB334B44C0C636b9259E10b07132638d7D1a92d7c";

const RED = "#F43F5E";
const BLUE = "#38BDF8";

type Side = "A" | "B";

type Fighter = {
  side: Side;
  name: string;
  handle: string;
  stake: number; // ETH
  color: string;
};

const FIGHTERS: Record<Side, Fighter> = {
  A: { side: "A", name: "Crimson", handle: "0xRedCorner", stake: 1.5, color: RED },
  B: { side: "B", name: "Glacier", handle: "0xBlueCorner", stake: 1.5, color: BLUE },
};

type Turn = { round: number; side: Side; text: string };

const TRANSCRIPT: Turn[] = [
  { round: 1, side: "A", text: "Decentralization is non-negotiable. Custody is theft waiting to happen." },
  { round: 1, side: "B", text: "Pure decentralization is a UX disaster. Adoption needs guardrails." },
  { round: 2, side: "A", text: "Guardrails become gatekeepers. Every 'safe' chain reintroduces the bank." },
  { round: 2, side: "B", text: "Tell that to the millions who lost keys. Recovery isn't tyranny." },
  { round: 3, side: "A", text: "Self-custody is a skill, not a flaw. We educate, we don't centralize." },
  { round: 3, side: "B", text: "Idealism doesn't onboard your grandmother. Pragmatism wins markets." },
];

const ROUND_WINS: Record<Side, number> = { A: 2, B: 1 };

export default function App() {
  const [judging, setJudging] = useState(false);
  const [winner, setWinner] = useState<Side | null>(null);

  const pool = useMemo(
    () => FIGHTERS.A.stake + FIGHTERS.B.stake,
    []
  );

  function judge() {
    if (judging || winner) return;
    setJudging(true);
    toast.loading("AI judge is reviewing the transcript…", { id: "judge" });
    setTimeout(() => {
      const win: Side = ROUND_WINS.A >= ROUND_WINS.B ? "A" : "B";
      setWinner(win);
      setJudging(false);
      toast.success(
        `${FIGHTERS[win].name} wins the pool · ${pool.toFixed(2)} ETH`,
        { id: "judge" }
      );
    }, 3000);
  }

  function reset() {
    setWinner(null);
    toast.dismiss();
  }

  return (
    <div className="min-h-screen bg-[#0C0A14] text-slate-100 antialiased">
      <Toaster theme="dark" richColors position="top-center" />

      {/* glow backdrop */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div
          className="absolute -left-40 top-0 h-[600px] w-[600px] rounded-full blur-[140px] opacity-20"
          style={{ background: RED }}
        />
        <div
          className="absolute -right-40 bottom-0 h-[600px] w-[600px] rounded-full blur-[140px] opacity-20"
          style={{ background: BLUE }}
        />
      </div>

      <div className="relative mx-auto max-w-5xl px-5 py-8">
        {/* Scoreboard */}
        <header className="mb-6 text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">
            DebateArena · Pool {pool.toFixed(2)} ETH
          </p>
          <div className="mt-3 flex items-center justify-center gap-6">
            <span className="text-4xl font-black" style={{ color: RED }}>
              {ROUND_WINS.A}
            </span>
            <div className="flex flex-col items-center">
              <span className="rounded-md bg-white/5 px-3 py-1 text-xs font-bold uppercase tracking-widest text-slate-300 ring-1 ring-white/10">
                Round Wins
              </span>
              <span className="mt-1 font-mono text-[10px] text-slate-600">
                3 rounds · final
              </span>
            </div>
            <span className="text-4xl font-black" style={{ color: BLUE }}>
              {ROUND_WINS.B}
            </span>
          </div>
        </header>

        {/* Versus split: corners + transcript */}
        <div className="grid grid-cols-1 items-start gap-4 md:grid-cols-[1fr_auto_1fr]">
          {/* RED corner */}
          <Corner fighter={FIGHTERS.A} align="left" winner={winner} />

          {/* VS badge */}
          <div className="hidden self-stretch md:flex md:flex-col md:items-center md:justify-center">
            <motion.div
              animate={{ scale: [1, 1.12, 1] }}
              transition={{ repeat: Infinity, duration: 2 }}
              className="grid h-14 w-14 place-items-center rounded-full bg-gradient-to-br from-rose-500 to-sky-400 text-lg font-black text-[#0C0A14] shadow-lg"
            >
              VS
            </motion.div>
          </div>

          {/* BLUE corner */}
          <Corner fighter={FIGHTERS.B} align="right" winner={winner} />
        </div>

        {/* Transcript */}
        <section className="mt-8 rounded-2xl border border-white/10 bg-white/[0.02] p-4 sm:p-6">
          <h2 className="mb-4 text-center text-xs font-semibold uppercase tracking-[0.25em] text-slate-500">
            Round-by-Round Transcript
          </h2>
          <div className="space-y-4">
            {TRANSCRIPT.map((t, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: t.side === "A" ? -24 : 24 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.05 * i }}
                className={
                  "flex " + (t.side === "A" ? "justify-start" : "justify-end")
                }
              >
                <div
                  className={
                    "max-w-[78%] rounded-2xl px-4 py-3 text-sm leading-relaxed ring-1 " +
                    (t.side === "A"
                      ? "rounded-tl-sm bg-rose-500/10 ring-rose-500/30"
                      : "rounded-tr-sm bg-sky-400/10 ring-sky-400/30")
                  }
                >
                  <div
                    className="mb-1 flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider"
                    style={{ color: t.side === "A" ? RED : BLUE }}
                  >
                    <span>{FIGHTERS[t.side].name}</span>
                    <span className="text-slate-600">· Round {t.round}</span>
                  </div>
                  <p className="text-slate-200">{t.text}</p>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Judge control */}
          <div className="mt-6 flex justify-center">
            {!winner && (
              <button
                onClick={judge}
                disabled={judging}
                className="group relative overflow-hidden rounded-full bg-gradient-to-r from-rose-500 to-sky-400 px-8 py-3 text-sm font-bold uppercase tracking-wider text-[#0C0A14] shadow-lg transition active:scale-95 disabled:opacity-70"
              >
                {judging ? "Judging…" : "Summon AI Judge"}
              </button>
            )}
            {winner && (
              <button
                onClick={reset}
                className="rounded-full border border-white/15 px-6 py-3 text-sm font-semibold text-slate-300 transition hover:bg-white/5"
              >
                Reset Match
              </button>
            )}
          </div>
        </section>

        <footer className="mt-8 text-center text-[11px] text-slate-600">
          Contract <span className="font-mono">{CONTRACT}</span>
        </footer>
      </div>

      {/* Winner banner drop */}
      <AnimatePresence>
        {winner && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 grid place-items-center bg-black/70 backdrop-blur-sm"
            onClick={reset}
          >
            <motion.div
              initial={{ y: -300, rotate: -6, opacity: 0 }}
              animate={{ y: 0, rotate: 0, opacity: 1 }}
              transition={{ type: "spring", stiffness: 120, damping: 12 }}
              onClick={(e) => e.stopPropagation()}
              className="relative w-[min(92vw,420px)] rounded-3xl border p-8 text-center shadow-2xl"
              style={{
                borderColor: FIGHTERS[winner].color,
                background:
                  "linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.01))",
                boxShadow: `0 0 60px ${FIGHTERS[winner].color}55`,
              }}
            >
              <p className="text-xs font-bold uppercase tracking-[0.4em] text-slate-400">
                Verdict
              </p>
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, type: "spring" }}
                className="mx-auto mt-4 grid h-20 w-20 place-items-center rounded-full text-3xl font-black text-[#0C0A14]"
                style={{ background: FIGHTERS[winner].color }}
              >
                {winner}
              </motion.div>
              <h2
                className="mt-4 text-2xl font-black"
                style={{ color: FIGHTERS[winner].color }}
              >
                {FIGHTERS[winner].name} Wins
              </h2>
              <p className="mt-1 text-sm text-slate-400">
                @{FIGHTERS[winner].handle} takes the pool
              </p>
              <p
                className="mt-4 text-3xl font-extrabold"
                style={{ color: FIGHTERS[winner].color }}
              >
                {pool.toFixed(2)} ETH
              </p>
              <button
                onClick={reset}
                className="mt-6 rounded-full border border-white/15 px-6 py-2 text-sm font-semibold text-slate-200 transition hover:bg-white/5"
              >
                Close
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function Corner({
  fighter,
  align,
  winner,
}: {
  fighter: Fighter;
  align: "left" | "right";
  winner: Side | null;
}) {
  const isWinner = winner === fighter.side;
  const isLoser = winner !== null && !isWinner;
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: isLoser ? 0.5 : 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className={
        "rounded-2xl border bg-white/[0.02] p-5 " +
        (align === "right" ? "text-right" : "text-left")
      }
      style={{
        borderColor: fighter.color + "55",
        boxShadow: isWinner ? `0 0 40px ${fighter.color}55` : undefined,
      }}
    >
      <div
        className={
          "flex items-center gap-3 " +
          (align === "right" ? "flex-row-reverse" : "")
        }
      >
        <div
          className="grid h-12 w-12 place-items-center rounded-xl text-lg font-black text-[#0C0A14]"
          style={{ background: fighter.color }}
        >
          {fighter.side}
        </div>
        <div className={align === "right" ? "text-right" : "text-left"}>
          <p className="text-lg font-bold" style={{ color: fighter.color }}>
            {fighter.name}
          </p>
          <p className="font-mono text-[11px] text-slate-500">
            {fighter.handle}
          </p>
        </div>
      </div>
      <div
        className={
          "mt-4 inline-flex items-center gap-2 rounded-lg bg-white/5 px-3 py-1.5 " +
          (align === "right" ? "flex-row-reverse" : "")
        }
      >
        <span className="text-[10px] uppercase tracking-wider text-slate-500">
          Staked
        </span>
        <span className="font-bold" style={{ color: fighter.color }}>
          {fighter.stake.toFixed(2)} ETH
        </span>
      </div>
      <p
        className="mt-3 text-[11px] font-semibold uppercase tracking-widest"
        style={{ color: fighter.color }}
      >
        {fighter.side === "A" ? "Red Corner" : "Blue Corner"}
      </p>
    </motion.div>
  );
}
