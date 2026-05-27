-- print3d_jobs: tracks async 3D model generation jobs for /v1/chat → /v1/generate/{jobId}
-- idempotency_keys: prevents duplicate POST processing for /v1/chat and /v1/download

-- ── Job status enum ───────────────────────────────────────────────────────────
create type print3d_job_status as enum ('pending', 'processing', 'complete', 'failed');

-- ── Jobs table ────────────────────────────────────────────────────────────────
create table print3d_jobs (
    id              uuid primary key default gen_random_uuid(),
    customer_id     text        not null,
    status          print3d_job_status not null default 'pending',
    progress        smallint    not null default 0 check (progress between 0 and 100),
    brief           jsonb,
    meshy_task_id   text,
    glb_path        text,
    stl_path        text,
    slice_result    jsonb,
    quote_result    jsonb,
    error           jsonb,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now(),
    expires_at      timestamptz not null default (now() + interval '24 hours')
);

create index print3d_jobs_customer_id_idx on print3d_jobs (customer_id);
create index print3d_jobs_status_idx      on print3d_jobs (status);
create index print3d_jobs_expires_at_idx  on print3d_jobs (expires_at);

-- Auto-update updated_at on row change
create or replace function update_print3d_jobs_updated_at()
returns trigger language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create trigger trg_print3d_jobs_updated_at
    before update on print3d_jobs
    for each row execute function update_print3d_jobs_updated_at();

-- RLS: service role only — the v1 API runs as service role, no anon access
alter table print3d_jobs enable row level security;

create policy "service role full access" on print3d_jobs
    using (auth.role() = 'service_role')
    with check (auth.role() = 'service_role');

-- ── Idempotency keys table ────────────────────────────────────────────────────
create table print3d_idempotency_keys (
    key             text        not null,
    customer_id     text        not null,
    response_body   jsonb       not null,
    created_at      timestamptz not null default now(),
    expires_at      timestamptz not null default (now() + interval '24 hours'),
    primary key (key, customer_id)
);

create index print3d_idempotency_expires_at_idx on print3d_idempotency_keys (expires_at);

alter table print3d_idempotency_keys enable row level security;

create policy "service role full access" on print3d_idempotency_keys
    using (auth.role() = 'service_role')
    with check (auth.role() = 'service_role');
