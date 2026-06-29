-- Auth + persistent gamification, and rich-question columns.
-- Apply after 0001_init.sql.

-- --- rich question columns ---------------------------------------------------
alter table questions add column if not exists stem_blocks jsonb default '[]'::jsonb;
alter table questions add column if not exists hint text;
alter table options   add column if not exists image text;
alter table attempts  add column if not exists attempt_no int default 1;

-- --- profiles (1:1 with auth.users), carrying persistent gamification --------
create table if not exists profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  email       text,
  points      int  default 0,
  streak      int  default 0,
  last_day    date,
  updated_at  timestamptz default now()
);

-- make learner tables user-scoped
alter table attempts alter column user_id set default auth.uid();
alter table mastery  alter column user_id set default auth.uid();

-- auto-create a profile row when a user signs up
create or replace function handle_new_user() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, email) values (new.id, new.email)
  on conflict (id) do nothing;
  return new;
end;
$$;
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users for each row execute function handle_new_user();

-- --- Row Level Security ------------------------------------------------------
alter table profiles enable row level security;
alter table attempts enable row level security;
alter table mastery  enable row level security;

-- questions/options/tags are public read (the shared bank)
alter table questions enable row level security;
alter table options   enable row level security;
alter table question_tags enable row level security;

do $$ begin
  -- own profile
  create policy profiles_self on profiles
    for all using (auth.uid() = id) with check (auth.uid() = id);
  -- own attempts / mastery
  create policy attempts_self on attempts
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
  create policy mastery_self on mastery
    for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
  -- public read of the bank
  create policy questions_read on questions for select using (true);
  create policy options_read   on options   for select using (true);
  create policy tags_read      on question_tags for select using (true);
exception when duplicate_object then null; end $$;

-- refresh the serving view to include rich fields
create or replace view question_full as
select q.*,
       (select jsonb_agg(jsonb_build_object(
                 'label', o.label, 'text', o.text, 'image', o.image,
                 'is_correct', o.is_correct, 'rationale', o.rationale,
                 'misconception', o.misconception) order by o.label)
        from options o where o.qid = q.qid) as options,
       (select jsonb_agg(t.value) from question_tags t
        where t.qid = q.qid and t.kind = 'concept') as concepts
from questions q;
