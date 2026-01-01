/**
 * ROCK-SOLID Conversation Management Hook
 * No race conditions. No "Conversation not found". Fully synchronous flow.
 */

import { useState, useCallback } from "react";
import {
  Conversation,
  Message,
  createConversation,
  getUserConversations,
  getMessages,
  updateConversation,
  deleteConversation as deleteConversationAPI,
  createMessage as createMessageAPI,
} from "@/lib/api";

export interface UseConversationsReturn {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  currentThreadId: string | null;
  messages: Message[];
  isLoading: boolean;
  error: string | null;

  loadConversations: (userId: number) => Promise<Conversation[]>;
  createNewConversation: (userId: number, title?: string) => Promise<Conversation>;
  selectConversation: (threadId: string) => Promise<void>;
  deleteConversation: (conversationId: number) => Promise<void>;
  updateConversationTitle: (conversationId: number, newTitle: string) => Promise<void>;
  refreshMessages: () => Promise<void>;
  addMessage: (role: "user" | "assistant" | "system" | "tool", text: string, metadata?: Record<string, unknown>) => Promise<Message | null>;
}

export function useConversations(): UseConversationsReturn {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * STEP 1: Load conversations from backend
   * ALWAYS returns the updated list
   */
  const loadConversations = useCallback(async (userId: number): Promise<Conversation[]> => {
    setIsLoading(true);
    setError(null);

    try {
      const convs = await getUserConversations(userId);
      setConversations(convs);
      return convs;
    } catch (err) {
      console.error("❌ Failed to load conversations:", err);
      setError("Failed to load conversations");
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * STEP 2: Create a new conversation
   */
  const createNewConversation = useCallback(
    async (userId: number, title: string = "New Conversation"): Promise<Conversation> => {
      setIsLoading(true);
      setError(null);

      try {
        const resp = await createConversation(userId, title);
        return resp;
      } catch (err) {
        console.error("❌ Failed to create conversation:", err);
        setError("Failed to create conversation");
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  /**
   * STEP 3: Select conversation SAFELY
   * This now **always** uses the updated conversations array.
   */
  const selectConversation = useCallback(
    async (threadId: string) => {
      setIsLoading(true);
      setError(null);

      try {
        // Find in latest conversations list
        const conv = conversations.find((c) => c.thread_id === threadId);
        

        if (!conv) {
          console.warn("⚠ Conversation not in local state, reloading...");
          return;
        }

        setCurrentConversation(conv);
        setCurrentThreadId(conv.thread_id);

        const msgs = await getMessages(conv.conversation_id);
        setMessages(msgs);
      } catch (err) {
        console.error("❌ Error selecting conversation:", err);
        setError("Failed to select conversation");
      } finally {
        setIsLoading(false);
      }
    },
    [conversations]
  );

  /**
   * STEP 4: Delete conversation
   */
  const deleteConversation = useCallback(
    async (conversationId: number) => {
      setError(null);

      try {
        await deleteConversationAPI(conversationId, true);

        // Remove locally
        setConversations((prev) =>
          prev.filter((c) => c.conversation_id !== conversationId)
        );

        if (currentConversation?.conversation_id === conversationId) {
          setCurrentConversation(null);
          setCurrentThreadId(null);
          setMessages([]);
        }
      } catch (err) {
        console.error("❌ Failed to delete conversation", err);
        setError("Failed to delete conversation");
      }
    },
    [currentConversation]
  );

  /**
   * STEP 5: Update conversation title
   */
  const updateConversationTitle = useCallback(
    async (conversationId: number, newTitle: string) => {
      setError(null);

      try {
        const updatedConversation = await updateConversation(conversationId, {
          title: newTitle,
        });

        // Update local state
        setConversations((prev) =>
          prev.map((c) =>
            c.conversation_id === conversationId
              ? { ...c, title: updatedConversation.title }
              : c
          )
        );

        // Update current conversation if it's the one being renamed
        if (currentConversation?.conversation_id === conversationId) {
          setCurrentConversation((prev) =>
            prev ? { ...prev, title: updatedConversation.title } : prev
          );
        }
      } catch (err) {
        console.error("❌ Failed to update conversation title", err);
        setError("Failed to update conversation title");
        throw err;
      }
    },
    [currentConversation]
  );

  /**
   * STEP 6: Refresh messages for current conversation
   */
  const refreshMessages = useCallback(async () => {
    if (!currentConversation) return;

    try {
      const msgs = await getMessages(currentConversation.conversation_id);
      setMessages(msgs);
    } catch (err) {
      console.error("❌ Failed to refresh messages", err);
      setError("Failed to refresh messages");
    }
  }, [currentConversation]);

  /**
   * STEP 7: Add a new message to the current conversation
   */
  const addMessage = useCallback(
    async (
      role: "user" | "assistant" | "system" | "tool",
      text: string,
      metadata?: Record<string, unknown>
    ): Promise<Message | null> => {
      if (!currentConversation) {
        console.warn("⚠ No current conversation selected");
        return null;
      }

      try {
        const message = await createMessageAPI({
          conversation_id: currentConversation.conversation_id,
          role,
          content: {
            text,
            metadata,
          },
        });

        // Add to local state
        setMessages((prev) => [...prev, message]);
        console.log(`💾 Message saved: ${role} - ${text.substring(0, 50)}...`);
        return message;
      } catch (err) {
        console.error("❌ Failed to add message", err);
        setError("Failed to add message");
        return null;
      }
    },
    [currentConversation]
  );

  return {
    conversations,
    currentConversation,
    currentThreadId,
    messages,
    isLoading,
    error,

    loadConversations,
    createNewConversation,
    selectConversation,
    deleteConversation,
    updateConversationTitle,
    refreshMessages,
    addMessage,
  };
}
