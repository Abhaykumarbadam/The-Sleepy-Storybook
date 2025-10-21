import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Loader2, Bot, User, Award } from 'lucide-react';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  storyQuality?: {
    clarity: number;
    moralValue: number;
    ageAppropriateness: number;
    score: number;
    iterations: number;
  };
}

interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isGenerating: boolean;
  loadingMessage?: string;
}

export default function ChatInterface({ messages, onSendMessage, isGenerating, loadingMessage = 'Thinking...' }: ChatInterfaceProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isGenerating) {
      onSendMessage(input.trim());
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Auto-resize textarea
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
        {messages.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-12"
          >
            <div className="text-6xl mb-4">📚</div>
            <h2 className="text-2xl font-bold text-blue-900 mb-2">
              Welcome to Story Time!
            </h2>
            <p className="text-blue-600 max-w-md mx-auto">
              I'm your storytelling companion. Tell me what kind of story you'd like to hear, or ask me to modify an existing one!
            </p>
            <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
              <button
                onClick={() => onSendMessage("Tell me a story about a brave little mouse")}
                className="p-4 bg-blue-50 hover:bg-blue-100 rounded-xl text-left transition-colors"
                disabled={isGenerating}
              >
                <div className="font-semibold text-blue-900">🐭 Brave Mouse</div>
                <div className="text-sm text-blue-600">A courageous adventure</div>
              </button>
              <button
                onClick={() => onSendMessage("Create a story about friendship in a magical forest")}
                className="p-4 bg-purple-50 hover:bg-purple-100 rounded-xl text-left transition-colors"
                disabled={isGenerating}
              >
                <div className="font-semibold text-purple-900">🌲 Magical Forest</div>
                <div className="text-sm text-purple-600">Friends and magic</div>
              </button>
              <button
                onClick={() => onSendMessage("Tell me a bedtime story about stars")}
                className="p-4 bg-yellow-50 hover:bg-yellow-100 rounded-xl text-left transition-colors"
                disabled={isGenerating}
              >
                <div className="font-semibold text-yellow-900">⭐ Starry Night</div>
                <div className="text-sm text-yellow-600">A dreamy tale</div>
              </button>
              <button
                onClick={() => onSendMessage("Write a story about a dragon who loves to bake")}
                className="p-4 bg-red-50 hover:bg-red-100 rounded-xl text-left transition-colors"
                disabled={isGenerating}
              >
                <div className="font-semibold text-red-900">🐉 Baker Dragon</div>
                <div className="text-sm text-red-600">Sweet and warm</div>
              </button>
            </div>
          </motion.div>
        ) : (
          <AnimatePresence>
            {messages.map((message, index) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.role === 'assistant' && (
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white">
                    <Bot size={18} />
                  </div>
                )}
                <div className={`max-w-[80%] ${message.role === 'user' ? '' : 'space-y-3'}`}>
                  <div
                    className={`rounded-2xl px-4 py-3 ${
                      message.role === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                  
                  {/* Story Quality Scores - Only for assistant messages with quality data */}
                  {message.role === 'assistant' && message.storyQuality && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.2 }}
                      className="bg-gradient-to-br from-yellow-50 to-amber-50 rounded-xl p-4 border-2 border-yellow-200"
                    >
                      <div className="flex items-center gap-2 mb-3">
                        <Award className="text-yellow-600" size={18} />
                        <h4 className="text-sm font-bold text-yellow-900">Story Quality</h4>
                      </div>
                      <div className="grid grid-cols-3 gap-3 mb-3">
                        <div className="text-center">
                          <div className="text-lg font-bold text-blue-600">
                            {message.storyQuality.clarity}/10
                          </div>
                          <div className="text-xs text-gray-600">Clarity</div>
                        </div>
                        <div className="text-center">
                          <div className="text-lg font-bold text-green-600">
                            {message.storyQuality.moralValue}/10
                          </div>
                          <div className="text-xs text-gray-600">Moral Value</div>
                        </div>
                        <div className="text-center">
                          <div className="text-lg font-bold text-purple-600">
                            {message.storyQuality.ageAppropriateness}/10
                          </div>
                          <div className="text-xs text-gray-600">Age Appropriate</div>
                        </div>
                      </div>
                      <div className="text-center pt-3 border-t border-yellow-300">
                        <div className="text-2xl font-bold text-yellow-700 mb-1">
                          {message.storyQuality.score}/10
                        </div>
                        <div className="text-xs text-gray-700">Overall Score</div>
                        <div className="text-xs text-gray-500 mt-1">
                          Refined through {message.storyQuality.iterations} iteration{message.storyQuality.iterations !== 1 ? 's' : ''}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </div>
                {message.role === 'user' && (
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center text-white">
                    <User size={18} />
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>
        )}
        
        {isGenerating && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-3"
          >
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white">
              <Bot size={18} />
            </div>
            <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl px-4 py-3">
              <div className="flex items-center gap-2">
                <Loader2 className="animate-spin text-blue-500" size={16} />
                <span className="text-gray-600 dark:text-gray-300">{loadingMessage}</span>
              </div>
            </div>
          </motion.div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t bg-white p-4">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="flex gap-2 items-end">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              placeholder="Tell me what story you'd like, or ask me to change something..."
              className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-2xl focus:outline-none focus:border-blue-400 resize-none text-gray-800 placeholder-gray-400 min-h-[52px] max-h-[200px]"
              disabled={isGenerating}
              rows={1}
            />
            <motion.button
              type="submit"
              disabled={!input.trim() || isGenerating}
              whileHover={{ scale: input.trim() && !isGenerating ? 1.05 : 1 }}
              whileTap={{ scale: input.trim() && !isGenerating ? 0.95 : 1 }}
              className={`p-3 rounded-xl transition-colors ${
                !input.trim() || isGenerating
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
            >
              <Send size={20} />
            </motion.button>
          </div>
        </form>
      </div>
    </div>
  );
}
