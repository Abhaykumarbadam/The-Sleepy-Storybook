import { motion } from 'framer-motion';
import { BookOpen, Clock, Volume2, Pause, ArrowLeft } from 'lucide-react';
import type { Story } from '../lib/api';
import { getTtsMp3 } from '../lib/api';
import { useState, useEffect, useRef } from 'react';

interface StoryEditorProps {
  story: Story | null;
  imagePrompt?: string;
  onBackToChat?: () => void;
}

export default function StoryEditor({ story, imagePrompt, onBackToChat }: StoryEditorProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [imageLoading, setImageLoading] = useState(true);
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(true);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null); // Add ref for audio element
  const typingIntervalRef = useRef<number | null>(null);

  if (!story) {
    return null;
  }
  // Sanitize content defensively in case any token like "undefined" slipped in from UI state
  const rawContent = typeof story.content === 'string' ? story.content : String(story.content ?? '');
  // Remove stray generation artifacts without impacting valid language like the word "none" in the middle of sentences
  // Normalize line endings and preserve paragraph breaks (\n\n)
  let sanitizedContent = rawContent
    .replace(/\r\n?/g, '\n')
    .replace(/\b(undefined|null)\b/gi, '') // remove literal 'undefined'/'null' tokens anywhere
    // collapse multiple spaces/tabs but preserve newlines
    .replace(/[ \t]{2,}/g, ' ')
    // normalize 3+ newlines down to exactly 2 (paragraph break)
    .replace(/\n[ \t]*\n[ \t]*\n+/g, '\n\n')
    // trim spaces around newlines
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n[ \t]+/g, '\n')
    .trim();
  // Specifically strip a trailing 'none'/'undefined'/'null' at the very end if present
  sanitizedContent = sanitizedContent.replace(/\s*(undefined|null|none)\s*$/i, '').trim();

  const estimatedReadingTime = Math.ceil((sanitizedContent.split(' ').filter(Boolean).length) / 100);

  // Typewriter effect (character-based) to avoid dropping tokens
  useEffect(() => {
    if (!sanitizedContent) return;

    setDisplayedText('');
    setIsTyping(true);

    let index = 0;
    const step = 3; // characters per tick

    const typeNext = () => {
      if (index < sanitizedContent.length) {
        index = Math.min(index + step, sanitizedContent.length);
        setDisplayedText(sanitizedContent.slice(0, index));
      } else {
        setIsTyping(false);
        if (typingIntervalRef.current) {
          clearInterval(typingIntervalRef.current);
          typingIntervalRef.current = null;
        }
      }
    };

    const interval = window.setInterval(typeNext, 20); // ~150 chars/sec
    typingIntervalRef.current = interval;

    return () => {
      if (typingIntervalRef.current) {
        clearInterval(typingIntervalRef.current);
        typingIntervalRef.current = null;
      }
    };
  }, [sanitizedContent]);

  // Text-to-Speech handlers
  const handleReadAloud = async () => {
    // Stop any currently playing audio
    if (isPlaying) {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      setIsPlaying(false);
      return;
    }

    // If text is still typing, finish it instantly so the screen matches TTS
    if (isTyping) {
      if (typingIntervalRef.current) {
        clearInterval(typingIntervalRef.current);
        typingIntervalRef.current = null;
      }
      setDisplayedText(sanitizedContent);
      setIsTyping(false);
    }

  // Prefer backend TTS (better pauses). If it fails, fall back to speechSynthesis.
    try {
      console.log('🔊 Requesting TTS from backend...');
      const blob = await getTtsMp3(sanitizedContent, 'en', false);
      console.log('✅ TTS blob received, size:', blob.size);
      
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      
      audio.onended = () => {
        console.log('✅ Audio playback ended');
        setIsPlaying(false);
        URL.revokeObjectURL(url);
        audioRef.current = null;
      };
      
      audio.onerror = (e) => {
        console.error('❌ Audio playback error:', e);
        setIsPlaying(false);
        URL.revokeObjectURL(url);
        audioRef.current = null;
      };
      
      await audio.play();
      console.log('▶️ Audio playback started');
      setIsPlaying(true);
      return;
    } catch (err) {
      console.error('❌ Backend TTS failed, falling back to browser TTS:', err);
      // Fall through to browser speech synthesis fallback
    }

    // Fallback: Use browser's built-in speech synthesis
    if (!window.speechSynthesis) {
      alert('Sorry, text-to-speech is not available in your browser.');
      return;
    }

    const utterance = new SpeechSynthesisUtterance(sanitizedContent);
    utterance.rate = 0.85; // Slightly slower for children
    utterance.pitch = 1.1; // Slightly higher pitch
    utterance.volume = 1;

    utterance.onend = () => {
      setIsPlaying(false);
    };

    utterance.onerror = () => {
      setIsPlaying(false);
    };

    utteranceRef.current = utterance;
    window.speechSynthesis.speak(utterance);
    setIsPlaying(true);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Cleanup audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      // Cleanup speech synthesis
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex gap-6 max-w-7xl mx-auto h-full"
    >
      {/* Left Side - Story Content */}
  <div className="flex-1 bg-white dark:bg-gray-800 rounded-3xl shadow-xl p-8 transition-colors">
        {/* Back to Chat Button */}
        {onBackToChat && (
          <motion.button
            onClick={onBackToChat}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="mb-6 flex items-center gap-2 px-4 py-2 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <ArrowLeft size={20} />
            <span className="font-medium">Back to Chat</span>
          </motion.button>
        )}

        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex items-start justify-between mb-6"
        >
          <div className="flex items-center gap-3">
            <BookOpen className="text-blue-500 dark:text-blue-400" size={32} />
            <div>
              <h2 className="text-3xl font-bold text-blue-900 dark:text-white">{story.title}</h2>
              <div className="flex items-center gap-4 mt-2 text-sm text-blue-600 dark:text-blue-400">
                <span className="flex items-center gap-1">
                  <Clock size={16} />
                  {estimatedReadingTime} min read
                </span>
              </div>
            </div>
          </div>
          
          {/* Text-to-Speech Button */}
          <motion.button
            onClick={handleReadAloud}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className={`p-3 rounded-full transition-colors ${
              isPlaying 
                ? 'bg-red-500 hover:bg-red-600 text-white' 
                : 'bg-blue-500 hover:bg-blue-600 text-white'
            }`}
            title={isPlaying ? 'Stop reading' : 'Read aloud'}
          >
            {isPlaying ? <Pause size={24} /> : <Volume2 size={24} />}
          </motion.button>
        </motion.div>

        <div className="prose prose-lg max-w-none">
          <div className="text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-wrap text-justify">
            {displayedText}
            {isTyping && (
              <motion.span
                animate={{ opacity: [1, 0] }}
                transition={{ duration: 0.5, repeat: Infinity }}
                className="inline-block w-1 h-5 bg-blue-500 ml-1"
              />
            )}
          </div>
        </div>
      </div>

      {/* Right Side - Story Illustration */}
      <div className="w-[45%] bg-white dark:bg-gray-800 rounded-3xl shadow-xl p-6 flex flex-col transition-colors sticky top-6 self-start h-[calc(100vh-6rem)]">
        <h3 className="text-xl font-bold text-blue-900 dark:text-white mb-4">Story Illustration</h3>
        <div className="flex-1 bg-gradient-to-br from-blue-50 to-purple-50 dark:from-gray-700 dark:to-gray-600 rounded-2xl shadow-lg overflow-hidden relative">
                    {/* Animated Loading State */}
          {imageLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50 dark:from-gray-800 dark:to-gray-900">
              <div className="text-center">
                <motion.div
                  className="text-6xl mb-4"
                  animate={{ 
                    scale: [1, 1.2, 1],
                    rotate: [0, 360],
                  }}
                  transition={{ 
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                >
                  🎨
                </motion.div>
                <motion.p 
                  className="text-gray-600 dark:text-gray-300 text-sm font-medium"
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                >
                  Painting magical scenes...
                </motion.p>
              </div>
            </div>
          )}
          
          <motion.div
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: imageLoading ? 0 : 1, scale: imageLoading ? 0.98 : 1 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="w-full h-full relative"
          >
            {/* Scrollable image viewport to preserve details without expanding layout */}
            <div className="absolute inset-0 overflow-auto">
              <img
                src={`https://image.pollinations.ai/prompt/${encodeURIComponent(
                  imagePrompt || 
                  `Children's book illustration: ${story.title}. ${sanitizedContent.substring(0, 150)}. Colorful, whimsical, watercolor style`
                )}?width=800&height=1200&enhance=true&nologo=true`}
                alt="Story illustration"
                onLoad={() => setImageLoading(false)}
                onError={() => setImageLoading(false)}
                className="max-w-full h-auto object-contain"
                loading="eager"
              />
            </div>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}
