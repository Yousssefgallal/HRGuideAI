/**
 * API Service Layer for Chat History
 * Handles all backend communication for conversations and messages
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

// ============================================================
// TYPES
// ============================================================

export interface Conversation {
  conversation_id: number;
  user_id: number;
  title: string;
  thread_id: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface MessageContent {
  text: string;
  metadata?: Record<string, unknown>;
  tool_calls?: Array<{
    name: string;
    args: Record<string, unknown>;
    id: string;
  }>;
}

export interface Message {
  message_id: number;
  conversation_id: number;
  role: "user" | "assistant" | "system" | "tool";
  content: MessageContent;
  created_at: string;
}

export interface CreateConversationRequest {
  user_id: number;
  title?: string;
}

export interface UpdateConversationRequest {
  title?: string;
  is_active?: boolean;
}

// ============================================================
// CONVERSATION API
// ============================================================

/**
 * Create a new conversation
 */
export async function createConversation(
  userId: number,
  title: string = "New Conversation"
): Promise<Conversation> {
  const response = await fetch(`${API_BASE_URL}/conversations/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_id: userId,
      title,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to create conversation: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get all conversations for a user
 */
export async function getUserConversations(
  userId: number,
  includeInactive: boolean = false
): Promise<Conversation[]> {
  const params = new URLSearchParams();
  if (includeInactive) {
    params.append("include_inactive", "true");
  }

  const url = `${API_BASE_URL}/conversations/user/${userId}${
    params.toString() ? `?${params.toString()}` : ""
  }`;

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Failed to fetch conversations: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get a specific conversation by ID
 */
export async function getConversation(conversationId: number): Promise<Conversation> {
  const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch conversation: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get a conversation by thread_id
 */
export async function getConversationByThreadId(threadId: string): Promise<Conversation> {
  const response = await fetch(`${API_BASE_URL}/conversations/thread/${threadId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch conversation: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Update a conversation (e.g., change title)
 */
export async function updateConversation(
  conversationId: number,
  updates: UpdateConversationRequest
): Promise<Conversation> {
  const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    throw new Error(`Failed to update conversation: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Delete a conversation
 */
export async function deleteConversation(
  conversationId: number,
  softDelete: boolean = true
): Promise<void> {
  const params = new URLSearchParams();
  params.append("soft_delete", softDelete.toString());

  const response = await fetch(
    `${API_BASE_URL}/conversations/${conversationId}?${params.toString()}`,
    {
      method: "DELETE",
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to delete conversation: ${response.statusText}`);
  }
}

// ============================================================
// MESSAGE API
// ============================================================

export async function createMessage(payload: {
  conversation_id: number;
  role: "user" | "assistant" | "system" | "tool";
  content: {
    text: string;
    metadata?: Record<string, unknown>;
  };
}) {
  const response = await fetch(`${API_BASE_URL}/messages/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error("Failed to save message");
  }

  return response.json();
}


/**
 * Get all messages for a conversation
 */
export async function getMessages(
  conversationId: number,
  limit: number = 100,
  offset: number = 0
): Promise<Message[]> {
  const params = new URLSearchParams();
  params.append("limit", limit.toString());
  params.append("offset", offset.toString());

  const response = await fetch(
    `${API_BASE_URL}/messages/${conversationId}?${params.toString()}`
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch messages: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get message count for a conversation
 */
export async function getMessageCount(conversationId: number): Promise<number> {
  const response = await fetch(`${API_BASE_URL}/messages/count/${conversationId}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch message count: ${response.statusText}`);
  }

  const data = await response.json();
  return data.message_count;
}

/**
 * Delete a specific message
 */
export async function deleteMessage(messageId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/messages/${messageId}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    throw new Error(`Failed to delete message: ${response.statusText}`);
  }
}

/**
 * Delete all messages in a conversation
 */
export async function deleteAllMessages(conversationId: number): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/messages/conversation/${conversationId}/all`,
    {
      method: "DELETE",
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to delete messages: ${response.statusText}`);
  }
}
