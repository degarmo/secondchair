"""Load the v1 intake question bank.

Idempotent: ``update_or_create`` keyed on (key, question_set_version), so
re-running refreshes wording and priority without duplicating rows.

Priorities step by 10 so a question can be slotted between two existing
ones later without renumbering the set.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from kb.models import ExtractionTarget, Question, QuestionCategory

QUESTION_SET_VERSION = "v1"
PRIORITY_STEP = 10

OPENER = QuestionCategory.OPENER
ROLE = QuestionCategory.ROLE
PROJECT = QuestionCategory.PROJECT
STORY = QuestionCategory.STORY
SKILL = QuestionCategory.SKILL
CONSTRAINT = QuestionCategory.CONSTRAINT
CLOSER = QuestionCategory.CLOSER

# (key, category, target_model, text) -- order here sets priority.
QUESTIONS = [
    (
        "warmup-current", OPENER, None,
        "In a sentence or two, what do you do right now?",
    ),
    (
        "warmup-looking", OPENER, None,
        "What made you start looking?",
    ),
    (
        "role-list", ROLE, ExtractionTarget.ROLE,
        "Walk me through your work history — company, title, roughly "
        "when, and what the job actually was. Don't polish it.",
    ),
    (
        "role-current-scope", ROLE, ExtractionTarget.ROLE,
        "In your current or most recent role, what were you actually "
        "responsible for day to day? Not the job description — what "
        "landed on you.",
    ),
    (
        "role-ownership", ROLE, ExtractionTarget.ROLE,
        "What in that role would have broken if you'd left suddenly?",
    ),
    (
        "role-transition", ROLE, ExtractionTarget.ROLE,
        "Why did you leave each of those jobs? Take them one at a time.",
    ),
    (
        "role-environment", ROLE, ExtractionTarget.ROLE,
        "What was the team and reporting structure like? Who did you work "
        "with most?",
    ),
    (
        "project-proud", PROJECT, ExtractionTarget.PROJECT,
        "What's something you built that you'd still defend today?",
    ),
    (
        "project-detail", PROJECT, ExtractionTarget.PROJECT,
        "Take that project — what was the actual technical problem? "
        "Walk me through how it worked.",
    ),
    (
        "project-stack", PROJECT, ExtractionTarget.PROJECT,
        "What did you build it with, and why those choices over the "
        "alternatives?",
    ),
    (
        "project-outcome", PROJECT, ExtractionTarget.PROJECT,
        "What changed because that thing existed? Numbers if you have them, "
        "honest guesses if you don't.",
    ),
    (
        "project-independent", PROJECT, ExtractionTarget.PROJECT,
        "What have you built outside of work? Side projects, things for "
        "other people, things that went nowhere.",
    ),
    (
        "project-current", PROJECT, ExtractionTarget.PROJECT,
        "What are you working on right now, even if it's half-finished?",
    ),
    (
        "project-scale", PROJECT, ExtractionTarget.PROJECT,
        "What's the largest system you've worked on, by whatever measure "
        "makes sense — users, data volume, integrations, money moving "
        "through it?",
    ),
    (
        "story-hard-problem", STORY, ExtractionTarget.STORY,
        "Tell me about the hardest technical problem you've solved. What "
        "made it hard?",
    ),
    (
        "story-failure", STORY, ExtractionTarget.STORY,
        "Tell me about something you built or decided that didn't work out. "
        "What happened, and what did you do about it?",
    ),
    (
        "story-conflict", STORY, ExtractionTarget.STORY,
        "Tell me about a time you disagreed with someone about a technical "
        "decision. How did it resolve?",
    ),
    (
        "story-ambiguity", STORY, ExtractionTarget.STORY,
        "Tell me about a time you had to act without enough information.",
    ),
    (
        "story-pressure", STORY, ExtractionTarget.STORY,
        "Tell me about something breaking in production, or the equivalent "
        "in your world. What did you actually do?",
    ),
    (
        "story-influence", STORY, ExtractionTarget.STORY,
        "Tell me about a time you got people to do something differently "
        "without having authority over them.",
    ),
    (
        "story-learning", STORY, ExtractionTarget.STORY,
        "Tell me about something you had to learn fast because a project "
        "depended on it.",
    ),
    (
        "story-boundary", STORY, ExtractionTarget.STORY,
        "Tell me about a time you pushed back on a request. What was the "
        "request and why did you push?",
    ),
    (
        "story-teaching", STORY, ExtractionTarget.STORY,
        "Tell me about a time you brought someone else up to speed on "
        "something complicated.",
    ),
    (
        "story-cleanup", STORY, ExtractionTarget.STORY,
        "Tell me about inheriting a mess. What did you find and what did you "
        "do with it?",
    ),
    (
        "skill-daily", SKILL, ExtractionTarget.SKILL,
        "What do you actually use every day? Languages, frameworks, tools.",
    ),
    (
        "skill-depth", SKILL, ExtractionTarget.SKILL,
        "Of those, which two or three would you say you know deeply, versus "
        "can work in?",
    ),
    (
        "skill-when", SKILL, ExtractionTarget.SKILL,
        "For each of the deep ones — roughly when did you start, and "
        "are you still using it?",
    ),
    (
        "skill-domain", SKILL, ExtractionTarget.SKILL,
        "What domain knowledge do you have that took years to acquire and "
        "would be hard to hire for?",
    ),
    (
        "skill-protocols", SKILL, ExtractionTarget.SKILL,
        "Any standards, protocols, or regulatory frameworks you've worked "
        "inside?",
    ),
    (
        "skill-rusty", SKILL, ExtractionTarget.SKILL,
        "What have you used before that you'd need a week to get back up to "
        "speed on? Be honest — this is more useful than the list of "
        "things you're good at.",
    ),
    (
        "skill-learning-now", SKILL, ExtractionTarget.SKILL,
        "What are you learning right now?",
    ),
    (
        "constraint-location", CONSTRAINT, ExtractionTarget.CONSTRAINT,
        "Where are you, and where would you actually be willing to work?",
    ),
    (
        "constraint-remote", CONSTRAINT, ExtractionTarget.CONSTRAINT,
        "Remote, hybrid, onsite — what do you want and what would you "
        "tolerate?",
    ),
    (
        "constraint-comp", CONSTRAINT, ExtractionTarget.CONSTRAINT,
        "What compensation range are you targeting? Include what you'd need "
        "to move for.",
    ),
    (
        "constraint-role-type", CONSTRAINT, ExtractionTarget.CONSTRAINT,
        "What kinds of roles are you looking at? Titles are fine, but "
        "describe the work if you can.",
    ),
    (
        "constraint-industry", CONSTRAINT, ExtractionTarget.CONSTRAINT,
        "Any industries you want, or want to avoid?",
    ),
    (
        "constraint-dealbreaker", CONSTRAINT, ExtractionTarget.CONSTRAINT,
        "What would make you turn down an otherwise good offer?",
    ),
    (
        "constraint-timeline", CONSTRAINT, ExtractionTarget.CONSTRAINT,
        "How fast are you looking to move?",
    ),
    (
        "closer-missing", CLOSER, None,
        "What haven't I asked about that someone evaluating you should know?",
    ),
    (
        "closer-misread", CLOSER, None,
        "What do people consistently get wrong about you or your background?",
    ),
]


class Command(BaseCommand):
    help = "Load the v1 intake question bank. Safe to run more than once."

    @transaction.atomic
    def handle(self, *args, **options):
        created = updated = 0
        for index, (key, category, target_model, text) in enumerate(QUESTIONS):
            _, was_created = Question.objects.update_or_create(
                key=key,
                question_set_version=QUESTION_SET_VERSION,
                defaults={
                    "text": text,
                    "category": category,
                    "target_model": target_model,
                    "priority": (index + 1) * PRIORITY_STEP,
                    "active": True,
                },
            )
            created += was_created
            updated += not was_created

        total = Question.objects.filter(
            question_set_version=QUESTION_SET_VERSION
        ).count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Question set {QUESTION_SET_VERSION}: {created} created, "
                f"{updated} updated, {total} total."
            )
        )
