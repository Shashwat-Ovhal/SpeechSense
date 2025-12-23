-- RUN THIS IN SUPABASE SQL EDITOR TO FIX THE "PROFILE CREATION" ERROR

-- 1. Create a Function to handle new user creation
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, full_name, role)
  values (
    new.id,
    new.raw_user_meta_data ->> 'full_name',
    coalesce(new.raw_user_meta_data ->> 'role', 'patient')
  );
  return new;
end;
$$;

-- 2. Create the Trigger
drop trigger if exists on_auth_user_created on auth.users;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- 3. Cleanup (Optional: remove permissive policies if you want strict security)
-- For now, we leave the SELECT policies so the app can read the profile.
