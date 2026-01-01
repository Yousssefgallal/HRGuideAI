/**
 * Message Persistence Hook
 * Bridges CopilotKit messages with backend database storage
 */

import { useEffect, useRef } from "react";
import { useCopilotMessagesContext } from "@copilotkit/react-core";
import { createMessage } from "@/lib/api";

interface UseMessagePersistenceProps {
  conversationId: number | null;
  enabled: boolean;
}

/**
 * Hook to automatically persist CopilotKit messages to the database
 */
export function useMessagePersistence({
  conversationId,
  enabled,
}: UseMessagePersistenceProps) {
  const { messages } = useCopilotMessagesContext();
  const savedMessageIds = useRef<Set<string>>(new Set());
  const isInitialLoad = useRef(true);

  // Reset saved message IDs when conversation changes
  useEffect(() => {
    savedMessageIds.current.clear();
    isInitialLoad.current = true;
  }, [conversationId]);

  useEffect(() => {
    if (!enabled || !conversationId) return;

    // Skip if no messages
    if (messages.length === 0) return;

    // After initial load, mark first load as complete
    if (isInitialLoad.current) {
      // Mark all existing messages as "seen" to avoid saving historical messages
      messages.forEach((msg) => {
        if (msg.id) {
          savedMessageIds.current.add(msg.id);
        }
      });
      isInitialLoad.current = false;
      return;
    }

    // Save new messages that haven't been saved yet
    const saveNewMessages = async () => {
      for (const message of messages) {
        // Skip if already saved
        if (!message.id || savedMessageIds.current.has(message.id)) {
          continue;
        }

        // Skip system messages
        if ((message as any).role === "system") {
          savedMessageIds.current.add(message.id);
          continue;
        }

        try {
          // Prepare message content
          const content: {
            text: string;
            metadata?: Record<string, unknown>;
          } = {
            text: typeof (message as any).content === "string"
              ? (message as any).content
              : JSON.stringify((message as any).content),
            metadata: {
              copilot_message_id: message.id,
              timestamp: new Date().toISOString(),
            },
          };

          // Determine role (CopilotKit uses "assistant" or "user")
          const role = (message as any).role === "assistant" ? "assistant" : "user";

          // Save to database
          await createMessage({
            conversation_id: conversationId,
            role,
            content,
          });

          // Mark as saved
          savedMessageIds.current.add(message.id);
          console.log(`💾 Saved ${role} message:`, message.id);
        } catch (error) {
          console.error("❌ Failed to save message:", error);
          // Don't mark as saved if it failed, will retry next time
        }
      }
    };

    saveNewMessages();
  }, [messages, conversationId, enabled]);

  return {
    savedMessageCount: savedMessageIds.current.size,
  };
}
