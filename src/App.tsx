import { useState, useEffect } from 'react';
import { Menu, Sparkles, Home, BookOpen } from 'lucide-react';
import { motion } from 'framer-motion';
import OpeningScreen from './components/OpeningScreen';
import ChatInterface, { type Message } from './components/ChatInterface';
import StoryEditor from './components/StoryEditor';
import StorySidebar from './components/StorySidebar';
import ThemeToggle from './components/ThemeToggle';
import { generateStory, getPreviousStories, sendChatMessage, type Story } from './lib/api';

type AppState = 'opening' | 'chat' | 'story';

function App() {
  const [appState, setAppState] = useState<AppState>('opening');
  const [currentStory, setCurrentStory] = useState<Story | null>(null);
  const [previousStories, setPreviousStories] = useState<Story[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('Thinking...');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [showStoryView, setShowStoryView] = useState(false);
  const [sessionId] = useState<string>(() => {
    // Fresh session per reload; no persistence
    const g = (window as any).crypto?.randomUUID?.();
    if (g) return g;
    return `sess_${Date.now()}_${Math.floor(Math.random()*1e6)}`;
  });

  useEffect(() => {
    loadPreviousStories();
  }, [sessionId]);

  const loadPreviousStories = async () => {
    try {
  const stories = await getPreviousStories(10, sessionId);
      setPreviousStories(stories);
    } catch (error) {
      console.error('Failed to load stories:', error);
    }
  };

  const handleSendMessage = async (userMessage: string) => {
    // Add user message to chat
    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMsg]);
    
    setIsGenerating(true);
    setLoadingMessage('Thinking...');
    
    try {
      // First, send message to conversational agent
  const chatResponse = await sendChatMessage(userMessage, messages, sessionId);
      
      // Stop loading to show response
      setIsGenerating(false);

      // Add AI response to chat
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: chatResponse.response,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMsg]);
      
      // If AI determined we should generate a story (non-modification), do it
      if (chatResponse.should_generate_story && chatResponse.story_prompt) {
        console.log('🎨 Generating story...');
        setIsGenerating(true);
        setLoadingMessage('Crafting your magical story... ✨');
        
        const prompt = chatResponse.story_prompt;
        
        // Extract length from user message or prompt
        const extractLength = (text: string): 'short' | 'medium' | 'long' => {
          const lower = text.toLowerCase();
          if (lower.includes('long story') || lower.includes('long') || lower.includes('longer')) {
            return 'long';
          }
          if (lower.includes('medium') || lower.includes('medium length')) {
            return 'medium';
          }
          return 'short'; // default
        };
        
        const requestedLength = extractLength(userMessage + ' ' + prompt);
        
        const storyResponse = await generateStory(prompt, requestedLength, messages, sessionId);
        const story = storyResponse.story;

        const storyMsg: Message = {
          id: (Date.now() + 2).toString(),
          role: 'assistant',
          content: `📖 **${story.title}**\n\nYour story is ready! Opening it in the editor. You can ask me to make any changes you'd like!`,
          timestamp: new Date(),
          storyQuality: story.final_score ? {
            clarity: story.final_score.clarity,
            moralValue: story.final_score.moralValue,
            ageAppropriateness: story.final_score.ageAppropriateness,
            score: story.final_score.score,
            iterations: story.iterations || 1
          } : undefined
        };
        
        // Add story content to conversation history so context analyzer can see it for modifications
        const storyContentMsg: Message = {
          id: (Date.now() + 3).toString(),
          role: 'assistant',
          content: `STORY_CONTENT: ${story.title}\n\n${story.content}`,
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, storyMsg, storyContentMsg]);
        
        setCurrentStory(story);
        setAppState('story');
        setShowStoryView(true); // auto-open the story editor when a new story is generated
        await loadPreviousStories();
      }
      
    } catch (error: any) {
      console.error('Failed to process message:', error);
  const status = error?.status;
      const friendly = status === 429
        ? 'We hit the model rate limit right now. Please try again in a minute. I can also switch to a faster model if it keeps happening.'
        : 'Oops! Something went wrong. Please try again.';

      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: friendly,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSelectStory = (story: Story) => {
    setCurrentStory(story);
    setAppState('story');
  };

  const handleNewConversation = () => {
    setMessages([]);
    setCurrentStory(null);
    setAppState('chat');
    setShowStoryView(false);
  };

  const handleBackToChat = () => {
    setShowStoryView(false);
  };

  const handleShowStory = () => {
    if (currentStory) {
      setShowStoryView(true);
    }
  };

  if (appState === 'opening') {
    return <OpeningScreen onEnter={() => setAppState('chat')} />;
  }

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-blue-50 via-blue-100 to-blue-200 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 transition-colors">
      <StorySidebar
        stories={previousStories}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        onSelectStory={handleSelectStory}
        currentStoryId={currentStory?.id || null}
      />

      <div className="sticky top-0 z-30 bg-white dark:bg-gray-900 shadow-md transition-colors">
        <div className="px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setIsSidebarOpen(true)}
              className="p-2 hover:bg-blue-50 dark:hover:bg-gray-800 rounded-lg transition-colors"
              aria-label="Open story sidebar"
            >
              <Menu size={24} className="text-blue-600 dark:text-blue-400" />
            </button>
            <div className="flex items-center gap-2">
              <Sparkles size={28} className="text-blue-500 dark:text-blue-400" />
              <h1 className="text-2xl font-bold text-blue-900 dark:text-white shadows-into-light-regular">The Sleepy Storybook</h1>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <ThemeToggle />
            <button
              onClick={handleNewConversation}
              className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-medium"
            >
              <Home size={20} />
              New Conversation
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Mobile/Desktop Toggle View */}
        {(!showStoryView || !currentStory) ? (
          /* Chat Interface - Full width when no story or story hidden */
          <div className="flex-1 bg-white dark:bg-gray-900 flex flex-col transition-colors">
            <ChatInterface
              messages={messages}
              onSendMessage={handleSendMessage}
              isGenerating={isGenerating}
              loadingMessage={loadingMessage}
            />
            
            {/* Show Story Button - appears when story exists but chat is visible */}
            {currentStory && appState === 'story' && (
              <div className="absolute bottom-20 right-6">
                <motion.button
                  onClick={handleShowStory}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-6 py-3 bg-blue-500 text-white rounded-full shadow-lg hover:bg-blue-600 transition-colors font-medium flex items-center gap-2"
                >
                  <BookOpen size={20} />
                  View Story
                </motion.button>
              </div>
            )}
          </div>
        ) : (
          /* Story Editor - Full width when story is visible */
          <div className="flex-1 bg-gradient-to-br from-blue-50 via-blue-100 to-blue-200 overflow-y-auto">
            <div className="p-6">
              <StoryEditor 
                story={currentStory} 
                imagePrompt={
                  currentStory?.title && currentStory?.content 
                    ? `A beautiful children's book illustration for the story "${currentStory.title}". The scene shows ${currentStory.content.slice(0, 150)}. Colorful, whimsical, child-friendly watercolor art style, detailed illustration, storybook quality, suitable for children ages 5-10`
                    : undefined
                }
                onBackToChat={handleBackToChat}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
