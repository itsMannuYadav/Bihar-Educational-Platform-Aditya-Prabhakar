# AI Teaching Companion for Government Schools (Bihar-Focused) — Product Architecture, UX, UI, Features, and Development Instructions

## Project Vision

You are an expert team consisting of:

* Product Manager
* Education Policy Specialist
* Senior Full-Stack Engineer
* AI Engineer
* UI/UX Designer
* Accessibility Expert
* Educational Psychologist
* Government Technology Consultant

Your task is to design and build an AI-powered teaching assistant platform for government and low-resource schools.

This is **not** another student-learning application.

The primary objective is to **improve teaching quality**.

The target users are:

* Government-school teachers
* Contract teachers
* Newly appointed teachers
* Teachers with heavy workloads
* Teachers with limited access to teaching resources

The first prototype should focus on **Bihar's educational ecosystem**, but the architecture must remain generic enough to support other Indian states in the future.

The system must be designed around one fundamental question:

> "How can we help a teacher prepare and deliver a better classroom session in less than 10 minutes?"

---

# Core Product Goals

The platform must:

* Reduce lesson-preparation time.
* Improve teaching quality.
* Standardize classroom delivery.
* Increase student engagement.
* Support bilingual teaching.
* Work in low-resource environments.
* Be usable by teachers with limited technical skills.

---

# Technology Stack

## Frontend

Mandatory technologies:

* Next.js
* TypeScript
* Tailwind CSS
* shadcn/ui

Additional recommendations:

* React Query
* Zustand
* Framer Motion
* React Hook Form
* Zod

---

## Backend

Mandatory technologies:

* Python
* FastAPI

Additional recommendations:

* Pydantic
* LangGraph
* OpenAI SDK
* Google Gemini API
* pgvector

---

## Database

* PostgreSQL

---

## Authentication

* Supabase Authentication

Authentication methods:

* Mobile OTP
* Email OTP
* Google Sign-in

---

## File Storage

* Supabase Storage

---

## Deployment

Frontend:

* Vercel

Backend:

* Railway or Azure

---

# Language Support

The entire platform must support three languages.

Language selector:

* English
* Hindi
* Hinglish

The user must be able to switch languages at any time.

All AI-generated content must support all three languages.

---

# User Types

## Teacher

Permissions:

* Generate content
* Save content
* Download resources

---

## School Administrator

Permissions:

* Manage teachers
* Access analytics

---

## Super Administrator

Permissions:

* Manage schools
* Manage content
* Monitor platform usage

---

# User Interface Requirements

The interface must be extremely simple.

Many teachers will have limited digital experience.

Avoid complicated dashboards.

The design should resemble:

* ChatGPT
* Google NotebookLM
* Modern educational applications

The interface should use large buttons and minimal text.

---

# Dashboard Layout

Top navigation:

* Search
* Library
* My Resources
* Saved Lessons
* Worksheets
* Analytics
* Settings

---

# Hero Section

Display a large search box.

Placeholder examples:

English:

"How should I teach photosynthesis?"

Hindi:

"प्रकाश संश्लेषण कैसे पढ़ाया जाए?"

Hinglish:

"Class 7 ke students ko photosynthesis kaise padhaun?"

---

# Voice Input

Add a microphone icon.

Teachers should be able to ask questions using speech.

Speech-to-text must support:

* Hindi
* English
* Hinglish

---

# Lesson Generation Workflow

Step 1:

Select:

* Class
* Subject
* Chapter
* Language
* Class duration

Class duration options:

* 30 minutes
* 40 minutes
* 60 minutes

---

Step 2:

Click:

Generate Teaching Kit

---

Step 3:

Generate all teaching resources simultaneously.

---

# AI Teaching Kit

The teaching kit must include:

---

## Lesson Plan

Generate:

* Learning objectives
* Introduction
* Core concepts
* Classroom discussion
* Assessment
* Homework

---

## Teaching Script

Generate a teacher-friendly script.

The script must:

* Use simple language.
* Encourage student interaction.
* Include pauses.
* Include classroom questions.

Never generate textbook-style explanations.

Generate actual teaching scripts.

---

## Blackboard Mode

Generate content optimized for board writing.

Example:

Headings

Definitions

Equations

Diagrams

---

## Local Context Generator

Generate Bihar-specific examples whenever possible.

Examples:

* Agriculture
* Rivers
* Villages
* Local crops
* Daily life

Students learn better from familiar examples.

---

## Activity Generator

Generate:

* Classroom activities
* Demonstrations
* Group activities

Activities should require minimal equipment.

---

## Question Generator

Generate:

* MCQs
* Short-answer questions
* Long-answer questions
* Higher-order thinking questions

Difficulty levels:

* Easy
* Moderate
* Advanced

---

## Previous-Year Questions

Generate similar examination questions.

Categorize questions according to difficulty.

---

## Worksheet Generator

Generate printable worksheets.

Include:

* Fill-in-the-blanks
* True/False
* Match-the-following
* Label-the-diagram questions

Allow export to PDF.

---

## PPT Generator

Generate three presentation versions.

Version 1:

5 slides

Version 2:

10 slides

Version 3:

15 slides

Allow:

* PPT download
* PDF download

Design requirements:

* Modern
* Educational
* Large fonts
* Teacher-friendly layouts

---

## Canva Integration

The architecture should support future Canva integration.

The generated slide content should be structured in a way that it can later be exported to Canva templates.

Do not tightly couple presentation generation to a single provider.

Create an abstraction layer.

---

## Mind Maps

Generate interactive mind maps.

Allow:

* Zooming
* Printing
* Downloading

---

## Flowcharts

Generate interactive flowcharts.

Support:

* SVG export
* PNG export

---

## Diagram Generator

Generate educational diagrams.

Examples:

* Plant cells
* Water cycles
* Food chains

---

## Audio Generation

Generate:

1-minute explanation

3-minute explanation

5-minute explanation

Allow:

* Play
* Pause
* Download

This feature should be prioritized over video generation.

---

## Animation Generator

Instead of AI-generated videos, create lightweight educational animations.

Generate:

* Animated diagrams
* Animated SVGs
* Step-by-step concept animations

Avoid expensive AI-generated video generation.

---

# Video Generation

Do not implement video generation.

Instead, display:

"Coming Soon"

The UI component should already exist.

The feature should be disabled.

---

# Teaching Modes

Add multiple teaching styles.

Modes:

* Story Mode
* Activity Mode
* Exam Mode
* Concept Mode
* Quick Revision Mode

---

# AI Teaching Personas

Do not imitate any individual educator.

Instead, extract general teaching characteristics.

Teaching characteristics:

* Storytelling
* Analogies
* Interactive questioning
* Humor
* Local examples
* Visual explanations

Avoid copying any specific teacher.

---

# Resource Caching

This is mandatory.

If one teacher generates:

Class 7 → Science → Photosynthesis → Hindi

Store the result.

If another teacher requests the same combination:

Serve the cached version.

Avoid unnecessary AI calls.

Implement aggressive caching.

---

# Offline Support

The platform should function in environments with unstable internet.

Cache:

* Lesson plans
* Worksheets
* PPTs
* Audio

Use Progressive Web App capabilities.

---

# Analytics Dashboard

Track:

* Most searched topics
* Most generated resources
* Frequently used subjects
* Teacher engagement

---

# Accessibility

Requirements:

* Large text
* High contrast
* Keyboard navigation
* Screen-reader compatibility

---

# Design System

Theme:

Warm and welcoming.

Avoid a corporate appearance.

Suggested colors:

* Orange
* White
* Soft gray

Design principles:

* Minimalism
* Large touch targets
* Simple navigation

---

# Mobile-First Design

Primary target:

Android smartphones.

Secondary target:

Desktop.

Optimize every screen for mobile devices.

---

# MVP Requirements

The first prototype must include only:

* Topic search
* Teaching-kit generation
* Lesson plans
* Teaching scripts
* Quiz generation
* Worksheets
* PPT generation
* Mind maps
* Audio generation
* Voice input

Everything else should be designed but not fully implemented.

---

# Development Instructions

Create the project incrementally.

Phase 1:

Project setup

Phase 2:

Authentication

Phase 3:

Database

Phase 4:

Teaching-kit generation

Phase 5:

Audio generation

Phase 6:

PPT generation

Phase 7:

Caching

Phase 8:

Testing

Phase 9:

Deployment

---

# Final Deliverables

Generate:

* Complete project architecture
* Database schema
* API design
* Folder structure
* UI wireframes
* User flows
* Component hierarchy
* Development roadmap
* Complete implementation plan

Do not immediately generate code.

Think like a senior architect.

Plan first.

Then implement the project module by module.
