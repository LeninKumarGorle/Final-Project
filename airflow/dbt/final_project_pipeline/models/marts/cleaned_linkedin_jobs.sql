select
    job_title,
    company_name,
    location,
    job_url,
    description,
    role
from {{ ref('stg_linkedin_jobs') }}
where description is not null