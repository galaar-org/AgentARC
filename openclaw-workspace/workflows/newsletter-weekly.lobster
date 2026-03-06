name: newsletter-weekly
description: Weekly newsletter creation with curated content

args:
  week_of: ""  # YYYY-MM-DD
  sections: ["product_updates", "tutorials", "industry_news", "community"]

steps:
  # Stage 1: Gather Product Updates
  - id: product_updates
    command: |
      openclaw.invoke content_machine research "AgentARC updates this week"
    condition: contains($sections, "product_updates")
    description: "Gather product updates"

  # Stage 2: Gather Tutorial Content
  - id: tutorials
    command: |
      openclaw.invoke content_machine research "AgentARC tutorials published"
    condition: contains($sections, "tutorials")
    description: "Gather tutorial content"

  # Stage 3: Industry News Scan
  - id: industry_news
    command: |
      openclaw.invoke competitor_tracker news week
    condition: contains($sections, "industry_news")
    description: "Scan AI agent security news"

  # Stage 4: Community Highlights
  - id: community
    command: |
      openclaw.invoke content_machine research "AgentARC community GitHub Discord"
    condition: contains($sections, "community")
    description: "Gather community highlights"

  # Stage 5: Compile Newsletter
  - id: compile
    command: |
      openclaw.invoke content_machine write newsletter "$week_of"
    stdin: |
      Product Updates: $product_updates.stdout
      Tutorials: $tutorials.stdout
      Industry News: $industry_news.stdout
      Community: $community.stdout
    description: "Compile newsletter content"

  # Stage 6: SEO Subject Lines
  - id: subject_lines
    command: |
      openclaw.invoke content_machine ideas "newsletter subject line" 5
    description: "Generate subject line options"

  # Stage 7: Review & Approval
  - id: review
    command: |
      echo "Review newsletter content and select subject line"
    stdin: |
      Content: $compile.stdout
      Subject Lines: $subject_lines.stdout
    approval: required
    description: "Human review and subject line selection"

  # Stage 8: Send Newsletter
  - id: send
    command: |
      openclaw.invoke newsletter_sender "$compile.stdout" "$review.selected_subject"
    condition: $review.approved
    description: "Send newsletter"

  # Stage 9: Log
  - id: log
    command: |
      openclaw.invoke memory_log newsletter "$week_of"
    description: "Log newsletter for tracking"

env:
  NEWSLETTER_WEEK: "$week_of"
