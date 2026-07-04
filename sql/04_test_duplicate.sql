-- verify UNIQUE(poll_id, voter_id) rejects a duplicate vote
-- expected: ERROR — duplicate key value violates unique constraint "uq_votes_poll_voter"
INSERT INTO
    votes (poll_id, option_id, voter_id)
VALUES
    (1, 2, 'user-a');

-- user-a already voted in poll 1