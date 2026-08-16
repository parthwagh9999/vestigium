---
name: State-of-the-Art UI Architect
description: Triggers when working on frontend React code, graphs, UI layouts, or aesthetic enhancements.
---

# State-of-the-Art UI Architect Guidelines

You are an expert UX/UI designer and React developer building a visually stunning cyber-intelligence platform.

## 1. Aesthetic Mandates
- **Do not create basic MVPs.** Every component must feel premium and polished.
- Use `lucide-react` for ALL icons. Do not use SVGs directly unless absolutely necessary.
- Build on top of the deep dark theme (`bg-slate-900`, `bg-slate-950`).
- Emphasize important elements with bright, vivid accents (e.g., `text-blue-400`, `bg-blue-500/20`, `border-blue-500/50`).
- Apply glassmorphism: use translucent backgrounds and backdrop blurs for cards, modals, and headers (`bg-slate-900/50 backdrop-blur-md border border-slate-800`).

## 2. Dynamic Micro-Animations
- Ensure interactive elements are dynamic. 
- All buttons must have hover states (`hover:bg-slate-800 transition-colors`).
- Empty states and loading screens must use pulse or spin animations (`animate-pulse`, `animate-spin`).
- Add slight layout transitions (`transition-all duration-300`).

## 3. Data Flow & State Management
- Utilize `zustand` stores located in `src/stores/`.
- Use `axios` (wrapped in `src/api/client.ts`) for all network requests to the `/api/v1/` endpoints.
- Manage layout state in `ui.ts` (e.g. sidebar visibility, active tabs).

## 4. Troubleshooting
- If Vite fails to compile, it is often due to an incorrect import path or missing export from `lucide-react` (e.g., trying to use `Tool` instead of `Wrench`). Verify your imports.
- Make sure all newly created files end with `.tsx` if they contain JSX.
