-- RUN THIS IN SUPABASE SQL EDITOR

-- 1. Reset Policies (to be safe)
drop policy if exists "Users can insert their own profile" on profiles;
drop policy if exists "Users can update own profile" on profiles;
drop policy if exists "Public profiles are viewable by everyone" on profiles;

-- 2. Ensure RLS is enabled
alter table profiles enable row level security;

-- 3. Create Permissive Policies for Auth Users
create policy "Public profiles are viewable by everyone"
  on profiles for select
  using ( true );

create policy "Users can insert their own profile"
  on profiles for insert
  with check ( auth.uid() = id );

create policy "Users can update own profile"
  on profiles for update
  using ( auth.uid() = id );

-- 4. CRITICAL: Handle Storage RLS
-- (Run this if you haven't created the bucket yet, or if it errors)
insert into storage.buckets (id, name, public)
values ('audio_recordings', 'audio_recordings', true)
on conflict (id) do nothing;

create policy "Any authenticated user can upload audio"
  on storage.objects for insert
  with check ( bucket_id = 'audio_recordings' and auth.role() = 'authenticated' );

create policy "Any user can view audio"
  on storage.objects for select
  using ( bucket_id = 'audio_recordings' );
