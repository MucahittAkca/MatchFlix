# Untitled

# MatchFlix – Frontend Design & UX Instructions

## PURPOSE

Design the frontend of MatchFlix: a movie recommendation and social matching platform.
This is NOT a flashy AI demo product.
This is a calm, confident, cinematic product that feels intentional and human.

The interface should feel:

- Thoughtful, not loud
- Intelligent, not showy
- Cinematic, not gamified
- Social, but not childish

Avoid generic AI gradients, glowing effects, over-animated charts, and buzzword visuals.

Focus only on frontend UI/UX.
No backend, no API logic, no fake data generation beyond placeholders.

---

## CORE DESIGN PHILOSOPHY

MatchFlix should feel like:

- A private screening room
- A quiet but smart assistant
- A product made by someone who actually watches movies

Key principles:

- Visual restraint
- Strong hierarchy
- Purposeful whitespace
- Poster-first design
- Subtle intelligence indicators (never shouting “AI”)

---

## COLOR SYSTEM

Primary palette:

- Background (main): #0E0E0F
- Background (secondary surfaces): #171717
- Card background: #1C1C1E
- Border / divider: #2A2A2D

Accent colors:

- Primary action: #D11F2A (deep cinema red, not Netflix red)
- Secondary action / intelligence cues: #4A78FF (soft, serious blue)

Text:

- Primary text: #F5F5F5
- Secondary text: #A3A3A3
- Muted text: #6B6B6B

No gradients by default.
No neon.
No glassmorphism.

---

## TYPOGRAPHY

Font family:

- Primary: Inter
- Alternative: Source Sans 3

Usage:

- Page titles: SemiBold
- Section titles: Medium
- Body text: Regular
- Numbers / scores: Medium

Font sizes should feel slightly smaller than typical SaaS products.
This is a media product, not a dashboard.

---

## GLOBAL LAYOUT SYSTEM

- Max content width: 1280px
- Generous horizontal padding
- Vertical rhythm is more important than compactness

Grid:

- 12-column grid on desktop
- 6-column tablet
- 4-column mobile

Motion:

- Very subtle
- Short durations
- Ease-out only
- No bounce, no springy animations

---

## NAVIGATION BAR

Style:

- Minimal
- Dark
- Slightly translucent
- Sticky

Left:

- MatchFlix wordmark (text-based, no icon-heavy logo)

Center:

- Navigation:
    - Home
    - Explore
    - Quick Match
    - Friends

Right:

- Search icon → expands to input
- Notification icon (small dot when unread)
- Profile avatar

No big buttons in navbar.

---

## PAGE DEFINITIONS

### 1. LANDING PAGE

Goal:
Explain the value quietly and clearly.

Hero section:

- Full viewport height
- Background: soft-focus movie still collage
- Dark overlay

Headline:
“Choosing a movie together shouldn’t be this hard.”

Subtext:
“MatchFlix understands taste — and finds what works for everyone.”

Actions:

- Primary button: Get Started
- Secondary text link: Learn how it works

Below hero:
Three horizontally aligned explanation blocks:

- Taste analysis (short, human wording)
- Compatibility (percentage explained simply)
- Quick Match (decide fast, no arguing)

No feature explosion.
No AI buzzwords.

---

### 2. AUTHENTICATION

Single card layout.
Centered.
Nothing fancy.

Fields:

- Email
- Password

Toggle:

- Login / Create account

Tone:
Private, calm, trustworthy.

---

### 3. HOME PAGE

This is where trust is built.

Sections (vertical scroll):

Section 1:
“Recommended for you”

- Horizontal row of movie cards
- Small label: “Based on your taste”

Section 2:
“Trending now”

- Slightly smaller cards

Section 3:
“Upcoming you might like”

- Calendar icon, subtle highlight

Section 4:
Genres

- Each genre is its own horizontal row

Movie card design:

- Poster only by default
- Bottom fade with title + rating
- Hover:
    - View details
    - Add to Quick Match

No clutter.
No excessive badges.

---

### 4. EXPLORE PAGE

Layout:

- Left filter column (fixed width)
- Right content grid

Filters:

- Genres (simple list)
- Rating range
- Year range
- Language
- Adult content toggle (clearly labeled)

Grid:

- Poster grid
- Clean alignment
- Infinite scroll

This page is for intentional browsing.

---

### 5. MOVIE DETAIL PAGE

Top:

- Full-width backdrop image
- Dark gradient overlay

Overlay content:

- Title
- Tagline
- Year • Runtime • Rating

Below:
Two-column layout:

Left:

- Poster

Right:

- Overview text
- Genre tags
- Key crew (director emphasized)

Actions:

- Rate
- Save
- Use in Quick Match

Tabs below:

- Cast
- Crew
- Similar movies

Feels like opening a Blu-ray case.

---

### 6. QUICK MATCH (MOST IMPORTANT PAGE)

This page must feel different.
More focused.
More intentional.

Step 1:
Select who you’re watching with.

- Avatars only
- Calm layout

Step 2:
Each person selects ONE movie.

- No lists, no noise
- Progress indicator, very subtle

Step 3:
Results.

Title:
“Matches that work for both of you”

Results:

- 3–5 movie cards
- Each card shows:
    - Compatibility percentage
    - Short explanation (shared genres, tone, etc.)

No charts.
No spinning loaders.
Confidence through simplicity.

---

### 7. FRIENDS & COMPATIBILITY

Left panel:

- Friend list
- Online indicator is subtle

Right panel:
Compatibility view:

- Large percentage number
- Below it:
    - Shared genres
    - Shared people (actors/directors)
    - Suggested movies

This page explains *why* matches work.

---

### 8. PROFILE PAGE

Top:

- Profile photo
- Username
- Short bio

Stats row:

- Movies watched
- Average rating
- Favorite genre

Tabs:

- Watched
- Rated
- Saved

Feels personal, not performative.

---

### 9. NOTIFICATIONS

Simple vertical list.
No cards inside cards.

Examples:

- “A new movie matching your taste is coming soon.”
- “Your compatibility with X was updated.”

Unread items are slightly brighter.

---

### 10. SETTINGS

Minimal sections:

- Notifications
- Email frequency
- Privacy
- Account

No hidden complexity.

---

## COMPONENT SYSTEM

Reusable components:

- MovieCard
- HorizontalSlider
- Avatar
- RatingIndicator
- CompatibilityPercentage
- FilterGroup
- Modal
- Button (Primary / Secondary / Text)

Buttons:

- Rectangular
- Slightly rounded
- No shadows

---

## RESPONSIVE BEHAVIOR

Mobile:

- Bottom navigation
- Vertical movie cards
- Quick Match becomes step-by-step full screen

Tablet:

- Reduced columns
- Same hierarchy

---

## FINAL INTENT

This product should feel like:
Someone who loves movies built it.
Someone who hates clutter designed it.
Someone who trusts intelligence doesn’t need to shout.

If something feels flashy, remove it.
If something feels empty, add meaning.