name: full-content-pipeline
description: Complete content pipeline from research to multi-platform publishing

args:
  topic: ""
  content_type: "blog"  # blog, tutorial, case-study, comparison
  platforms: ["twitter", "linkedin", "wordpress"]

steps:
  # Stage 1: Research
  - id: research
    command: |
      openclaw.invoke content_machine research "$topic"
    description: "Deep research on topic"

  # Stage 2: Generate Ideas
  - id: ideas
    command: |
      openclaw.invoke content_machine ideas "$topic" 5
    stdin: $research.stdout
    description: "Generate content ideas from research"

  # Stage 3: Select Best Idea (Human Approval)
  - id: select_idea
    command: |
      echo "Review ideas and select the best one for $content_type"
    stdin: $ideas.stdout
    approval: required
    description: "Human selects best content idea"

  # Stage 4: Write Long-Form Content
  - id: write_draft
    command: |
      openclaw.invoke content_machine write "$content_type" "$topic"
    condition: $select_idea.approved
    description: "Write full draft"

  # Stage 5: Fact Check
  - id: fact_check
    command: |
      openclaw.invoke fact_checker "$write_draft.stdout"
    stdin: $write_draft.stdout
    description: "Verify all claims"

  # Stage 6: SEO Optimize
  - id: seo_optimize
    command: |
      openclaw.invoke seo_optimizer optimize "$write_draft.stdout"
    stdin: $fact_check.stdout
    description: "Optimize for search engines"

  # Stage 7: Humanize Content
  - id: humanize
    command: |
      openclaw.invoke ai_trace_remover humanize "$seo_optimize.stdout"
    stdin: $seo_optimize.stdout
    description: "Remove AI patterns"

  # Stage 8: Score Content
  - id: score
    command: |
      openclaw.invoke content_machine score "$humanize.stdout"
    stdin: $humanize.stdout
    description: "Quality score check"

  # Stage 9: Repurpose for Platforms
  - id: repurpose
    command: |
      openclaw.invoke content_machine repurpose "$humanize.stdout"
    stdin: $humanize.stdout
    description: "Create platform-specific versions"

  # Stage 10: Final Review (Human Approval)
  - id: final_review
    command: |
      echo "Review all content versions before publishing"
    stdin: $repurpose.stdout
    approval: required
    description: "Final human approval before publishing"

  # Stage 11: Publish to WordPress
  - id: publish_wordpress
    command: |
      openclaw.invoke wordpress_publisher publish "$humanize.stdout"
    condition: $final_review.approved && contains($platforms, "wordpress")
    description: "Publish blog post"

  # Stage 12: Publish to Twitter
  - id: publish_twitter
    command: |
      openclaw.invoke social_poster twitter "$repurpose.twitter"
    condition: $final_review.approved && contains($platforms, "twitter")
    description: "Post Twitter thread"

  # Stage 13: Publish to LinkedIn
  - id: publish_linkedin
    command: |
      openclaw.invoke social_poster linkedin "$repurpose.linkedin"
    condition: $final_review.approved && contains($platforms, "linkedin")
    description: "Post to LinkedIn"

  # Stage 14: Log to Memory
  - id: log_performance
    command: |
      openclaw.invoke memory_log content "$topic" "$platforms"
    description: "Log published content for tracking"

env:
  CONTENT_TYPE: "$content_type"
  TOPIC: "$topic"
