/**
 * API Service for Bedtime Story App
 * Handles all backend communication
 */

const API_BASE_URL = 'http://localhost:8001';

export interface Story {
  _id?: string;
  id: string; // Computed from _id or id
  title: string;
  content: string;
  prompt: string;
  length_type: string;
  iterations: number;
  final_score?: {
    clarity: number;
    moralValue: number;
    ageAppropriateness: number;
    score: number;
    approved: boolean;
    feedback: string;
  };
  age_range?: string;
  image_url?: string;
  created_at: string;
  updated_at?: string;
}

export interface ChatResponse {
  success: boolean;
  response: string;
  should_generate_story: boolean;
  story_prompt?: string;
}

export interface StoryResponse {
  success: boolean;
  story: Story;
}

/**
 * Get TTS audio (MP3) for a given text using backend gTTS.
 */
export async function getTtsMp3(text: string, lang: string = 'en', slow: boolean = false): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/api/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, lang, slow })
  });
  if (!response.ok) {
    throw new Error(`TTS error: ${response.status}`);
  }
  return await response.blob();
}

/**
 * Send a chat message to the conversational agent
 */
export async function sendChatMessage(
  message: string,
  conversationHistory: Array<{ role: string; content: string }> = [],
  sessionId?: string,
): Promise<ChatResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        conversation_history: conversationHistory,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      let detail = '';
      try {
        const data = await response.json();
        detail = data?.detail || '';
      } catch {
        try { detail = await response.text(); } catch {}
      }
      const err = new Error(`HTTP error! status: ${response.status}${detail ? ` - ${detail}` : ''}`);
      // @ts-ignore augment
      (err as any).status = response.status;
      throw err;
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error sending chat message:', error);
    throw error;
  }
}

/**
 * Generate a new story
 */
export async function generateStory(
  prompt: string,
  lengthType: 'short' | 'medium' | 'long' = 'short',
  conversationHistory: Array<{ role: string; content: string }> = [],
  sessionId?: string,
): Promise<StoryResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/generate-story`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt,
        lengthType,
        conversation_history: conversationHistory,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      let detail = '';
      try {
        const data = await response.json();
        detail = data?.detail || '';
      } catch {
        try { detail = await response.text(); } catch {}
      }
      const err = new Error(`HTTP error! status: ${response.status}${detail ? ` - ${detail}` : ''}`);
      // @ts-ignore augment
      (err as any).status = response.status;
      throw err;
    }

    const data = await response.json();
    
    // Normalize storage ID to standard 'id' field for frontend compatibility
    if (data.story) {
      data.story.id = data.story.id || '';
    }
    
    return data;
  } catch (error) {
    console.error('Error generating story:', error);
    throw error;
  }
}

/**
 * Get previous stories from storage
 */
export async function getPreviousStories(limit: number = 10, sessionId?: string): Promise<Story[]> {
  try {
    const url = new URL(`${API_BASE_URL}/api/stories`);
    url.searchParams.set('limit', String(limit));
    if (sessionId) url.searchParams.set('session_id', sessionId);
    const response = await fetch(url.toString());

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    const stories = data.stories || [];
    
    // Normalize storage ID to standard 'id' field for frontend compatibility
    return stories.map((story: any) => ({
      ...story,
      id: story.id || ''
    }));
  } catch (error) {
    console.error('Error fetching stories:', error);
    return [];
  }
}

/**
 * Get a specific story by ID
 */
export async function getStoryById(storyId: string): Promise<Story | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/stories/${storyId}`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    const story = data.story;
    
    // Normalize storage ID to standard 'id' field for frontend compatibility
    if (story) {
      return {
        ...story,
        id: story.id || ''
      };
    }
    return null;
  } catch (error) {
    console.error('Error fetching story:', error);
    return null;
  }
}
