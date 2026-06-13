# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
import json
from genlayer import *

ROUNDS_MAX = 3
MIN_ARGUMENT_LEN = 50


class DebateArena(gl.Contract):
    host: str
    debates: TreeMap[str, str]
    debate_count: u256

    def __init__(self):
        self.host = str(gl.message.sender_address)
        self.debate_count = u256(0)

    @gl.public.write
    def open_debate(self, topic: str, rounds: int) -> str:
        topic = str(topic).strip()
        if not topic or len(topic) > 500:
            raise Exception("topic required (max 500 chars)")
        rounds = max(1, min(ROUNDS_MAX, int(rounds)))

        key = str(int(self.debate_count))
        debate = {
            "topic": topic,
            "creator": str(gl.message.sender_address),
            "rounds": rounds,
            "current_round": 0,
            "side_a": "",
            "side_b": "",
            "arguments_a": [],
            "arguments_b": [],
            "status": "open",
            "winner": "",
            "scores": [],
        }
        self.debates[key] = json.dumps(debate)
        self.debate_count += u256(1)
        return key

    @gl.public.write
    def join(self, debate_key: str, side: str) -> None:
        debate_key = str(debate_key)
        if debate_key not in self.debates:
            raise Exception("unknown debate")
        d = json.loads(self.debates[debate_key])
        if d["status"] != "open":
            raise Exception("debate not open")

        addr = str(gl.message.sender_address)
        side = str(side).strip().lower()
        if side == "a":
            if d["side_a"]:
                raise Exception("side A taken")
            d["side_a"] = addr
        elif side == "b":
            if d["side_b"]:
                raise Exception("side B taken")
            d["side_b"] = addr
        else:
            raise Exception("side must be 'a' or 'b'")

        if d["side_a"] and d["side_b"]:
            d["status"] = "active"
            d["current_round"] = 1
        self.debates[debate_key] = json.dumps(d)

    @gl.public.write
    def argue(self, debate_key: str, argument: str) -> None:
        debate_key = str(debate_key)
        if debate_key not in self.debates:
            raise Exception("unknown debate")
        d = json.loads(self.debates[debate_key])
        if d["status"] != "active":
            raise Exception("debate not active")

        argument = str(argument).strip()
        if len(argument) < MIN_ARGUMENT_LEN:
            raise Exception(f"argument too short (min {MIN_ARGUMENT_LEN} chars)")

        addr = str(gl.message.sender_address)
        current = d["current_round"]

        if addr == d["side_a"]:
            if len(d["arguments_a"]) >= current:
                raise Exception("already argued this round")
            d["arguments_a"].append(argument[:2000])
        elif addr == d["side_b"]:
            if len(d["arguments_b"]) >= current:
                raise Exception("already argued this round")
            d["arguments_b"].append(argument[:2000])
        else:
            raise Exception("not a participant")

        # Advance round if both sides argued
        if len(d["arguments_a"]) >= current and len(d["arguments_b"]) >= current:
            if current >= d["rounds"]:
                d["status"] = "judging"
            else:
                d["current_round"] = current + 1

        self.debates[debate_key] = json.dumps(d)

    @gl.public.write
    def judge_debate(self, debate_key: str) -> None:
        debate_key = str(debate_key)
        if debate_key not in self.debates:
            raise Exception("unknown debate")
        d = json.loads(self.debates[debate_key])
        if d["status"] != "judging":
            raise Exception("debate not ready for judgment")

        verdict = self._ai_judge(d)
        d["winner"] = verdict["winner"]
        d["scores"] = verdict["round_scores"]
        d["status"] = "finished"
        self.debates[debate_key] = json.dumps(d)

    def _ai_judge(self, debate: dict) -> dict:
        topic = debate["topic"]
        args_a = debate["arguments_a"]
        args_b = debate["arguments_b"]

        def leader_fn() -> str:
            rounds_text = ""
            for i in range(len(args_a)):
                rounds_text += f"\n--- Round {i+1} ---\n"
                rounds_text += f"Side A: {args_a[i][:800]}\n"
                rounds_text += f"Side B: {args_b[i][:800]}\n"

            prompt = f"""You are judging a structured debate.

TOPIC: {topic}

DEBATE TRANSCRIPT:{rounds_text}

SCORING RULES:
1. Score each round separately: who made a stronger argument? (A or B)
2. Consider: evidence quality, logical coherence, addressing opponent's points, originality.
3. The side that wins more rounds wins overall.
4. If tied, pick the side with better overall argumentation quality.

Reply ONLY valid JSON:
{{"winner": "a" or "b", "round_scores": [{{"round": 1, "winner": "a"/"b", "reason": "..."}}], "summary": "<overall reasoning>"}}
No markdown."""

            raw = gl.nondet.exec_prompt(prompt, response_format="json")
            if isinstance(raw, dict):
                return json.dumps(raw)
            return str(raw).strip()

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                data = json.loads(leader_result.calldata)
                if data.get("winner") not in ("a", "b"):
                    return False
                if not isinstance(data.get("round_scores"), list):
                    return False
                return True
            except Exception:
                return False

        result_str = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        return json.loads(result_str)

    # -- Views --

    @gl.public.view
    def get_debate(self, key: str) -> dict:
        key = str(key)
        if key not in self.debates:
            return {"exists": False}
        return json.loads(self.debates[key])

    @gl.public.view
    def read_winner(self, key: str) -> dict:
        """StakePool reads this to distribute winnings."""
        key = str(key)
        if key not in self.debates:
            return {"resolved": False}
        d = json.loads(self.debates[key])
        if d["status"] != "finished":
            return {"resolved": False}
        winner_addr = d["side_a"] if d["winner"] == "a" else d["side_b"]
        return {"resolved": True, "winner": d["winner"], "winner_address": winner_addr}

    @gl.public.view
    def stats(self) -> dict:
        total = int(self.debate_count)
        finished = 0
        for i in range(total):
            d = json.loads(self.debates[str(i)])
            if d["status"] == "finished":
                finished += 1
        return {"total_debates": total, "finished": finished}
