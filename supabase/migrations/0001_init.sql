-- PSLE question bank + learner data (Supabase / Postgres)
-- Serving layer: questions/options/tags are exported from Neo4j; attempts and
-- mastery capture learner interactions for spaced repetition + gamification.

create table if not exists questions (
  qid               text primary key,
  stem              text not null,
  subject           text not null,
  syllabus_version  text,
  theme             text,
  cognitive_level   text,
  difficulty_band   text,
  status            text default 'answered',
  provenance        text default 'ingested',
  created_at        timestamptz default now()
);

create table if not exists options (
  qid           text references questions(qid) on delete cascade,
  label         text not null,                 -- '1'..'4'
  text          text not null,
  is_correct    boolean not null default false,
  rationale     text,
  misconception text,
  primary key (qid, label)
);

create table if not exists question_tags (
  qid   text references questions(qid) on delete cascade,
  kind  text not null,                          -- 'concept' | 'learning_outcome' | 'theme'
  value text not null,
  primary key (qid, kind, value)
);

-- Learner data ---------------------------------------------------------------
create table if not exists attempts (
  id          bigint generated always as identity primary key,
  user_id     uuid,
  qid         text references questions(qid),
  chosen      text,
  is_correct  boolean,
  latency_ms  integer,
  created_at  timestamptz default now()
);

-- One mastery row per (user, concept) drives spaced repetition (SM-2-ish).
create table if not exists mastery (
  user_id     uuid,
  concept     text,
  ability     real default 0,        -- running estimate 0..1
  reps        integer default 0,
  ease        real default 2.5,      -- SM-2 ease factor
  interval_d  integer default 0,     -- days until next review
  due_at      timestamptz default now(),
  updated_at  timestamptz default now(),
  primary key (user_id, concept)
);

create index if not exists idx_questions_subject on questions(subject, syllabus_version);
create index if not exists idx_questions_theme on questions(theme);
create index if not exists idx_tags_value on question_tags(kind, value);
create index if not exists idx_mastery_due on mastery(user_id, due_at);

-- Convenience view: a question with its options as JSON (for serving).
create or replace view question_full as
select q.*,
       (select jsonb_agg(jsonb_build_object(
                 'label', o.label, 'text', o.text, 'is_correct', o.is_correct,
                 'rationale', o.rationale, 'misconception', o.misconception)
                 order by o.label)
        from options o where o.qid = q.qid) as options,
       (select jsonb_agg(t.value) from question_tags t
        where t.qid = q.qid and t.kind = 'concept') as concepts
from questions q;
