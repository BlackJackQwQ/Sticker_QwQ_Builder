import customtkinter as ctk
import cv2
import threading
from PIL import Image, ImageSequence
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Tuple, Any

from Core.Config import logger
from UI.ViewUtils import load_ctk_image

class AsyncLoader:
    """
    The Engine.
    Handles heavy media loading (High-Res Images, GIFs, Videos) 
    off the main thread to prevent UI freezing.
    
    Features:
    - Thread Pooling (Max 2 workers to prevent IO saturation).
    - Debouncing (Waits for resize events to settle).
    - Request Invalidation (Ignores old results if user switched views).
    """
    
    def __init__(self, app):
        self.app = app
        
        # Concurrency
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="DetailLoader")
        
        # State Management
        self._current_load_id: int = 0
        self._debounce_job: Optional[str] = None
        self._anim_loop_id: Optional[str] = None

    def get_new_load_id(self) -> int:
        """Invalidates all previous pending requests."""
        self._current_load_id += 1
        return self._current_load_id

    def request_image_load(self, path: str, label_widget: ctk.CTkLabel, width: int, req_id: int):
        """
        Public API. Call this when the view changes or resizes.
        Implements a 150ms debounce to prevent thrashing during window resize.
        """
        # 1. Cancel pending tasks
        if self._debounce_job:
            self.app.after_cancel(self._debounce_job)
            self._debounce_job = None
            
        if self._anim_loop_id:
            self.app.after_cancel(self._anim_loop_id)
            self._anim_loop_id = None
            
        # 2. Immediate UI Feedback
        # Only clear if we are actually starting a new logical load (id change)
        # or if the path is invalid.
        if not path:
            if label_widget.winfo_exists():
                label_widget.configure(image=None, text="(No Image)")
            return

        # 3. Schedule the work
        # We pass req_id through to ensure we don't process stale results
        self._debounce_job = self.app.after(
            150, 
            lambda: self._start_loading(path, label_widget, width, req_id)
        )

    def _start_loading(self, path: str, label_widget: ctk.CTkLabel, width: int, req_id: int):
        """Internal: Dispatches work to thread pool or loads static immediately."""
        if self._current_load_id != req_id: return
        if not label_widget.winfo_exists(): return

        # Calc target size
        new_size = max(50, width - 20)
        size_tuple = (new_size, new_size)
        
        # Define callback wrapper to ensure thread safety
        def on_frames_ready(frames, duration):
            if self._current_load_id == req_id:
                self._play_frames(frames, duration, label_widget, req_id)

        # A. Video Files (WebM, MP4) -> Heavy -> Thread
        if path.lower().endswith(('.webm', '.mp4', '.mkv')):
            if label_widget.winfo_exists(): 
                # FIX: Explicitly clear image=None to prevent "pyimage doesn't exist" error
                label_widget.configure(image=None, text="Loading Video...")
            
            self.executor.submit(
                self._background_load_video, path, size_tuple, on_frames_ready, req_id
            )
            return

        # B. Animated Images (GIF/WebP) -> Medium -> Thread
        is_anim = False
        try:
            if path.lower().endswith(".gif"):
                is_anim = True
            else:
                # Peek for animation frames
                with Image.open(path) as test:
                    if getattr(test, "is_animated", False): is_anim = True
        except Exception as e:
            # Log warning but continue (fallback to static)
            logger.warning(f"Failed to check animation status for {path}: {e}")

        if is_anim:
            if label_widget.winfo_exists(): 
                # FIX: Explicitly clear image here too
                label_widget.configure(image=None, text="Loading Anim...")
            
            self.executor.submit(
                self._background_load_gif, path, size_tuple, on_frames_ready, req_id
            )
            return

        # C. Static Images -> Light -> Main Thread
        # ViewUtils.load_ctk_image handles caching internally
        img = load_ctk_image(path, size_tuple)
        if img and label_widget.winfo_exists():
            label_widget.configure(image=img, text="")
        elif label_widget.winfo_exists():
            label_widget.configure(text="⚠ Load Failed")

    # ==========================================================================
    #   WORKERS (Run in Background Threads)
    # ==========================================================================

    def _background_load_video(self, path, size, callback, req_id):
        if self._current_load_id != req_id: return
        
        pil_frames = []
        cap = None
        try:
            cap = cv2.VideoCapture(path)
            i = 0
            while True:
                if self._current_load_id != req_id: break
                
                ret, frame = cap.read()
                if not ret or i > 60: break # Hard cap frames
                
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_frame)
                pil_img.thumbnail(size, Image.Resampling.LANCZOS)
                pil_frames.append(pil_img)
                i += 1
        except Exception as e:
            logger.error(f"Video load error: {e}")
        finally:
            if cap: cap.release()
            
        if pil_frames and self._current_load_id == req_id:
            # Convert PIL to CTkImage on main thread via callback
            self.app.after(0, lambda: self._finalize_frames(pil_frames, 50, callback))

    def _background_load_gif(self, path, size, callback, req_id):
        if self._current_load_id != req_id: return
        
        pil_frames = []
        duration = 100
        try:
            with Image.open(path) as im:
                duration = im.info.get('duration', 100) or 100
                if duration < 20: duration = 100
                
                iterator = ImageSequence.Iterator(im)
                for i, frame in enumerate(iterator):
                    if self._current_load_id != req_id: return
                    if i > 60: break
                    
                    f = frame.copy()
                    f.thumbnail(size, Image.Resampling.LANCZOS)
                    pil_frames.append(f)
        except Exception as e:
             logger.error(f"GIF load error ({path}): {e}")

        if pil_frames and self._current_load_id == req_id:
            self.app.after(0, lambda: self._finalize_frames(pil_frames, duration, callback))

    def _finalize_frames(self, pil_frames, duration, callback):
        """Converts PIL to CTkImage on Main Thread."""
        try:
            final_frames = []
            for p in pil_frames:
                w, h = p.size
                final_frames.append(ctk.CTkImage(light_image=p, dark_image=p, size=(w, h)))
            callback(final_frames, duration)
        except Exception as e:
            logger.error(f"Frame finalization error: {e}")

    # ==========================================================================
    #   ANIMATION LOOP
    # ==========================================================================

    def _play_frames(self, frames, duration, label, req_id):
        """Recursive animation loop."""
        if not frames: return
        if self._current_load_id != req_id: return

        def animate(idx):
            if self._current_load_id != req_id: return
            if not label.winfo_exists(): return
            
            try:
                label.configure(image=frames[idx], text="")
                self._anim_loop_id = self.app.after(
                    duration, 
                    lambda: animate((idx + 1) % len(frames))
                )
            except Exception as e:
                # Common if widget is destroyed mid-update
                logger.debug(f"Animation loop stopped: {e}")
            
        animate(0)