import { motion, AnimatePresence } from 'framer-motion';
import { BookMarked, X, ChevronRight } from 'lucide-react';
import type { Story } from '../lib/api';

interface StorySidebarProps {
  stories: Story[];
  isOpen: boolean;
  onClose: () => void;
  onSelectStory: (story: Story) => void;
  currentStoryId: string | null;
}

export default function StorySidebar({ stories, isOpen, onClose, onSelectStory, currentStoryId }: StorySidebarProps) {
  return (
    <>
      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={onClose}
              className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
            />

            <motion.div
              initial={{ x: -320 }}
              animate={{ x: 0 }}
              exit={{ x: -320 }}
              transition={{ type: 'spring', damping: 30, stiffness: 300 }}
              className="fixed left-0 top-0 bottom-0 w-80 bg-white shadow-2xl z-50 overflow-hidden flex flex-col"
            >
              <div className="p-6 bg-gradient-to-r from-blue-500 to-blue-600 text-white">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <BookMarked size={28} />
                    <h2 className="text-2xl font-bold">Previous Stories</h2>
                  </div>
                  <button
                    onClick={onClose}
                    className="p-2 hover:bg-white hover:bg-opacity-20 rounded-lg transition-colors"
                    aria-label="Close sidebar"
                  >
                    <X size={24} />
                  </button>
                </div>
                <p className="text-blue-100 text-sm">
                  Revisit your magical adventures
                </p>
              </div>

              <div className="flex-1 overflow-y-auto p-4">
                {stories.length === 0 ? (
                  <div className="text-center py-12">
                    <BookMarked size={48} className="mx-auto text-gray-300 mb-4" />
                    <p className="text-gray-500">No stories yet!</p>
                    <p className="text-sm text-gray-400 mt-2">
                      Create your first magical tale
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {stories.map((story, index) => (
                      <motion.button
                        key={story.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        onClick={() => {
                          onSelectStory(story);
                          onClose();
                        }}
                        className={`w-full text-left p-4 rounded-xl transition-all ${
                          currentStoryId === story.id
                            ? 'bg-blue-500 text-white shadow-lg'
                            : 'bg-gray-50 hover:bg-gray-100 text-gray-800'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <h3 className={`font-bold mb-1 truncate ${
                              currentStoryId === story.id ? 'text-white' : 'text-blue-900'
                            }`}>
                              {story.title}
                            </h3>
                            <p className={`text-xs line-clamp-2 mb-2 ${
                              currentStoryId === story.id ? 'text-blue-100' : 'text-gray-600'
                            }`}>
                              {story.content.substring(0, 80)}...
                            </p>
                            <div className="flex items-center gap-2">
                              <span className={`text-xs px-2 py-1 rounded-full ${
                                currentStoryId === story.id
                                  ? 'bg-blue-400 text-white'
                                  : 'bg-blue-100 text-blue-700'
                              }`}>
                                {story.length_type}
                              </span>
                              <span className={`text-xs ${
                                currentStoryId === story.id ? 'text-blue-200' : 'text-gray-500'
                              }`}>
                                {new Date(story.created_at).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                          <ChevronRight
                            size={20}
                            className={currentStoryId === story.id ? 'text-white' : 'text-gray-400'}
                          />
                        </div>
                      </motion.button>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
