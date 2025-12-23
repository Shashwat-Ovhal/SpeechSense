-- 1. Create Profiles Table (Publicly viewable profiles)
create table public.profiles (
  id uuid not null references auth.users on delete cascade,
  full_name text,
  role text check (role in ('patient', 'doctor', 'admin')),
  created_at timestamptz default now(),
  primary key (id)
);

-- 2. Enable RLS on Profiles
alter table public.profiles enable row level security;

create policy "Public profiles are viewable by everyone"
  on profiles for select
  using ( true );

create policy "Users can insert their own profile"
  on profiles for insert
  with check ( auth.uid() = id );

create policy "Users can update own profile"
  on profiles for update
  using ( auth.uid() = id );

-- 3. Create Recordings Table
create table public.recordings (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users not null,
  audio_path text not null,
  audio_url text, -- optional if we generate signed urls dynamically
  duration_sec float,
  features jsonb, -- AI results go here
  metadata jsonb, -- Patient status, age, gender etc
  created_at timestamptz default now()
);

-- 4. Enable RLS on Recordings
alter table public.recordings enable row level security;

-- Doctors/Admins can view all, Patients view their own (Simplified: Everyone view all in MVP for now?)
-- Let's do: Users view own. Doctors view all.
create policy "Users view own recordings"
  on recordings for select
  using ( auth.uid() = user_id );

create policy "Users insert own recordings"
  on recordings for insert
  with check ( auth.uid() = user_id );

-- (Optional) Doctors view all policy would need logic to check profile role.

-- 5. Storage Bucket Setup (You might need to do this in UI)
-- Create a bucket named 'audio_recordings'.
-- Policy: SELECT for Authenticated. INSERT for Authenticated.
