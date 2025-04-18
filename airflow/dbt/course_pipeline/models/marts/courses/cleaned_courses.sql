WITH base AS (
  SELECT *
  FROM {{ ref('raw_courses') }}
),

cleaned AS (
  SELECT
    title,
    url,
    TRY_CAST(rating AS FLOAT) AS rating,
    TRY_CAST(reviews AS INT) AS reviews,
    skills,
    job_role
  FROM base
 WHERE
    title IS NOT NULL
    AND url IS NOT NULL
    AND skills IS NOT NULL
),

filtered AS (
  SELECT *
  FROM cleaned
  WHERE
    rating >= 4.5
    AND reviews >= 3000
)

SELECT * FROM filtered