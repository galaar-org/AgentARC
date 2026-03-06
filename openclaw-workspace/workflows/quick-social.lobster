name: quick-social
description: Quick social media post creation and publishing

args:
  topic: ""
  platforms: ["twitter", "linkedin"]
  approval_required: true

steps:
  # Stage 1: Generate Social Content
  - id: generate
    command: |
      openclaw.invoke content_machine write social "$topic"
    description: "Generate social-first content"

  # Stage 2: Platform Adaptation
  - id: adapt_twitter
    command: |
      openclaw.invoke social_poster format twitter "$generate.stdout"
    stdin: $generate.stdout
    condition: contains($platforms, "twitter")
    description: "Format for Twitter"

  - id: adapt_linkedin
    command: |
      openclaw.invoke social_poster format linkedin "$generate.stdout"
    stdin: $generate.stdout
    condition: contains($platforms, "linkedin")
    description: "Format for LinkedIn"

  - id: adapt_instagram
    command: |
      openclaw.invoke social_poster format instagram "$generate.stdout"
    stdin: $generate.stdout
    condition: contains($platforms, "instagram")
    description: "Format for Instagram"

  # Stage 3: Quick Fact Check
  - id: verify
    command: |
      openclaw.invoke fact_checker product "$generate.stdout"
    stdin: $generate.stdout
    description: "Quick product claim verification"

  # Stage 4: Humanize
  - id: humanize
    command: |
      openclaw.invoke ai_trace_remover light "$generate.stdout"
    stdin: $verify.stdout
    description: "Light AI pattern removal"

  # Stage 5: Approval (Optional)
  - id: approve
    command: |
      echo "Review social content before posting"
    approval: required
    condition: $approval_required == true
    description: "Human approval"

  # Stage 6: Publish
  - id: publish
    command: |
      openclaw.invoke social_poster all "$humanize.stdout" "$platforms"
    condition: $approve.approved || $approval_required == false
    description: "Publish to all platforms"

  # Stage 7: Log
  - id: log
    command: |
      openclaw.invoke memory_log social "$topic" "$platforms"
    description: "Log for performance tracking"
