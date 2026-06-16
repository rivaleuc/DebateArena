import json


def _prompt(gl_mod, ret):
    gl_mod.nondet.exec_prompt = lambda *a, **k: ret


def _make_judging(contract, gl_mod, rounds=1):
    gl_mod.message.sender_address = "0xHost"
    k = contract.open_debate("Is static typing better than dynamic typing?", rounds)
    gl_mod.message.sender_address = "0xAAA"
    contract.join(k, "a")
    gl_mod.message.sender_address = "0xBBB"
    contract.join(k, "b")
    arg = "This is a sufficiently long argument that clears the minimum length bar."
    for _ in range(rounds):
        gl_mod.message.sender_address = "0xAAA"
        contract.argue(k, arg)
        gl_mod.message.sender_address = "0xBBB"
        contract.argue(k, arg)
    d = contract.get_debate(k)
    assert d["status"] == "judging"
    return k


def test_anchor_majority_recomputed(contract, gl_mod):
    # Model claims winner 'b' but the per-round winners give A the majority (2-1).
    _prompt(gl_mod, {
        "winner": "b",
        "round_scores": [
            {"round": 1, "winner": "a", "reason": "x"},
            {"round": 2, "winner": "b", "reason": "y"},
            {"round": 3, "winner": "a", "reason": "z"},
        ],
        "summary": "close debate",
    })
    k = _make_judging(contract, gl_mod, rounds=1)
    contract.judge_debate(k)
    d = contract.get_debate(k)
    assert d["winner"] == "a"  # recomputed majority, not the model's claim


def test_anchor_tie_goes_to_a(contract, gl_mod):
    _prompt(gl_mod, {
        "winner": "b",
        "round_scores": [
            {"round": 1, "winner": "a", "reason": "x"},
            {"round": 2, "winner": "b", "reason": "y"},
        ],
        "summary": "tied",
    })
    k = _make_judging(contract, gl_mod, rounds=1)
    contract.judge_debate(k)
    d = contract.get_debate(k)
    assert d["winner"] == "a"  # tie -> 'a'


def test_validator_rejects_bad_inputs(contract, gl_mod):
    _prompt(gl_mod, {"winner": "a", "round_scores": [{"round": 1, "winner": "a", "reason": "r"}], "summary": "s"})
    k = _make_judging(contract, gl_mod, rounds=1)
    contract.judge_debate(k)
    v = gl_mod.vm._last_validator
    R = gl_mod.vm.Return
    assert v(object()) is False
    assert v(R("not json")) is False
    # bad overall winner enum
    assert v(R(json.dumps({"winner": "c", "round_scores": [{"winner": "a"}]}))) is False
    # empty round_scores (range check)
    assert v(R(json.dumps({"winner": "a", "round_scores": []}))) is False
    # per-round winner not in enum
    assert v(R(json.dumps({"winner": "a", "round_scores": [{"winner": "x"}]}))) is False
    # winner != recomputed majority (2 b's -> should be 'b', claims 'a')
    assert v(R(json.dumps({"winner": "a", "round_scores": [{"winner": "b"}, {"winner": "b"}]}))) is False
    # valid: majority 'b'
    assert v(R(json.dumps({"winner": "b", "round_scores": [{"winner": "b"}, {"winner": "b"}, {"winner": "a"}]}))) is True
    # valid: tie -> 'a'
    assert v(R(json.dumps({"winner": "a", "round_scores": [{"winner": "a"}, {"winner": "b"}]}))) is True


def test_normalized_output_always_validates(contract, gl_mod):
    # Messy per-round winners (uppercase / invalid) get normalized; winner derived.
    _prompt(gl_mod, {
        "winner": "zzz",
        "round_scores": [
            {"round": 1, "winner": "B", "reason": "r1"},
            {"round": 2, "winner": "bogus", "reason": "r2"},
            {"round": 3, "winner": "b", "reason": "r3"},
        ],
        "summary": "s",
    })
    k = _make_judging(contract, gl_mod, rounds=1)
    contract.judge_debate(k)  # raises if normalized output failed validation
    out = gl_mod.vm._last_leader()
    assert gl_mod.vm._last_validator(gl_mod.vm.Return(out)) is True
    data = json.loads(out)
    # round2 'bogus' -> 'a'; rounds are b, a, b => majority 'b'
    assert data["winner"] == "b"
    assert all(rs["winner"] in ("a", "b") for rs in data["round_scores"])
