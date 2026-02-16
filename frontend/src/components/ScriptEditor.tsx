import { useState, useCallback } from 'react';
import { motion } from 'motion/react';

interface ScriptEditorProps {
  script: string;
  onSave: (script: string, resume: boolean) => void;
  onCancel: () => void;
  isLoading: boolean;
}

export function ScriptEditor({ script: initialScript, onSave, onCancel, isLoading }: ScriptEditorProps) {
  const [script, setScript] = useState(initialScript);
  const [resume, setResume] = useState(true);

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    onSave(script, resume);
  }, [script, resume, onSave]);

  return (
    <motion.div
      className="h-full flex flex-col"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs font-medium tracking-widest text-muted uppercase">Edit Script</span>
        <div className="flex items-center gap-2">
          <motion.button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="text-xs text-muted hover:text-ink transition-colors disabled:opacity-50"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            Cancel
          </motion.button>
        </div>
      </div>
      
      <form onSubmit={handleSubmit} className="flex-1 flex flex-col">
        <div className="flex-1 relative mb-4">
          <textarea
            value={script}
            onChange={(e) => setScript(e.target.value)}
            disabled={isLoading}
            className="
              w-full h-full p-4 bg-card border border-border rounded-none
              text-sm font-mono leading-relaxed resize-none
              focus:outline-none focus:border-accent
              disabled:opacity-50 disabled:cursor-not-allowed
            "
            placeholder="LEO: Welcome to the show..."
            spellCheck={false}
          />
        </div>
        
        <div className="flex items-center justify-between pt-4 border-t border-border">
          <label className="flex items-center gap-3 cursor-pointer group">
            <input
              type="checkbox"
              checked={resume}
              onChange={(e) => setResume(e.target.checked)}
              disabled={isLoading}
              className="w-4 h-4 rounded border-border text-accent focus:ring-accent focus:ring-offset-0"
            />
            <span className="text-sm text-muted group-hover:text-ink transition-colors">
              Resume generation after saving
            </span>
          </label>
          
          <motion.button
            type="submit"
            disabled={isLoading || !script.trim()}
            className="
              px-6 py-2 bg-ink text-paper text-sm font-medium
              hover:bg-ink/90 transition-colors
              disabled:opacity-50 disabled:cursor-not-allowed
            "
            whileHover={{ scale: isLoading ? 1 : 1.02 }}
            whileTap={{ scale: isLoading ? 1 : 0.98 }}
          >
            {isLoading ? 'Saving...' : 'Save Changes'}
          </motion.button>
        </div>
      </form>
    </motion.div>
  );
}