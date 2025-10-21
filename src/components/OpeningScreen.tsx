import { motion } from 'framer-motion';
import { Moon, Star, Sparkles } from 'lucide-react';

interface OpeningScreenProps {
  onEnter: () => void;
}

export default function OpeningScreen({ onEnter }: OpeningScreenProps) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center overflow-hidden relative">
      {/* Animated falling stars */}
      <div className="absolute inset-0 overflow-hidden">
        {[...Array(35)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute text-yellow-200 opacity-70"
            initial={{
              x: Math.random() * window.innerWidth,
              y: -20,
              scale: Math.random() * 0.5 + 0.5
            }}
            animate={{
              y: window.innerHeight + 20,
              x: Math.random() * window.innerWidth,
            }}
            transition={{
              duration: Math.random() * 10 + 15,
              repeat: Infinity,
              ease: 'linear',
              delay: Math.random() * 5
            }}
          >
            <Star size={16} fill="currentColor" />
          </motion.div>
        ))}
      </div>
      
      {/* Static twinkling stars */}
      <div className="absolute inset-0">
        {[...Array(50)].map((_, i) => (
          <motion.div
            key={`static-${i}`}
            className="absolute text-yellow-100"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
            }}
            animate={{
              opacity: [0.3, 1, 0.3],
              scale: [0.8, 1.2, 0.8],
            }}
            transition={{
              duration: Math.random() * 3 + 2,
              repeat: Infinity,
              ease: 'easeInOut',
              delay: Math.random() * 2
            }}
          >
            <Star size={Math.random() * 8 + 4} fill="currentColor" />
          </motion.div>
        ))}
      </div>

      <div className="relative z-10 text-center px-6 max-w-2xl">
        <motion.div
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{
            type: 'spring',
            stiffness: 100,
            damping: 15,
            delay: 0.2
          }}
          className="mb-8 flex justify-center"
        >
          <div className="relative">
            <Moon size={80} className="text-yellow-100" fill="currentColor" />
            <motion.div
              animate={{
                rotate: [0, 10, -10, 0],
              }}
              transition={{
                duration: 4,
                repeat: Infinity,
                ease: 'easeInOut'
              }}
              className="absolute -top-2 -right-2"
            >
              <Sparkles size={32} className="text-yellow-300" />
            </motion.div>
          </div>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.8 }}
          className="text-5xl md:text-6xl font-bold text-gray-900 dark:text-white mb-4 bg-white dark:bg-transparent px-6 py-3 rounded-2xl shadow-2xl shadows-into-light-regular"
        >
          The Sleepy Storybook
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.8 }}
          className="text-xl md:text-2xl text-gray-100 mb-12"
        >
          Where imagination meets storytelling magic ✨
        </motion.p>

        <motion.button
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 1.1, duration: 0.5 }}
          whileHover={{ 
            scale: 1.08,
            boxShadow: '0 20px 40px rgba(251, 191, 36, 0.4)'
          }}
          whileTap={{ scale: 0.95 }}
          onClick={onEnter}
          className="group relative bg-black text-white font-bold text-lg px-12 py-5 rounded-full shadow-2xl transition-all duration-300 border-2 border-black overflow-hidden
                     hover:bg-white hover:text-black hover:border-black"
        >
          {/* Glow effect background */}
          <span className="absolute inset-0 bg-gradient-to-r from-yellow-400 via-yellow-300 to-yellow-400 opacity-0 group-hover:opacity-20 transition-opacity duration-300 blur-xl"></span>
          
          {/* Button text */}
          <span className="relative z-10 flex items-center gap-2">
            Start Your Adventure
            <motion.span
              animate={{ x: [0, 5, 0] }}
              transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
            >
              →
            </motion.span>
          </span>
        </motion.button>
      </div>

      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-black to-transparent"></div>
    </div>
  );
}
