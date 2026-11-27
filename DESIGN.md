# MailMind Local Desk Design System

## Direction

The local dashboard borrows the legibility and steady rhythm of a rail-concourse split-flap board. Email and calendar records share one fixed-column reading surface; a narrow station rail keeps the user oriented as they move down the page. The interface names its fixture-only status wherever sample records or assistant output appear.

## Color

| Role | Value | Use |
| --- | --- | --- |
| Page | `#111516` | Main canvas |
| Rail | `#171c1d` | Workspace navigation |
| Panel | `#1c2223` | Composer and focused work areas |
| Raised panel | `#232a2b` | Split-flap character cells |
| Primary text | `#f1f3ed` | Headings and record titles |
| Secondary text | `#b6bfbb` | Supporting copy |
| Quiet text | `#899490` | Metadata and captions |
| Rule | `#3a4443` | Column and section dividers |
| Amber | `#f3bb55` | Demo markers and primary action |
| Error | `#ff7770` | Unavailable and failed states |
| Success | `#8ed3a6` | Local API available state |

Use semantic colors for state only; do not treat status colors as decoration. Text and controls maintain visible focus and hover treatments.

## Typography

- Use the native sans-serif stack for product copy and controls.
- Use a condensed system sans for high-level headings and split-flap cells.
- Reserve the system monospace stack for compact labels, columns, and connection status.
- Keep paragraphs in a readable measure and allow long content to wrap instead of clipping.

## Composition

- A narrow, persistent wayfinding rail sits beside the workspace on wide screens.
- The main content is an ordered vertical sequence: desk, question, mail records, agenda, prototype boundaries.
- Data boards use fixed headers, consistent columns, and thin horizontal rules rather than nested cards.
- The right-side status and safety notes stay secondary to the main workflow.
- Amber identifies sample or attention states; it does not imply urgency in fixture content.

## Interaction and states

- Section navigation follows the vertical content sequence and marks the active destination.
- The question form posts to the same-origin FastAPI SSE endpoint and renders text with safe DOM text nodes.
- Loading, offline, empty, response, and citation states are visible and announced.
- External mail/calendar actions remain disabled and are not represented as available controls.
- Prefer reduced motion when requested; row-arrival motion is brief and nonessential.

## Responsive behavior

- At tablet widths, the fixed rail becomes a horizontally scrollable top station bar and the main content becomes a single column.
- At phone widths, the intro and fixture stamp stack, secondary table columns collapse, and email dates move into the sender column.
- Preserve the primary task, source labels, record identity, and sample-data warning at every width.
