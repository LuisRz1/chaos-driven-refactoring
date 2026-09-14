create extension if not exists pgcrypto;

create schema if not exists cdr;

create table if not exists cdr.projects (
  id text primary key,
  name text not null,
  repo_url text not null,
  default_branch text not null default 'main',
  services jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists cdr.scenarios (
  id text primary key,
  project_id text references cdr.projects (id) on delete cascade,
  name text not null,
  config jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists cdr.runs (
  id text primary key,
  project_id text,
  scenario_id text,
  scenario_name text not null,
  status text not null default 'queued',
  mode text not null default 'mock',
  target_repo text not null,
  commit_sha text not null default '',
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  collapse_detected boolean not null default false,
  summary jsonb not null default '{}'::jsonb
);

create table if not exists cdr.run_phases (
  id bigint generated always as identity primary key,
  run_id text not null references cdr.runs (id) on delete cascade,
  phase text not null,
  status text not null,
  label text not null,
  detail text,
  created_at timestamptz not null default now()
);

create table if not exists cdr.telemetry_samples (
  id bigint generated always as identity primary key,
  run_id text not null references cdr.runs (id) on delete cascade,
  kind text not null default 'before',
  t integer not null,
  p95 numeric not null,
  p99 numeric not null,
  error_rate numeric not null,
  rps numeric not null
);

create table if not exists cdr.findings (
  id uuid primary key default gen_random_uuid(),
  run_id text not null references cdr.runs (id) on delete cascade,
  category text not null,
  confidence numeric not null,
  root_cause text not null,
  evidence jsonb not null default '[]'::jsonb,
  file_path text not null,
  symbol text not null,
  created_at timestamptz not null default now()
);

create table if not exists cdr.diagnoses (
  id uuid primary key default gen_random_uuid(),
  run_id text not null references cdr.runs (id) on delete cascade,
  finding_id uuid references cdr.findings (id) on delete set null,
  model text not null,
  analysis_md text not null,
  proposed_change text not null,
  bob_task_id text,
  bobcoins numeric,
  target_files jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists cdr.patches (
  id uuid primary key default gen_random_uuid(),
  run_id text not null references cdr.runs (id) on delete cascade,
  branch text not null,
  pr_url text,
  files_changed jsonb not null default '[]'::jsonb,
  diff text not null,
  source text not null default 'template',
  bob_task_id text,
  bobcoins numeric,
  created_at timestamptz not null default now()
);

create table if not exists cdr.verifications (
  id uuid primary key default gen_random_uuid(),
  run_id text not null references cdr.runs (id) on delete cascade,
  stable boolean not null,
  before jsonb not null,
  after jsonb not null,
  improvement_pct jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists runs_started_at_idx on cdr.runs (started_at desc);
create index if not exists run_phases_run_id_idx on cdr.run_phases (run_id);
create index if not exists telemetry_samples_run_id_idx on cdr.telemetry_samples (run_id);
create index if not exists findings_run_id_idx on cdr.findings (run_id);

alter table cdr.projects enable row level security;
alter table cdr.scenarios enable row level security;
alter table cdr.runs enable row level security;
alter table cdr.run_phases enable row level security;
alter table cdr.telemetry_samples enable row level security;
alter table cdr.findings enable row level security;
alter table cdr.diagnoses enable row level security;
alter table cdr.patches enable row level security;
alter table cdr.verifications enable row level security;

create policy "public read projects" on cdr.projects for select using (true);
create policy "public read scenarios" on cdr.scenarios for select using (true);
create policy "public read runs" on cdr.runs for select using (true);
create policy "public read run_phases" on cdr.run_phases for select using (true);
create policy "public read telemetry_samples" on cdr.telemetry_samples for select using (true);
create policy "public read findings" on cdr.findings for select using (true);
create policy "public read diagnoses" on cdr.diagnoses for select using (true);
create policy "public read patches" on cdr.patches for select using (true);
create policy "public read verifications" on cdr.verifications for select using (true);

grant usage on schema cdr to anon, authenticated, service_role;
grant select on all tables in schema cdr to anon, authenticated;
grant all on all tables in schema cdr to service_role;
grant usage, select on all sequences in schema cdr to anon, authenticated;
grant all on all sequences in schema cdr to service_role;
