// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title StakePool — both debaters stake ETH, winner takes all
/// @notice Resolver reads GenLayer's read_winner() and pays out.
///         Simple: no token, just native ETH stakes.
contract StakePool {
    enum State { Empty, OneStaked, BothStaked, Resolved }

    struct Match {
        address sideA;
        address sideB;
        uint256 stake;
        State state;
        address winner;
    }

    address public resolver;
    mapping(uint256 => Match) public matches;

    event Staked(uint256 indexed debateId, address indexed player, string side);
    event Resolved(uint256 indexed debateId, address indexed winner, uint256 payout);

    modifier onlyResolver() {
        require(msg.sender == resolver, "only resolver");
        _;
    }

    constructor(address _resolver) {
        resolver = _resolver;
    }

    /// @notice First player stakes for a debate. Sets the stake amount.
    function stakeA(uint256 debateId) external payable {
        Match storage m = matches[debateId];
        require(m.state == State.Empty, "A already staked");
        require(msg.value > 0, "must stake ETH");
        m.sideA = msg.sender;
        m.stake = msg.value;
        m.state = State.OneStaked;
        emit Staked(debateId, msg.sender, "a");
    }

    /// @notice Second player matches the stake exactly.
    function stakeB(uint256 debateId) external payable {
        Match storage m = matches[debateId];
        require(m.state == State.OneStaked, "not ready for B");
        require(msg.value == m.stake, "must match stake");
        m.sideB = msg.sender;
        m.state = State.BothStaked;
        emit Staked(debateId, msg.sender, "b");
    }

    /// @notice Resolver declares winner after GenLayer judgment.
    function resolve(uint256 debateId, address winnerAddr) external onlyResolver {
        Match storage m = matches[debateId];
        require(m.state == State.BothStaked, "not both staked");
        require(winnerAddr == m.sideA || winnerAddr == m.sideB, "invalid winner");
        m.winner = winnerAddr;
        m.state = State.Resolved;
        uint256 payout = m.stake * 2;
        payable(winnerAddr).transfer(payout);
        emit Resolved(debateId, winnerAddr, payout);
    }

    function getMatch(uint256 debateId) external view returns (
        address sideA, address sideB, uint256 stake, State state, address winner
    ) {
        Match storage m = matches[debateId];
        return (m.sideA, m.sideB, m.stake, m.state, m.winner);
    }
}
