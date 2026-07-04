-- tally query
SELECT
    p.id AS poll_id,
    p.title AS poll_title,
    o.id AS option_id,
    o.label AS option_label,
    COUNT(v.id) AS vote_count
FROM
    polls p
    JOIN options o ON o.poll_id = p.id
    LEFT JOIN votes v ON v.option_id = o.id
WHERE
    p.id = 1 -- change to target a different poll
GROUP BY
    p.id,
    p.title,
    o.id,
    o.label
ORDER BY
    vote_count DESC,
    o.id;