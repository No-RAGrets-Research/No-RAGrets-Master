# Console Warnings Filter

Paste this into your browser console to silence specific warnings:

```javascript
// Save original console methods
const originalWarn = console.warn;
const originalLog = console.log;

// List of warning patterns to suppress
const suppressWarnings = [
  /React Flow.*nodeTypes.*edgeTypes/i,
  /Baleen Content Loaded/i,
  /chrome-extension.*ERR_FILE_NOT_FOUND/i,
  /contentScript\.bundle/i,
];

// Override console.warn
console.warn = function (...args) {
  const message = args.join(" ");
  const shouldSuppress = suppressWarnings.some((pattern) =>
    pattern.test(message)
  );

  if (!shouldSuppress) {
    originalWarn.apply(console, args);
  }
};

// Override console.log to filter specific messages
console.log = function (...args) {
  const message = args.join(" ");
  const shouldSuppress = suppressWarnings.some((pattern) =>
    pattern.test(message)
  );

  if (!shouldSuppress) {
    originalLog.apply(console, args);
  }
};

console.log(
  "Console filters applied - React Flow and extension warnings suppressed"
);
```

## Alternative: Hide via Chrome DevTools Filter

Instead of JavaScript, you can use Chrome's built-in console filter:

1. Open DevTools (F12)
2. Click on the Console tab
3. In the filter box (top), enter this regex:
   ```
   -/React Flow|Baleen|chrome-extension|contentScript/
   ```
4. This will hide any log containing those patterns

## Alternative: Comment out debug logs

If you want to permanently reduce logging, we can replace `console.log` with our custom logger utility in specific files:

- `GraphView.tsx` - Entity/connection logs
- `AnnotatedView.tsx` - Relation search logs
- `PaperView.tsx` - Paper loading logs
- `DoclingRenderer.tsx` - Figure rendering logs

Would you like me to update any of these files to use the conditional logger?
