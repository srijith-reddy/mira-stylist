# MIRA Stylist

MIRA Stylist is a luxury AI fashion companion designed for people who want more than generic outfit advice. It turns virtual try-on, editorial commentary, fit guidance, saved looks, motion, and voice into one calm styling experience.

## What MIRA Does

- guides users through a conversational style onboarding flow
- generates virtual try-on looks from a person image and a garment image
- explains how a look reads with refined editorial commentary
- answers follow-up styling questions in a more conversational voice
- supports personalized size guidance using saved profile context
- saves looks into a wardrobe with favorites and collections
- animates still looks into short fashion motion clips
- adds optional voice narration for a more immersive stylist experience

## Product Direction

This repository is built around a premium styling experience rather than a heavy app shell.

The current app is:

- luxury-toned
- voice-capable
- profile-aware
- designed to feel elegant instead of transactional

## Key Flows

### Home

The landing experience focuses on:

- introducing MIRA as a premium AI stylist
- guiding users into onboarding or try-on quickly
- presenting the product as calm, elevated, and editorial

### Onboarding

Users can:

- answer conversational style questions
- define aesthetic, silhouette, and occasion preferences
- share color preferences and style goals
- generate a narrative style identity summary

### Try-On

Users can:

- upload or link a person image
- upload or link a garment image
- generate a styled try-on result
- receive commentary, fit perspective, and follow-up styling answers
- optionally generate motion and voice output

### Wardrobe

- save generated looks
- favorite looks
- organize looks into collections
- filter looks by favorites, collection, or occasion

### Profile

- review a saved style profile
- update personal snapshot details
- add brand sizing references
- improve downstream fit recommendations

## Motion And Voice

MIRA includes optional media layers that make the experience feel more alive.

That means it can:

- turn a still try-on into a short editorial motion clip
- narrate commentary in MIRA's voice
- generate a welcome voice moment
- support speech transcription for voice input flows

What it does not do:

- work as an offline-first styling app
- replace the backend services required for try-on, motion, or AI outputs

## Tech Stack

- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Framer Motion
- FastAPI
- OpenAI
- FASHN
- Kling
- Cartesia

## Repository Structure

```text
backend/            FastAPI app, routes, services, models, env-backed settings
frontend/           Next.js app, components, styles, client API layer
output/             generated media and local artifacts
run_backend.sh      local backend runner
run_frontend.sh     local frontend runner
```

## Local Development

### Backend

```bash
cp backend/.env.example .env
./run_backend.sh
```

### Frontend

```bash
./run_frontend.sh
```


## Environment

The backend reads from the repo root `.env` file.

Core keys:

- `OPENAI_API_KEY`
- `FASHN_API_KEY`

Optional keys:

- `KLING_ACCESS_KEY`
- `KLING_SECRET_KEY`
- `CARTESIA_API_KEY`
- `CARTESIA_VOICE`

Local frontend requests are proxied to the backend, so `frontend/.env.local` can stay blank unless you want to point at a custom API host.

## Current Status

What is real today:

- polished frontend flows
- style onboarding and saved profile state
- virtual try-on pipeline
- editorial commentary and stylist Q&A
- size recommendation support
- wardrobe, favorites, and collections
- motion and voice integrations

What still depends on external providers or future hardening:

- try-on, motion, and voice reliability across provider outages
- production deployment hardening
- deeper testing coverage
- more robust sharing, comparison, and collaboration flows

## Why This Repo Exists

Personal styling tools are often either too generic, too transactional, or too visually flat.

MIRA exists to make AI styling feel more personal, more tasteful, and more composed by combining intelligent fashion guidance with an elegant digital experience.
