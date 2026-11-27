# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Working assumption: the first user is a person evaluating or trying the local MailMind prototype. A more specific audience has not been established.

## Product Purpose

The project explores an assistant for email and calendar productivity. The currently implemented product is a local browser dashboard that lets people inspect sample email/calendar evidence and try a placeholder chat endpoint.

## Positioning

No product differentiator is implemented yet. The local demo is intentionally limited to fixture data and makes that limitation visible rather than implying real account access.

## Operating Context

The first surface runs locally alongside the FastAPI service. Users can inspect sample source records and submit a question to the demo endpoint.

## Capabilities and Constraints

- The API exposes health, streamed demo chat, and memory endpoints.
- A responsive dashboard is served by FastAPI and reads the demo overview and chat stream from the same origin.
- Gmail and Calendar data shown by the demo are fixtures, not a connected account.
- Chat does not interpret questions with an LLM.
- OAuth, live Google integrations, persistence, real memory, real RAG, and action approval/execution are not implemented.
- The frontend must not claim actions were taken or imply sample data is personal data.

## Brand Commitments

The product name is MailMind (also styled as MindMail in repository/project naming). No logo or visual identity has been supplied.

## Evidence on Hand

The repository contains FastAPI prototype code, sample Gmail/Calendar fixtures, product target-state documents, and tests. It contains no production user data, customer evidence, or deployment evidence.

## Product Principles

- Be explicit about what is implemented versus planned.
- Keep sample data distinguishable from connected personal information.
- Never imply that an external action occurred unless it was actually executed.
- Make the local prototype easy to run without account credentials.
