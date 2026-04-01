/**
 * MIRA Stylist — API Client
 * Clean, typed interface to the backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

interface APIResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  errors?: string[];
}

async function request<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<APIResponse<T>> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    return {
      success: false,
      data: null as any,
      message:
        body?.detail ||
        body?.message ||
        "Something unexpected happened. Please try again.",
    };
  }

  return res.json();
}

// ── Onboarding ─────────────────────────────────────────────────────────────

export async function getOnboardingQuestions() {
  return request("/api/onboarding/questions");
}

export async function submitOnboarding(responses: { question_id: string; answer: any }[]) {
  return request("/api/onboarding/submit", {
    method: "POST",
    body: JSON.stringify(responses),
  });
}

// ── Profile ────────────────────────────────────────────────────────────────

export async function getProfile(profileId: string) {
  return request(`/api/profile/${profileId}`);
}

export async function updateProfile(profileId: string, updates: Record<string, any>) {
  return request(`/api/profile/${profileId}`, {
    method: "PUT",
    body: JSON.stringify(updates),
  });
}

export async function listProfiles() {
  return request("/api/profile/");
}

// ── Try-On ─────────────────────────────────────────────────────────────────

export async function runTryOn(params: {
  person_image: string;
  garment_image: string;
  garment_category?: string;
}) {
  return request("/api/tryon/run", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function validateImages(personImage: string, garmentImage: string) {
  return request("/api/tryon/validate", {
    method: "POST",
    body: JSON.stringify({ person_image: personImage, garment_image: garmentImage }),
  });
}

// ── Saved Looks ────────────────────────────────────────────────────────────

export async function saveLook(look: any) {
  return request("/api/looks/", {
    method: "POST",
    body: JSON.stringify(look),
  });
}

export async function listLooks(params?: { collection_id?: string; favorites_only?: boolean }) {
  const query = new URLSearchParams();
  if (params?.collection_id) query.set("collection_id", params.collection_id);
  if (params?.favorites_only) query.set("favorites_only", "true");
  return request(`/api/looks/list?${query.toString()}`);
}

export async function getLook(lookId: string) {
  return request(`/api/looks/${lookId}`);
}

export async function toggleFavorite(lookId: string) {
  return request(`/api/looks/${lookId}/favorite`, { method: "POST" });
}

export async function deleteLook(lookId: string) {
  return request(`/api/looks/${lookId}`, { method: "DELETE" });
}

// ── Collections ────────────────────────────────────────────────────────────

export async function listCollections() {
  return request("/api/looks/collections/all");
}

export async function createCollection(collection: { name: string; description?: string }) {
  return request("/api/looks/collections/create", {
    method: "POST",
    body: JSON.stringify(collection),
  });
}

// ── Stylist ────────────────────────────────────────────────────────────────

export async function generateCommentary(params: {
  look_image_url: string;
  garment_category?: string;
  user_profile_id?: string;
  mode?: string;
  occasion?: string;
}) {
  return request("/api/stylist/commentary", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function compareLooks(lookIdA: string, lookIdB: string, profileId?: string) {
  const query = new URLSearchParams({ look_id_a: lookIdA, look_id_b: lookIdB });
  if (profileId) query.set("profile_id", profileId);
  return request(`/api/stylist/compare?${query.toString()}`, { method: "POST" });
}

export async function askStylist(params: {
  question: string;
  look_image_url: string;
  user_profile_id?: string;
  garment_brand?: string;
  garment_fit?: string;
  occasion?: string;
  commentary_payload?: Record<string, any>;
}) {
  return request("/api/stylist/ask", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

// ── Sizing ─────────────────────────────────────────────────────────────────

export async function recommendSize(params: {
  user_profile_id: string;
  garment_category: string;
  brand?: string;
  silhouette_intent?: string;
  fabric_stretch?: boolean;
}) {
  return request("/api/sizing/recommend", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function getSizeChart(brand?: string, category?: string) {
  const query = new URLSearchParams();
  if (brand) query.set("brand", brand);
  if (category) query.set("category", category);
  return request(`/api/sizing/chart?${query.toString()}`);
}

export async function explainSize(params: {
  user_profile_id: string;
  garment_category: string;
  brand?: string;
}) {
  return request("/api/sizing/explain", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

// ── Motion ─────────────────────────────────────────────────────────────────

export async function generateMotion(params: {
  look_id?: string;
  source_image_url: string;
  motion_preset?: string;
  custom_prompt?: string;
}) {
  return request("/api/motion/generate", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function getMotionPresets() {
  return request("/api/motion/presets");
}

// ── Voice ──────────────────────────────────────────────────────────────────

export async function synthesizeVoice(text: string, voiceStyle?: string) {
  return request("/api/voice/synthesize", {
    method: "POST",
    body: JSON.stringify({ text, voice_style: voiceStyle || "warm" }),
  });
}

export async function getWelcomeVoice(userName?: string) {
  const query = userName ? `?user_name=${encodeURIComponent(userName)}` : "";
  return request(`/api/voice/welcome${query}`);
}
