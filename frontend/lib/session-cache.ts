const PROFILE_PREFIX = "mira_profile_snapshot:";
const LOOKS_KEY = "mira_looks_snapshot";
const USER_NAME_KEY = "mira_user_name";

type CacheEnvelope<T> = {
  data: T;
  savedAt: number;
};

function isBrowser() {
  return typeof window !== "undefined";
}

function readCache<T>(key: string): T | null {
  if (!isBrowser()) return null;

  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as CacheEnvelope<T> | T;
    if (parsed && typeof parsed === "object" && "data" in parsed) {
      return (parsed as CacheEnvelope<T>).data;
    }
    return parsed as T;
  } catch {
    return null;
  }
}

function writeCache<T>(key: string, data: T) {
  if (!isBrowser()) return;

  try {
    const payload: CacheEnvelope<T> = {
      data,
      savedAt: Date.now(),
    };
    window.localStorage.setItem(key, JSON.stringify(payload));
  } catch {
    // Ignore storage write failures so the app flow stays uninterrupted.
  }
}

export function getCachedProfileSnapshot<T = any>(profileId: string) {
  return readCache<T>(`${PROFILE_PREFIX}${profileId}`);
}

export function cacheProfileSnapshot(profile: any) {
  if (!profile?.id) return;
  writeCache(`${PROFILE_PREFIX}${profile.id}`, profile);

  if (typeof profile.name === "string" && profile.name.trim()) {
    try {
      window.localStorage.setItem(USER_NAME_KEY, profile.name.trim());
    } catch {
      // Ignore storage write failures.
    }
  }
}

export function getCachedLooksSnapshot<T = any[]>() {
  return readCache<T>(LOOKS_KEY);
}

export function cacheLooksSnapshot(looks: any[]) {
  writeCache(LOOKS_KEY, looks.slice(0, 40));
}

export function upsertCachedLook(look: any) {
  if (!look?.look_id) return;
  const current = getCachedLooksSnapshot<any[]>() || [];
  const next = [look, ...current.filter((item) => item?.look_id !== look.look_id)];
  cacheLooksSnapshot(next);
}

export function removeCachedLook(lookId: string) {
  const current = getCachedLooksSnapshot<any[]>() || [];
  cacheLooksSnapshot(current.filter((item) => item?.look_id !== lookId));
}
