-- sample data
BEGIN;

INSERT INTO
    polls (id, title, closes_at)
VALUES
    (
        1,
        'Favourite cloud provider',
        NOW() + INTERVAL '7 days'
    ),
    (
        2,
        'Best programming language',
        NOW() + INTERVAL '7 days'
    );

INSERT INTO
    options (id, poll_id, label)
VALUES
    (1, 1, 'AWS'),
    (2, 1, 'GCP'),
    (3, 1, 'Azure'),
    (4, 2, 'Python'),
    (5, 2, 'Go'),
    (6, 2, 'Rust');

INSERT INTO
    votes (poll_id, option_id, voter_id)
VALUES
    (1, 1, 'user-a'),
    (1, 1, 'user-b'),
    (1, 2, 'user-c'),
    (1, 3, 'user-d'),
    (2, 4, 'user-a'),
    (2, 5, 'user-b'),
    (2, 4, 'user-c');

-- keep sequences in sync after explicit id inserts
SELECT
    setval(
        'polls_id_seq',
        (
            SELECT
                MAX(id)
            FROM
                polls
        )
    );

SELECT
    setval(
        'options_id_seq',
        (
            SELECT
                MAX(id)
            FROM
                options
        )
    );

COMMIT;