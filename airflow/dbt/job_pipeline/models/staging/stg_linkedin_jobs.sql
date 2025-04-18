with raw as (
    select * from {{ ref('raw_linkedin_jobs') }}
)

select
    initcap(title) as job_title,
    upper(company) as company_name,
    location,
    job_url,
    coalesce(nullif(description, ''), 'N/A') as description,
    role
from raw
where job_url is not null