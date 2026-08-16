import { useState, useCallback } from 'react';

export function useHistory<T>(initialState: T, maxHistory: number = 50) {
  const [past, setPast] = useState<T[]>([]);
  const [present, setPresent] = useState<T>(initialState);
  const [future, setFuture] = useState<T[]>([]);

  const canUndo = past.length > 0;
  const canRedo = future.length > 0;

  const set = useCallback((newState: T | ((curr: T) => T)) => {
    setPresent((current) => {
      const resolvedState = typeof newState === 'function' ? (newState as Function)(current) : newState;
      if (current === resolvedState) return current;

      setPast((p) => {
        const newPast = [...p, current];
        if (newPast.length > maxHistory) {
          return newPast.slice(newPast.length - maxHistory);
        }
        return newPast;
      });
      setFuture([]);
      return resolvedState;
    });
  }, [maxHistory]);

  const undo = useCallback(() => {
    if (!canUndo) return;
    const previous = past[past.length - 1];
    const newPast = past.slice(0, past.length - 1);
    
    setPast(newPast);
    setFuture([present, ...future]);
    setPresent(previous);
  }, [canUndo, past, present, future]);

  const redo = useCallback(() => {
    if (!canRedo) return;
    const next = future[0];
    const newFuture = future.slice(1);
    
    setPast([...past, present]);
    setFuture(newFuture);
    setPresent(next);
  }, [canRedo, past, present, future]);

  const reset = useCallback((newState: T) => {
    setPast([]);
    setPresent(newState);
    setFuture([]);
  }, []);

  return { present, set, undo, redo, canUndo, canRedo, reset };
}
