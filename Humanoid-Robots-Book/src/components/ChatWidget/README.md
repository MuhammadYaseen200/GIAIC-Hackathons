# ChatWidget Component

React component for the RAG-powered Physical AI Tutor chatbot, integrated globally across all Docusaurus pages.

## Features

- ✅ **Floating Chat Button**: Bottom-right corner, always accessible
- ✅ **Modern UI**: Tailwind CSS with smooth animations
- ✅ **Real-time Chat**: Connects to FastAPI backend (Gemini-powered)
- ✅ **Citations**: Displays sources from textbook chapters
- ✅ **Loading States**: Animated loader during API calls
- ✅ **Error Handling**: User-friendly error messages
- ✅ **Rate Limiting**: Graceful handling of 429 responses
- ✅ **Responsive**: Works on mobile and desktop
- ✅ **Accessibility**: ARIA labels, keyboard navigation

## Architecture

```
src/components/ChatWidget/
├── index.tsx          # Main ChatWidget component
├── types.ts           # TypeScript type definitions
└── README.md          # This file

src/theme/
└── Root.tsx           # Docusaurus Root wrapper (injects ChatWidget globally)
```

## API Integration

**Endpoint**: `POST /api/chat`

**Request**:
```typescript
{
  question: string;
  session_id: string;  // UUID v4, generated per browser session
  chapter_context?: string;  // Optional current chapter
}
```

**Response**:
```typescript
{
  answer: string;  // Markdown-formatted response
  citations: Citation[];  // Source references
  tokens_used: number;
}
```

**Citation Format**:
```typescript
{
  title: string;  // "Chapter 2: Publisher-Subscriber Communication"
  url: string;    // "../module-1-ros2-basics/chapter-2-pub-sub.md"
  chapter_id: string;  // "module-1-ros2-basics/chapter-2"
}
```

## Usage

### Installation

```bash
# Install dependencies
npm install

# Dependencies added:
# - lucide-react: ^0.294.0 (icons)
# - uuid: ^9.0.1 (session ID generation)
# - @types/uuid: ^9.0.7 (TypeScript types)
```

### Development

```bash
# Start Docusaurus dev server
npm start

# The ChatWidget will appear on all pages
# Backend must be running at http://localhost:8000
```

### Production

```bash
# Build static site
npm run build

# Update API_BASE_URL in index.tsx before deploying:
const API_BASE_URL = 'https://your-app.railway.app';
```

## Component Details

### State Management

- **Session ID**: Generated once per browser session using UUID v4
- **Messages**: Stored in React state (lost on page refresh)
- **Loading**: Boolean flag for API request status
- **Error**: String for displaying error messages

### Icons (lucide-react)

- `MessageCircle`: Chat button icon
- `X`: Close button
- `Send`: Send message button
- `Loader2`: Loading spinner (animated)
- `BookOpen`: Empty state and header icon
- `ExternalLink`: Citation links

### Styling (Tailwind CSS)

**Color Palette**:
- Primary: Blue 600 (`bg-blue-600`)
- Hover: Blue 700 (`hover:bg-blue-700`)
- Background: Gray 50 (`bg-gray-50`)
- Border: Gray 200 (`border-gray-200`)

**Key Classes**:
- `fixed bottom-6 right-6`: Positioning
- `rounded-2xl`: Rounded corners
- `shadow-2xl`: Large shadow
- `z-50`: High z-index (above all content)

### Keyboard Shortcuts

- **Enter**: Send message
- **Shift+Enter**: New line in textarea
- **Escape**: (future) Close chat window

## Error Handling

**Rate Limiting (429)**:
```
"Rate limit exceeded. Please wait a moment and try again."
```

**Network Errors**:
```
"An error occurred. Please try again."
```

**API Errors**:
Displays `error.detail` or `error.error` from backend response.

## Testing

### Manual Testing

1. **Start Backend**:
   ```bash
   cd backend
   uvicorn src.main:app --reload
   ```

2. **Start Frontend**:
   ```bash
   npm start
   ```

3. **Test Flow**:
   - Click chat button (bottom-right)
   - Type: "How do I create a ROS 2 subscriber?"
   - Verify response with citations
   - Click citation link → Navigate to chapter

### Edge Cases

- Empty message → Send button disabled
- Long message (>500 chars) → Textarea max length enforced
- Rate limit → Error message displayed
- Backend offline → Connection error displayed

## Customization

### Change API URL

Edit `src/components/ChatWidget/index.tsx`:
```typescript
const API_BASE_URL = 'https://your-custom-api.com';
```

### Change Colors

Edit Tailwind classes in `index.tsx`:
```typescript
// Replace bg-blue-600 with your color
className="bg-purple-600 hover:bg-purple-700"
```

### Change Position

Edit fixed positioning:
```typescript
// Move to bottom-left
className="fixed bottom-6 left-6"
```

### Change Size

Edit dimensions:
```typescript
// Larger chat window
className="w-[500px] h-[700px]"
```

## Accessibility

- **ARIA Labels**: All buttons have `aria-label` attributes
- **Keyboard Navigation**: Tab through interactive elements
- **Focus Management**: Auto-focus input when chat opens
- **Screen Readers**: Semantic HTML structure

## Performance

- **Lazy Loading**: Component only renders on client-side (SSR-safe)
- **Auto-scroll**: Messages container scrolls to bottom on new message
- **Debouncing**: (future) Prevent rapid message sending
- **Caching**: (future) Cache responses for common questions

## Known Issues

- Messages lost on page refresh (no persistence)
- No conversation history across sessions
- Citations open in same tab (future: modal preview)

## Future Enhancements

- [ ] Persistent conversation history (backend storage)
- [ ] Markdown rendering in responses (code syntax highlighting)
- [ ] Copy code button for code blocks
- [ ] Dark mode support
- [ ] Typing indicator ("Claude is typing...")
- [ ] Message reactions (👍 👎)
- [ ] Export conversation as PDF
- [ ] Voice input/output
- [ ] Multi-language support (Urdu translation)

## Troubleshooting

### ChatWidget not appearing

**Issue**: Component not visible on page

**Solutions**:
1. Check browser console for errors
2. Verify `src/theme/Root.tsx` exists
3. Run `npm install` to ensure dependencies installed
4. Clear browser cache and rebuild: `npm run clear && npm run build`

### API Connection Failed

**Issue**: "Failed to get response" error

**Solutions**:
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check CORS settings in backend `.env`:
   ```
   ALLOWED_ORIGINS=http://localhost:3000
   ```
3. Check browser network tab for CORS errors

### Styling Issues

**Issue**: Tailwind classes not working

**Solutions**:
1. Verify `tailwind.config.js` includes ChatWidget path:
   ```js
   content: ['./src/**/*.{js,jsx,ts,tsx}']
   ```
2. Rebuild: `npm run build`
3. Check `src/css/custom.css` imports Tailwind:
   ```css
   @tailwind base;
   @tailwind components;
   @tailwind utilities;
   ```

## Contributing

When modifying ChatWidget:
1. Update TypeScript types in `types.ts`
2. Test with backend running
3. Check accessibility with screen reader
4. Verify responsive design (mobile + desktop)
5. Update this README

## License

MIT License (same as main project)
